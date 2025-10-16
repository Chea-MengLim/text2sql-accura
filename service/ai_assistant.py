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
                use_usd = self._user_requests_usd(user_question)
                currency = "USD ($)" if use_usd else "KRW (₩)"
                
                prompt = f"""You are a helpful database assistant. Explain this query result clearly and concisely.

User's Question: {user_question}

SQL Query:
{sql_query}

DATASET SUMMARY:
- Total Records: {summary['total_records']}
- Columns: {', '.join(summary['columns'])}

STATISTICAL INSIGHTS (pre-formatted with correct scale):
{json.dumps(summary['statistics'], indent=2, default=str)}

SAMPLE DATA (first 5 of {row_count} records):
{json.dumps(sample_results, indent=2, default=str)}

CRITICAL: The statistical insights above are already pre-formatted with correct scale abbreviations (K, M, B, T).
Use these EXACT formatted values in your explanation. DO NOT reformat or reinterpret them.

CURRENCY RULES:
- Use {currency} for all monetary values
- {"Use USD with exchange rate: 1 KRW = 0.00070 USD" if use_usd else "Use KRW by default - this is Korean financial data"}
- Always include the currency symbol ({"$" if use_usd else "₩"})
- Use the pre-formatted scale values from statistical insights exactly as shown (e.g., "207.9M ₩", "124.65M ₩")

Provide a clear explanation that:
1. Directly answers the user's question
2. Highlights key statistical insights from the data
3. Mentions important numbers, trends, or patterns
4. Keep it concise (2-3 sentences)
5. Focus on the statistical summary rather than individual records
6. Use the correct currency ({currency})
7. DO NOT include markdown tables, code blocks, or raw data formatting
8. Write in natural, conversational language
9. Use consistent currency formatting (e.g., "2.045M ₩" for 2,045,000, NOT "2.045B ₩")

Explanation:"""
            else:
                # For smaller datasets, still provide statistical context
                summary = self._generate_statistical_summary(result_data)
                sample_results = result_data[:3] if row_count > 3 else result_data
                use_usd = self._user_requests_usd(user_question)
                currency = "USD ($)" if use_usd else "KRW (₩)"
                
                prompt = f"""You are a helpful database assistant. Explain this query result clearly and concisely.

User's Question: {user_question}

SQL Query:
{sql_query}

DATASET SUMMARY:
- Total Records: {summary['total_records']}
- Columns: {', '.join(summary['columns'])}

STATISTICAL INSIGHTS (pre-formatted with correct scale):
{json.dumps(summary['statistics'], indent=2, default=str)}

SAMPLE DATA (first {len(sample_results)} of {row_count} records):
{json.dumps(sample_results, indent=2, default=str)}

CRITICAL: The statistical insights above are already pre-formatted with correct scale abbreviations (K, M, B, T).
Use these EXACT formatted values in your explanation. DO NOT reformat or reinterpret them.

CURRENCY RULES:
- Use {currency} for all monetary values
- {"Use USD with exchange rate: 1 KRW = 0.00070 USD" if use_usd else "Use KRW by default - this is Korean financial data"}
- Always include the currency symbol ({"$" if use_usd else "₩"})
- Use the pre-formatted scale values from statistical insights exactly as shown (e.g., "207.9M ₩", "124.65M ₩")

Provide a clear explanation that:
1. Directly answers the user's question
2. Highlights key statistical insights from the data
3. Mentions important numbers, patterns, or trends
4. Keep it concise (2-3 sentences)
5. Use the correct currency ({currency})
6. DO NOT include markdown tables, code blocks, or raw data formatting
7. Write in natural, conversational language
8. Use consistent currency formatting (e.g., "2.045M ₩" for 2,045,000, NOT "2.045B ₩")

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
            
            # Debug: Log data consistency info
            if row_count > 0:
                logger.info(f"Data consistency check - Records: {row_count}, Columns: {list(result_data[0].keys()) if result_data else []}")
                if summary.get('statistics'):
                    for col, stats in summary['statistics'].items():
                        if isinstance(stats, dict) and 'min' in stats and 'max' in stats:
                            logger.info(f"Column {col}: min={stats['min']}, max={stats['max']}, avg={stats.get('avg', 'N/A')}")
                            # Log raw vs formatted values for debugging
                            if '_raw_max' in stats:
                                logger.info(f"  → Raw max: {stats['_raw_max']} → Formatted: {stats['max']}")
                                # Log scale detection for debugging
                                raw_max = stats['_raw_max']
                                if raw_max >= 1_000_000_000_000:
                                    logger.info(f"  → Scale: TRILLIONS (T) - value has 13+ digits")
                                elif raw_max >= 1_000_000_000:
                                    logger.info(f"  → Scale: BILLIONS (B) - value has 10-12 digits")
                                elif raw_max >= 1_000_000:
                                    logger.info(f"  → Scale: MILLIONS (M) - value has 7-9 digits")
                                elif raw_max >= 1_000:
                                    logger.info(f"  → Scale: THOUSANDS (K) - value has 4-6 digits")
            
            return explanation
            
        except Exception as e:
            logger.error(f"Failed to generate explanation: {str(e)}")
            return f"Found {len(result_data)} record(s) matching your criteria."
    
    def _user_requests_usd(self, user_question: str) -> bool:
        """Check if user specifically requests USD currency"""
        usd_keywords = ['usd', 'dollar', '$', 'us dollars', 'american currency']
        return any(keyword in user_question.lower() for keyword in usd_keywords)
    
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
                        # Calculate additional statistical insights
                        sorted_values = sorted(numeric_values)
                        n = len(sorted_values)
                        
                        # Calculate percentiles for better insights
                        p25 = sorted_values[int(n * 0.25)] if n > 0 else 0
                        p50 = sorted_values[int(n * 0.5)] if n > 0 else 0  # median
                        p75 = sorted_values[int(n * 0.75)] if n > 0 else 0
                        
                        # Format values for better AI understanding
                        def format_currency_value(value: float, is_currency: bool = True) -> str:
                            """Format currency values with proper scale abbreviations"""
                            if is_currency:
                                if value >= 1_000_000_000_000:
                                    return f"{value/1_000_000_000_000:.1f}T"
                                elif value >= 1_000_000_000:
                                    return f"{value/1_000_000_000:.1f}B"
                                elif value >= 1_000_000:
                                    return f"{value/1_000_000:.1f}M"
                                elif value >= 1_000:
                                    return f"{value/1_000:.1f}K"
                                else:
                                    return f"{value:.2f}"
                            else:
                                if value >= 1_000_000_000:
                                    return f"{value/1_000_000_000:.1f}B"
                                elif value >= 1_000_000:
                                    return f"{value/1_000_000:.1f}M"
                                elif value >= 1_000:
                                    return f"{value/1_000:.1f}K"
                                else:
                                    return f"{value:.2f}"
                        
                        # Check if this is a currency column
                        col_lower = col.lower()
                        is_currency_col = any(word in col_lower for word in ['amt', 'amount', 'price', 'cost', 'value', 'total', 'sale'])
                        
                        summary["statistics"][col] = {
                            "min": format_currency_value(min(numeric_values), is_currency_col),
                            "max": format_currency_value(max(numeric_values), is_currency_col),
                            "avg": format_currency_value(round(sum(numeric_values) / len(numeric_values), 2), is_currency_col),
                            "median": format_currency_value(p50, is_currency_col),
                            "p25": format_currency_value(p25, is_currency_col),
                            "p75": format_currency_value(p75, is_currency_col),
                            "sum": format_currency_value(sum(numeric_values), is_currency_col),
                            "count": len(numeric_values),
                            "range": format_currency_value(max(numeric_values) - min(numeric_values), is_currency_col),
                            # Keep raw values for debugging
                            "_raw_min": min(numeric_values),
                            "_raw_max": max(numeric_values),
                            "_raw_avg": round(sum(numeric_values) / len(numeric_values), 2),
                            "_raw_sum": sum(numeric_values)
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
            
            # Check if user requests USD
            use_usd = self._user_requests_usd(user_question)
            
            # Pre-analyze if data is suitable for charting
            if not self._is_data_suitable_for_chart(sql_result, user_question):
                logger.info("Data pre-analysis: not suitable for charting")
                return None
            
            # Smart sampling for large datasets with statistical context
            if len(sql_result) > 50:
                sampled_data = self._smart_sample_for_chart(sql_result, max_samples=50)
                summary_info = f" (sampled from {len(sql_result)} total records)"
                
                # Add statistical summary to prevent context overflow
                stats = self._generate_statistical_summary(sql_result)
                stats_info = f"\n\nSTATISTICAL CONTEXT:\n{json.dumps(stats, indent=2, default=str)}"
            else:
                sampled_data = sql_result
                summary_info = ""
                stats_info = ""
            
            result_str = json.dumps(sampled_data, default=str, indent=2)
            prompt = self._build_chart_prompt(user_question, sql_query, result_str, summary_info + stats_info, use_usd)
            
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
    
    async def generate_follow_up_questions(
        self,
        user_question: str,
        sql_query: str,
        result_data: List[Dict[str, Any]],
        execution_success: bool,
        error_message: Optional[str] = None
    ) -> List[str]:
        """Generate follow-up questions based on query results and data availability"""
        try:
            follow_up_questions = []
            
            # Check if we have meaningful data (not just null/empty results)
            has_meaningful_data = self._has_meaningful_data(result_data)
            
            # Case 1: No meaningful data found (empty results or all null values)
            if execution_success and not has_meaningful_data:
                logger.info("No meaningful data found - generating suggestions for available data")
                suggestions = await self._generate_no_data_suggestions(user_question, sql_query)
                follow_up_questions.extend(suggestions)
            
            # Case 2: Data exists - generate related follow-up questions
            elif execution_success and has_meaningful_data:
                logger.info("Meaningful data found - generating related follow-up questions")
                related_questions = await self._generate_related_follow_ups(user_question, sql_query, result_data)
                follow_up_questions.extend(related_questions)
            
            # Case 3: Query execution failed
            elif not execution_success and error_message:
                logger.info("Query failed - generating alternative suggestions")
                alternatives = await self._generate_alternative_suggestions(user_question, error_message)
                follow_up_questions.extend(alternatives)
            
            # Limit to 2 follow-up questions as requested
            return follow_up_questions[:2]
            
        except Exception as e:
            logger.error(f"Follow-up question generation failed: {str(e)}")
            return []
    
    async def _generate_no_data_suggestions(self, user_question: str, sql_query: str) -> List[str]:
        """Generate suggestions when no data is found for the query"""
        try:
            # Analyze the SQL query to extract requested time period and key concepts
            requested_year = self._extract_requested_year(sql_query, user_question)
            key_concepts = self._extract_key_concepts(user_question, sql_query)
            
            prompt = f"""You are a helpful database assistant. The user asked a question but no data was found in the database.

