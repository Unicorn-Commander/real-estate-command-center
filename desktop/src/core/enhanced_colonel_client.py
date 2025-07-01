"""
Enhanced Colonel Client with Open Interpreter Integration
Supports Ollama, OpenAI, and Open Interpreter backends
"""
import sys
import os
import requests
import json
import re
from typing import Dict, List, Any, Optional
from core.property_service import PropertyService
from core.lead_generator import LeadGenerator
from core.settings_manager import settings_manager
import openai
from core.real_estate_interpreter import RealEstateInterpreter
from sqlalchemy import create_engine, text

class EnhancedColonelClient:
    """Enhanced AI client supporting multiple backends including Open Interpreter"""
    
    def __init__(self, settings: Dict[str, Any] = None):
        self.settings = settings or settings_manager.get_all_settings()
        self.ai_settings = self.settings.get('ai_backend', {})
        
        # Initialize based on backend type
        self.backend_type = self.ai_settings.get('backend_type', 'ollama')
        self.ollama_url = self.ai_settings.get('ollama_url', 'http://localhost:11434')
        self.openai_api_key = self.ai_settings.get('openai_api_key', '')
        self.interpreter_mode = self.ai_settings.get('open_interpreter_mode', 'local')

        # Initialize database engine
        self.db_engine = create_engine("postgresql://realestate:commander123@localhost:5433/realestate_db")

        # Initialize real data services
        self.property_service = PropertyService(
            preferred_mls_provider=self.settings.get('mls_providers', {}).get('preferred_provider', 'bridge'),
            use_multiple_providers=self.settings.get('mls_providers', {}).get('use_multiple_providers', True),
            settings=self.settings
        )

        self._campaigns = [
            {'id': 1, 'name': 'Summer Sale', 'status': 'Active', 'start_date': '2024-06-01'},
            {'id': 2, 'name': 'Holiday Promo', 'status': 'Planned', 'start_date': '2024-11-15'},
            {'id': 3, 'name': 'Referral Drive', 'status': 'Completed', 'start_date': '2024-03-20'},
        ]

        # Get custom models from settings
        custom_models = self.ai_settings.get('custom_models', {})
        
        # Specialized Agent Profiles with configurable models
        self.agent_profiles = {
            'property_analyst': {
                'ollama_model': custom_models.get('property_analyst', 'qwen2.5vl:q4_k_m'),
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
                'ollama_model': custom_models.get('market_researcher', 'qwen3:q4_k_m'),
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
                'ollama_model': custom_models.get('lead_manager', 'gemma3:4b-q4_k_m'),
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
                'ollama_model': custom_models.get('marketing_expert', 'gemma3:4b-q4_k_m'),
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
            },
            'real_estate_agent': {
                'ollama_model': custom_models.get('real_estate_agent', 'llama3:8b'), # Assuming a capable model for complex tasks
                'openai_model': 'gpt-4o',
                'system_message': """You are a highly skilled Real Estate Agent AI, specializing in contract review, negotiation strategies, and deal closing. Your expertise includes:
- Analyzing real estate contracts for key clauses, risks, and opportunities.
- Proposing effective negotiation tactics based on market conditions and client goals.
- Identifying potential legal pitfalls and advising on mitigation.
- Providing clear, concise summaries of complex legal documents.
- Assisting with offer drafting and counter-offer strategies.

Always provide actionable advice and highlight critical information for the user.""",
                'name': 'Real Estate Agent'
            }
        }
        
        # Initialize the selected backend
        self._init_backend()
    
    def analyze_contract(self, contract_text: str) -> Dict[str, Any]:
        """Analyzes a real estate contract for key terms, risks, and negotiation points.
        This is a placeholder for future advanced contract analysis.
        """
        print(f"[REAL ESTATE AGENT AI] Analyzing contract (first 100 chars): {contract_text[:100]}...")
        # In a real implementation, this would involve sending the contract_text
        # to the 'real_estate_agent' AI for detailed analysis.
        # For now, return a mock response.
        return {
            "summary": "Mock contract summary: Key terms identified, potential negotiation points highlighted.",
            "risks": ["Mock risk: Clause X might be unfavorable."],
            "negotiation_points": ["Mock negotiation: Push for a lower closing cost."]
        }
    
    def _init_backend(self):
        """Initialize the selected AI backend"""
        self.available_agents = {}
        self.backend_ready = False
        
        if self.backend_type == 'openai':
            self._init_openai()
        elif self.backend_type == 'ollama':
            self._init_ollama()
        elif self.backend_type == 'open_interpreter':
            self._init_open_interpreter()
        elif self.backend_type == 'real_estate_interpreter':
            self._init_real_estate_interpreter()
        else:
            print(f"⚠️ Unknown backend type: {self.backend_type}")
    
    def _init_openai(self):
        """Initialize OpenAI backend"""
        if not self.openai_api_key:
            print("⚠️ OpenAI API key not configured")
            return
        
        try:
            self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
            # Test connection
            self.openai_client.models.list()
            
            for agent_type, config in self.agent_profiles.items():
                self.available_agents[agent_type] = {
                    'model': config['openai_model'],
                    'system_message': config['system_message'],
                    'name': config['name']
                }
                print(f"✅ {config['name']} ready with OpenAI model {config['openai_model']}")
            
            self.backend_ready = True
            print(f"✅ OpenAI backend ready ({len(self.available_agents)}/4 agents)")
            
        except Exception as e:
            print(f"⚠️ Could not connect to OpenAI: {e}")
    
    def _init_ollama(self):
        """Initialize Ollama backend"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                available_ollama_models = [model['name'] for model in models]
                
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
                
                self.backend_ready = True
                print(f"✅ Ollama backend ready ({len(self.available_agents)}/4 agents)")
            else:
                raise Exception(f"Ollama not responding: {response.status_code}")
                
        except Exception as e:
            print(f"⚠️ Could not connect to Ollama: {e}")
    
    def _init_open_interpreter(self):
        """Initialize Open Interpreter backend"""
        try:
            # Import open-interpreter
            try:
                from interpreter import interpreter
                self.interpreter = interpreter
            except ImportError:
                print("⚠️ open-interpreter not installed. Install with: pip install open-interpreter")
                return
            
            # Configure interpreter based on mode
            if self.interpreter_mode == 'local':
                self.interpreter.offline = True
                self.interpreter.llm.model = "openai/x"
                self.interpreter.llm.api_key = "fake_key"
                self.interpreter.llm.api_base = self.ollama_url + "/v1"
                print("🔧 Open Interpreter configured for local mode (Ollama)")
            elif self.interpreter_mode == 'hosted' and self.openai_api_key:
                self.interpreter.offline = False
                self.interpreter.llm.model = "gpt-3.5-turbo"
                self.interpreter.llm.api_key = self.openai_api_key
                print("🔧 Open Interpreter configured for hosted mode (OpenAI)")
            elif self.interpreter_mode == 'custom':
                # Allow custom configuration
                print("🔧 Open Interpreter in custom mode")
            else:
                print("⚠️ Open Interpreter mode not properly configured")
                return
            
            # Set up system message for real estate context
            self.interpreter.system_message = """You are an AI assistant for a Real Estate Command Center application.
