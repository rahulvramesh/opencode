# OpenCode Python SDK Examples

This directory contains example scripts demonstrating various features of the OpenCode Python SDK.

## Examples

### 1. Basic Usage (`basic_usage.py`)

A placeholder demonstrating the basic structure of using the OpenCode SDK. This will be updated after client generation.

**Usage:**
```bash
python examples/basic_usage.py
```

### 2. File Status (`file_status.py`)

Demonstrates how to query file status in the current OpenCode workspace.

**Usage:**
```bash
python examples/file_status.py
```

**Output:**
Shows the path and type (tracked, untracked, modified) of files in the workspace.

### 3. Session List (`session_list.py`)

Shows how to list all active sessions in OpenCode.

**Usage:**
```bash
python examples/session_list.py
```

**Output:**
Prints the IDs of all sessions.

### 4. GitHub Copilot Info (`copilot_info.py`)

**NEW** - Quick reference guide for GitHub Copilot integration with OpenCode.

**Usage:**
```bash
python examples/copilot_info.py
```

**What it shows:**
- Connection test to OpenCode server
- Setup instructions for GitHub Copilot
- Available models and their descriptions
- Subscription requirements
- Basic Python SDK usage patterns
- Links to documentation

**Note:** This script works without authentication and provides setup guidance.

---

### 5. GitHub Copilot Usage (`github_copilot_usage.py`)

**NEW** - Demonstrates GitHub Copilot workflow with OpenCode Python SDK.

**Prerequisites:**
- OpenCode server running (`opencode`)
- GitHub Copilot authentication configured
- Active GitHub Copilot subscription

**Setup:**
```bash
# 1. Authenticate with GitHub Copilot
opencode auth login
# Select "GitHub Copilot" and follow OAuth flow

# 2. Start OpenCode server (if not running)
opencode
```

**Usage:**
```bash
python examples/github_copilot_usage.py
```

**What it demonstrates:**
- Connecting to OpenCode server
- Listing available GitHub Copilot models
- Creating a session
- Sending prompts to GitHub Copilot models
- Processing responses
- Error handling and troubleshooting

**Available Models:**

⚠️  **Note:** Some models require manual enablement in [GitHub Copilot settings](https://github.com/settings/copilot/features) and may need Pro+ subscription.

- `claude-sonnet-3.5` - Anthropic Claude via Copilot (requires Pro+)
- `claude-haiku` - Anthropic Claude (lighter) via Copilot
- `gpt-4o` - OpenAI GPT-4o via Copilot
- `gpt-4o-mini` - OpenAI GPT-4o Mini via Copilot
- `o1` - OpenAI o1 (reasoning) via Copilot (requires Pro+)
- `o1-mini` - OpenAI o1-mini via Copilot (requires Pro+)

## Running Examples

### Prerequisites

1. **Install OpenCode Python SDK:**
   ```bash
   pip install opencode-ai
   ```

   Or for development:
   ```bash
   cd packages/sdk/python
   uv sync --dev
   uv run python examples/<example_name>.py
   ```

2. **Start OpenCode Server:**
   ```bash
   opencode
   ```
   
   The server runs on `http://localhost:4096` by default.

3. **Authentication (if required):**
   ```bash
   opencode auth login
   ```

### Common Issues

#### "Connection refused" error
- Ensure OpenCode server is running: `opencode`
- Check if port 4096 is available
- Verify base URL in example matches server URL

#### "Authentication required" error
- Run `opencode auth login` and authenticate with provider
- Check credentials: `opencode auth list`

#### "Model not supported" error
- Enable model in provider settings (e.g., GitHub Copilot settings)
- Verify subscription tier supports the model
- Check provider configuration in `opencode.json`

## Development

To add a new example:

1. Create a new Python file in this directory
2. Add docstring explaining the example
3. Include error handling and helpful messages
4. Update this README with the new example
5. Test the example with a fresh OpenCode installation

## Further Resources

- **OpenCode Documentation**: https://opencode.ai/docs
- **Python SDK Documentation**: https://opencode.ai/docs/sdk
- **GitHub Copilot Integration**: See `docs/github-copilot-integration.md`
- **API Types**: `src/opencode_ai/types.py`

## Support

For issues or questions:
- GitHub Issues: https://github.com/sst/opencode/issues
- Discord: https://discord.gg/opencode
- Documentation: https://opencode.ai/docs