User's Question: {user_question}

Generated SQL Query:
{sql_query}

CRITICAL ANALYSIS:
- The query executed successfully but returned no results (null or empty data)
- This means the requested data does NOT exist in the database
- The user asked for data from: {requested_year if requested_year else 'unknown time period'}
- Key concepts in the user's question: {', '.join(key_concepts) if key_concepts else 'general data'}
- Based on the database schema, data is typically available from 2023-2025

IMPORTANT: Generate follow-up questions that are SPECIFIC to what the user originally asked about, but for AVAILABLE time periods.

Generate exactly 2 follow-up questions that:
1. Keep the SAME topic/concept as the original question (e.g., if they asked about profit, ask about profit)
2. Suggest exploring data from AVAILABLE time periods (2023-2025)
3. Are specific and contextual to the user's original question
4. Are written in natural, conversational language

GOOD examples (when user asked about profit in 2022):
- "What profit did you earn in 2023-2025 instead?"
- "Can you show me the most recent profit data available?"
- "What was your total profit for 2023, 2024, or 2025?"

GOOD examples (when user asked about sales in 2027):
- "What sales data is available for 2023-2025 instead?"
- "Can you show me the most recent sales figures available?"

BAD examples (avoid these):
- Generic questions like "What data is available?" (too vague)
- Questions about the same unavailable time period
- Questions that don't relate to the original topic

