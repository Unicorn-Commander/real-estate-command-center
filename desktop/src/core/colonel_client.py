"""
The Colonel Client - Real Estate AI Assistant using Ollama
"""
import sys
import os
import requests
import json
import re
from typing import Dict, List, Any, Optional
from core.property_service import PropertyService
from core.lead_generator import LeadGenerator
import openai

class ColonelClient:
    def __init__(self, url: str = None):
        self.url = url or "http://localhost:11434"
        self.ollama_url = "http://localhost:11434"
        self.use_openai = os.getenv("USE_OPENAI", "False").lower() == "true"
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = None

        # Initialize real data services
        self.property_service = PropertyService()
        self.lead_generator = LeadGenerator()

        # Initialize with sample realistic leads
        self._leads = self.lead_generator.generate_sample_leads(20)
        self._campaigns = [
            {'id': 1, 'name': 'Summer Sale', 'status': 'Active', 'start_date': '2024-06-01'},
            {'id': 2, 'name': 'Holiday Promo', 'status': 'Planned', 'start_date': '2024-11-15'},
            {'id': 3, 'name': 'Referral Drive', 'status': 'Completed', 'start_date': '2024-03-20'},
        ]

        # Specialized Agent Profiles with models
        self.agent_profiles = {
            'property_analyst': {
                'ollama_model': 'qwen2.5vl:q4_k_m',
                'openai_model': 'gpt-4o',
                'system_message': """You are a specialized Property Analysis Agent for real estate professionals.
Your expertise includes:
- Property valuation and assessment
- Comparable sales analysis (CMA)
- Investment potential evaluation
- Property condition assessment
- Market positioning recommendations

Always provide data-driven insights with specific recommendations.""",
                'name': 'Property Analyst'
            },
            'market_researcher': {
                'ollama_model': 'qwen3:q4_k_m',
                'openai_model': 'gpt-4o',
                'system_message': """You are a Market Research Specialist for real estate.
Your expertise includes:
- Local market trends and statistics
- Neighborhood analysis and demographics
- Price trend forecasting
- Market timing recommendations
- Competitive market analysis

Focus on actionable market intelligence and trends.""",
                'name': 'Market Researcher'
            },
            'lead_manager': {
                'ollama_model': 'gemma3:4b-q4_k_m',
                'openai_model': 'gpt-3.5-turbo',
                'system_message': """You are a Lead Management Specialist for real estate agents.
Your expertise includes:
- Lead qualification and scoring
- Communication strategy recommendations
- Follow-up scheduling and automation
- Conversion optimization tactics
- Client relationship management

Provide practical lead nurturing strategies.""",
                'name': 'Lead Manager'
            },
            'marketing_expert': {
                'ollama_model': 'gemma3:4b-q4_k_m',
                'openai_model': 'gpt-3.5-turbo',
                'system_message': """You are a Real Estate Marketing Expert.
Your expertise includes:
- Property listing optimization
- Marketing campaign development
- Social media strategy for real estate
- Content creation for property promotion
- Target audience identification

Create compelling marketing strategies that convert.""",
                'name': 'Marketing Expert'
            }
        }

        # Initialize The Colonel interpreter
        self._init_colonel()

    def _init_colonel(self):
        """Initialize AI connection (Ollama or OpenAI)"""
        self.available_agents = {}
        if self.use_openai:
            if not self.openai_api_key:
                print("⚠️ OPENAI_API_KEY environment variable not set. OpenAI integration disabled.")
                self.colonel_mode = None
                return

            try:
                self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
                # Test OpenAI connection by listing models (or a simpler call)
                self.openai_client.models.list() # This will raise an exception if API key is invalid
                
                for agent_type, config in self.agent_profiles.items():
                    self.available_agents[agent_type] = {
                        'model': config['openai_model'],
                        'system_message': config['system_message'],
                        'name': config['name']
                    }
                    print(f"✅ {config['name']} ready with OpenAI model {config['openai_model']}")
                self.colonel_mode = "openai"
                print(f"✅ The Colonel OpenAI integration ready ({len(self.available_agents)}/4 agents)")
            except Exception as e:
                print(f"⚠️ Could not connect to OpenAI or invalid API key: {e}")
                self.colonel_mode = None
        else:
            try:
                # Test Ollama connection
                response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    available_ollama_models = [model['name'] for model in models]

                    # Check which agent models are available
                    for agent_type, config in self.agent_profiles.items():
                        model_name = config['ollama_model']
                        if model_name in available_ollama_models:
                            self.available_agents[agent_type] = {
                                'model': config['ollama_model'],
                                'system_message': config['system_message'],
                                'name': config['name']
                            }
                            print(f"✅ {config['name']} ready with Ollama model {model_name}")
                        else:
                            print(f"⚠️ {config['name']} Ollama model {model_name} not available")

                    self.colonel_mode = "ollama"
                    print(f"✅ The Colonel Ollama integration ready ({len(self.available_agents)}/4 agents)")
                else:
                    raise Exception(f"Ollama not responding: {response.status_code}")

            except Exception as e:
                print(f"⚠️ Could not connect to Ollama: {e}")
                self.colonel_mode = None
        
        self.colonel = self  # Use self for interface

    def chat_with_agent(self, message: str, agent_type: str = 'property_analyst', stream: bool = False) -> str:
        """Send a message to a specialized agent using the configured AI backend"""
        if agent_type not in self.available_agents:
            available = list(self.available_agents.keys())
            return f"Agent {agent_type} not available. Available agents: {available}"
        
        # Check if message contains an address and fetch real property data
        enhanced_message = self._enhance_message_with_property_data(message)
        
        agent_config = self.available_agents[agent_type]
        
        if self.colonel_mode == "ollama":
            return self._chat_with_ollama(enhanced_message, agent_config['model'], agent_config['system_message'], agent_config['name'], stream)
        elif self.colonel_mode == "openai":
            return self._chat_with_openai(enhanced_message, agent_config['model'], agent_config['system_message'], agent_config['name'], stream)
        else:
            return "The Colonel is not configured. Please check AI settings."
    
    def _chat_with_openai(self, message: str, model: str, system_message: str, agent_name: str, stream: bool = False) -> str:
        """Chat with OpenAI API directly"""
        try:
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ]
            
            if stream:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=True
                )
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                return f"[{agent_name}]: {full_response.strip()}"
            else:
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=False
                )
                content = response.choices[0].message.content.strip()
                return f"[{agent_name}]: {content}"
        except Exception as e:
            return f"[{agent_name}]: Error - {str(e)[:100]}"

    def _chat_with_ollama(self, message: str, model: str, system_message: str, agent_name: str, stream: bool = False) -> str:
        """Chat with Ollama API directly"""
        try:
            # Prepare the request
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ],
                "stream": stream
            }
            
            # Make request to Ollama
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                if stream:
                    # Handle streaming response
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            if 'message' in chunk and 'content' in chunk['message']:
                                full_response += chunk['message']['content']
                    return f"[{agent_name}]: {full_response.strip()}"
                else:
                    # Handle single response
                    result = response.json()
                    if 'message' in result and 'content' in result['message']:
                        content = result['message']['content'].strip()
                        return f"[{agent_name}]: {content}"
                    else:
                        return f"[{agent_name}]: Unexpected response format"
            else:
                return f"[{agent_name}]: Error {response.status_code} - {response.text[:100]}"
                
        except requests.exceptions.Timeout:
            return f"[{agent_name}]: Request timed out. Model may be loading..."
        except Exception as e:
            return f"[{agent_name}]: Error - {str(e)[:100]}"
    
    def _enhance_message_with_property_data(self, message: str) -> str:
        """Detect addresses in message and enhance with real property data"""
        try:
            # Simple address detection patterns
            address_patterns = [
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Drive|Dr|Road|Rd|Lane|Ln|Way|Blvd|Boulevard|Circle|Cir|Court|Ct|Place|Pl)\b[^,]*(?:,\s*[A-Za-z\s]+)?(?:,\s*[A-Z]{2})?\s*\d{5}?',
                r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Drive|Dr|Road|Rd|Lane|Ln|Way|Blvd|Boulevard|Circle|Cir|Court|Ct|Place|Pl)',
            ]
            
            detected_addresses = []
            for pattern in address_patterns:
                matches = re.findall(pattern, message, re.IGNORECASE)
                detected_addresses.extend(matches)
            
            if detected_addresses:
                # Take the first detected address
                address = detected_addresses[0].strip()
                print(f"🏠 Detected address: {address}")
                
                # Fetch real property data
                property_data = self.property_service.lookup_property(address)
                
                if 'error' not in property_data:
                    # Enhance the message with property context
                    property_context = f"""

REAL PROPERTY DATA FOR: {address}
===========================================
Property Type: {property_data['property']['type']}
Bedrooms: {property_data['property']['bedrooms']}
Bathrooms: {property_data['property']['bathrooms']}
Square Feet: {property_data['property']['square_feet']:,}
Year Built: {property_data['property']['year_built']}
Estimated Value: ${property_data['property']['estimated_value']:,}
Last Sale: ${property_data['property']['last_sale_price']:,} ({property_data['property']['last_sale_date']})
Location: {property_data['property']['city']}, {property_data['property']['state']}

MARKET DATA:
Median Home Value: ${property_data['market']['median_home_value']:,}
Market Trend: {property_data['market']['market_trend']}
Days on Market: {property_data['market']['days_on_market']}
Price per Sq Ft: ${property_data['market']['price_per_sqft']}

COMPARABLE SALES:
"""
                    for i, comp in enumerate(property_data['comparables'][:3], 1):
                        property_context += f"{i}. {comp['address']} - ${comp['sale_price']:,} ({comp['sale_date']}) - {comp['bedrooms']}BR/{comp['bathrooms']}BA, {comp['square_feet']:,} sq ft\n"
                    
                    property_context += "\n===========================================\n"
                    
                    enhanced_message = property_context + f"\nUSER QUESTION: {message}"
                    return enhanced_message
                else:
                    # Address detected but lookup failed
                    return f"{message}\n\n[Note: Attempted to lookup property data for '{address}' but encountered: {property_data.get('error', 'Unknown error')}]"
            
            return message
            
        except Exception as e:
            print(f"Error enhancing message: {e}")
            return message
    
    def chat(self, message: str, model: str = None) -> str:
        """Send a message to The Colonel using default or specified agent"""
        if not self.colonel_mode:
            return "The Colonel is not available. Please check AI settings."
        
        # Use property_analyst as default agent
        if 'property_analyst' in self.available_agents:
            return self.chat_with_agent(message, 'property_analyst')
        elif self.available_agents:
            # Use first available agent
            first_agent = list(self.available_agents.keys())[0]
            return self.chat_with_agent(message, first_agent)
        else:
            return "No agents are currently available. Please check AI settings."
    
    def analyze_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use The Colonel to analyze property data"""
        prompt = f"""
