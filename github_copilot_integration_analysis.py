#!/usr/bin/env python3
"""
GitHub Copilot Integration Analysis and Python Implementation

This file documents how GitHub Copilot is integrated in the OpenCode codebase
and provides a complete Python implementation to reproduce the functionality.

=============================================================================
ARCHITECTURE OVERVIEW
=============================================================================

The OpenCode codebase integrates GitHub Copilot through a plugin-based system:

1. Plugin System (packages/opencode/src/plugin/index.ts)
   - Automatically loads `opencode-copilot-auth@0.0.7` plugin
   - Plugin provides OAuth authentication flow
   - Plugin provides custom fetch handler for API calls

2. Provider System (packages/opencode/src/provider/provider.ts)
   - Uses `@ai-sdk/openai-compatible` as the base SDK
   - Merges plugin-provided options (baseURL, custom fetch)
   - Models fetched from https://models.dev/api.json

3. Authentication Flow
   - OAuth Device Flow with GitHub
   - Tokens stored in ~/.local/share/opencode/auth.json
   - Access tokens refreshed via Copilot internal API

=============================================================================
AUTHENTICATION FLOW DETAILS
=============================================================================

Step 1: Device Code Request
   POST https://github.com/login/device/code
   Body: {"client_id": "Iv1.b507a08c87ecfe98", "scope": "read:user"}

Step 2: User Authorization
   User visits verification_uri and enters user_code

Step 3: Poll for Access Token
   POST https://github.com/login/oauth/access_token
   Body: {"client_id": "...", "device_code": "...", "grant_type": "urn:ietf:params:oauth:grant-type:device_code"}

Step 4: Get Copilot Token (for API calls)
   GET https://api.github.com/copilot_internal/v2/token
   Headers: {"Authorization": "Bearer <github_access_token>"}

Step 5: Make API Calls
   POST https://api.githubcopilot.com/chat/completions
   Headers: {"Authorization": "Bearer <copilot_token>", ...special headers}

=============================================================================
"""

import json
import time
import os
import requests
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List, Any, Generator
import webbrowser


# =============================================================================
# CONSTANTS (from opencode-copilot-auth plugin)
# =============================================================================

# This is the official GitHub Copilot OAuth Client ID
# Used by VSCode Copilot extension
CLIENT_ID = "Iv1.b507a08c87ecfe98"

# These headers are required for the Copilot API to work
# They identify the client as a VSCode Copilot Chat extension
COPILOT_HEADERS = {
    "User-Agent": "GitHubCopilotChat/0.32.4",
    "Editor-Version": "vscode/1.105.1",
    "Editor-Plugin-Version": "copilot-chat/0.32.4",
    "Copilot-Integration-Id": "vscode-chat",
}

# API Endpoints
GITHUB_DEVICE_CODE_URL = "https://github.com/login/device/code"
GITHUB_ACCESS_TOKEN_URL = "https://github.com/login/oauth/access_token"
COPILOT_TOKEN_URL = "https://api.github.com/copilot_internal/v2/token"
COPILOT_API_BASE = "https://api.githubcopilot.com"