You have access to real property data, lead management, and market analysis tools.
When users ask about properties, leads, or market data, you can help analyze and provide insights.
Be professional, accurate, and focused on real estate workflows.
Always prioritize data-driven responses and actionable recommendations."""
            
            # Configure interpreter settings
            self.interpreter.auto_run = False  # Don't auto-execute code for safety
            self.interpreter.safe_mode = "ask"  # Ask before running potentially dangerous code
            
            # All agents use the same interpreter instance but with different contexts
            for agent_type, config in self.agent_profiles.items():
                self.available_agents[agent_type] = {
                    'model': 'open_interpreter',
                    'system_message': config['system_message'],
                    'name': config['name']
                }
                print(f"✅ {config['name']} ready with Open Interpreter")
            
            self.backend_ready = True
            print(f"✅ Open Interpreter backend ready ({len(self.available_agents)}/4 agents)")
            
        except Exception as e:
            print(f"⚠️ Could not initialize Open Interpreter: {e}")
    
    def _init_real_estate_interpreter(self):
        """Initialize Real Estate Interpreter (integrated Colonel fork)"""
        try:
            self.interpreter = RealEstateInterpreter(self.settings)
            
            # All agents use the real estate interpreter
            for agent_type, config in self.agent_profiles.items():
                self.available_agents[agent_type] = {
                    'model': 'real_estate_interpreter',
                    'system_message': config['system_message'],
                    'name': config['name']
                }
                print(f"✅ {config['name']} ready with Real Estate Interpreter")
            
            self.backend_ready = True
            print(f"✅ Real Estate Interpreter backend ready ({len(self.available_agents)}/4 agents)")
            
        except Exception as e:
            print(f"⚠️ Could not initialize Real Estate Interpreter: {e}")
    
    def chat_with_agent(self, message: str, agent_type: str = 'property_analyst', stream: bool = False) -> str:
        """Send a message to a specialized agent"""
        if not self.backend_ready:
            return "AI backend is not configured or available. Please check settings."
        
        if agent_type not in self.available_agents:
            available = list(self.available_agents.keys())
            return f"Agent {agent_type} not available. Available agents: {available}"
        
        # Enhance message with property data if address detected
        enhanced_message = self._enhance_message_with_property_data(message)
        
        agent_config = self.available_agents[agent_type]
        
        if self.backend_type == 'ollama':
            return self._chat_with_ollama(enhanced_message, agent_config['model'], 
                                        agent_config['system_message'], agent_config['name'], stream)
        elif self.backend_type == 'openai':
            return self._chat_with_openai(enhanced_message, agent_config['model'], 
                                        agent_config['system_message'], agent_config['name'], stream)
        elif self.backend_type == 'open_interpreter':
            return self._chat_with_interpreter(enhanced_message, agent_config['system_message'], 
                                             agent_config['name'])
        elif self.backend_type == 'real_estate_interpreter':
            return self._chat_with_real_estate_interpreter(enhanced_message, agent_type, 
                                                          agent_config['name'])
        else:
            return "Unknown backend type configured."
    
    def _chat_with_openai(self, message: str, model: str, system_message: str, agent_name: str, stream: bool = False) -> str:
        """Chat with OpenAI API"""
        try:
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": message}
            ]
            
            if stream:
                response = self.openai_client.chat.completions.create(
                    model=model, messages=messages, stream=True
                )
                full_response = ""
                for chunk in response:
                    if chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                return f"[{agent_name}]: {full_response.strip()}"
            else:
                response = self.openai_client.chat.completions.create(
                    model=model, messages=messages, stream=False
                )
                content = response.choices[0].message.content.strip()
                return f"[{agent_name}]: {content}"
                
        except Exception as e:
            return f"[{agent_name}]: Error - {str(e)[:100]}"
    
    def _chat_with_ollama(self, message: str, model: str, system_message: str, agent_name: str, stream: bool = False) -> str:
        """Chat with Ollama API"""
        try:
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": message}
                ],
                "stream": stream
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/chat",
                json=data,
                timeout=120
            )
            
            if response.status_code == 200:
                if stream:
                    full_response = ""
                    for line in response.iter_lines():
                        if line:
                            chunk = json.loads(line)
                            if 'message' in chunk and 'content' in chunk['message']:
                                full_response += chunk['message']['content']
                    return f"[{agent_name}]: {full_response.strip()}"
                else:
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
    
    def _chat_with_interpreter(self, message: str, system_message: str, agent_name: str) -> str:
        """Chat with Open Interpreter"""
        try:
            # Temporarily set the system message for this agent
            original_message = self.interpreter.system_message
            self.interpreter.system_message = system_message
            
            # Chat with interpreter
            response = self.interpreter.chat(message, stream=False)
            
            # Restore original system message
            self.interpreter.system_message = original_message
            
            # Extract response content
            if isinstance(response, str):
                return f"[{agent_name}]: {response}"
            elif isinstance(response, list) and response:
                # Get the last message from assistant
                for msg in reversed(response):
                    if isinstance(msg, dict) and msg.get('role') == 'assistant' and msg.get('content'):
                        return f"[{agent_name}]: {msg['content']}"
                return f"[{agent_name}]: {str(response)}"
            else:
                return f"[{agent_name}]: {str(response)}"
                
        except Exception as e:
            return f"[{agent_name}]: Error - {str(e)[:100]}"
    
    def _chat_with_real_estate_interpreter(self, message: str, agent_type: str, agent_name: str) -> str:
        """Chat with Real Estate Interpreter"""
        try:
            # Use the integrated interpreter with tool calling
            response = self.interpreter.chat(message, agent_type)
            return f"[{agent_name}]: {response}"
            
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
                address = detected_addresses[0].strip()
                print(f"🏠 Detected address: {address}")
                
                # Fetch real property data
                property_data = self.property_service.lookup_property(address)
                
                if 'error' not in property_data:
                    # Build enhanced context
                    property_context = f"""

