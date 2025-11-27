# GitHub Copilot Integration - Deep Dive Analysis

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Authentication Flow](#authentication-flow)
4. [API Request Flow](#api-request-flow)
5. [Token Management](#token-management)
6. [Available Models](#available-models)
7. [Python Reproduction Guide](#python-reproduction-guide)
8. [Key Files Reference](#key-files-reference)

---

## Executive Summary

The OpenCode codebase integrates GitHub Copilot through a **plugin-based provider architecture** built on Vercel's AI SDK. The integration uses:

- **OAuth Device Flow** for authentication (same as VSCode Copilot extension)
- **OpenAI-compatible API** at `https://api.githubcopilot.com`
- **Plugin system** for dynamic provider loading
- **Custom fetch handler** for token refresh and header injection

### Key Discovery
The GitHub Copilot API is essentially an **OpenAI-compatible API** that accepts standard chat completion requests but requires:
1. A valid Copilot OAuth token (not a regular GitHub PAT)
2. Special headers identifying the client as a Copilot extension
3. Specific headers for agent/tool calls and vision requests

---

## Architecture Overview

```
+------------------+     +-------------------+     +------------------+
|   OpenCode CLI   | --> |   Plugin System   | --> |  Provider System |
+------------------+     +-------------------+     +------------------+
                               |                           |
                               v                           v
                    +--------------------+      +---------------------+
                    | copilot-auth@0.0.7 |      | @ai-sdk/openai-     |
                    | (NPM package)      |      | compatible          |
                    +--------------------+      +---------------------+
                               |                           |
                               v                           v
                    +--------------------+      +---------------------+
                    | OAuth Device Flow  |      | Custom fetch()      |
                    | Token Storage      |      | with headers        |
                    +--------------------+      +---------------------+
                                                          |
                                                          v
                                              +------------------------+
                                              | api.githubcopilot.com  |
                                              | /chat/completions      |
                                              +------------------------+
```

### Component Breakdown

1. **Plugin System** (`packages/opencode/src/plugin/index.ts`)
   - Loads `opencode-copilot-auth@0.0.7` by default
   - Plugins provide authentication methods and custom loaders

2. **Provider System** (`packages/opencode/src/provider/provider.ts`)
   - Manages all LLM providers
   - Uses `@ai-sdk/openai-compatible` for Copilot
   - Merges plugin-provided options

3. **Auth Module** (`packages/opencode/src/auth/index.ts`)
   - Stores tokens in `~/.local/share/opencode/auth.json`
   - Supports OAuth and API key authentication types

4. **Copilot Auth Plugin** (NPM: `opencode-copilot-auth@0.0.7`)
   - Implements OAuth device flow
   - Provides custom fetch handler for API calls
   - Handles token refresh automatically

---

## Authentication Flow

### OAuth Device Flow Sequence

```
User                   CLI                      GitHub                 Copilot API
  |                     |                          |                        |
  |    Start Auth       |                          |                        |
  |-------------------->|                          |                        |
  |                     |     POST /login/device/code                       |
  |                     |------------------------->|                        |
  |                     |   {client_id, scope}     |                        |
  |                     |                          |                        |
  |                     |   verification_uri       |                        |
  |                     |   user_code              |                        |
  |                     |   device_code            |                        |
  |                     |<-------------------------|                        |
  |                     |                          |                        |
  |   Display URL/Code  |                          |                        |
  |<--------------------|                          |                        |
  |                     |                          |                        |
  |   Visit URL & Enter Code                       |                        |
  |----------------------------------------------->|                        |
  |                     |                          |                        |
  |                     |   Poll for token         |                        |
  |                     |------------------------->|                        |
  |                     |   (every 5 seconds)      |                        |
  |                     |                          |                        |
  |                     |   access_token           |                        |
  |                     |<-------------------------|                        |
  |                     |                          |                        |
  |                     |   Store token            |                        |
  |                     |   (as refresh token)     |                        |
  |                     |                          |                        |
  |   Auth Complete     |                          |                        |
  |<--------------------|                          |                        |
```

### Token Types

| Token Type | Source | Purpose | Expiry |
|------------|--------|---------|--------|
| GitHub OAuth Token | OAuth device flow | Refresh token, stored permanently | Never (unless revoked) |
| Copilot API Token | `/copilot_internal/v2/token` | API authentication | ~30 minutes |

### Code: Device Flow Implementation

```python
# Step 1: Request device code
response = requests.post(
    "https://github.com/login/device/code",
    headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "GitHubCopilotChat/0.35.0",
    },
    json={
        "client_id": "Iv1.b507a08c87ecfe98",  # Official Copilot client ID
        "scope": "read:user",
    },
)

# Response:
# {
#     "device_code": "...",
#     "user_code": "ABCD-1234",
#     "verification_uri": "https://github.com/login/device",
#     "expires_in": 899,
#     "interval": 5
# }
```

```python
# Step 2: Poll for access token
while True:
    response = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        json={
            "client_id": "Iv1.b507a08c87ecfe98",
            "device_code": device_code,
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        },
    )

    data = response.json()
    if "access_token" in data:
        github_token = data["access_token"]
        break
    elif data.get("error") == "authorization_pending":
        time.sleep(interval)
    else:
        raise Exception(f"Error: {data.get('error')}")
```

---

## API Request Flow

### Request Headers (Critical)

```python
COPILOT_HEADERS = {
    # Identifies as VSCode Copilot Chat extension
    "User-Agent": "GitHubCopilotChat/0.32.4",
    "Editor-Version": "vscode/1.105.1",
    "Editor-Plugin-Version": "copilot-chat/0.32.4",
    "Copilot-Integration-Id": "vscode-chat",

    # Authentication
    "Authorization": "Bearer <copilot_api_token>",

    # Request type indicators
    "Openai-Intent": "conversation-edits",
    "X-Initiator": "user",  # or "agent" for tool calls
}

# For vision requests, add:
"Copilot-Vision-Request": "true"
```

### API Request Structure

```python
# Chat Completion Request
POST https://api.githubcopilot.com/chat/completions

{
    "model": "gpt-4o",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a hello world in Python"}
    ],
    "temperature": 0.0,
    "max_tokens": 4096,
    "stream": false
}
```

### Agent Call Detection

The plugin detects agent calls to set the `X-Initiator` header:

```javascript
// From copilot-auth plugin
isAgentCall = body.messages.some(
    (msg) => msg.role && ["tool", "assistant"].includes(msg.role)
);

// For Responses API format
const RESPONSES_API_ALTERNATE_INPUT_TYPES = [
    "file_search_call", "computer_call", "web_search_call",
    "function_call", "mcp_call", "reasoning", ...
];
```

---

## Token Management

### Token Refresh Flow

```
                                   API Request
                                        |
                                        v
                              +-------------------+
                              | Check token       |
                              | expiration        |
                              +-------------------+
                                   |         |
                              expired     valid
                                   |         |
                                   v         |
                    +------------------------+|
                    | GET /copilot_internal/ ||
                    |     v2/token           ||
                    +------------------------+|
                              |              |
                              v              |
                    +-------------------+    |
                    | Update stored     |    |
                    | token & expiry    |    |
                    +-------------------+    |
                              |              |
                              +------+-------+
                                     |
                                     v
                          +-------------------+
                          | Make API request  |
                          | with valid token  |
                          +-------------------+
```

### Token Storage Format

```json
// ~/.local/share/opencode/auth.json
{
    "github-copilot": {
        "type": "oauth",
        "refresh": "gho_xxxxxxxxxxxx",  // GitHub OAuth token
        "access": "tid=xxxx;...",        // Copilot API token
        "expires": 1701234567890          // Milliseconds
    },
    "github-copilot-enterprise": {
        "type": "oauth",
        "refresh": "gho_xxxxxxxxxxxx",
        "access": "...",
        "expires": 1701234567890,
        "enterpriseUrl": "company.ghe.com"
    }
}
```

---

## Available Models

From `https://models.dev/api.json` - GitHub Copilot provider:

### OpenAI Models
| Model ID | Name | Context | Output | Features |
|----------|------|---------|--------|----------|
| gpt-4o | GPT-4o | 64K | 16K | Vision, Tools |
| gpt-4.1 | GPT-4.1 | 128K | 16K | Vision, Tools |
| gpt-5 | GPT-5 | 128K | 128K | Vision, Tools, Reasoning |
| gpt-5-mini | GPT-5-mini | 128K | 64K | Vision, Tools, Reasoning |
| gpt-5-codex | GPT-5-Codex | 128K | 128K | Reasoning, Tools |
| gpt-5.1 | GPT-5.1 | 128K | 128K | Vision, Reasoning, Tools |
| gpt-5.1-codex | GPT-5.1-Codex | 128K | 128K | Reasoning, Tools |

### Anthropic Models
| Model ID | Name | Context | Output | Features |
|----------|------|---------|--------|----------|
| claude-sonnet-4 | Claude Sonnet 4 | 128K | 16K | Vision, Tools, Reasoning |
| claude-sonnet-4.5 | Claude Sonnet 4.5 | 128K | 16K | Vision, Tools, Reasoning |
| claude-opus-41 | Claude Opus 4.1 | 80K | 16K | Vision, Reasoning |
| claude-opus-4.5 | Claude Opus 4.5 | 128K | 16K | Vision, Tools, Reasoning |
| claude-haiku-4.5 | Claude Haiku 4.5 | 128K | 16K | Vision, Tools, Reasoning |

### Google Models
| Model ID | Name | Context | Output | Features |
|----------|------|---------|--------|----------|
| gemini-2.5-pro | Gemini 2.5 Pro | 128K | 64K | Vision, Audio, Video, Tools |
| gemini-3-pro-preview | Gemini 3 Pro Preview | 128K | 64K | Vision, Audio, Video, Tools, Reasoning |

### Other Models
| Model ID | Name | Context | Output |
|----------|------|---------|--------|
| grok-code-fast-1 | Grok Code Fast 1 | 128K | 64K |
| oswe-vscode-prime | Raptor Mini (Preview) | 200K | 64K |

### Enabling Models
Some models require explicit enabling at:
**https://github.com/settings/copilot/features**

---

## Python Reproduction Guide

### Minimal Implementation

```python
import requests
import time

# Constants
CLIENT_ID = "Iv1.b507a08c87ecfe98"
COPILOT_HEADERS = {
    "User-Agent": "GitHubCopilotChat/0.32.4",
    "Editor-Version": "vscode/1.105.1",
    "Editor-Plugin-Version": "copilot-chat/0.32.4",
    "Copilot-Integration-Id": "vscode-chat",
}

class CopilotClient:
    def __init__(self, github_token: str):
        self.github_token = github_token
        self.copilot_token = None
        self.token_expires = 0

    def _refresh_token(self):
        if self.token_expires > time.time() * 1000:
            return

        response = requests.get(
            "https://api.github.com/copilot_internal/v2/token",
            headers={
                "Authorization": f"Bearer {self.github_token}",
                **COPILOT_HEADERS,
            },
        )
        data = response.json()
        self.copilot_token = data["token"]
        self.token_expires = data["expires_at"] * 1000

    def chat(self, messages: list, model: str = "gpt-4o") -> str:
        self._refresh_token()

        response = requests.post(
            "https://api.githubcopilot.com/chat/completions",
            headers={
                **COPILOT_HEADERS,
                "Authorization": f"Bearer {self.copilot_token}",
                "Content-Type": "application/json",
                "Openai-Intent": "conversation-edits",
                "X-Initiator": "user",
            },
            json={
                "model": model,
                "messages": messages,
                "temperature": 0.0,
                "max_tokens": 4096,
            },
        )

        return response.json()["choices"][0]["message"]["content"]

# Usage
client = CopilotClient(github_token="gho_xxx")
response = client.chat([
    {"role": "user", "content": "Hello, write a hello world in Python"}
])
print(response)
```

### Full Implementation

See `github_copilot_integration_analysis.py` for a complete implementation including:
- OAuth device flow authentication
- Token storage and refresh
- Streaming support
- Tool/function calling
- Vision request support
- GitHub Enterprise support

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `packages/opencode/src/plugin/index.ts` | Plugin loader, loads copilot-auth |
| `packages/opencode/src/provider/provider.ts` | Provider registry and SDK loading |
| `packages/opencode/src/provider/auth.ts` | OAuth flow orchestration |
| `packages/opencode/src/auth/index.ts` | Token storage |
| `packages/opencode/src/provider/transform.ts` | Provider-specific transformations |
| `packages/opencode/src/provider/models.ts` | Model data from models.dev |
| NPM: `opencode-copilot-auth@0.0.7` | Copilot OAuth plugin |

### External Resources

- **Models Database**: https://models.dev/api.json
- **Copilot Settings**: https://github.com/settings/copilot/features
- **OAuth Device Flow**: https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps#device-flow

---

## GitHub Enterprise Support

For GitHub Enterprise, the URLs change:

```python
# Regular GitHub.com
DEVICE_CODE_URL = "https://github.com/login/device/code"
ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
API_BASE = "https://api.githubcopilot.com"

# GitHub Enterprise (e.g., company.ghe.com)
DEVICE_CODE_URL = "https://company.ghe.com/login/device/code"
ACCESS_TOKEN_URL = "https://company.ghe.com/login/oauth/access_token"
COPILOT_TOKEN_URL = "https://api.company.ghe.com/copilot_internal/v2/token"
API_BASE = "https://copilot-api.company.ghe.com"
```

---

## Summary

The GitHub Copilot integration in OpenCode demonstrates a clean plugin-based architecture that:

1. **Separates concerns**: Authentication logic is in a plugin, API handling in the provider system
2. **Uses standard protocols**: OAuth device flow, OpenAI-compatible API
3. **Handles enterprise**: Supports both GitHub.com and GitHub Enterprise
4. **Manages tokens automatically**: Refresh tokens before expiry

The Python implementation provided (`github_copilot_integration_analysis.py`) reproduces this functionality with ~500 lines of code, demonstrating that the integration is straightforward once the authentication flow and required headers are understood.