Analyze this property data and provide insights:
{json.dumps(property_data, indent=2)}

Please provide:
1. Market analysis
2. Price evaluation
3. Investment potential
4. Recommendations

Return as structured analysis.
"""
        response = self.chat(prompt)
        return {'analysis': response, 'status': 'completed'}
    
    def generate_market_report(self, area: str, property_type: str) -> str:
        """Generate market report using The Colonel"""
        prompt = f"""
Generate a market report for {property_type} properties in {area}.
Include:
- Current market trends
- Average prices
- Market outlook
- Key factors affecting the market

Format as a professional report.
"""
        return self.chat(prompt)
    
    def suggest_listing_price(self, property_features: Dict[str, Any]) -> Dict[str, Any]:
        """Get listing price suggestion from The Colonel"""
        prompt = f"""
Based on these property features:
{json.dumps(property_features, indent=2)}

Suggest an appropriate listing price range and provide reasoning.
Consider market conditions, comparable sales, and property features.
"""
        response = self.chat_with_agent(prompt, 'property_analyst')
        return {'suggestion': response, 'confidence': 'medium'}
    
    # Specialized Agent Methods
    def analyze_property_with_specialist(self, property_data: Dict[str, Any]) -> str:
        """Use Property Analyst agent for detailed property analysis"""
        prompt = f"""
