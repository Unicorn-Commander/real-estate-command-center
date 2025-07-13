#!/usr/bin/env python3
"""
Test script for AI Provider Integration
Tests the new multi-provider AI support in Real Estate Command Center
"""

import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.ai_providers import AIProviderManager
from core.enhanced_colonel_client import EnhancedColonelClient
from core.settings_manager import settings_manager
import json

def test_ai_providers():
    """Test AI provider integration"""
    print("=" * 80)
    print("Real Estate Command Center - AI Provider Test")
    print("=" * 80)
    
    # Initialize AI manager
    ai_manager = AIProviderManager()
    
    # Test connections
    print("\n1. Testing AI Provider Connections:")
    print("-" * 40)
    results = ai_manager.test_all_connections()
    
    for provider, result in results.items():
        status = "✅ Connected" if result['status'] == 'success' else f"❌ {result['message']}"
        print(f"{provider:15} {status}")
    
    # List available models
    print("\n2. Available AI Models:")
    print("-" * 40)
    models = ai_manager.list_all_models()
    
    if models:
        print(f"Found {len(models)} models across {len(set(m.provider for m in models))} providers\n")
        
        # Group by provider
        by_provider = {}
        for model in models:
            if model.provider not in by_provider:
                by_provider[model.provider] = []
            by_provider[model.provider].append(model)
        
        for provider, provider_models in by_provider.items():
            print(f"\n{provider.upper()}:")
            for model in provider_models[:3]:  # Show first 3 models per provider
                print(f"  - {model.id}")
                print(f"    Cost: ${model.input_cost:.2f}/$1M input, ${model.output_cost:.2f}/$1M output")
                print(f"    Quality: {model.quality}, Speed: {model.speed}")
                print(f"    Context: {model.context_window:,} tokens")
    else:
        print("No models available. Please configure API keys.")
    
    # Test enhanced colonel client
    print("\n3. Testing Enhanced Colonel Client:")
    print("-" * 40)
    
    # Initialize client
    client = EnhancedColonelClient()
    
    # Get backend status
    status = client.get_backend_status()
    print(f"Backend Type: {status['backend_type']}")
    print(f"Available Providers: {', '.join(status['available_providers'])}")
    print(f"Total Models: {status['total_models']}")
    
    # Get model recommendations
    print("\n4. Model Recommendations for Real Estate Tasks:")
    print("-" * 40)
    recommendations = client.get_model_recommendations()
    
    for task, models in recommendations.items():
        print(f"\n{task}:")
        for category, model_id in models.items():
            if model_id:
                print(f"  {category:12} → {model_id}")
    
    # Test cost estimation
    print("\n5. Cost Estimation Example:")
    print("-" * 40)
    test_message = "Analyze this property: 123 Main Street, Portland OR. What's the market value?"
    
    # Try different quality levels
    for quality, prefer_cheap in [("frontier", False), ("good", True)]:
        model_id = client.get_model_for_agent('property_analyst', quality=quality, prefer_cheap=prefer_cheap)
        if model_id:
            cost_estimate = client.estimate_cost(test_message, 'property_analyst', model_id)
            if 'error' not in cost_estimate:
                print(f"\n{quality.title()} Quality {'(Cheap)' if prefer_cheap else ''}:")
                print(f"  Model: {cost_estimate['model']}")
                print(f"  Provider: {cost_estimate['provider']}")
                print(f"  Estimated Cost: ${cost_estimate['total_cost']:.4f}")
                print(f"  (Input: ${cost_estimate['input_cost']:.4f}, Output: ${cost_estimate['output_cost']:.4f})")
    
    # Interactive test
    print("\n6. Interactive Test:")
    print("-" * 40)
    print("You can now test the AI agents. Type 'quit' to exit.")
    print("Available agents: property_analyst, market_researcher, lead_manager, marketing_expert")
    print("\nExample queries:")
    print("- Analyze property at 456 Oak Street, Seattle WA")
    print("- What are the market trends in Portland?")
    print("- Help me qualify a lead with $500k budget")
    print("- Create a listing description for a 3BR/2BA home")
    
    while True:
        print("\n" + "-" * 40)
        agent = input("Select agent (or 'quit'): ").strip()
        if agent.lower() == 'quit':
            break
            
        if agent not in client.agent_profiles:
            print(f"Unknown agent. Available: {list(client.agent_profiles.keys())}")
            continue
            
        message = input("Enter your message: ").strip()
        if not message:
            continue
            
        # Show cost estimate
        model_id = client.get_model_for_agent(agent, prefer_cheap=True)
        if model_id:
            cost = client.estimate_cost(message, agent, model_id)
            if 'error' not in cost:
                print(f"\nUsing model: {model_id}")
                print(f"Estimated cost: ${cost['total_cost']:.4f}")
        
        print("\nGenerating response...")
        try:
            response = client.chat_with_agent(message, agent)
            print(f"\n{response}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    # Check for API keys
    print("Checking for API keys...")
    api_keys_found = []
    
    env_vars = [
        ('OPENAI_API_KEY', 'OpenAI'),
        ('ANTHROPIC_API_KEY', 'Anthropic'),
        ('DEEPSEEK_API_KEY', 'DeepSeek'),
        ('GROQ_API_KEY', 'Groq'),
        ('XAI_API_KEY', 'xAI'),
        ('OPENROUTER_API_KEY', 'OpenRouter')
    ]
    
    for env_var, provider in env_vars:
        if os.getenv(env_var):
            api_keys_found.append(provider)
    
    if api_keys_found:
        print(f"Found API keys for: {', '.join(api_keys_found)}")
    else:
        print("\n⚠️  No API keys found in environment variables.")
        print("To test AI providers, set one or more of these environment variables:")
        for env_var, provider in env_vars:
            print(f"  export {env_var}='your-{provider.lower()}-api-key'")
        print("\nYou can still run the test to see the system architecture.")
    
    print()
    test_ai_providers()