Format your response as a JSON array of exactly 2 strings:
["question 1", "question 2"]

Follow-up questions:"""

            response = await self._ollama_generate(
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 200,
                    "num_gpu": -1,
                    "num_thread": 1,
                    "num_batch": 512,
                }
            )
            
            # Extract JSON array from response
            follow_ups = self._extract_follow_up_questions(response)
            logger.info(f"Generated no-data suggestions: {follow_ups}")
            return follow_ups
            
        except Exception as e:
            logger.error(f"Failed to generate no-data suggestions: {str(e)}")
            return [
                "What time periods do we have data for?",
                "Can you show me the most recent data available?"
            ]
    
    async def _generate_related_follow_ups(self, user_question: str, sql_query: str, result_data: List[Dict[str, Any]]) -> List[str]:
        """Generate related follow-up questions when data exists"""
        try:
            # Generate statistical summary for context
            summary = self._generate_statistical_summary(result_data)
            
            prompt = f"""You are a helpful database assistant. The user asked a question and got results. Generate 2 related follow-up questions that would help them explore the data further.

User's Question: {user_question}

SQL Query:
{sql_query}

Query Results Summary:
- Total Records: {summary.get('total_records', len(result_data))}
- Columns: {', '.join(summary.get('columns', []))}

Sample Data (first 3 records):
{json.dumps(result_data[:3], indent=2, default=str)}