Analyze this property data:
{json.dumps(property_data, indent=2)}

Provide a comprehensive property analysis including valuation, investment potential, and recommendations.
"""
        return self.chat_with_agent(prompt, 'property_analyst')
    
    def research_market_with_specialist(self, area: str, property_type: str = "residential") -> str:
        """Use Market Research agent for market analysis"""
        prompt = f"""
Research the {property_type} market in {area}.
Provide current trends, pricing analysis, and market outlook.
"""
        return self.chat_with_agent(prompt, 'market_researcher')
    
    def get_lead_strategy(self, lead_data: Dict[str, Any]) -> str:
        """Use Lead Manager agent for lead strategy"""
        prompt = f"""
Analyze this lead data and provide a nurturing strategy:
{json.dumps(lead_data, indent=2)}

Include qualification scoring and recommended next steps.
"""
        return self.chat_with_agent(prompt, 'lead_manager')
    
    def create_marketing_strategy(self, property_data: Dict[str, Any]) -> str:
        """Use Marketing Expert agent for marketing strategies"""
        prompt = f"""
Create a marketing strategy for this property:
{json.dumps(property_data, indent=2)}

Include listing optimization, target audience, and campaign recommendations.
"""
        return self.chat_with_agent(prompt, 'marketing_expert')
    
    def get_multi_agent_analysis(self, query: str) -> Dict[str, str]:
        """Get perspectives from multiple specialized agents"""
        results = {}
        
        # Get analysis from each agent
        for agent_type, agent_info in self.agent_profiles.items():
            try:
                response = self.chat_with_agent(query, agent_type)
                results[agent_info['name']] = response
            except Exception as e:
                results[agent_info['name']] = f"Error: {e}"
        
        return results

    def ping(self) -> bool:
        """Stub ping method."""
        return True

    # Leads
    def list_leads(self):
        """Return list of leads."""
        return self._leads

    def create_lead(self, name: str, email: str, status: str) -> dict:
        """Create a new lead."""
        new_id = max((l['id'] for l in self._leads), default=0) + 1
        lead = {'id': new_id, 'name': name, 'email': email, 'status': status}
        self._leads.append(lead)
        return lead

    def update_lead(self, lead_id: int, data: dict):
        """Update an existing lead."""
        for l in self._leads:
            if l['id'] == lead_id:
                l.update(data)
                return l
        return None

    def delete_lead(self, lead_id: int):
        """Delete a lead."""
        self._leads = [l for l in self._leads if l['id'] != lead_id]

    # Campaigns
    def list_campaigns(self):
        """Return list of campaigns."""
        return self._campaigns

    def create_campaign(self, name: str, status: str, start_date: str) -> dict:
        """Create a new campaign."""
        new_id = max((c['id'] for c in self._campaigns), default=0) + 1
        camp = {'id': new_id, 'name': name, 'status': status, 'start_date': start_date}
        self._campaigns.append(camp)
        return camp

    def update_campaign(self, campaign_id: int, data: dict):
        """Update existing campaign."""
        for c in self._campaigns:
            if c['id'] == campaign_id:
                c.update(data)
                return c
        return None

    def delete_campaign(self, campaign_id: int):
        """Delete a campaign."""
        self._campaigns = [c for c in self._campaigns if c['id'] != campaign_id]
