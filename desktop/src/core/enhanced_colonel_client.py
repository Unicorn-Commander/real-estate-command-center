"""
Enhanced Colonel Client with Multiple AI Provider Support
Supports: OpenAI, Anthropic, DeepSeek, Groq, xAI, OpenRouter, Ollama, and Open Interpreter
"""
import sys
import os
import requests
import json
import re
import logging
from typing import Dict, List, Any, Optional, Union, Generator
from core.property_service import PropertyService
from core.lead_generator import LeadGenerator
from core.settings_manager import settings_manager
from core.ai_providers import AIProviderManager, AIModel
from core.api_key_manager import api_key_manager
import openai
try:
    from core.real_estate_interpreter import RealEstateInterpreter
except ImportError:
    RealEstateInterpreter = None
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from core.models import Base, Lead, Property, Campaign, Task
from core.agents import AgentManager, MarketMonitorAgent, LeadScoringAgent, PropertyWatcherAgent, CampaignOptimizerAgent

logger = logging.getLogger(__name__)

class EnhancedColonelClient:
    """Enhanced AI client supporting multiple backends including Open Interpreter"""
    
    def __init__(self, settings: Dict[str, Any] = None):
        self.settings = settings or settings_manager.get_all_settings()
        self.ai_settings = self.settings.get('ai_backend', {})
        
        # Initialize AI provider manager
        self.ai_manager = AIProviderManager()
        
        # Initialize based on backend type
        self.backend_type = self.ai_settings.get('backend_type', 'auto')  # 'auto' selects best available
        self.ollama_url = self.ai_settings.get('ollama_url', 'http://localhost:11434')
        self.openai_api_key = self.ai_settings.get('openai_api_key', '')
        self.interpreter_mode = self.ai_settings.get('open_interpreter_mode', 'local')
        self.prefer_cheap_models = self.ai_settings.get('prefer_cheap_models', False)
        self.prefer_fast_models = self.ai_settings.get('prefer_fast_models', False)

        # Initialize database engine
        self.db_engine = create_engine("postgresql://realestate:commander123@localhost:5433/realestate_db")
        Base.metadata.create_all(self.db_engine) # Create tables if they don't exist
        self.Session = sessionmaker(bind=self.db_engine)

        # Initialize real data services
        self.property_service = PropertyService(
            preferred_mls_provider=self.settings.get('mls_providers', {}).get('preferred_provider', 'bridge'),
            use_multiple_providers=self.settings.get('mls_providers', {}).get('use_multiple_providers', True),
            settings=self.settings
        )
        
        # Initialize MLS client for agent use
        self.mls_client = self.property_service.primary_mls_client
        
        # Initialize Agent Manager
        self.agent_manager = AgentManager(
            ai_provider_manager=self.ai_manager,
            colonel_client=self,
            property_service=self.property_service,
            mls_client=self.mls_client,
            database=self.db_engine
        )
        
        # Register all agents
        self._register_agents()

        self._campaigns = [
            {'id': 1, 'name': 'Summer Sale', 'status': 'Active', 'start_date': '2024-06-01'},
            {'id': 2, 'name': 'Holiday Promo', 'status': 'Planned', 'start_date': '2024-11-15'},
            {'id': 3, 'name': 'Referral Drive', 'status': 'Completed', 'start_date': '2024-03-20'},
        ]

        # Get custom models from settings
        custom_models = self.ai_settings.get('custom_models', {})
        
        # Specialized Agent Profiles with recommended models per provider
        self.agent_profiles = {
            'property_analyst': {
                'name': 'Property Analyst',
                'system_message': """You are a specialized Property Analysis Agent for real estate professionals.
Your expertise includes:
- Property valuation and assessment
- Comparable sales analysis (CMA)
- Investment potential evaluation
- Property condition assessment
- Market positioning recommendations

Always provide data-driven insights with specific recommendations.""",
                'recommended_models': {
                    'openai': 'gpt-4o',
                    'anthropic': 'claude-sonnet-4-20250514',
                    'deepseek': 'deepseek-reasoner',
                    'groq': 'llama-3.3-70b-versatile',
                    'xai': 'grok-4',
                    'openrouter': 'anthropic/claude-3.5-sonnet',
                    'ollama': custom_models.get('property_analyst', 'qwen2.5vl:q4_k_m')
                }
            },
            'market_researcher': {
                'name': 'Market Researcher',
                'system_message': """You are a Market Research Specialist for real estate.
Your expertise includes:
- Local market trends and statistics
- Neighborhood analysis and demographics
- Price trend forecasting
- Market timing recommendations
- Competitive market analysis

Focus on actionable market intelligence and trends.""",
                'recommended_models': {
                    'openai': 'gpt-4o',
                    'anthropic': 'claude-sonnet-4-20250514',
                    'deepseek': 'deepseek-chat',
                    'groq': 'mixtral-8x7b-32768',
                    'xai': 'grok-2-1212',
                    'openrouter': 'openai/gpt-4o',
                    'ollama': custom_models.get('market_researcher', 'qwen3:q4_k_m')
                }
            },
            'lead_manager': {
                'name': 'Lead Manager',
                'system_message': """You are a Lead Management Specialist for real estate agents.
Your expertise includes:
- Lead qualification and scoring
- Communication strategy recommendations
- Follow-up scheduling and automation
- Conversion optimization tactics
- Client relationship management

Provide practical lead nurturing strategies.""",
                'recommended_models': {
                    'openai': 'gpt-4o-mini',
                    'anthropic': 'claude-3-5-haiku-20241022',
                    'deepseek': 'deepseek-chat',
                    'groq': 'llama-3.1-8b-instant',
                    'xai': 'grok-2-1212',
                    'openrouter': 'meta-llama/llama-3.3-70b-instruct:free',
                    'ollama': custom_models.get('lead_manager', 'gemma3:4b-q4_k_m')
                }
            },
            'marketing_expert': {
                'name': 'Marketing Expert',
                'system_message': """You are a Real Estate Marketing Expert.
Your expertise includes:
- Property listing optimization
- Marketing campaign development
- Social media strategy for real estate
- Content creation for property promotion
- Target audience identification

Create compelling marketing strategies that convert.""",
                'recommended_models': {
                    'openai': 'gpt-4o-mini',
                    'anthropic': 'claude-3-5-haiku-20241022',
                    'deepseek': 'deepseek-chat',
                    'groq': 'gemma2-9b-it',
                    'xai': 'grok-2-1212',
                    'openrouter': 'google/gemini-2.0-flash-thinking-exp:free',
                    'ollama': custom_models.get('marketing_expert', 'gemma3:4b-q4_k_m')
                }
            },
            'real_estate_agent': {
                'name': 'Real Estate Agent',
                'system_message': """You are a highly skilled Real Estate Agent AI, specializing in contract review, negotiation strategies, and deal closing. Your expertise includes:
- Analyzing real estate contracts for key clauses, risks, and opportunities.
- Proposing effective negotiation tactics based on market conditions and client goals.
- Identifying potential legal pitfalls and advising on mitigation.
- Providing clear, concise summaries of complex legal documents.
- Assisting with offer drafting and counter-offer strategies.

Always provide actionable advice and highlight critical information for the user.""",
                'recommended_models': {
                    'openai': 'gpt-4o',
                    'anthropic': 'claude-opus-4-20250514',
                    'deepseek': 'deepseek-reasoner',
                    'groq': 'llama-3.3-70b-versatile',
                    'xai': 'grok-4-heavy',
                    'openrouter': 'anthropic/claude-3.5-sonnet',
                    'ollama': custom_models.get('real_estate_agent', 'llama3:8b')
                }
            }
        }
        
        # Available models cache
        self._available_models = None
        self._model_recommendations = None
        
        # Initialize the selected backend
        self._init_backend()
        self._test_connections()
    
    def _test_connections(self):
        """Test all AI provider connections"""
        logger.info("Testing AI provider connections...")
        results = self.ai_manager.test_all_connections()
        
        for provider, result in results.items():
            if result['status'] == 'success':
                logger.info(f"✅ {provider}: Connected")
            else:
                logger.info(f"⚠️ {provider}: {result['message']}")
    
    def get_available_models(self) -> List[AIModel]:
        """Get all available AI models"""
        if self._available_models is None:
            self._available_models = self.ai_manager.list_all_models()
        return self._available_models
    
    def get_model_for_agent(self, agent_type: str, quality: str = 'good', 
                           prefer_cheap: bool = None, prefer_fast: bool = None) -> Optional[str]:
        """Get the best model for a specific agent type"""
        # Use global preferences if not specified
        if prefer_cheap is None:
            prefer_cheap = self.prefer_cheap_models
        if prefer_fast is None:
            prefer_fast = self.prefer_fast_models
            
        if agent_type not in self.agent_profiles:
            return None
            
        profile = self.agent_profiles[agent_type]
        available_models = self.get_available_models()
        
        # First try recommended models
        quality_levels = ['basic', 'good', 'excellent', 'frontier']
        for provider, model_id in profile['recommended_models'].items():
            if any(m.id == model_id for m in available_models):
                model = next(m for m in available_models if m.id == model_id)
                
                # Check if it meets quality requirements
                if quality_levels.index(model.quality) >= quality_levels.index(quality):
                    if prefer_cheap and model.input_cost > 5.0:  # Skip expensive models
                        continue
                    if prefer_fast and model.speed in ['slow', 'medium']:  # Skip slow models
                        continue
                    return model_id
                    
        # Fallback to finding any suitable model
        if prefer_cheap:
            model = self.ai_manager.get_cheapest_model(quality)
        elif prefer_fast:
            model = self.ai_manager.get_fastest_model(quality)
        else:
            # Get any model meeting quality requirements
            suitable_models = [m for m in available_models 
                             if quality_levels.index(m.quality) >= quality_levels.index(quality)]
            if suitable_models:
                model = suitable_models[0]
            else:
                model = None
                
        return model.id if model else None
    
    def analyze_contract(self, contract_text: str, model_preference: str = None) -> Dict[str, Any]:
        """Analyzes a real estate contract using AI"""
        prompt = f"""Analyze this real estate contract for key terms, risks, and negotiation points:

{contract_text}

Provide:
1. Summary of key terms and conditions
2. Identified risks or concerning clauses
3. Potential negotiation points
4. Recommended actions

Format your response with clear sections."""
        
        model_id = model_preference or self.get_model_for_agent('real_estate_agent', quality='excellent')
        response = self.chat_with_agent(prompt, 'real_estate_agent', model_id=model_id)
        
        return {
            'analysis': response,
            'model_used': model_id,
            'status': 'completed'
        }
    
    def _init_backend(self):
        """Initialize the selected AI backend"""
        self.available_agents = {}
        self.backend_ready = False
        
        # If backend_type is 'auto', determine the best available backend
        if self.backend_type == 'auto':
            available_providers = list(self.ai_manager.providers.keys())
            if available_providers:
                # Prefer providers in this order
                preferred_order = ['openai', 'anthropic', 'deepseek', 'groq', 'openrouter', 'xai', 'ollama']
                for provider in preferred_order:
                    if provider in available_providers:
                        self.backend_type = provider
                        break
                else:
                    self.backend_type = available_providers[0]
                logger.info(f"Auto-selected backend: {self.backend_type}")
            else:
                # Fall back to legacy backends
                if self._check_ollama_available():
                    self.backend_type = 'ollama'
                elif self.backend_type == 'open_interpreter':
                    self.backend_type = 'open_interpreter'
                else:
                    logger.warning("No AI backend available")
                    return
        
        # Initialize modern AI providers
        if self.backend_type in ['openai', 'anthropic', 'deepseek', 'groq', 'xai', 'openrouter']:
            self._init_ai_provider()
        # Legacy backends
        elif self.backend_type == 'ollama':
            self._init_ollama()
        elif self.backend_type == 'open_interpreter':
            self._init_open_interpreter()
        elif self.backend_type == 'real_estate_interpreter' and RealEstateInterpreter:
            self._init_real_estate_interpreter()
        else:
            logger.warning(f"Unknown backend type: {self.backend_type}")
    
    def _check_ollama_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _init_ai_provider(self):
        """Initialize modern AI provider backend"""
        provider = self.ai_manager.get_provider(self.backend_type)
        if not provider:
            logger.warning(f"Provider {self.backend_type} not configured")
            return
            
        # Set up available agents for this provider
        for agent_type, profile in self.agent_profiles.items():
            # Get the best model for this agent
            model_id = self.get_model_for_agent(agent_type)
            if model_id:
                self.available_agents[agent_type] = {
                    'model': model_id,
                    'system_message': profile['system_message'],
                    'name': profile['name']
                }
                logger.info(f"✅ {profile['name']} ready with {model_id}")
            else:
                logger.warning(f"⚠️ No suitable model for {profile['name']}")
        
        self.backend_ready = len(self.available_agents) > 0
        logger.info(f"✅ {self.backend_type} backend ready ({len(self.available_agents)}/{len(self.agent_profiles)} agents)")
    
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
    
    def chat_with_agent(self, message: str, agent_type: str = 'property_analyst', 
                       model_id: str = None, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Send a message to a specialized agent using the best available model"""
        if not self.backend_ready and not self.ai_manager.providers:
            return "No AI backend is configured or available. Please check settings."
        
        # If using modern AI providers
        if self.backend_type in ['openai', 'anthropic', 'deepseek', 'groq', 'xai', 'openrouter'] or model_id:
            return self._chat_with_ai_provider(message, agent_type, model_id, stream, **kwargs)
        
        # Legacy backend handling
        if agent_type not in self.available_agents:
            available = list(self.available_agents.keys())
            return f"Agent {agent_type} not available. Available agents: {available}"
        
        # Enhance message with property data if address detected
        enhanced_message = self._enhance_message_with_property_data(message)
        
        agent_config = self.available_agents[agent_type]
        
        if self.backend_type == 'ollama':
            return self._chat_with_ollama(enhanced_message, agent_config['model'], 
                                        agent_config['system_message'], agent_config['name'], stream)
        elif self.backend_type == 'open_interpreter':
            return self._chat_with_interpreter(enhanced_message, agent_config['system_message'], 
                                             agent_config['name'])
        elif self.backend_type == 'real_estate_interpreter':
            return self._chat_with_real_estate_interpreter(enhanced_message, agent_type, 
                                                          agent_config['name'])
        else:
            return "Unknown backend type configured."
    
    def _chat_with_ai_provider(self, message: str, agent_type: str, model_id: str = None, 
                              stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Chat using modern AI providers"""
        if agent_type not in self.agent_profiles:
            available = list(self.agent_profiles.keys())
            return f"Agent {agent_type} not available. Available agents: {available}"
            
        # Get model if not specified
        if not model_id:
            model_id = self.get_model_for_agent(agent_type, **kwargs)
            if not model_id:
                return f"No suitable AI model available for {agent_type}"
                
        # Enhance message with property data if applicable
        enhanced_message = self._enhance_message_with_property_data(message)
        
        # Prepare messages
        profile = self.agent_profiles[agent_type]
        messages = [
            {"role": "system", "content": profile['system_message']},
            {"role": "user", "content": enhanced_message}
        ]
        
        try:
            response = self.ai_manager.chat(messages, model_id, stream, **kwargs)
            
            if stream:
                def generate():
                    yield f"[{profile['name']} via {model_id}]: "
                    for chunk in response:
                        yield chunk
                return generate()
            else:
                return f"[{profile['name']} via {model_id}]: {response}"
                
        except Exception as e:
            logger.error(f"Error chatting with {model_id}: {e}")
            return f"[{profile['name']}]: Error - {str(e)[:200]}"
    
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
                timeout=300
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
        self.backend_type = self.ai_settings.get('backend_type', 'auto')
        self.prefer_cheap_models = self.ai_settings.get('prefer_cheap_models', False)
        self.prefer_fast_models = self.ai_settings.get('prefer_fast_models', False)
        
        # Reinitialize AI manager with new settings
        self.ai_manager = AIProviderManager()
        
        # Clear caches
        self._available_models = None
        self._model_recommendations = None
        
        # Reinitialize if backend changed
        if old_backend != self.backend_type:
            self._init_backend()
            self._test_connections()
        
        # Update property service settings
        mls_settings = self.settings.get('mls_providers', {})
        self.property_service = PropertyService(
            preferred_mls_provider=mls_settings.get('preferred_provider', 'bridge'),
            use_multiple_providers=mls_settings.get('use_multiple_providers', True),
            settings=new_settings
        )
    
    def get_backend_status(self) -> Dict[str, Any]:
        """Get current backend status information"""
        status = {
            'backend_type': self.backend_type,
            'backend_ready': self.backend_ready,
            'available_agents': len(self.available_agents),
            'total_agents': len(self.agent_profiles),
            'agent_names': [config['name'] for config in self.available_agents.values()],
            'available_providers': list(self.ai_manager.providers.keys()),
            'total_models': len(self.get_available_models())
        }
        
        # Add model recommendations
        if not self._model_recommendations:
            self._model_recommendations = self.get_model_recommendations()
        status['model_recommendations'] = self._model_recommendations
        
        return status
    
    def get_model_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for which models to use for different tasks"""
        recommendations = {}
        
        for agent_type in self.agent_profiles.keys():
            task_name = agent_type.replace('_', ' ').title()
            recommendations[task_name] = {
                'best_quality': self.get_model_for_agent(agent_type, quality='frontier'),
                'best_value': self.get_model_for_agent(agent_type, quality='good', prefer_cheap=True),
                'fastest': self.get_model_for_agent(agent_type, quality='good', prefer_fast=True)
            }
            
        return recommendations
    
    def estimate_cost(self, message: str, agent_type: str = 'property_analyst', 
                     model_id: str = None, expected_response_tokens: int = 1000) -> Dict[str, float]:
        """Estimate the cost of a query"""
        if not model_id:
            model_id = self.get_model_for_agent(agent_type)
            
        available_models = self.get_available_models()
        model = next((m for m in available_models if m.id == model_id), None)
        
        if not model:
            return {'error': f'Model {model_id} not found'}
            
        # Rough token estimation (1 token ≈ 4 characters)
        input_tokens = len(message) / 4
        
        input_cost = (input_tokens / 1_000_000) * model.input_cost
        output_cost = (expected_response_tokens / 1_000_000) * model.output_cost
        
        return {
            'model': model_id,
            'provider': model.provider,
            'estimated_input_tokens': int(input_tokens),
            'estimated_output_tokens': expected_response_tokens,
            'input_cost': round(input_cost, 6),
            'output_cost': round(output_cost, 6),
            'total_cost': round(input_cost + output_cost, 6),
            'cost_per_million_tokens': (model.input_cost + model.output_cost) / 2
        }
    
    def compare_multi_agent_responses(self, query: str, agents: List[str] = None) -> Dict[str, str]:
        """Get responses from multiple agents for comparison"""
        if not agents:
            agents = list(self.agent_profiles.keys())
            
        responses = {}
        
        for agent in agents:
            if agent in self.agent_profiles:
                try:
                    # Use different models for variety
                    model_id = self.get_model_for_agent(agent, prefer_cheap=True)
                    response = self.chat_with_agent(query, agent, model_id=model_id)
                    responses[self.agent_profiles[agent]['name']] = response
                except Exception as e:
                    responses[self.agent_profiles[agent]['name']] = f"Error: {str(e)}"
                    
        return responses
    
    # Legacy compatibility methods
    def ping(self) -> bool:
        return self.backend_ready
    
    # Leads
    def list_leads(self):
        """Return list of leads from the database using ORM."""
        session = self.Session()
        try:
            leads = session.query(Lead).order_by(Lead.last_contact.desc()).all()
            return [l.__dict__ for l in leads] # Convert to dictionary for compatibility
        finally:
            session.close()
    
    def create_lead(self, name: str, email: str, status: str, phone: str = None, source: str = None) -> dict:
        """Create a new lead in the database using ORM."""
        session = self.Session()
        try:
            new_lead = Lead(name=name, email=email, status=status, phone=phone, source=source)
            session.add(new_lead)
            session.commit()
            session.refresh(new_lead)
            return new_lead.__dict__
        finally:
            session.close()

    def update_lead(self, lead_id: int, data: dict):
        """Update an existing lead in the database using ORM."""
        session = self.Session()
        try:
            lead = session.query(Lead).filter_by(id=lead_id).first()
            if lead:
                for key, value in data.items():
                    setattr(lead, key, value)
                session.commit()
                session.refresh(lead)
                return lead.__dict__
            return None
        finally:
            session.close()

    def delete_lead(self, lead_id: int):
        """Delete a lead from the database using ORM."""
        session = self.Session()
        try:
            lead = session.query(Lead).filter_by(id=lead_id).first()
            if lead:
                session.delete(lead)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_lead(self, lead_id: int):
        """Retrieve a single lead by ID from the database using ORM."""
        session = self.Session()
        try:
            lead = session.query(Lead).filter_by(id=lead_id).first()
            return lead.__dict__ if lead else None
        finally:
            session.close()

    # Properties
    def create_property(self, data: Dict[str, Any]) -> dict:
        """Create a new property in the database using ORM."""
        session = self.Session()
        try:
            new_property = Property(**data)
            session.add(new_property)
            session.commit()
            session.refresh(new_property)
            return new_property.__dict__
        finally:
            session.close()

    def list_properties(self) -> List[Dict[str, Any]]:
        """Return list of properties from the database using ORM."""
        session = self.Session()
        try:
            properties = session.query(Property).order_by(Property.last_updated.desc()).all()
            return [p.__dict__ for p in properties]
        finally:
            session.close()

    def update_property(self, property_id: int, data: Dict[str, Any]):
        """Update an existing property in the database using ORM."""
        session = self.Session()
        try:
            prop = session.query(Property).filter_by(id=property_id).first()
            if prop:
                for key, value in data.items():
                    setattr(prop, key, value)
                session.commit()
                session.refresh(prop)
                return prop.__dict__
            return None
        finally:
            session.close()

    def delete_property(self, property_id: int):
        """Delete a property from the database using ORM."""
        session = self.Session()
        try:
            prop = session.query(Property).filter_by(id=property_id).first()
            if prop:
                session.delete(prop)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_property(self, property_id: int):
        """Retrieve a single property by ID from the database using ORM."""
        session = self.Session()
        try:
            prop = session.query(Property).filter_by(id=property_id).first()
            return prop.__dict__ if prop else None
        finally:
            session.close()
    
    # Campaigns
    def list_campaigns(self) -> List[Dict[str, Any]]:
        """Return list of campaigns from the database using ORM."""
        session = self.Session()
        try:
            campaigns = session.query(Campaign).order_by(Campaign.last_updated.desc()).all()
            return [c.__dict__ for c in campaigns]
        finally:
            session.close()

    def create_campaign(self, name: str, status: str, start_date: str) -> dict:
        """Create a new campaign in the database using ORM."""
        session = self.Session()
        try:
            new_campaign = Campaign(name=name, status=status, start_date=start_date)
            session.add(new_campaign)
            session.commit()
            session.refresh(new_campaign)
            return new_campaign.__dict__
        finally:
            session.close()

    def update_campaign(self, campaign_id: int, data: dict):
        """Update existing campaign in the database using ORM."""
        session = self.Session()
        try:
            campaign = session.query(Campaign).filter_by(id=campaign_id).first()
            if campaign:
                for key, value in data.items():
                    setattr(campaign, key, value)
                session.commit()
                session.refresh(campaign)
                return campaign.__dict__
            return None
        finally:
            session.close()

    def delete_campaign(self, campaign_id: int):
        """Delete a campaign from the database using ORM."""
        session = self.Session()
        try:
            campaign = session.query(Campaign).filter_by(id=campaign_id).first()
            if campaign:
                session.delete(campaign)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_campaign(self, campaign_id: int):
        """Retrieve a single campaign by ID from the database using ORM."""
        session = self.Session()
        try:
            campaign = session.query(Campaign).filter_by(id=campaign_id).first()
            return campaign.__dict__ if campaign else None
        finally:
            session.close()

    # Tasks
    def create_task(self, data: Dict[str, Any]) -> dict:
        """Create a new task in the database using ORM."""
        session = self.Session()
        try:
            new_task = Task(**data)
            session.add(new_task)
            session.commit()
            session.refresh(new_task)
            return new_task.__dict__
        finally:
            session.close()

    def list_tasks(self) -> List[Dict[str, Any]]:
        """Return list of tasks from the database using ORM."""
        session = self.Session()
        try:
            tasks = session.query(Task).order_by(Task.due_date.asc()).all()
            return [t.__dict__ for t in tasks]
        finally:
            session.close()

    def update_task(self, task_id: int, data: Dict[str, Any]):
        """Update an existing task in the database using ORM."""
        session = self.Session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if task:
                for key, value in data.items():
                    setattr(task, key, value)
                session.commit()
                session.refresh(task)
                return task.__dict__
            return None
        finally:
            session.close()

    def delete_task(self, task_id: int):
        """Delete a task from the database using ORM."""
        session = self.Session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            if task:
                session.delete(task)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def get_task(self, task_id: int):
        """Retrieve a single task by ID from the database using ORM."""
        session = self.Session()
        try:
            task = session.query(Task).filter_by(id=task_id).first()
            return task.__dict__ if task else None
        finally:
            session.close()

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
    
    def _register_agents(self):
        """Register all autonomous agents with the agent manager"""
        try:
            # Market Monitor Agent
            market_monitor = MarketMonitorAgent()
            self.agent_manager.register_agent(market_monitor, auto_start=True)
            
            # Lead Scoring Agent
            lead_scorer = LeadScoringAgent()
            self.agent_manager.register_agent(lead_scorer, auto_start=True)
            
            # Property Watcher Agent
            property_watcher = PropertyWatcherAgent()
            self.agent_manager.register_agent(property_watcher, auto_start=True)
            
            # Campaign Optimizer Agent
            campaign_optimizer = CampaignOptimizerAgent()
            self.agent_manager.register_agent(campaign_optimizer, auto_start=True)
            
            logger.info("All autonomous agents registered successfully")
        except Exception as e:
            logger.error(f"Failed to register agents: {str(e)}")
    
    def get_agent_manager(self):
        """Get the agent manager instance"""
        return self.agent_manager