REAL PROPERTY DATA FOR: {address}
===========================================
Property Type: {property_data['property'].get('type', 'Unknown')}
Bedrooms: {property_data['property'].get('bedrooms', 'Unknown')}
Bathrooms: {property_data['property'].get('bathrooms', 'Unknown')}
Square Feet: {property_data['property'].get('square_feet', 'Unknown'):,}
Year Built: {property_data['property'].get('year_built', 'Unknown')}
Estimated Value: ${property_data['property'].get('estimated_value', 0):,}
Last Sale: ${property_data['property'].get('last_sale_price', 0):,} ({property_data['property'].get('last_sale_date', 'Unknown')})
County: {property_data.get('county', 'Unknown')}

MARKET DATA:
Median Home Value: ${property_data['market'].get('median_home_value', 0):,}
Market Trend: {property_data['market'].get('market_trend', 'Unknown')}
Days on Market: {property_data['market'].get('days_on_market', 'Unknown')}
Market Temperature: {property_data['market'].get('market_temperature', 'Unknown')}

DATA SOURCES USED: {', '.join(property_data.get('data_sources_used', ['Unknown']))}
DATA CONFIDENCE: {property_data.get('data_confidence', 0.0):.1%}

COMPARABLE SALES:
"""
                    for i, comp in enumerate(property_data.get('comparables', [])[:3], 1):
                        property_context += f"{i}. {comp.get('address', 'Unknown')} - ${comp.get('sale_price', 0):,} ({comp.get('sale_date', 'Unknown')}) - {comp.get('bedrooms', '?')}BR/{comp.get('bathrooms', '?')}BA, {comp.get('square_feet', 0):,} sq ft\n"
                    
                    property_context += "\n===========================================\n"
                    
                    # Include public records if available
                    if property_data.get('public_records'):
                        property_context += f"\nPUBLIC RECORDS: Available from {', '.join(property_data['public_records'].get('data_sources', []))}\n"
                    
                    enhanced_message = property_context + f"\nUSER QUESTION: {message}"
                    return enhanced_message
                else:
                    return f"{message}\n\n[Note: Attempted to lookup property data for '{address}' but encountered: {property_data.get('error', 'Unknown error')}]"
            
            return message
            
        except Exception as e:
            print(f"Error enhancing message: {e}")
            return message
    
    def chat(self, message: str, model: str = None) -> str:
        """Send a message using default agent"""
        if not self.backend_ready:
            return "AI backend is not configured or available. Please check settings."
        
        # Use property_analyst as default agent
        if 'property_analyst' in self.available_agents:
            return self.chat_with_agent(message, 'property_analyst')
        elif self.available_agents:
            # Use first available agent
            first_agent = list(self.available_agents.keys())[0]
            return self.chat_with_agent(message, first_agent)
        else:
            return "No agents are currently available. Please check AI settings."
    
    def update_settings(self, new_settings: Dict[str, Any]):
        """Update client settings and reinitialize if needed"""
        old_backend = self.backend_type
        
        self.settings = new_settings
        self.ai_settings = self.settings.get('ai_backend', {})
        self.backend_type = self.ai_settings.get('backend_type', 'ollama')
        
        # Reinitialize if backend changed
        if old_backend != self.backend_type:
            self._init_backend()
        
        # Update property service settings
        mls_settings = self.settings.get('mls_providers', {})
        self.property_service = PropertyService(
            preferred_mls_provider=mls_settings.get('preferred_provider', 'bridge'),
            use_multiple_providers=mls_settings.get('use_multiple_providers', True)
        )
    
    def get_backend_status(self) -> Dict[str, Any]:
        """Get current backend status information"""
        return {
            'backend_type': self.backend_type,
            'backend_ready': self.backend_ready,
            'available_agents': len(self.available_agents),
            'total_agents': len(self.agent_profiles),
            'agent_names': [config['name'] for config in self.available_agents.values()]
        }
    
    # Legacy compatibility methods
    def ping(self) -> bool:
        return self.backend_ready
    
    # Leads
    def list_leads(self):
        """Return list of leads from the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT id, name, phone, email, source, status, last_contact FROM leads ORDER BY last_contact DESC"
            ))
            leads = [dict(row) for row in result.mappings()]
            return leads
    
    def create_lead(self, name: str, email: str, status: str) -> dict:
        """Create a new lead in the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(
                text("INSERT INTO leads (name, email, status, last_contact) VALUES (:name, :email, :status, NOW()) RETURNING id"),
                {"name": name, "email": email, "status": status}
            )
            conn.commit()
            new_id = result.scalar_one()
            return {'id': new_id, 'name': name, 'email': email, 'status': status}

    def update_lead(self, lead_id: int, data: dict):
        """Update an existing lead in the database."""
        set_clauses = []
        params = {"id": lead_id}
        for key, value in data.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        if not set_clauses:
            return None # No data to update

        query = text(f"UPDATE leads SET {', '.join(set_clauses)} WHERE id = :id")
        with self.db_engine.connect() as conn:
            conn.execute(query, params)
            conn.commit()
            return self.get_lead(lead_id) # Fetch updated lead

    def delete_lead(self, lead_id: int):
        """Delete a lead from the database."""
        with self.db_engine.connect() as conn:
            conn.execute(text("DELETE FROM leads WHERE id = :id"), {"id": lead_id})
            conn.commit()

    def get_lead(self, lead_id: int):
        """Retrieve a single lead by ID from the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, name, phone, email, source, status, last_contact FROM leads WHERE id = :id"),
                {"id": lead_id}
            )
            lead = result.mappings().first()
            return dict(lead) if lead else None

    # Properties
    def create_property(self, data: Dict[str, Any]) -> dict:
        """Create a new property in the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(
                text("""INSERT INTO properties (
                    address, city, state, zip_code, property_type, bedrooms, bathrooms, square_feet, lot_size, year_built, listing_price, listing_status, mls_id
                ) VALUES (
                    :address, :city, :state, :zip_code, :property_type, :bedrooms, :bathrooms, :square_feet, :lot_size, :year_built, :listing_price, :listing_status, :mls_id
                ) RETURNING id"""),
                data
            )
            conn.commit()
            new_id = result.scalar_one()
            return {**data, "id": new_id}

    def list_properties(self) -> List[Dict[str, Any]]:
        """Return list of properties from the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT id, address, city, state, zip_code, property_type, bedrooms, bathrooms, square_feet, lot_size, year_built, listing_price, listing_status, mls_id, date_added, last_updated FROM properties ORDER BY last_updated DESC"
            ))
            properties = [dict(row) for row in result.mappings()]
            return properties

    def update_property(self, property_id: int, data: Dict[str, Any]):
        """Update an existing property in the database."""
        set_clauses = []
        params = {"id": property_id}
        for key, value in data.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        if not set_clauses:
            return None # No data to update

        query = text(f"UPDATE properties SET {', '.join(set_clauses)}, last_updated = NOW() WHERE id = :id")
        with self.db_engine.connect() as conn:
            conn.execute(query, params)
            conn.commit()
            return self.get_property(property_id) # Fetch updated property

    def delete_property(self, property_id: int):
        """Delete a property from the database."""
        with self.db_engine.connect() as conn:
            conn.execute(text("DELETE FROM properties WHERE id = :id"), {"id": property_id})
            conn.commit()

    def get_property(self, property_id: int):
        """Retrieve a single property by ID from the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, address, city, state, zip_code, property_type, bedrooms, bathrooms, square_feet, lot_size, year_built, listing_price, listing_status, mls_id, date_added, last_updated FROM properties WHERE id = :id"),
                {"id": property_id}
            )
            prop = result.mappings().first()
            return dict(prop) if prop else None
    
    # Campaigns
    def list_campaigns(self) -> List[Dict[str, Any]]:
        """Return list of campaigns from the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT id, name, status, start_date, date_created, last_updated FROM campaigns ORDER BY last_updated DESC"
            ))
            campaigns = [dict(row) for row in result.mappings()]
            return campaigns

    def create_campaign(self, name: str, status: str, start_date: str) -> dict:
        """Create a new campaign in the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(
                text("INSERT INTO campaigns (name, status, start_date) VALUES (:name, :status, :start_date) RETURNING id"),
                {"name": name, "status": status, "start_date": start_date}
            )
            conn.commit()
            new_id = result.scalar_one()
            return {'id': new_id, 'name': name, 'status': status, 'start_date': start_date}

    def update_campaign(self, campaign_id: int, data: dict):
        """Update existing campaign in the database."""
        set_clauses = []
        params = {"id": campaign_id}
        for key, value in data.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        if not set_clauses:
            return None # No data to update

        query = text(f"UPDATE campaigns SET {', '.join(set_clauses)}, last_updated = NOW() WHERE id = :id")
        with self.db_engine.connect() as conn:
            conn.execute(query, params)
            conn.commit()
            return self.get_campaign(campaign_id) # Fetch updated campaign

    def delete_campaign(self, campaign_id: int):
        """Delete a campaign from the database."""
        with self.db_engine.connect() as conn:
            conn.execute(text("DELETE FROM campaigns WHERE id = :id"), {"id": campaign_id})
            conn.commit()

    def get_campaign(self, campaign_id: int):
        """Retrieve a single campaign by ID from the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, name, status, start_date, date_created, last_updated FROM campaigns WHERE id = :id"),
                {"id": campaign_id}
            )
            campaign = result.mappings().first()
            return dict(campaign) if campaign else None

    # Tasks
    def create_task(self, data: Dict[str, Any]) -> dict:
        """Create a new task in the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(
                text("""INSERT INTO tasks (
                    title, description, due_date, status, priority, assigned_to, lead_id, property_id
                ) VALUES (
                    :title, :description, :due_date, :status, :priority, :assigned_to, :lead_id, :property_id
                ) RETURNING id"""
                ),
                data
            )
            conn.commit()
            new_id = result.scalar_one()
            return {**data, "id": new_id}

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Return list of tasks from the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT id, title, description, due_date, status, priority, assigned_to, lead_id, property_id, date_created, last_updated FROM tasks ORDER BY due_date ASC"
            ))
            tasks = [dict(row) for row in result.mappings()]
            return tasks

    def update_task(self, task_id: int, data: Dict[str, Any]):
        """Update an existing task in the database."""
        set_clauses = []
        params = {"id": task_id}
        for key, value in data.items():
            set_clauses.append(f"{key} = :{key}")
            params[key] = value
        
        if not set_clauses:
            return None # No data to update

        query = text(f"UPDATE tasks SET {', '.join(set_clauses)}, last_updated = NOW() WHERE id = :id")
        with self.db_engine.connect() as conn:
            conn.execute(query, params)
            conn.commit()
            return self.get_task(task_id) # Fetch updated task

    def delete_task(self, task_id: int):
        """Delete a task from the database."""
        with self.db_engine.connect() as conn:
            conn.execute(text("DELETE FROM tasks WHERE id = :id"), {"id": task_id})
            conn.commit()

    def get_task(self, task_id: int):
        """Retrieve a single task by ID from the database."""
        with self.db_engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, title, description, due_date, status, priority, assigned_to, lead_id, property_id, date_created, last_updated FROM tasks WHERE id = :id"),
                {"id": task_id}
            )
            task = result.mappings().first()
            return dict(task) if task else None

    # Marketing Automation
    async def generate_marketing_content(self, content_type: str, prompt: str) -> str:
        """Generate marketing content using the Marketing Expert AI agent."""
        full_prompt = f"Generate a {content_type} for real estate based on the following prompt: {prompt}"
        return self.chat_with_agent(full_prompt, 'marketing_expert')

    async def send_email(self, recipient: str, subject: str, body: str) -> bool:
        """Placeholder for sending email. In a real app, integrate with an email service like SendGrid."""
        print(f"[EMAIL SERVICE] Sending email to {recipient} with subject '{subject}' and body: {body[:100]}...")
        # TODO: Integrate with a real email sending service (e.g., SendGrid, Mailgun)
        return True # Simulate success

    async def send_sms(self, recipient_phone: str, message: str) -> bool:
        """Placeholder for sending SMS. In a real app, integrate with an SMS gateway like Twilio."""
        print(f"[SMS SERVICE] Sending SMS to {recipient_phone} with message: {message[:100]}...")
        # TODO: Integrate with a real SMS gateway (e.g., Twilio)
        return True # Simulate success