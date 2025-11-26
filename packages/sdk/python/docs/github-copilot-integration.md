# GitHub Copilot Integration in OpenCode

This document explains how GitHub Copilot is integrated into OpenCode and how to use it programmatically via the Python SDK.

## Overview

OpenCode integrates with GitHub Copilot to provide access to multiple AI models through your existing GitHub Copilot subscription. This allows developers to use models like Claude Sonnet 3.5, GPT-4o, and o1 through the familiar OpenCode interface.

## Architecture

### Component Overview

The GitHub Copilot integration consists of several key components:

1. **Authentication Plugin** (`opencode-copilot-auth`)
   - Handles OAuth2 device flow authentication with GitHub
   - Manages token refresh and storage
   - Located as an external plugin loaded at runtime

2. **Provider System** (`packages/opencode/src/provider/provider.ts`)
   - Registers GitHub Copilot as a provider
   - Supports both regular and Enterprise Copilot
   - Maps models from GitHub Copilot to OpenCode's model registry

3. **Models Database** (from Models.dev)
   - Contains metadata about available Copilot models
   - Includes pricing, capabilities, and limits
   - Dynamically updated

4. **Authentication Storage**
   - OAuth tokens stored in `~/.local/share/opencode/auth.json`
   - Supports both `github-copilot` and `github-copilot-enterprise` providers

### Authentication Flow

```
1. User runs: opencode auth login
2. User selects: GitHub Copilot
3. Plugin generates device code
4. User visits: github.com/login/device
5. User enters code and authorizes
6. Plugin receives OAuth token
7. Token saved to auth.json
8. Plugin configures provider with token
9. Models become available in OpenCode
```

### Provider Registration

The GitHub Copilot provider is registered through the plugin system:

```typescript
// packages/opencode/src/plugin/index.ts
if (!Flag.OPENCODE_DISABLE_DEFAULT_PLUGINS) {
  plugins.push("opencode-copilot-auth@0.0.7")
}
```

When initialized, the plugin:
- Checks for stored authentication
- Configures the OpenAI-compatible SDK with Copilot endpoints
- Registers available models with OpenCode

### Enterprise Support

OpenCode automatically creates a `github-copilot-enterprise` provider that inherits from the base `github-copilot` provider:

```typescript
// packages/opencode/src/provider/provider.ts
if (database["github-copilot"]) {
  const githubCopilot = database["github-copilot"]
  database["github-copilot-enterprise"] = {
    ...githubCopilot,
    id: "github-copilot-enterprise",
    name: "GitHub Copilot Enterprise",
    api: undefined, // Set dynamically based on enterprise URL
  }
}
```

## Available Models

GitHub Copilot provides access to several AI models:

### Claude Models (via Anthropic)
- **claude-sonnet-3.5** - Most capable model, best for complex code generation
- **claude-haiku** - Faster, lighter model for simple tasks

### GPT Models (via OpenAI)
- **gpt-4o** - Advanced reasoning and code understanding
- **gpt-4o-mini** - Faster, more cost-effective version

### Reasoning Models (via OpenAI)
- **o1** - Advanced reasoning for complex problems
- **o1-mini** - Lighter reasoning model

## Usage with Python SDK

### Prerequisites

1. Install the Python SDK:
   ```bash
   pip install opencode-ai
   ```

2. Authenticate with GitHub Copilot:
   ```bash
   opencode auth login
   # Select "GitHub Copilot"
   # Follow OAuth flow at github.com/login/device
   ```

3. Ensure OpenCode server is running:
   ```bash
   opencode
   ```

### Basic Example

```python
from opencode_ai import OpenCodeClient
from opencode_ai.models import SessionCreate, PromptMessage

# Connect to OpenCode server
client = OpenCodeClient(base_url="http://localhost:4096")

# Create a session
session = client.create_session(
    body=SessionCreate(title="Copilot Example")
)

# Send a prompt to Claude Sonnet via Copilot
prompt = PromptMessage(
    model={
        "providerID": "github-copilot",
        "modelID": "claude-sonnet-3.5"
    },
    parts=[{
        "type": "text",
        "text": "Write a Python function to calculate fibonacci numbers"
    }]
)

response = client.post_session_by_id_prompt(
    path={"id": session.id},
    body=prompt
)

# Process response
for part in response.parts:
    if hasattr(part, 'text'):
        print(part.text)
```

