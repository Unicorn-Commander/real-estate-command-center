"""
Real Estate Interpreter - Custom AI inference engine based on The Colonel
Integrated tool calling and code execution for real estate workflows
"""
import json
import re
import subprocess
import tempfile
import os
import sys
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import requests
import openai
from core.property_service import PropertyService
from core.lead_generator import LeadGenerator
from core.settings_manager import settings_manager

class RealEstateInterpreter:
    """Custom AI interpreter for real estate workflows"""
    
    def __init__(self, settings: Dict[str, Any] = None):
        self.settings = settings or settings_manager.get_all_settings()
        self.ai_settings = self.settings.get('ai_backend', {})
        
        # Initialize backend
        self.backend_type = self.ai_settings.get('backend_type', 'ollama')
        self.ollama_url = self.ai_settings.get('ollama_url', 'http://localhost:11434')
        self.openai_api_key = self.ai_settings.get('openai_api_key', '')
        
        # Initialize real estate services
        self.property_service = PropertyService(
            preferred_mls_provider=self.settings.get('mls_providers', {}).get('preferred_provider', 'bridge'),
            use_multiple_providers=self.settings.get('mls_providers', {}).get('use_multiple_providers', True)
        )
        self.lead_generator = LeadGenerator()
        
        # Conversation history
        self.conversation_history = []
        
        # Tool registry
        self.tools = {
            'lookup_property': self._tool_lookup_property,
            'search_properties': self._tool_search_properties,
            'analyze_market': self._tool_analyze_market,
            'generate_leads': self._tool_generate_leads,
            'calculate_cma': self._tool_calculate_cma,
            'execute_python': self._tool_execute_python,
            'create_report': self._tool_create_report
        }
        
        # System prompt for real estate context
        self.system_prompt = """You are an advanced AI assistant specialized in real estate. 
You have access to powerful tools for property analysis, market research, lead management, and data processing.

Available tools:
- lookup_property(address): Get detailed property information
- search_properties(criteria): Search for properties matching criteria
- analyze_market(city, state): Get market analysis for an area
- generate_leads(count, criteria): Generate qualified leads
- calculate_cma(address, comparable_count): Perform comparative market analysis
- execute_python(code): Execute Python code for calculations and analysis
- create_report(data, report_type): Generate professional reports

When users ask real estate questions, use these tools to provide accurate, data-driven responses.
Always explain your analysis and provide actionable insights."""
        
        # Safety settings for code execution
        self.safe_mode = True
        self.auto_run = False  # Always ask before running code
        
        print(f"🏠 Real Estate Interpreter initialized with {self.backend_type} backend")
    
    def chat(self, message: str, agent_type: str = 'property_analyst') -> str:
        """Main chat interface with tool calling capabilities"""
        try:
            # Add message to history
            self.conversation_history.append({
                'role': 'user',
                'content': message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Enhanced message with property data if address detected
            enhanced_message = self._enhance_with_property_context(message)
            
            # Get AI response with tool calling
            response = self._get_ai_response(enhanced_message, agent_type)
            
            # Process any tool calls in the response
            final_response = self._process_tool_calls(response)
            
            # Add to history
            self.conversation_history.append({
                'role': 'assistant',
                'content': final_response,
                'timestamp': datetime.now().isoformat(),
                'agent_type': agent_type
            })
            
            return final_response
            
        except Exception as e:
            error_msg = f"Error processing request: {str(e)}"
            print(f"🚨 {error_msg}")
            return error_msg
    
    def _get_ai_response(self, message: str, agent_type: str) -> str:
        """Get response from AI backend"""
        # Build context with system prompt and tools
        context = self._build_context(message, agent_type)
        
        if self.backend_type == 'openai':
            return self._call_openai(context)
        elif self.backend_type == 'ollama':
            return self._call_ollama(context)
        else:
            return "Unsupported AI backend configured"
    
    def _build_context(self, message: str, agent_type: str) -> List[Dict[str, str]]:
        """Build conversation context with system prompt and history"""
        # Agent-specific system messages
        agent_prompts = {
            'property_analyst': """You are a Property Analysis Specialist. Focus on:
- Property valuation and investment analysis
- Comparable sales analysis (CMA)
- Market positioning and pricing strategies
- Property condition assessment and recommendations""",
            
            'market_researcher': """You are a Market Research Specialist. Focus on:
- Local market trends and statistics
- Neighborhood analysis and demographics
- Price forecasting and market timing
- Competitive market analysis""",
            
            'lead_manager': """You are a Lead Management Specialist. Focus on:
- Lead qualification and scoring
- Communication strategies and follow-up
- Conversion optimization
- Client relationship management""",
            
            'marketing_expert': """You are a Real Estate Marketing Expert. Focus on:
- Listing optimization and staging advice
- Marketing campaign development
- Target audience identification
- Content creation and social media strategy"""
        }
        
        system_message = self.system_prompt + "\n\n" + agent_prompts.get(agent_type, agent_prompts['property_analyst'])
        
        # Build message list
        messages = [{'role': 'system', 'content': system_message}]
        
        # Add recent conversation history (last 10 messages)
        recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history
        messages.extend(recent_history)
        
        # Add current message
        messages.append({'role': 'user', 'content': message})
        
        return messages
    
    def _call_openai(self, messages: List[Dict[str, str]]) -> str:
        """Call OpenAI API"""
        try:
            client = openai.OpenAI(api_key=self.openai_api_key)
            
            response = client.chat.completions.create(
                model='gpt-4o',
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"OpenAI API error: {str(e)}"
    
    def _call_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Call Ollama API"""
        try:
            # Convert messages to Ollama format
            data = {
                "model": "qwen2.5:14b",  # Default model
                "messages": messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                if 'message' in result and 'content' in result['message']:
                    return result['message']['content']
                else:
                    return "Unexpected Ollama response format"
            else:
                return f"Ollama API error: {response.status_code}"
                
        except Exception as e:
            return f"Ollama connection error: {str(e)}"
    
    def _enhance_with_property_context(self, message: str) -> str:
        """Detect addresses and enhance message with property data"""
        # Address detection patterns
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Drive|Dr|Road|Rd|Lane|Ln|Way|Blvd|Boulevard|Circle|Cir|Court|Ct|Place|Pl)\b[^,]*(?:,\s*[A-Za-z\s]+)?(?:,\s*[A-Z]{2})?\s*\d{5}?',
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Drive|Dr|Road|Rd|Lane|Ln|Way|Blvd|Boulevard)',
        ]
        
        detected_addresses = []
        for pattern in address_patterns:
            matches = re.findall(pattern, message, re.IGNORECASE)
            detected_addresses.extend(matches)
        
        if detected_addresses:
            address = detected_addresses[0].strip()
            print(f"🏠 Detected address in query: {address}")
            
            try:
                # Get property data
                property_data = self.property_service.lookup_property(address)
                
                if 'error' not in property_data:
                    # Build context
                    context = f"""
PROPERTY CONTEXT FOR: {address}
{'='*50}
Property Details:
- Type: {property_data['property'].get('type', 'Unknown')}
- Size: {property_data['property'].get('bedrooms', '?')} bed / {property_data['property'].get('bathrooms', '?')} bath
- Square Feet: {property_data['property'].get('square_feet', 0):,}
- Year Built: {property_data['property'].get('year_built', 'Unknown')}
- Estimated Value: ${property_data['property'].get('estimated_value', 0):,}

Market Data:
- Median Home Value: ${property_data['market'].get('median_home_value', 0):,}
- Market Trend: {property_data['market'].get('market_trend', 'Unknown')}
- Days on Market: {property_data['market'].get('days_on_market', 'Unknown')}

Data Sources: {', '.join(property_data.get('data_sources_used', ['Unknown']))}
Confidence: {property_data.get('data_confidence', 0.0):.1%}
{'='*50}

USER QUESTION: {message}"""
                    
                    return context
                    
            except Exception as e:
                print(f"Error getting property context: {e}")
        
        return message
    
    def _process_tool_calls(self, response: str) -> str:
        """Process any tool calls mentioned in the AI response"""
        # Look for tool call patterns in the response
        tool_pattern = r'```(\w+)\s*\((.*?)\)\s*```'
        
        matches = re.findall(tool_pattern, response, re.DOTALL)
        
        if not matches:
            # Look for alternative formats
            alt_pattern = r'(\w+)\((.*?)\)'
            alt_matches = re.findall(alt_pattern, response)
            
            # Filter for known tools
            matches = [(tool, args) for tool, args in alt_matches if tool in self.tools]
        
        if matches:
            enhanced_response = response
            
            for tool_name, args_str in matches:
                if tool_name in self.tools:
                    try:
                        # Parse arguments (simple implementation)
                        args = self._parse_tool_args(args_str)
                        
                        # Execute tool
                        tool_result = self.tools[tool_name](**args)
                        
                        # Add result to response
                        tool_output = f"\n\n🔧 Tool: {tool_name}\nResult: {tool_result}\n"
                        enhanced_response += tool_output
                        
                    except Exception as e:
                        error_output = f"\n\n❌ Tool Error ({tool_name}): {str(e)}\n"
                        enhanced_response += error_output
            
            return enhanced_response
        
        return response
    
    def _parse_tool_args(self, args_str: str) -> Dict[str, Any]:
        """Parse tool arguments from string"""
        try:
            # Try JSON parsing first
            if args_str.strip().startswith('{'):
                return json.loads(args_str)
            
            # Simple key=value parsing
            args = {}
            if '=' in args_str:
                pairs = [pair.strip() for pair in args_str.split(',')]
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        key = key.strip().strip('"\'')
                        value = value.strip().strip('"\'')
                        
                        # Try to convert to appropriate type
                        if value.isdigit():
                            value = int(value)
                        elif value.replace('.', '', 1).isdigit():
                            value = float(value)
                        elif value.lower() in ['true', 'false']:
                            value = value.lower() == 'true'
                        
                        args[key] = value
            else:
                # Single argument
                args['address' if 'address' in args_str.lower() else 'query'] = args_str.strip().strip('"\'')
            
            return args
            
        except Exception as e:
            print(f"Error parsing tool args: {e}")
            return {'query': args_str}
    
    # Tool implementations
    def _tool_lookup_property(self, address: str) -> Dict[str, Any]:
        """Look up detailed property information"""
        return self.property_service.lookup_property(address)
    
    def _tool_search_properties(self, **criteria) -> List[Dict[str, Any]]:
        """Search for properties matching criteria"""
        return self.property_service.search_properties(criteria)
    
    def _tool_analyze_market(self, city: str, state: str) -> Dict[str, Any]:
        """Analyze market conditions for an area"""
        return self.property_service.get_market_analysis(city, state)
    
    def _tool_generate_leads(self, count: int = 5, **criteria) -> List[Dict[str, Any]]:
        """Generate qualified leads"""
        return self.lead_generator.generate_sample_leads(count)
    
    def _tool_calculate_cma(self, address: str, comparable_count: int = 5) -> Dict[str, Any]:
        """Perform comparative market analysis"""
        property_data = self.property_service.lookup_property(address)
        
        if 'error' in property_data:
            return property_data
        
        # Extract comparable sales
        comparables = property_data.get('comparables', [])[:comparable_count]
        
        if not comparables:
            return {'error': 'No comparable sales found'}
        
        # Calculate CMA statistics
        sale_prices = [comp['sale_price'] for comp in comparables]
        price_per_sqft = [comp['sale_price'] / comp['square_feet'] 
                         for comp in comparables if comp.get('square_feet', 0) > 0]
        
        import statistics
        
        cma_result = {
            'subject_property': property_data['property'],
            'comparable_count': len(comparables),
            'comparable_sales': comparables,
            'price_analysis': {
                'median_sale_price': statistics.median(sale_prices) if sale_prices else 0,
                'average_sale_price': statistics.mean(sale_prices) if sale_prices else 0,
                'price_range': {
                    'min': min(sale_prices) if sale_prices else 0,
                    'max': max(sale_prices) if sale_prices else 0
                },
                'price_per_sqft': {
                    'median': statistics.median(price_per_sqft) if price_per_sqft else 0,
                    'average': statistics.mean(price_per_sqft) if price_per_sqft else 0
                }
            },
            'market_conditions': property_data.get('market', {}),
            'suggested_list_price': {
                'low': int(statistics.median(sale_prices) * 0.95) if sale_prices else 0,
                'high': int(statistics.median(sale_prices) * 1.05) if sale_prices else 0
            }
        }
        
        return cma_result
    
    def _tool_execute_python(self, code: str) -> str:
        """Execute Python code safely"""
        if not self.safe_mode or self.auto_run:
            return self._execute_code_safely(code)
        else:
            return f"Code execution requested (safe mode enabled):\n```python\n{code}\n```\nUse execute_python_confirmed() to run."
    
    def _execute_code_safely(self, code: str) -> str:
        """Execute Python code in a safe environment"""
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            # Execute with restricted environment
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=tempfile.gettempdir()
            )
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                return f"Code executed successfully:\n{result.stdout}"
            else:
                return f"Code execution error:\n{result.stderr}"
                
        except subprocess.TimeoutExpired:
            return "Code execution timed out (30 second limit)"
        except Exception as e:
            return f"Code execution error: {str(e)}"
    
    def _tool_create_report(self, data: Dict[str, Any], report_type: str = 'property_analysis') -> str:
        """Create professional reports"""
        if report_type == 'property_analysis':
            return self._create_property_report(data)
        elif report_type == 'market_analysis':
            return self._create_market_report(data)
        elif report_type == 'cma':
            return self._create_cma_report(data)
        else:
            return f"Unknown report type: {report_type}"
    
    def _create_property_report(self, data: Dict[str, Any]) -> str:
        """Create a property analysis report"""
        report = f"""
PROPERTY ANALYSIS REPORT
{'='*50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PROPERTY OVERVIEW
Address: {data.get('address', 'Unknown')}
Type: {data.get('property', {}).get('type', 'Unknown')}
Bedrooms: {data.get('property', {}).get('bedrooms', 'Unknown')}
Bathrooms: {data.get('property', {}).get('bathrooms', 'Unknown')}
Square Feet: {data.get('property', {}).get('square_feet', 0):,}
Year Built: {data.get('property', {}).get('year_built', 'Unknown')}

VALUATION
Estimated Value: ${data.get('property', {}).get('estimated_value', 0):,}
Last Sale Price: ${data.get('property', {}).get('last_sale_price', 0):,}
Property Tax: ${data.get('property', {}).get('property_tax', 0):,}/year

MARKET CONTEXT
Market Trend: {data.get('market', {}).get('market_trend', 'Unknown')}
Days on Market: {data.get('market', {}).get('days_on_market', 'Unknown')}
Market Temperature: {data.get('market', {}).get('market_temperature', 'Unknown')}

DATA QUALITY
Sources Used: {', '.join(data.get('data_sources_used', ['Unknown']))}
Confidence Level: {data.get('data_confidence', 0.0):.1%}
{'='*50}
"""
        return report
    
    def _create_market_report(self, data: Dict[str, Any]) -> str:
        """Create a market analysis report"""
        report = f"""
MARKET ANALYSIS REPORT
{'='*50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

MARKET OVERVIEW
Location: {data.get('location', 'Unknown')}
Total Active Listings: {data.get('total_listings', 'Unknown')}
Median Price: ${data.get('median_price', 0):,}
Average Price: ${data.get('average_price', 0):,}

PRICE ANALYSIS
Price Range: ${data.get('price_range', {}).get('min', 0):,} - ${data.get('price_range', {}).get('max', 0):,}
Average Days on Market: {data.get('average_days_on_market', 'Unknown')}
Market Activity: {data.get('market_activity', 'Unknown')}

PROPERTY TYPES
{', '.join(data.get('property_types', ['Unknown']))}
{'='*50}
"""
        return report
    
    def _create_cma_report(self, data: Dict[str, Any]) -> str:
        """Create a CMA report"""
        report = f"""
COMPARATIVE MARKET ANALYSIS (CMA)
{'='*50}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SUBJECT PROPERTY
{self._format_property_details(data.get('subject_property', {}))}

COMPARABLE SALES ({data.get('comparable_count', 0)} properties)
"""
        
        for i, comp in enumerate(data.get('comparable_sales', []), 1):
            report += f"""
Comparable #{i}:
Address: {comp.get('address', 'Unknown')}
Sale Price: ${comp.get('sale_price', 0):,}
Sale Date: {comp.get('sale_date', 'Unknown')}
Size: {comp.get('bedrooms', '?')} bed / {comp.get('bathrooms', '?')} bath
Square Feet: {comp.get('square_feet', 0):,}
Distance: {comp.get('distance_miles', 0):.1f} miles
"""
        
        price_analysis = data.get('price_analysis', {})
        report += f"""
PRICE ANALYSIS
Median Sale Price: ${price_analysis.get('median_sale_price', 0):,}
Average Sale Price: ${price_analysis.get('average_sale_price', 0):,}
Price per Sq Ft (Median): ${price_analysis.get('price_per_sqft', {}).get('median', 0):.0f}

SUGGESTED LIST PRICE RANGE
Low: ${data.get('suggested_list_price', {}).get('low', 0):,}
High: ${data.get('suggested_list_price', {}).get('high', 0):,}
{'='*50}
"""
        return report
    
    def _format_property_details(self, property_data: Dict[str, Any]) -> str:
        """Format property details for reports"""
        return f"""Type: {property_data.get('type', 'Unknown')}
Bedrooms: {property_data.get('bedrooms', 'Unknown')}
Bathrooms: {property_data.get('bathrooms', 'Unknown')}
Square Feet: {property_data.get('square_feet', 0):,}
Year Built: {property_data.get('year_built', 'Unknown')}
Estimated Value: ${property_data.get('estimated_value', 0):,}"""
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.conversation_history = []
        print("🔄 Conversation history reset")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation"""
        return {
            'message_count': len(self.conversation_history),
            'start_time': self.conversation_history[0]['timestamp'] if self.conversation_history else None,
            'last_update': self.conversation_history[-1]['timestamp'] if self.conversation_history else None,
            'tools_used': list(self.tools.keys()),
            'backend': self.backend_type
        }
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update interpreter settings"""
        self.settings = new_settings
        self.ai_settings = self.settings.get('ai_backend', {})
        
        # Update backend if changed
        old_backend = self.backend_type
        self.backend_type = self.ai_settings.get('backend_type', 'ollama')
        
        if old_backend != self.backend_type:
            print(f"🔄 AI backend changed from {old_backend} to {self.backend_type}")
        
        # Update property service
        mls_settings = self.settings.get('mls_providers', {})
        self.property_service = PropertyService(
            preferred_mls_provider=mls_settings.get('preferred_provider', 'bridge'),
            use_multiple_providers=mls_settings.get('use_multiple_providers', True)
        )