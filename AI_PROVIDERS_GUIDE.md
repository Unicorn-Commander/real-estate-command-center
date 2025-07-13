# AI Providers Guide - Real Estate Command Center

## Overview

The Real Estate Command Center now supports multiple AI providers, giving you access to over 400+ AI models from leading providers. This guide will help you set up and use these providers effectively.

## Supported Providers

### 1. **OpenAI** 
- **Models**: GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo
- **Best for**: High-quality responses, vision capabilities, function calling
- **Pricing**: $2.50-$30 per million tokens
- **Setup**: Get API key from https://platform.openai.com/api-keys

### 2. **Anthropic (Claude)**
- **Models**: Claude Opus 4, Claude Sonnet 4, Claude 3.5 Sonnet/Haiku
- **Best for**: Long context (200K tokens), thoughtful analysis
- **Pricing**: $0.80-$75 per million tokens
- **Setup**: Get API key from https://console.anthropic.com

### 3. **DeepSeek**
- **Models**: DeepSeek V3 Chat, DeepSeek R1 Reasoning
- **Best for**: Cost-effective performance (10x cheaper than GPT-4)
- **Pricing**: $0.27-$2.19 per million tokens
- **Setup**: Get API key from https://platform.deepseek.com

### 4. **Groq**
- **Models**: Llama 3.3 70B, Mixtral 8x7B, Gemma 2
- **Best for**: Ultra-fast responses (sub-millisecond latency)
- **Pricing**: $0.05-$0.79 per million tokens
- **Setup**: Get API key from https://console.groq.com

### 5. **xAI (Grok)**
- **Models**: Grok 4, Grok 4 Heavy, Grok 2
- **Best for**: Real-time web search, multi-agent reasoning
- **Pricing**: ~$5-$30 per million tokens
- **Setup**: Get API key from https://console.x.ai

### 6. **OpenRouter**
- **Models**: 400+ models from all major providers
- **Best for**: Access to many models with one API key
- **Pricing**: Same as provider + 5.5% fee
- **Setup**: Get API key from https://openrouter.ai

## Quick Setup

### 1. Set Environment Variables

```bash
# Add to your ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY='sk-...'
export ANTHROPIC_API_KEY='sk-ant-...'
export DEEPSEEK_API_KEY='...'
export GROQ_API_KEY='gsk_...'
export XAI_API_KEY='...'
export OPENROUTER_API_KEY='sk-or-...'
```

### 2. Or Use the Settings Dialog

1. Launch Real Estate Command Center
2. Press `Ctrl+K` to open API Key Management
3. Enter your API keys for each provider
4. Keys are saved securely in your settings

### 3. Configure AI Preferences

In Settings > AI Configuration:
- **Backend Type**: Select 'auto' for automatic provider selection
- **Prefer Cheap Models**: Check to prioritize cost-effective models
- **Prefer Fast Models**: Check to prioritize speed over quality

## Usage Examples

### Property Analysis (High Quality)
```python
# Uses GPT-4o or Claude Opus for best analysis
client.chat_with_agent(
    "Analyze property at 123 Main St, Portland OR",
    agent_type='property_analyst',
    quality='excellent'
)
```

### Quick Lead Scoring (Fast & Cheap)
```python
# Uses Groq Llama or DeepSeek for speed
client.chat_with_agent(
    "Score this lead: John Doe, $500k budget, pre-approved",
    agent_type='lead_manager',
    prefer_fast=True,
    prefer_cheap=True
)
```

### Market Research (Balanced)
```python
# Uses mid-tier models like Claude Sonnet or GPT-4o Mini
client.chat_with_agent(
    "What are the market trends in Seattle?",
    agent_type='market_researcher',
    quality='good'
)
```

## Model Selection Strategy

### By Task Type

| Task | Recommended Quality | Recommended Models |
|------|-------------------|-------------------|
| Property Valuation | Excellent/Frontier | GPT-4o, Claude Opus 4, DeepSeek R1 |
| Market Analysis | Excellent | Claude Sonnet 4, GPT-4o |
| Lead Management | Good | GPT-4o Mini, Claude Haiku, DeepSeek Chat |
| Marketing Copy | Good | GPT-4o Mini, Gemini Flash (free) |
| Quick Queries | Basic/Good | Groq Llama, Llama 3.3 (free) |

### By Budget

| Budget | Strategy | Providers |
|--------|----------|-----------|
| Free | Use free models via OpenRouter | Gemini 2.0 Flash, Llama 3.3 |
| Low (<$0.01/query) | DeepSeek, Groq | Fast and cheap |
| Medium ($0.01-0.10) | OpenAI Mini, Claude Haiku | Good balance |
| High (>$0.10) | GPT-4o, Claude Opus | Best quality |

## Cost Examples

For a typical property analysis (500 tokens in, 1000 tokens out):

- **DeepSeek V3**: $0.0001 - $0.0011
- **GPT-4o Mini**: $0.0001 - $0.0006
- **GPT-4o**: $0.0013 - $0.0100
- **Claude Opus 4**: $0.0075 - $0.0750

## Testing Your Setup

Run the test script to verify your AI providers:

```bash
cd /home/ucadmin/Development/real-estate-command-center/desktop
python test_ai_providers.py
```

This will:
1. Test all configured providers
2. List available models
3. Show cost estimates
4. Let you test different agents

## Troubleshooting

### "No API key configured"
- Check environment variables: `echo $OPENAI_API_KEY`
- Verify in Settings > AI Configuration
- Restart the application after setting keys

### "Rate limit exceeded"
- Some providers have rate limits
- Use multiple providers for redundancy
- Consider upgrading your plan

### "Model not available"
- Some models require special access
- Check provider documentation
- Use fallback models

## Best Practices

1. **Use Multiple Providers**: Configure 2-3 providers for redundancy
2. **Set Quality by Task**: Use frontier models only when needed
3. **Monitor Costs**: Use cost estimation before expensive queries
4. **Cache Results**: Reuse responses when possible
5. **Test Models**: Compare responses to find best models for your use

## Advanced Features

### Multi-Agent Comparison
```python
# Compare responses from different models
responses = client.compare_multi_agent_responses(
    "What's the value of 456 Oak St?",
    agents=['property_analyst', 'market_researcher']
)
```

### Custom Model Selection
```python
# Use specific model
response = client.chat_with_agent(
    message="Analyze this property",
    agent_type='property_analyst',
    model_id='claude-opus-4-20250514'
)
```

### Cost Optimization
```python
# Get cheapest model for task
model = client.ai_manager.get_cheapest_model(quality='good')
print(f"Using {model.id} at ${model.input_cost}/M tokens")
```

## Support

For issues or questions:
- Check the test script: `test_ai_providers.py`
- Review logs in the application
- Update to latest version
- Report issues on GitHub