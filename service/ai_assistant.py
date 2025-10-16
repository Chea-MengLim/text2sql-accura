import httpx
from typing import List, Dict, Any, Optional
import logging
import json
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class AIAssistant:
    """Unified Llama model via Ollama for explanations and chart generation"""
    
    def __init__(self, model_name: str = "llama3.1:8b", host: str = "http://localhost:11434"):
        self.model_name = model_name
        self.host = host
        logger.info(f"Using Ollama model: {model_name} at {host}")
        
        # Verify model is available
        try:
            import ollama
            ollama.show(model_name)
            logger.info(f"Model {model_name} is ready")
        except Exception as e:
            logger.error(f"Model {model_name} not found. Run: ollama pull {model_name}")
            raise
    
    async def _ollama_generate(self, prompt: str, options: dict) -> str:
        """Async Ollama generation via HTTP"""
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self.host}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": options
                }
            )
            
            if resp.status_code != 200:
                raise Exception(f"Ollama error: {resp.text}")
            
            data = resp.json()
            return (data.get("response") or "").strip()
    
    async def explain_result(
        self,
        user_question: str,
        sql_query: str,
        result_data: List[Dict[str, Any]]
    ) -> str:
        """Generate natural language explanation of query results"""
        try:
            if not result_data:
                return "No results were found for your query."
            
            row_count = len(result_data)
            
            # For large datasets, use statistical summary instead of raw data
            if row_count > 50:
                summary = self._generate_statistical_summary(result_data)
                sample_results = result_data[:5]  # Just a small sample for context
                
                prompt = f"""You are a helpful database assistant. Explain this query result clearly and concisely.

User's Question: {user_question}

SQL Query:
{sql_query}

DATASET SUMMARY:
- Total Records: {summary['total_records']}
- Columns: {', '.join(summary['columns'])}

STATISTICAL INSIGHTS:
{json.dumps(summary['statistics'], indent=2, default=str)}

SAMPLE DATA (first 5 of {row_count} records):
{json.dumps(sample_results, indent=2, default=str)}

Provide a clear explanation that:
1. Directly answers the user's question
2. Highlights key statistical insights from the data
3. Mentions important numbers, trends, or patterns
4. Keep it concise (2-3 sentences)
5. Focus on the statistical summary rather than individual records

Explanation:"""
            else:
                # For smaller datasets, use existing approach
                sample_results = result_data[:3] if row_count > 3 else result_data
                results_str = json.dumps(sample_results, indent=2, default=str)
                
                prompt = f"""You are a helpful database assistant. Explain this query result clearly and concisely.

User's Question: {user_question}

SQL Query:
{sql_query}

Query Results (showing {len(sample_results)} of {row_count} records):
{results_str}

Provide a clear explanation that:
1. Directly answers the user's question
2. Highlights key insights from the data
3. Mentions important numbers or values
4. Keep it concise (2-3 sentences)

Explanation:"""
            
            explanation = await self._ollama_generate(
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 250,  # max tokens
                    "num_gpu": -1,       # ← Use ALL GPU layers
                    "num_thread": 1,     # ← Minimize CPU threads
                    "num_batch": 512,    # ← Larger batch for GPU efficiency
                }
            )
            
            logger.info(f"Generated explanation: {explanation[:100]}...")
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {str(e)}")
            return f"Found {len(result_data)} record(s) matching your criteria."
    
    def _generate_statistical_summary(self, result_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate statistical summary of large datasets"""
        if not result_data:
            return {}
        
        summary = {
            "total_records": len(result_data),
            "sample_size": min(10, len(result_data)),
            "columns": list(result_data[0].keys()) if result_data else [],
            "statistics": {}
        }
        
        # Generate statistics for numeric columns
        for col in summary["columns"]:
            values = [row.get(col) for row in result_data if row.get(col) is not None]
            if values:
                try:
                    # More robust numeric detection
                    numeric_values = []
                    for v in values:
                        try:
                            # Try to convert to float
                            float_val = float(v)
                            numeric_values.append(float_val)
                        except (ValueError, TypeError):
                            # Check if it's a string that looks like a number
                            str_v = str(v).strip()
                            if str_v.replace('.', '').replace('-', '').replace('+', '').isdigit():
                                numeric_values.append(float(str_v))
                    
                    if numeric_values:
                        summary["statistics"][col] = {
                            "min": min(numeric_values),
                            "max": max(numeric_values),
                            "avg": sum(numeric_values) / len(numeric_values),
                            "sum": sum(numeric_values),
                            "count": len(numeric_values)
                        }
                except:
                    # Non-numeric column
                    unique_values = list(set(str(v) for v in values))
                    summary["statistics"][col] = {
                        "unique_count": len(unique_values),
                        "top_values": unique_values[:5]  # Top 5 unique values
                    }
        
        return summary

    def _smart_sample_for_chart(self, sql_result: List[Dict[str, Any]], max_samples: int = 50) -> List[Dict[str, Any]]:
        """Intelligently sample data for chart generation"""
        if len(sql_result) <= max_samples:
            return sql_result
        
        # For time series data, try to preserve temporal distribution
        first_row = sql_result[0]
        keys = list(first_row.keys())
        
        # Check if we have a time-related column
        time_column = None
        for key in keys:
            if any(word in key.lower() for word in ['date', 'time', 'year', 'month', 'day']):
                time_column = key
                break
        
        if time_column:
            # For time series, sample evenly across the time range
            step = len(sql_result) // max_samples
            sampled = [sql_result[i] for i in range(0, len(sql_result), step)][:max_samples]
            
            # Always include first and last records
            if sampled[0] != sql_result[0]:
                sampled.insert(0, sql_result[0])
            if sampled[-1] != sql_result[-1]:
                sampled.append(sql_result[-1])
            
            return sampled[:max_samples]
        else:
            # For non-time series, use random sampling with statistical representation
            import random
            # Ensure we get a good mix: first few, last few, and random middle
            sample_size = max_samples
            first_n = min(5, sample_size // 3)
            last_n = min(5, sample_size // 3)
            middle_n = sample_size - first_n - last_n
            
            sampled = []
            sampled.extend(sql_result[:first_n])
            sampled.extend(sql_result[-last_n:])
            
            if middle_n > 0 and len(sql_result) > first_n + last_n:
                middle_start = first_n
                middle_end = len(sql_result) - last_n
                middle_indices = random.sample(range(middle_start, middle_end), 
                                             min(middle_n, middle_end - middle_start))
                sampled.extend([sql_result[i] for i in sorted(middle_indices)])
            
            return sampled[:max_samples]

    def _is_data_suitable_for_chart(self, sql_result: List[Dict[str, Any]], user_question: str) -> bool:
        """Pre-analyze if data is suitable for charting without calling AI"""
        if not sql_result or len(sql_result) == 0:
            return False
        
        # Check for single count/aggregate results
        if len(sql_result) == 1:
            row = sql_result[0]
            # Single row with count-like fields
            count_fields = ['count', 'total', 'sum', 'total_tables', 'total_count', 'num_tables']
            if any(field in str(row).lower() for field in count_fields):
                logger.info("Single count result - not suitable for charting")
                return False
            
            # Single row with only one value
            if len(row) == 1:
                logger.info("Single value result - not suitable for charting")
                return False
        
        # Check for database metadata queries
        metadata_keywords = ['table', 'schema', 'database', 'count(*)', 'information_schema']
        if any(keyword in user_question.lower() for keyword in metadata_keywords):
            logger.info("Database metadata query - not suitable for charting")
            return False
        
        # Check if we have meaningful data to visualize
        if len(sql_result) < 2:
            logger.info("Less than 2 data points - not suitable for charting")
            return False
        
        return True

    async def generate_chart_spec(
        self,
        user_question: str,
        sql_query: str,
        sql_result: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Generate chart specification from SQL results"""
        try:
            if not sql_result:
                return None
            
            # Pre-analyze if data is suitable for charting
            if not self._is_data_suitable_for_chart(sql_result, user_question):
                logger.info("Data pre-analysis: not suitable for charting")
                return None
            
            # Smart sampling for large datasets
            if len(sql_result) > 50:
                sampled_data = self._smart_sample_for_chart(sql_result, max_samples=50)
                summary_info = f" (sampled from {len(sql_result)} total records)"
            else:
                sampled_data = sql_result
                summary_info = ""
            
            result_str = json.dumps(sampled_data, default=str, indent=2)
            prompt = self._build_chart_prompt(user_question, sql_query, result_str, summary_info)
            
            answer = await self._ollama_generate(
                prompt=prompt,
                options={
                    "temperature": 0.3,  # Lower for consistent JSON
                    "num_predict": 800,
                    "num_gpu": -1,       # ← Use ALL GPU layers
                    "num_thread": 1,     # ← Minimize CPU threads
                    "num_batch": 512,    # ← Larger batch for GPU efficiency
                }
            )
            
            # Debug: Log the AI response
            logger.info(f"AI chart response: {answer[:200]}...")
            
            # Check if response is "no"
            if answer.lower().strip().strip('"\'') == "no":
                logger.info("AI determined: no suitable chart for this data")
                return None
            
            # Extract and validate JSON
            chart_spec = self._extract_json(answer)
            
            if chart_spec and self._validate_chart_spec(chart_spec):
                # Post-process to format dates if needed
                chart_spec = self._post_process_chart_dates(chart_spec)
                logger.info(f"Generated chart spec: {chart_spec['chart_type']}")
                return chart_spec
            else:
                logger.warning("AI failed to generate valid chart, trying fallback...")
                # Fallback: Generate simple chart for common patterns
                fallback_chart = self._generate_fallback_chart(sql_result, user_question)
                if fallback_chart:
                    logger.info("Fallback chart generated successfully")
                    return fallback_chart
                else:
                    logger.warning("No chart specification generated")
                    return None
                
        except Exception as e:
            logger.error(f"Chart generation failed: {str(e)}")
            return None
    
    def _build_chart_prompt(self, question: str, query: str, response: str, summary_info: str = "") -> str:
        """Build chart generation prompt for shadcn/Recharts format"""
        return f"""You are a data visualization assistant. Generate chart specifications for suitable data.

User Input:
{question}

SQL Query:
{query}

SQL Result{summary_info}:
{response}

IMPORTANT: This data may be sampled from a larger dataset. Focus on the patterns and trends visible in the provided data.

DECISION LOGIC:
- If data has 2+ rows with meaningful categories/values → GENERATE CHART
- If data is single count/aggregate → RESPOND "no"
- If user explicitly asks for chart → GENERATE CHART (if data allows)

CHART TYPE SELECTION RULES:
- Time series data (dates, years, months) with 5+ data points → LINE CHART
- Time series data with <5 data points → BAR CHART
- Categorical data (names, types, categories) → BAR CHART
- Proportions/percentages → PIE CHART
- Cumulative trends over time → AREA CHART

YOUR DATA ANALYSIS:
- Number of rows: Multiple rows detected
- Data type: Analyze the data structure to determine if it's time series or categorical
- Chart type: Choose appropriate chart type based on data pattern

RESPONSE FORMAT:
If suitable, generate JSON:
{{
    "chart_type": "line chart",  // or "bar chart", "pie chart", "area chart"
    "data": [
        {{"name": "Jan 01, 2025", "total_sale_amt": 10154732}},
        {{"name": "Jan 02, 2025", "total_sale_amt": 47969005}}
    ],
    "config": {{
        "total_sale_amt": {{"label": "Total Sale Amount"}}
    }},
    "explain": "Daily total sale amount by date"
}}

If NOT suitable, respond: "no"

NAMING RULES:
- Use actual field values in "name" (years, categories, etc.)
- Keep numeric values as numbers (not strings)
- Use meaningful field names for values
- Format dates in human-readable format (e.g., "Jan 01, 2025" instead of "20250101")

Generate chart specification:"""
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from response"""
        try:
            return json.loads(text)
        except:
            # Try to find JSON in text
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(0))
                except:
                    pass
        return None
    
    def _format_date_string(self, date_str: str) -> str:
        """
        Format date strings to be human-readable
        
        Converts:
        - YYYYMMDD (20241231) -> Dec 31, 2024
        - YYYYMM (202412) -> Dec 2024
        - YYYY (2024) -> 2024 (unchanged)
        """
        # Remove any non-digit characters
        date_digits = re.sub(r'\D', '', str(date_str))
        
        try:
            # YYYYMMDD format (8 digits)
            if len(date_digits) == 8:
                date_obj = datetime.strptime(date_digits, '%Y%m%d')
                return date_obj.strftime('%b %d, %Y')  # e.g., "Dec 31, 2024"
            
            # YYYYMM format (6 digits)
            elif len(date_digits) == 6:
                date_obj = datetime.strptime(date_digits, '%Y%m')
                return date_obj.strftime('%b %Y')  # e.g., "Dec 2024"
            
            # YYYY format (4 digits) - return as-is
            elif len(date_digits) == 4:
                return date_digits
            
            # Not a recognized date format
            else:
                return str(date_str)
        
        except ValueError:
            # If parsing fails, return original string
            return str(date_str)
    
    def _post_process_chart_dates(self, chart_spec: Dict) -> Dict:
        """
        Post-process chart specification to format dates in 'name' fields
        This is a fallback if the AI doesn't format dates properly
        """
        if not chart_spec or "data" not in chart_spec:
            return chart_spec
        
        for item in chart_spec["data"]:
            if "name" in item:
                name = str(item["name"])
                
                # Check if name looks like a date (all digits, 4-8 chars)
                if re.match(r'^\d{4,8}$', name):
                    formatted = self._format_date_string(name)
                    if formatted != name:
                        logger.info(f"Formatted date: {name} -> {formatted}")
                        item["name"] = formatted
        
        return chart_spec
    
    def _validate_chart_spec(self, spec: Dict) -> bool:
        """Validate chart specification has required fields for shadcn/Recharts"""
        # Check required fields
        if not all(field in spec for field in ["chart_type", "data", "explain"]):
            return False
        
        # Validate data array is not empty
        if not isinstance(spec["data"], list) or len(spec["data"]) == 0:
            return False
        
        # Validate each data object has a "name" field (Recharts requirement)
        for item in spec["data"]:
            if not isinstance(item, dict) or "name" not in item:
                logger.warning(f"Invalid data item: {item} - missing 'name' field")
                return False
        
        return True
    
    def _generate_fallback_chart(self, sql_result: List[Dict[str, Any]], user_question: str) -> Optional[Dict[str, Any]]:
        """Generate a simple chart specification for common data patterns"""
        try:
            if not sql_result or len(sql_result) < 2:
                return None
            
            # Get the first row to understand the structure
            first_row = sql_result[0]
            keys = list(first_row.keys())
            
            # Find potential name and value fields
            name_field = None
            value_field = None
            
            # Look for common patterns
            for key in keys:
                key_lower = key.lower()
                if any(word in key_lower for word in ['year', 'month', 'date', 'name', 'category', 'type']):
                    name_field = key
                elif any(word in key_lower for word in ['total', 'sum', 'count', 'amount', 'value', 'profit', 'sales', 'revenue']):
                    value_field = key
            
            # If we can't find clear patterns, use first two fields
            if not name_field or not value_field:
                if len(keys) >= 2:
                    name_field = keys[0]
                    value_field = keys[1]
                else:
                    return None
            
            # Generate chart data
            chart_data = []
            for row in sql_result:
                name_value = str(row.get(name_field, ''))
                value_value = row.get(value_field, 0)
                
                # Convert string numbers to float if needed
                if isinstance(value_value, str):
                    try:
                        value_value = float(value_value)
                    except ValueError:
                        continue
                
                # Format date strings if they look like dates
                formatted_name = self._format_date_string(name_value)
                
                chart_data.append({
                    "name": formatted_name,
                    value_field: value_value
                })
            
            if not chart_data:
                return None
            
            # Determine chart type based on data
            chart_type = "bar chart"
            
            # Check if this is time series data
            is_time_series = False
            name_field_lower = name_field.lower()
            
            # Check for time-related field names
            time_keywords = ['year', 'month', 'date', 'day', 'time', 'period', 'quarter', 'week']
            if any(keyword in name_field_lower for keyword in time_keywords):
                is_time_series = True
            
            # Check if the data values look like dates (YYYYMMDD, YYYY-MM-DD, etc.)
            if not is_time_series and chart_data:
                sample_name = str(chart_data[0].get('name', ''))
                # Check for date patterns
                import re
                date_patterns = [
                    r'^\d{{8}}$',  # YYYYMMDD
                    r'^\d{{4}}-\d{{2}}-\d{{2}}$',  # YYYY-MM-DD
                    r'^\d{{4}}\d{{2}}$',  # YYYYMM
                    r'^\d{{4}}$'  # YYYY
                ]
                if any(re.match(pattern, sample_name) for pattern in date_patterns):
                    is_time_series = True
            
            # Choose chart type based on time series detection and data points
            if is_time_series:
                chart_type = "line chart" if len(chart_data) > 5 else "bar chart"
            else:
                chart_type = "bar chart"
            
            # Generate config
            config = {value_field: {"label": value_field.replace('_', ' ').title()}}
            
            # Generate explanation
            explain = f"{value_field.replace('_', ' ').title()} by {name_field.replace('_', ' ').title()}"
            
            return {
                "chart_type": chart_type,
                "data": chart_data,
                "config": config,
                "explain": explain
            }
            
        except Exception as e:
            logger.error(f"Fallback chart generation failed: {str(e)}")
            return None