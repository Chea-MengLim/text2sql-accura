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
            
            result_str = json.dumps(sql_result[:20], default=str, indent=2)
            prompt = self._build_chart_prompt(user_question, sql_query, result_str)
            
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
    
    def _build_chart_prompt(self, question: str, query: str, response: str) -> str:
        """Build chart generation prompt for shadcn/Recharts format"""
        return f"""You are a data visualization assistant. Generate chart specifications for suitable data.

User Input:
{question}

SQL Query:
{query}

SQL Result:
{response}

DECISION LOGIC:
- If data has 2+ rows with meaningful categories/values → GENERATE CHART
- If data is single count/aggregate → RESPOND "no"
- If user explicitly asks for chart → GENERATE CHART (if data allows)

YOUR DATA ANALYSIS:
- Number of rows: Multiple rows detected
- Data type: Time series data (years)
- Suitable for chart: YES - This is perfect for a bar chart

RESPONSE FORMAT:
If suitable, generate JSON:
{{
    "chart_type": "bar chart",
    "data": [
        {{"name": "2023", "total_profit_in_krw": 52065005448.76}},
        {{"name": "2024", "total_profit_in_krw": 58483971661.00}}
    ],
    "config": {{
        "total_profit_in_krw": {{"label": "Total Profit (KRW)"}}
    }},
    "explain": "Profit comparison by year"
}}

If NOT suitable, respond: "no"

NAMING RULES:
- Use actual field values in "name" (years, categories, etc.)
- Keep numeric values as numbers (not strings)
- Use meaningful field names for values

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
                
                chart_data.append({
                    "name": name_value,
                    value_field: value_value
                })
            
            if not chart_data:
                return None
            
            # Determine chart type based on data
            chart_type = "bar chart"
            if 'year' in name_field.lower() or 'month' in name_field.lower() or 'date' in name_field.lower():
                chart_type = "line chart" if len(chart_data) > 5 else "bar chart"
            
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