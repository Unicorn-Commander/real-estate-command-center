"""
AI Providers Integration Module
Supports multiple AI providers: OpenAI, Anthropic, DeepSeek, Groq, xAI, and OpenRouter
"""
import os
import json
import requests
import logging
from typing import Dict, List, Any, Optional, Generator, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
import openai
import anthropic

logger = logging.getLogger(__name__)

@dataclass
class AIModel:
    """Represents an AI model with its properties"""
    id: str
    name: str
    provider: str
    input_cost: float  # per million tokens
    output_cost: float  # per million tokens
    context_window: int
    capabilities: List[str]  # e.g., ['text', 'vision', 'function_calling']
    speed: str  # 'fast', 'medium', 'slow'
    quality: str  # 'basic', 'good', 'excellent', 'frontier'
    
class AIProvider(ABC):
    """Base class for AI providers"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.base_url = None
        self.headers = {}
        
    @abstractmethod
    def list_models(self) -> List[AIModel]:
        """List available models"""
        pass
        
    @abstractmethod
    def chat(self, messages: List[Dict[str, str]], model: str, stream: bool = False, 
             **kwargs) -> Union[str, Generator[str, None, None]]:
        """Send chat request to the provider"""
        pass
        
    @abstractmethod
    def test_connection(self) -> Dict[str, Any]:
        """Test the connection to the provider"""
        pass

class OpenAIProvider(AIProvider):
    """OpenAI API provider"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.environ.get('OPENAI_API_KEY'))
        self.client = openai.OpenAI(api_key=self.api_key) if self.api_key else None
        
    def list_models(self) -> List[AIModel]:
        """List OpenAI models with 2025 pricing"""
        return [
            AIModel(
                id="gpt-4o",
                name="GPT-4o (Omni)",
                provider="openai",
                input_cost=2.50,  # per million tokens
                output_cost=10.00,
                context_window=128000,
                capabilities=['text', 'vision', 'function_calling'],
                speed='medium',
                quality='excellent'
            ),
            AIModel(
                id="gpt-4o-mini", 
                name="GPT-4o Mini",
                provider="openai",
                input_cost=0.15,
                output_cost=0.60,
                context_window=128000,
                capabilities=['text', 'vision', 'function_calling'],
                speed='fast',
                quality='good'
            ),
            AIModel(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider="openai",
                input_cost=10.00,
                output_cost=30.00,
                context_window=128000,
                capabilities=['text', 'vision', 'function_calling'],
                speed='medium',
                quality='excellent'
            ),
            AIModel(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                input_cost=0.50,
                output_cost=1.50,
                context_window=16385,
                capabilities=['text', 'function_calling'],
                speed='fast',
                quality='good'
            )
        ]
        
    def chat(self, messages: List[Dict[str, str]], model: str, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Send chat request to OpenAI"""
        if not self.client:
            raise ValueError("OpenAI API key not configured")
            
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=stream,
                **kwargs
            )
            
            if stream:
                def generate():
                    for chunk in response:
                        if chunk.choices[0].delta.content:
                            yield chunk.choices[0].delta.content
                return generate()
            else:
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
            
    def test_connection(self) -> Dict[str, Any]:
        """Test OpenAI connection"""
        try:
            if not self.client:
                return {"status": "error", "message": "API key not configured"}
                
            # Try to list models as a connection test
            self.client.models.list()
            return {"status": "success", "provider": "OpenAI"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class AnthropicProvider(AIProvider):
    """Anthropic (Claude) API provider"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.environ.get('ANTHROPIC_API_KEY'))
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None
        
    def list_models(self) -> List[AIModel]:
        """List Anthropic models with 2025 pricing"""
        return [
            AIModel(
                id="claude-opus-4-20250514",
                name="Claude Opus 4",
                provider="anthropic",
                input_cost=15.00,
                output_cost=75.00,
                context_window=200000,
                capabilities=['text', 'vision'],
                speed='slow',
                quality='frontier'
            ),
            AIModel(
                id="claude-sonnet-4-20250514",
                name="Claude Sonnet 4",
                provider="anthropic",
                input_cost=3.00,
                output_cost=15.00,
                context_window=200000,
                capabilities=['text', 'vision'],
                speed='medium',
                quality='excellent'
            ),
            AIModel(
                id="claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                input_cost=3.00,
                output_cost=15.00,
                context_window=200000,
                capabilities=['text', 'vision'],
                speed='medium',
                quality='excellent'
            ),
            AIModel(
                id="claude-3-5-haiku-20241022",
                name="Claude 3.5 Haiku",
                provider="anthropic",
                input_cost=0.80,
                output_cost=4.00,
                context_window=200000,
                capabilities=['text'],
                speed='fast',
                quality='good'
            )
        ]
        
    def chat(self, messages: List[Dict[str, str]], model: str, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Send chat request to Anthropic"""
        if not self.client:
            raise ValueError("Anthropic API key not configured")
            
        try:
            # Convert OpenAI format to Anthropic format
            system_message = None
            claude_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    claude_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
                    
            response = self.client.messages.create(
                model=model,
                messages=claude_messages,
                system=system_message,
                max_tokens=kwargs.get('max_tokens', 4096),
                stream=stream
            )
            
            if stream:
                def generate():
                    for chunk in response:
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                            yield chunk.delta.text
                return generate()
            else:
                return response.content[0].text
                
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
            
    def test_connection(self) -> Dict[str, Any]:
        """Test Anthropic connection"""
        try:
            if not self.client:
                return {"status": "error", "message": "API key not configured"}
                
            # Try a minimal request
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return {"status": "success", "provider": "Anthropic"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class DeepSeekProvider(AIProvider):
    """DeepSeek API provider"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.environ.get('DEEPSEEK_API_KEY'))
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def list_models(self) -> List[AIModel]:
        """List DeepSeek models with 2025 pricing"""
        return [
            AIModel(
                id="deepseek-chat",
                name="DeepSeek V3 Chat",
                provider="deepseek",
                input_cost=0.27,
                output_cost=1.10,
                context_window=64000,
                capabilities=['text'],
                speed='fast',
                quality='excellent'
            ),
            AIModel(
                id="deepseek-reasoner",
                name="DeepSeek R1 Reasoning",
                provider="deepseek",
                input_cost=0.55,
                output_cost=2.19,
                context_window=64000,
                capabilities=['text', 'reasoning'],
                speed='medium',
                quality='frontier'
            )
        ]
        
    def chat(self, messages: List[Dict[str, str]], model: str, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Send chat request to DeepSeek"""
        if not self.api_key:
            raise ValueError("DeepSeek API key not configured")
            
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": stream,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                def generate():
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]
                                if data != '[DONE]':
                                    chunk = json.loads(data)
                                    if chunk['choices'][0]['delta'].get('content'):
                                        yield chunk['choices'][0]['delta']['content']
                return generate()
            else:
                result = response.json()
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            raise
            
    def test_connection(self) -> Dict[str, Any]:
        """Test DeepSeek connection"""
        try:
            if not self.api_key:
                return {"status": "error", "message": "API key not configured"}
                
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            response.raise_for_status()
            return {"status": "success", "provider": "DeepSeek"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class GroqProvider(AIProvider):
    """Groq LPU API provider"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.environ.get('GROQ_API_KEY'))
        self.base_url = "https://api.groq.com/openai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def list_models(self) -> List[AIModel]:
        """List Groq models - pricing varies by model size"""
        return [
            AIModel(
                id="llama-3.3-70b-versatile",
                name="Llama 3.3 70B",
                provider="groq",
                input_cost=0.59,
                output_cost=0.79,
                context_window=128000,
                capabilities=['text'],
                speed='fast',
                quality='excellent'
            ),
            AIModel(
                id="llama-3.1-8b-instant",
                name="Llama 3.1 8B",
                provider="groq",
                input_cost=0.05,
                output_cost=0.08,
                context_window=128000,
                capabilities=['text'],
                speed='very_fast',
                quality='good'
            ),
            AIModel(
                id="mixtral-8x7b-32768",
                name="Mixtral 8x7B",
                provider="groq",
                input_cost=0.24,
                output_cost=0.24,
                context_window=32768,
                capabilities=['text'],
                speed='fast',
                quality='good'
            ),
            AIModel(
                id="gemma2-9b-it",
                name="Gemma 2 9B",
                provider="groq",
                input_cost=0.20,
                output_cost=0.20,
                context_window=8192,
                capabilities=['text'],
                speed='very_fast',
                quality='good'
            )
        ]
        
    def chat(self, messages: List[Dict[str, str]], model: str, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Send chat request to Groq"""
        if not self.api_key:
            raise ValueError("Groq API key not configured")
            
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": stream,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                def generate():
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]
                                if data != '[DONE]':
                                    chunk = json.loads(data)
                                    if chunk['choices'][0]['delta'].get('content'):
                                        yield chunk['choices'][0]['delta']['content']
                return generate()
            else:
                result = response.json()
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise
            
    def test_connection(self) -> Dict[str, Any]:
        """Test Groq connection"""
        try:
            if not self.api_key:
                return {"status": "error", "message": "API key not configured"}
                
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            response.raise_for_status()
            return {"status": "success", "provider": "Groq"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class XAIProvider(AIProvider):
    """xAI (Grok) API provider"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.environ.get('XAI_API_KEY'))
        self.base_url = "https://api.x.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def list_models(self) -> List[AIModel]:
        """List xAI Grok models"""
        return [
            AIModel(
                id="grok-4",
                name="Grok 4",
                provider="xai",
                input_cost=5.00,  # Estimated based on premium pricing
                output_cost=15.00,
                context_window=131072,
                capabilities=['text', 'web_search'],
                speed='medium',
                quality='frontier'
            ),
            AIModel(
                id="grok-4-heavy",
                name="Grok 4 Heavy (Multi-Agent)",
                provider="xai",
                input_cost=10.00,  # Premium model
                output_cost=30.00,
                context_window=131072,
                capabilities=['text', 'web_search', 'multi_agent'],
                speed='slow',
                quality='frontier'
            ),
            AIModel(
                id="grok-2-1212",
                name="Grok 2",
                provider="xai",
                input_cost=2.00,
                output_cost=10.00,
                context_window=131072,
                capabilities=['text', 'web_search'],
                speed='medium',
                quality='excellent'
            )
        ]
        
    def chat(self, messages: List[Dict[str, str]], model: str, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Send chat request to xAI"""
        if not self.api_key:
            raise ValueError("xAI API key not configured")
            
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": stream,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                def generate():
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]
                                if data != '[DONE]':
                                    chunk = json.loads(data)
                                    if chunk['choices'][0]['delta'].get('content'):
                                        yield chunk['choices'][0]['delta']['content']
                return generate()
            else:
                result = response.json()
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            logger.error(f"xAI API error: {e}")
            raise
            
    def test_connection(self) -> Dict[str, Any]:
        """Test xAI connection"""
        try:
            if not self.api_key:
                return {"status": "error", "message": "API key not configured"}
                
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            response.raise_for_status()
            return {"status": "success", "provider": "xAI"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class OpenRouterProvider(AIProvider):
    """OpenRouter unified API provider"""
    
    def __init__(self, api_key: str = None):
        super().__init__(api_key or os.environ.get('OPENROUTER_API_KEY'))
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://real-estate-command-center.local",
            "X-Title": "Real Estate Command Center"
        }
        
    def list_models(self) -> List[AIModel]:
        """List some popular OpenRouter models"""
        # Note: OpenRouter has 400+ models, this is just a sample
        return [
            AIModel(
                id="openai/gpt-4o",
                name="GPT-4o (via OpenRouter)",
                provider="openrouter",
                input_cost=2.50,
                output_cost=10.00,
                context_window=128000,
                capabilities=['text', 'vision'],
                speed='medium',
                quality='excellent'
            ),
            AIModel(
                id="anthropic/claude-3.5-sonnet",
                name="Claude 3.5 Sonnet (via OpenRouter)",
                provider="openrouter",
                input_cost=3.00,
                output_cost=15.00,
                context_window=200000,
                capabilities=['text', 'vision'],
                speed='medium',
                quality='excellent'
            ),
            AIModel(
                id="google/gemini-2.0-flash-thinking-exp:free",
                name="Gemini 2.0 Flash (Free)",
                provider="openrouter",
                input_cost=0.00,
                output_cost=0.00,
                context_window=32768,
                capabilities=['text'],
                speed='fast',
                quality='good'
            ),
            AIModel(
                id="deepseek/deepseek-chat",
                name="DeepSeek Chat (via OpenRouter)",
                provider="openrouter",
                input_cost=0.14,
                output_cost=0.28,
                context_window=64000,
                capabilities=['text'],
                speed='fast',
                quality='excellent'
            ),
            AIModel(
                id="meta-llama/llama-3.3-70b-instruct:free",
                name="Llama 3.3 70B (Free)",
                provider="openrouter",
                input_cost=0.00,
                output_cost=0.00,
                context_window=8000,
                capabilities=['text'],
                speed='medium',
                quality='excellent'
            )
        ]
        
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Fetch all available models from OpenRouter API"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()['data']
        except Exception as e:
            logger.error(f"Failed to fetch OpenRouter models: {e}")
            return []
            
    def chat(self, messages: List[Dict[str, str]], model: str, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Send chat request to OpenRouter"""
        if not self.api_key:
            raise ValueError("OpenRouter API key not configured")
            
        try:
            data = {
                "model": model,
                "messages": messages,
                "stream": stream,
                **kwargs
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=data,
                stream=stream
            )
            response.raise_for_status()
            
            if stream:
                def generate():
                    for line in response.iter_lines():
                        if line:
                            line = line.decode('utf-8')
                            if line.startswith('data: '):
                                data = line[6:]
                                if data != '[DONE]':
                                    chunk = json.loads(data)
                                    if chunk['choices'][0]['delta'].get('content'):
                                        yield chunk['choices'][0]['delta']['content']
                return generate()
            else:
                result = response.json()
                return result['choices'][0]['message']['content']
                
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise
            
    def test_connection(self) -> Dict[str, Any]:
        """Test OpenRouter connection"""
        try:
            if not self.api_key:
                return {"status": "error", "message": "API key not configured"}
                
            response = requests.get(
                f"{self.base_url}/models",
                headers=self.headers
            )
            response.raise_for_status()
            return {"status": "success", "provider": "OpenRouter"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class AIProviderManager:
    """Manages multiple AI providers"""
    
    def __init__(self):
        self.providers = {}
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize all available providers"""
        # OpenAI
        if os.environ.get('OPENAI_API_KEY') or settings_manager.get_setting('ai.api_keys.openai'):
            self.providers['openai'] = OpenAIProvider()
            
        # Anthropic
        if os.environ.get('ANTHROPIC_API_KEY') or settings_manager.get_setting('ai.api_keys.anthropic'):
            self.providers['anthropic'] = AnthropicProvider()
            
        # DeepSeek
        if os.environ.get('DEEPSEEK_API_KEY') or settings_manager.get_setting('ai.api_keys.deepseek'):
            self.providers['deepseek'] = DeepSeekProvider()
            
        # Groq
        if os.environ.get('GROQ_API_KEY') or settings_manager.get_setting('ai.api_keys.groq'):
            self.providers['groq'] = GroqProvider()
            
        # xAI
        if os.environ.get('XAI_API_KEY') or settings_manager.get_setting('ai.api_keys.xai'):
            self.providers['xai'] = XAIProvider()
            
        # OpenRouter
        if os.environ.get('OPENROUTER_API_KEY') or settings_manager.get_setting('ai.api_keys.openrouter'):
            self.providers['openrouter'] = OpenRouterProvider()
            
    def get_provider(self, provider_name: str) -> Optional[AIProvider]:
        """Get a specific provider"""
        return self.providers.get(provider_name)
        
    def list_all_models(self) -> List[AIModel]:
        """List all available models from all providers"""
        all_models = []
        for provider in self.providers.values():
            try:
                all_models.extend(provider.list_models())
            except Exception as e:
                logger.error(f"Error listing models from {provider.__class__.__name__}: {e}")
        return all_models
        
    def chat(self, messages: List[Dict[str, str]], model_id: str, stream: bool = False, **kwargs) -> Union[str, Generator[str, None, None]]:
        """Chat using a specific model"""
        # Determine provider from model ID
        provider_name = None
        
        if model_id.startswith('gpt-'):
            provider_name = 'openai'
        elif model_id.startswith('claude-'):
            provider_name = 'anthropic'
        elif model_id.startswith('deepseek-'):
            provider_name = 'deepseek'
        elif model_id.startswith('grok-'):
            provider_name = 'xai'
        elif '/' in model_id:  # OpenRouter format
            provider_name = 'openrouter'
        else:
            # Check all providers for the model
            for name, provider in self.providers.items():
                models = provider.list_models()
                if any(m.id == model_id for m in models):
                    provider_name = name
                    break
                    
        if not provider_name or provider_name not in self.providers:
            raise ValueError(f"No provider found for model {model_id}")
            
        provider = self.providers[provider_name]
        return provider.chat(messages, model_id, stream, **kwargs)
        
    def test_all_connections(self) -> Dict[str, Dict[str, Any]]:
        """Test all provider connections"""
        results = {}
        for name, provider in self.providers.items():
            results[name] = provider.test_connection()
        return results
        
    def get_cheapest_model(self, quality: str = 'good', capabilities: List[str] = None) -> Optional[AIModel]:
        """Get the cheapest model matching requirements"""
        all_models = self.list_all_models()
        
        # Filter by quality
        quality_levels = ['basic', 'good', 'excellent', 'frontier']
        min_quality_index = quality_levels.index(quality)
        filtered = [m for m in all_models if quality_levels.index(m.quality) >= min_quality_index]
        
        # Filter by capabilities
        if capabilities:
            filtered = [m for m in filtered if all(cap in m.capabilities for cap in capabilities)]
            
        # Sort by average cost
        if filtered:
            filtered.sort(key=lambda m: (m.input_cost + m.output_cost) / 2)
            return filtered[0]
            
        return None
        
    def get_fastest_model(self, quality: str = 'good') -> Optional[AIModel]:
        """Get the fastest model with minimum quality"""
        all_models = self.list_all_models()
        
        # Filter by quality
        quality_levels = ['basic', 'good', 'excellent', 'frontier']
        min_quality_index = quality_levels.index(quality)
        filtered = [m for m in all_models if quality_levels.index(m.quality) >= min_quality_index]
        
        # Sort by speed
        speed_order = ['very_fast', 'fast', 'medium', 'slow']
        if filtered:
            filtered.sort(key=lambda m: speed_order.index(m.speed) if m.speed in speed_order else 999)
            return filtered[0]
            
        return None

# Import settings manager
from core.settings_manager import settings_manager

# Global instance
ai_provider_manager = AIProviderManager()