Statistical Insights:
{json.dumps(summary.get('statistics', {}), indent=2, default=str)}

Generate exactly 2 follow-up questions that are:
1. Related to the original question and data
2. Helpful for deeper analysis or exploration
3. Based on the actual data structure and content
4. Written in natural, conversational language

Examples of good follow-up questions:
- "What's the trend over time for this data?"
- "Which category has the highest values?"
- "Can you show me a breakdown by month?"
- "What's the average compared to the maximum?"

Focus on questions that would provide additional insights about the data that was just retrieved.

Format your response as a JSON array of exactly 2 strings:
["question 1", "question 2"]

Follow-up questions:"""

            response = await self._ollama_generate(
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 200,
                    "num_gpu": -1,
                    "num_thread": 1,
                    "num_batch": 512,
                }
            )
            
            # Extract JSON array from response
            follow_ups = self._extract_follow_up_questions(response)
            logger.info(f"Generated related follow-ups: {follow_ups}")
            return follow_ups
            
        except Exception as e:
            logger.error(f"Failed to generate related follow-ups: {str(e)}")
            return [
                "What's the trend over time for this data?",
                "Can you show me more details about the top results?"
            ]
    
    async def _generate_alternative_suggestions(self, user_question: str, error_message: str) -> List[str]:
        """Generate alternative suggestions when query execution fails"""
        try:
            prompt = f"""You are a helpful database assistant. The user asked a question but the SQL query failed to execute.

User's Question: {user_question}

Error Message: {error_message}

The query failed to execute, which could be due to:
1. Syntax errors in the generated SQL
2. Invalid column or table references
3. Data type mismatches
4. Complex query that needs simplification

Generate exactly 2 alternative follow-up questions that:
1. Simplify the original question
2. Ask for more basic information first
3. Suggest exploring the database structure
4. Are written in natural, conversational language