### Advanced Usage

#### Model Selection

You can dynamically select models based on task complexity:

```python
def get_model_for_task(task_complexity):
    """Select appropriate Copilot model based on task."""
    if task_complexity == "high":
        return "claude-sonnet-3.5"
    elif task_complexity == "reasoning":
        return "o1"
    else:
        return "gpt-4o-mini"

model = get_model_for_task("high")
```

#### Streaming Responses

For real-time responses, use the event subscription API:

```python
# Subscribe to events for streaming responses
events = client.event.subscribe()

for event in events.stream:
    if event.type == "message.part":
        # Process streamed content
        print(event.properties.get("text", ""), end="", flush=True)
```

#### Error Handling

```python
try:
    response = client.post_session_by_id_prompt(
        path={"id": session.id},
        body=prompt
    )
except Exception as e:
    if "not supported" in str(e):
        print("Model not enabled in Copilot settings")
        print("Visit: https://github.com/settings/copilot/features")
    else:
        print(f"Error: {e}")
```

## Configuration

### Model Enablement

Some Copilot models require manual enablement in GitHub settings:

1. Visit: https://github.com/settings/copilot/features
2. Enable desired models (e.g., Claude, o1)
3. Models will appear in OpenCode after enabling

### Enterprise Configuration

For GitHub Copilot Enterprise with custom endpoints:

```json
// opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {
    "github-copilot-enterprise": {
      "options": {
        "enterpriseUrl": "https://github.mycompany.com"
      }
    }
  }
}
```

## Troubleshooting

### Authentication Issues

**Problem**: "No authentication found for github-copilot"

**Solution**:
```bash
# Check current auth
opencode auth list

# Re-authenticate if needed
opencode auth login
# Select GitHub Copilot
```

### Model Not Available

**Problem**: "The requested model is not supported"

**Solution**:
1. Verify Copilot subscription is active
2. Enable model in GitHub settings: https://github.com/settings/copilot/features
3. Some models require Pro+ subscription

### Connection Issues

**Problem**: Cannot connect to OpenCode server

**Solution**:
```bash
# Start OpenCode server
opencode

# Or specify custom port
opencode --port 4096
```

## Rate Limits and Quotas

GitHub Copilot has usage limits that vary by subscription tier. While exact limits are not publicly documented, typical behavior includes:

- **Individual**: Subject to GitHub's fair use policy (~500-1000 requests/month typical usage)
- **Business**: Higher limits, usage monitoring available in admin dashboard
- **Enterprise**: Custom limits based on agreement, dedicated capacity options

For current rate limits, refer to [GitHub Copilot Documentation](https://docs.github.com/en/copilot/managing-copilot/managing-copilot-as-an-individual-subscriber/about-github-copilot-individual).

When limits are reached, the API will return a 429 status code. Implement exponential backoff:

```python
from time import sleep

max_retries = 3
for attempt in range(max_retries):
    try:
        response = client.post_session_by_id_prompt(...)
        break
    except Exception as e:
        if "429" in str(e) and attempt < max_retries - 1:
            sleep(2 ** attempt)  # Exponential backoff
        else:
            raise
```

## Best Practices

1. **Model Selection**: Use faster models (haiku, gpt-4o-mini) for simple tasks
2. **Context Management**: Keep prompts focused to reduce token usage
3. **Error Handling**: Always handle authentication and rate limit errors
4. **Token Management**: Plugin handles token refresh automatically
5. **Caching**: Reuse sessions when making multiple related queries

## Security Considerations

- OAuth tokens are stored locally in `~/.local/share/opencode/auth.json`
- Tokens are encrypted at rest (platform-dependent)
- Never commit auth.json to version control
- Use environment-specific authentication in CI/CD
- Enterprise users should follow company security policies

## Further Reading

- [OpenCode Providers Documentation](https://opencode.ai/docs/providers)
- [GitHub Copilot Documentation](https://docs.github.com/en/copilot)
- [OpenCode SDK Documentation](https://opencode.ai/docs/sdk)
- [Models.dev](https://models.dev) - Model metadata database

## Support

For issues or questions:
- GitHub Issues: https://github.com/sst/opencode/issues
- Discord: https://discord.gg/opencode
- Documentation: https://opencode.ai/docs