# Available models from models.dev (non-deprecated)
AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4.1",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-codex",
    "gpt-5.1",
    "gpt-5.1-codex",
    "gpt-5.1-codex-mini",
    "claude-sonnet-4",
    "claude-sonnet-4.5",
    "claude-opus-41",
    "claude-opus-4.5",
    "claude-haiku-4.5",
    "gemini-2.5-pro",
    "gemini-3-pro-preview",
    "grok-code-fast-1",
    "oswe-vscode-prime",  # Raptor Mini
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CopilotAuth:
    """Stores GitHub Copilot authentication tokens"""
    github_token: str  # The GitHub OAuth access token (used as refresh token)
    copilot_token: Optional[str] = None  # The Copilot API token
    expires_at: int = 0  # Token expiration timestamp (milliseconds)
    enterprise_url: Optional[str] = None  # For GitHub Enterprise

    def is_expired(self) -> bool:
        """Check if the Copilot token is expired"""
        return self.expires_at < int(time.time() * 1000)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON storage"""
        return {
            "type": "oauth",
            "refresh": self.github_token,
            "access": self.copilot_token or "",
            "expires": self.expires_at,
            "enterpriseUrl": self.enterprise_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CopilotAuth":
        """Create from dictionary (JSON storage format)"""
        return cls(
            github_token=data["refresh"],
            copilot_token=data.get("access"),
            expires_at=data.get("expires", 0),
            enterprise_url=data.get("enterpriseUrl"),
        )


@dataclass
class Message:
    """Chat message"""
    role: str  # "system", "user", "assistant"
    content: str


# =============================================================================
# AUTHENTICATION
# =============================================================================

class CopilotAuthenticator:
    """
    Handles GitHub Copilot OAuth Device Flow authentication.

    This replicates the authentication flow from:
    /tmp/copilot-auth/package/index.mjs (opencode-copilot-auth plugin)
    """

    def __init__(self, enterprise_url: Optional[str] = None):
        """
        Initialize authenticator.

        Args:
            enterprise_url: GitHub Enterprise URL (e.g., "company.ghe.com")
                          Leave None for regular GitHub.com
        """
        self.enterprise_url = enterprise_url
        self.domain = self._normalize_domain(enterprise_url) if enterprise_url else "github.com"

    def _normalize_domain(self, url: str) -> str:
        """Remove protocol and trailing slash from URL"""
        return url.replace("https://", "").replace("http://", "").rstrip("/")

    def _get_urls(self) -> Dict[str, str]:
        """Get the API URLs for the current domain"""
        return {
            "device_code": f"https://{self.domain}/login/device/code",
            "access_token": f"https://{self.domain}/login/oauth/access_token",
            "copilot_token": f"https://api.{self.domain}/copilot_internal/v2/token",
        }

    def start_device_flow(self) -> Dict[str, Any]:
        """
        Start the OAuth device flow.

        Returns:
            dict with verification_uri, user_code, device_code, interval
        """
        urls = self._get_urls()

        response = requests.post(
            urls["device_code"],
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "GitHubCopilotChat/0.35.0",
            },
            json={
                "client_id": CLIENT_ID,
                "scope": "read:user",
            },
        )
        response.raise_for_status()
        return response.json()

    def poll_for_token(self, device_code: str, interval: int = 5) -> Optional[str]:
        """
        Poll for the access token after user authorization.

        Args:
            device_code: The device code from start_device_flow
            interval: Polling interval in seconds

        Returns:
            The GitHub access token, or None if authorization failed
        """
        urls = self._get_urls()

        while True:
            response = requests.post(
                urls["access_token"],
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "GitHubCopilotChat/0.35.0",
                },
                json={
                    "client_id": CLIENT_ID,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
            )

            if not response.ok:
                return None

            data = response.json()

            if "access_token" in data:
                return data["access_token"]

            if data.get("error") == "authorization_pending":
                time.sleep(interval)
                continue

            if "error" in data:
                print(f"Authorization error: {data.get('error_description', data['error'])}")
                return None

            time.sleep(interval)

    def authenticate_interactive(self) -> Optional[CopilotAuth]:
        """
        Run the full interactive authentication flow.

        Returns:
            CopilotAuth object if successful, None if failed
        """
        print("Starting GitHub Copilot authentication...")

        # Start device flow
        device_data = self.start_device_flow()

        verification_uri = device_data["verification_uri"]
        user_code = device_data["user_code"]
        device_code = device_data["device_code"]
        interval = device_data.get("interval", 5)

        print(f"\n{'='*60}")
        print(f"Please visit: {verification_uri}")
        print(f"Enter code: {user_code}")
        print(f"{'='*60}\n")

        # Try to open the browser
        try:
            webbrowser.open(verification_uri)
        except Exception:
            pass

        print("Waiting for authorization...")

        # Poll for token
        github_token = self.poll_for_token(device_code, interval)

        if not github_token:
            print("Authorization failed!")
            return None

        print("Authorization successful!")

        return CopilotAuth(
            github_token=github_token,
            enterprise_url=self.enterprise_url,
        )


# =============================================================================
# COPILOT CLIENT
# =============================================================================

class CopilotClient:
    """
    GitHub Copilot API Client.

    This replicates the API interaction from:
    - packages/opencode/src/provider/provider.ts (SDK loading)
    - /tmp/copilot-auth/package/index.mjs (custom fetch handler)
    """

    def __init__(self, auth: CopilotAuth):
        """
        Initialize the Copilot client.

        Args:
            auth: CopilotAuth object with tokens
        """
        self.auth = auth
        self._setup_base_url()

    def _setup_base_url(self):
        """Set up the API base URL based on deployment type"""
        if self.auth.enterprise_url:
            domain = self.auth.enterprise_url.replace("https://", "").replace("http://", "").rstrip("/")
            self.base_url = f"https://copilot-api.{domain}"
            self.token_url = f"https://api.{domain}/copilot_internal/v2/token"
        else:
            self.base_url = COPILOT_API_BASE
            self.token_url = COPILOT_TOKEN_URL

    def _refresh_token_if_needed(self):
        """Refresh the Copilot API token if expired"""
        if not self.auth.is_expired():
            return

        print("Refreshing Copilot token...")

        response = requests.get(
            self.token_url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {self.auth.github_token}",
                **COPILOT_HEADERS,
            },
        )

        if not response.ok:
            raise Exception(f"Failed to refresh token: {response.status_code} {response.text}")

        data = response.json()

        self.auth.copilot_token = data["token"]
        self.auth.expires_at = data["expires_at"] * 1000  # Convert to milliseconds

        print(f"Token refreshed, expires at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.auth.expires_at / 1000))}")

    def _get_headers(self, is_agent_call: bool = False, is_vision: bool = False) -> Dict[str, str]:
        """
        Get the headers for API calls.

        Args:
            is_agent_call: True if this is an agent/tool call (not initial user message)
            is_vision: True if the request contains images
        """
        self._refresh_token_if_needed()

        headers = {
            **COPILOT_HEADERS,
            "Authorization": f"Bearer {self.auth.copilot_token}",
            "Content-Type": "application/json",
            "Openai-Intent": "conversation-edits",
            "X-Initiator": "agent" if is_agent_call else "user",
        }

        if is_vision:
            headers["Copilot-Vision-Request"] = "true"

        return headers

    def chat_completion(
        self,
        messages: List[Message],
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        stream: bool = False,
        tools: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Make a chat completion request to the Copilot API.

        Args:
            messages: List of Message objects
            model: Model ID (e.g., "gpt-4o", "claude-sonnet-4")
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response
            tools: Optional list of tool definitions

        Returns:
            The API response as a dictionary
        """
        # Check if this is an agent call (has assistant/tool messages)
        is_agent_call = any(m.role in ("assistant", "tool") for m in messages)

        # Check if this is a vision request (has images)
        is_vision = False  # Would check for image_url parts in messages

        # Build request body
        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if tools:
            body["tools"] = tools

        # Make request
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(is_agent_call, is_vision),
            json=body,
        )

        if not response.ok:
            error_text = response.text
            # Add helpful message for unsupported models
            if "The requested model is not supported" in error_text:
                error_text += "\n\nMake sure the model is enabled in your copilot settings: https://github.com/settings/copilot/features"
            raise Exception(f"API error: {response.status_code} {error_text}")

        return response.json()

    def chat_completion_stream(
        self,
        messages: List[Message],
        model: str = "gpt-4o",
        temperature: float = 0.0,
        max_tokens: int = 4096,
        tools: Optional[List[Dict]] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Make a streaming chat completion request.

        Yields:
            Parsed SSE chunks from the API
        """
        is_agent_call = any(m.role in ("assistant", "tool") for m in messages)

        body = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        if tools:
            body["tools"] = tools

        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self._get_headers(is_agent_call),
            json=body,
            stream=True,
        )

        if not response.ok:
            raise Exception(f"API error: {response.status_code} {response.text}")

        for line in response.iter_lines():
            if not line:
                continue

            line = line.decode("utf-8")
            if line.startswith("data: "):
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    yield json.loads(data)
                except json.JSONDecodeError:
                    continue


# =============================================================================
# TOKEN STORAGE
# =============================================================================

class TokenStorage:
    """
    Stores and retrieves authentication tokens.

    Uses the same format as OpenCode:
    ~/.local/share/opencode/auth.json
    """

    def __init__(self, storage_path: Optional[Path] = None):
        if storage_path:
            self.storage_path = storage_path
        else:
            # Default to OpenCode's storage location
            self.storage_path = Path.home() / ".local" / "share" / "opencode" / "auth.json"

    def save(self, provider_id: str, auth: CopilotAuth):
        """Save authentication for a provider"""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        data = {}
        if self.storage_path.exists():
            data = json.loads(self.storage_path.read_text())

        data[provider_id] = auth.to_dict()

        self.storage_path.write_text(json.dumps(data, indent=2))
        os.chmod(self.storage_path, 0o600)  # Secure file permissions

    def load(self, provider_id: str) -> Optional[CopilotAuth]:
        """Load authentication for a provider"""
        if not self.storage_path.exists():
            return None

        data = json.loads(self.storage_path.read_text())

        if provider_id not in data:
            return None

        return CopilotAuth.from_dict(data[provider_id])

    def remove(self, provider_id: str):
        """Remove authentication for a provider"""
        if not self.storage_path.exists():
            return

        data = json.loads(self.storage_path.read_text())

        if provider_id in data:
            del data[provider_id]
            self.storage_path.write_text(json.dumps(data, indent=2))


# =============================================================================
# HIGH-LEVEL API
# =============================================================================

def authenticate(enterprise_url: Optional[str] = None) -> Optional[CopilotClient]:
    """
    Authenticate with GitHub Copilot and return a client.

    Args:
        enterprise_url: GitHub Enterprise URL (optional)

    Returns:
        CopilotClient if authentication successful, None otherwise
    """
    storage = TokenStorage()
    provider_id = "github-copilot-enterprise" if enterprise_url else "github-copilot"

    # Try to load existing auth
    auth = storage.load(provider_id)

    if auth:
        print("Using existing authentication...")
        return CopilotClient(auth)

    # Need to authenticate
    authenticator = CopilotAuthenticator(enterprise_url)
    auth = authenticator.authenticate_interactive()

    if not auth:
        return None

    # Save for future use
    storage.save(provider_id, auth)

    return CopilotClient(auth)


def chat(
    prompt: str,
    model: str = "gpt-4o",
    system: Optional[str] = None,
    enterprise_url: Optional[str] = None,
) -> str:
    """
    Simple chat function - authenticate and send a message.

    Args:
        prompt: User message
        model: Model to use
        system: Optional system prompt
        enterprise_url: GitHub Enterprise URL (optional)

    Returns:
        Assistant response
    """
    client = authenticate(enterprise_url)

    if not client:
        raise Exception("Authentication failed")

    messages = []
    if system:
        messages.append(Message(role="system", content=system))
    messages.append(Message(role="user", content=prompt))

    response = client.chat_completion(messages, model=model)

    return response["choices"][0]["message"]["content"]


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def example_basic_chat():
    """Example: Basic chat with Copilot"""
    client = authenticate()

    if not client:
        print("Failed to authenticate!")
        return

    messages = [
        Message(role="system", content="You are a helpful coding assistant."),
        Message(role="user", content="Write a Python function to calculate factorial."),
    ]

    response = client.chat_completion(
        messages,
        model="gpt-4o",
        temperature=0.0,
    )

    print("Response:")
    print(response["choices"][0]["message"]["content"])


def example_streaming():
    """Example: Streaming chat"""
    client = authenticate()

    if not client:
        return

    messages = [
        Message(role="user", content="Explain quantum computing in simple terms."),
    ]

    print("Streaming response:")
    for chunk in client.chat_completion_stream(messages, model="claude-sonnet-4"):
        if "choices" in chunk and len(chunk["choices"]) > 0:
            delta = chunk["choices"][0].get("delta", {})
            if "content" in delta:
                print(delta["content"], end="", flush=True)
    print()


def example_with_tools():
    """Example: Using tools/function calling"""
    client = authenticate()

    if not client:
        return

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get the current weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The city and state, e.g. San Francisco, CA",
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    messages = [
        Message(role="user", content="What's the weather in San Francisco?"),
    ]

    response = client.chat_completion(
        messages,
        model="gpt-4o",
        tools=tools,
    )

    print("Response with tools:")
    print(json.dumps(response, indent=2))


def list_available_models():
    """List all available Copilot models"""
    print("Available GitHub Copilot Models:")
    print("=" * 50)
    for model in AVAILABLE_MODELS:
        print(f"  - {model}")
    print("=" * 50)
    print("\nNote: Some models require enabling in GitHub settings:")
    print("  https://github.com/settings/copilot/features")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "auth":
            # Just authenticate
            client = authenticate()
            if client:
                print("Authentication successful!")
            else:
                print("Authentication failed!")

        elif command == "models":
            list_available_models()

        elif command == "chat":
            # Simple chat
            if len(sys.argv) < 3:
                print("Usage: python github_copilot_integration_analysis.py chat 'your message'")
                sys.exit(1)

            message = " ".join(sys.argv[2:])
            model = os.environ.get("COPILOT_MODEL", "gpt-4o")

            try:
                response = chat(message, model=model)
                print(response)
            except Exception as e:
                print(f"Error: {e}")
                sys.exit(1)

        elif command == "example":
            # Run examples
            print("\n=== Basic Chat Example ===\n")
            example_basic_chat()

        else:
            print(f"Unknown command: {command}")
            print("Available commands: auth, models, chat, example")
    else:
        print(__doc__)
        print("\nUsage:")
        print("  python github_copilot_integration_analysis.py auth     # Authenticate")
        print("  python github_copilot_integration_analysis.py models   # List models")
        print("  python github_copilot_integration_analysis.py chat 'message'  # Chat")
        print("  python github_copilot_integration_analysis.py example  # Run example")