Examples of good alternatives:
- "Can you show me what tables are available?"
- "What data do we have for a simpler time period?"
- "Can you show me a basic summary of the data?"

Format your response as a JSON array of exactly 2 strings:
["question 1", "question 2"]

Alternative questions:"""

            response = await self._ollama_generate(
                prompt=prompt,
                options={
                    "temperature": 0.7,
                    "num_predict": 200,
                    "num_gpu": -1,
                    "num_thread": 1,
                    "num_batch": 512,
                }
            )
            
            # Extract JSON array from response
            follow_ups = self._extract_follow_up_questions(response)
            logger.info(f"Generated alternative suggestions: {follow_ups}")
            return follow_ups
            
        except Exception as e:
            logger.error(f"Failed to generate alternative suggestions: {str(e)}")
            return [
                "Can you show me what data is available?",
                "What's the simplest query you can run?"
            ]
    
    def _extract_follow_up_questions(self, response: str) -> List[str]:
        """Extract follow-up questions from AI response"""
        try:
            # Try to parse as JSON first
            import json
            questions = json.loads(response)
            if isinstance(questions, list) and len(questions) >= 2:
                return questions[:2]
        except:
            pass
        
        # Fallback: try to extract questions from text
        import re
        # Look for quoted strings or numbered questions
        patterns = [
            r'"([^"]+)"',  # Quoted strings
            r'\d+\.\s*([^?\n]+[?])',  # Numbered questions
            r'-\s*([^?\n]+[?])',  # Bullet point questions
        ]
        
        questions = []
        for pattern in patterns:
            matches = re.findall(pattern, response)
            for match in matches:
                question = match.strip()
                if question.endswith('?') and len(question) > 10:
                    questions.append(question)
                    if len(questions) >= 2:
                        break
            if len(questions) >= 2:
                break
        
        # If we still don't have enough, add some defaults
        if len(questions) < 2:
            questions.extend([
                "What other data would you like to explore?",
                "Can you show me related information?"
            ])
        
        return questions[:2]
    
    def _extract_requested_year(self, sql_query: str, user_question: str) -> Optional[str]:
        """Extract the requested year from SQL query or user question"""
        import re
        
        # First try to extract from SQL query (look for LIKE patterns with years)
        year_patterns = [
            r"LIKE\s+'(\d{4})%'",  # LIKE '2027%'
            r"=.*'(\d{4})'",       # = '2027'
            r"IN\s*\([^)]*'(\d{4})'",  # IN ('2027', ...)
            r"WHERE.*(\d{4})",     # WHERE year = 2027
        ]
        
        for pattern in year_patterns:
            matches = re.findall(pattern, sql_query, re.IGNORECASE)
            if matches:
                return matches[0]
        
        # If not found in SQL, try to extract from user question
        year_matches = re.findall(r'\b(20\d{2})\b', user_question)
        if year_matches:
            return year_matches[0]
        
        return None
    
    def _extract_key_concepts(self, user_question: str, sql_query: str) -> List[str]:
        """Extract key concepts/topics from user question and SQL query"""
        concepts = []
        
        # Common business/financial concepts to look for
        concept_keywords = {
            'profit': ['profit', 'earn', 'earning', 'income', 'revenue', 'gain'],
            'sales': ['sales', 'sell', 'sold', 'sale_amt', 'revenue'],
            'purchase': ['purchase', 'buy', 'bought', 'buy_amt', 'cost'],
            'transaction': ['transaction', 'trsc', 'deal', 'trade'],
            'amount': ['amount', 'amt', 'total', 'sum', 'value'],
            'customer': ['customer', 'client', 'user', 'buyer', 'seller'],
            'product': ['product', 'item', 'goods', 'merchandise'],
            'date': ['date', 'time', 'period', 'month', 'year', 'day'],
            'region': ['region', 'area', 'location', 'place', 'city'],
            'category': ['category', 'type', 'class', 'group', 'kind']
        }
        
        # Check user question for concepts
        question_lower = user_question.lower()
        for concept, keywords in concept_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                concepts.append(concept)
        
        # Check SQL query for additional concepts (column names, table names)
        sql_lower = sql_query.lower()
        sql_concepts = {
            'profit': ['profit', 'sale_amt', 'buy_amt', 'revenue', 'income'],
            'sales': ['sale', 'sell', 'revenue'],
            'purchase': ['buy', 'purchase', 'cost'],
            'transaction': ['trsc', 'transaction'],
            'amount': ['amt', 'amount', 'total', 'sum'],
            'customer': ['user', 'customer', 'client'],
            'date': ['dt', 'date', 'time']
        }
        
        for concept, keywords in sql_concepts.items():
            if any(keyword in sql_lower for keyword in keywords) and concept not in concepts:
                concepts.append(concept)
        
        # Remove duplicates and return top 3 most relevant concepts
        unique_concepts = list(dict.fromkeys(concepts))  # Preserves order while removing duplicates
        return unique_concepts[:3]
    
    def _has_meaningful_data(self, result_data: List[Dict[str, Any]]) -> bool:
        """Check if result data contains meaningful (non-null, non-empty) values"""
        if not result_data or len(result_data) == 0:
            return False
        
        # Check if all values in all rows are null or empty
        for row in result_data:
            for key, value in row.items():
                # Consider a value meaningful if it's not None, not empty string, and not just whitespace
                if value is not None and str(value).strip() != '' and str(value).strip().lower() != 'null':
                    return True
        
        return False
    
    def _build_chart_prompt(self, question: str, query: str, response: str, summary_info: str = "", use_usd: bool = False) -> str:
        """Build chart generation prompt for shadcn/Recharts format"""
        currency = "USD ($)" if use_usd else "KRW (₩)"
        currency_instruction = f"""CURRENCY RULES:
- Use {currency} for all monetary values in chart labels
- {"Use USD with exchange rate: 1 KRW = 0.00070 USD" if use_usd else "Use KRW by default - this is Korean financial data"}
- CRITICAL: Format numbers using EXACT scale abbreviations:
  * K = Thousand (1,000 = 1K)
  * M = Million (1,000,000 = 1M, NOT 1B)
  * B = Billion (1,000,000,000 = 1B, NOT 1T)
  * T = Trillion (1,000,000,000,000 = 1T)
- Examples: {"1,000,000,000 USD = 1.0B USD, 1,000,000 USD = 1.0M USD, 500,000 USD = 0.5M USD" if use_usd else "1,000,000,000 KRW = 1.0B KRW, 1,000,000 KRW = 1.0M KRW, 500,000 KRW = 0.5M KRW, 1,000,000,000,000 KRW = 1.0T KRW"}
- Always include the currency symbol ({"$" if use_usd else "₩"})
- DO NOT confuse millions with billions - verify the number of zeros before choosing the scale"""

        return f"""You are a data visualization assistant. Generate chart specifications for suitable data.

User Input:
{question}

SQL Query:
{query}

SQL Result{summary_info}:
{response}

IMPORTANT: This data may be sampled from a larger dataset. Focus on the patterns and trends visible in the provided data.
Use the STATISTICAL CONTEXT below for accurate min/max/average values to ensure consistency with explanations.

{currency_instruction}

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
        "total_sale_amt": {{"label": "Total Sale Amount ({currency})"}}
    }},
    "explain": "Daily total sale amount by date in {currency}"
}}

If NOT suitable, respond: "no"

NAMING RULES:
- Use actual field values in "name" (years, categories, etc.)
- Keep numeric values as numbers (not strings)
- Use meaningful field names for values
- Format dates in human-readable format (e.g., "Jan 01, 2025" instead of "20250101")
- DO NOT include markdown tables or code blocks in explanations
- Write explanations in natural, conversational language

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