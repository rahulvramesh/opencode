"""
GitHub Copilot Integration Example for OpenCode Python SDK

This example demonstrates how to use the OpenCode Python SDK with GitHub Copilot
as the LLM provider. It shows the complete workflow from authentication to
making API calls with Copilot models.

Prerequisites:
1. OpenCode server running locally (or specify a different base URL)
2. GitHub Copilot authentication configured via `opencode auth login`
3. Python 3.8+ with the opencode-ai package installed

Usage:
    python examples/github_copilot_usage.py
"""

from opencode_ai import OpenCodeClient
from opencode_ai.models import SessionCreate, PromptMessage
import sys


def main():
    """
    Demonstrate GitHub Copilot integration with OpenCode SDK.
    
    This example shows:
    1. Connecting to the OpenCode server
    2. Listing available GitHub Copilot models
    3. Creating a session with Copilot
    4. Sending prompts to GitHub Copilot models
    5. Handling responses
    """
    
    # Initialize the OpenCode client
    # By default, it connects to http://localhost:4096
    print("🔌 Connecting to OpenCode server...")
    client = OpenCodeClient(base_url="http://localhost:4096")
    
    try:
        # Step 1: Get configuration to verify connection
        print("\n📋 Fetching OpenCode configuration...")
        config = client.get_config()
        print(f"✅ Connected to OpenCode (version: {config.version if hasattr(config, 'version') else 'unknown'})")
        
        # Step 2: List available providers and models
        print("\n🤖 Checking for GitHub Copilot models...")
        
        # Note: To use GitHub Copilot, you must first authenticate:
        # Run: opencode auth login
        # Then select "GitHub Copilot" and follow the OAuth flow
        
        # The following models are typically available with GitHub Copilot:
        # - claude-sonnet-3.5 (Anthropic Claude via Copilot)
        # - claude-haiku (Anthropic Claude via Copilot)
        # - gpt-4o (OpenAI GPT-4o via Copilot)
        # - gpt-4o-mini (OpenAI GPT-4o Mini via Copilot)
        # - o1 (OpenAI o1 via Copilot)
        # - o1-mini (OpenAI o1-mini via Copilot)
        
        copilot_models = [
            "claude-sonnet-3.5",
            "claude-haiku", 
            "gpt-4o",
            "gpt-4o-mini",
            "o1",
            "o1-mini"
        ]
        
        print("\n📦 Available GitHub Copilot models:")
        for model in copilot_models:
            print(f"   • github-copilot/{model}")
        
        # Step 3: Create a new session
        print("\n🆕 Creating a new session...")
        session_data = SessionCreate(
            title="GitHub Copilot Example Session"
        )
        session = client.create_session(body=session_data)
        print(f"✅ Session created with ID: {session.id}")
        
        # Step 4: Send a prompt to GitHub Copilot
        print("\n💬 Sending prompt to GitHub Copilot (claude-sonnet-3.5)...")
        
        # Prepare the prompt message
        prompt_data = PromptMessage(
            model={
                "providerID": "github-copilot",
                "modelID": "claude-sonnet-3.5"
            },
            parts=[{
                "type": "text",
                "text": "Explain in 2-3 sentences what GitHub Copilot is and how it helps developers."
            }]
        )
        
        # Send the prompt and get response
        response = client.post_session_by_id_prompt(
            path={"id": session.id},
            body=prompt_data
        )
        
        print("\n📝 Response from GitHub Copilot:")
        print("=" * 60)
        
        # The response contains message parts
        if hasattr(response, 'parts') and response.parts:
            for part in response.parts:
                if hasattr(part, 'text'):
                    print(part.text)
        else:
            print(response)
        
        print("=" * 60)
        
        # Step 5: List all sessions to verify
        print("\n📚 Listing all sessions...")
        sessions = client.list_sessions() or []
        print(f"✅ Total sessions: {len(sessions)}")
        
        # Step 6: Clean up (optional)
        print(f"\n🗑️  To delete this session, run:")
        print(f"   client.delete_session_by_id(path={{'id': '{session.id}'}})")
        
        print("\n✨ Example completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n⚠️  Common issues:")
        print("   1. Ensure OpenCode server is running: `opencode`")
        print("   2. Authenticate with GitHub Copilot: `opencode auth login`")
        print("   3. Select 'GitHub Copilot' and complete OAuth flow")
        print("   4. Ensure you have an active GitHub Copilot subscription")
        print("\n📖 For more info, visit: https://opencode.ai/docs/providers#github-copilot")
        sys.exit(1)


def list_copilot_capabilities():
    """
    Additional helper function to demonstrate GitHub Copilot capabilities.
    
    GitHub Copilot in OpenCode supports:
    - Multiple AI models (Claude, GPT-4, o1)
    - Code generation and explanation
    - Code review and suggestions
    - Documentation generation
    - Bug fixing and debugging assistance
    """
    
    capabilities = {
        "Models": [
            "Claude Sonnet 3.5 - Best for code generation and complex tasks",
            "Claude Haiku - Fast, efficient for simpler queries",
            "GPT-4o - Advanced reasoning and code understanding",
            "GPT-4o Mini - Fast, cost-effective for simple tasks",
            "o1 - OpenAI's reasoning model for complex problems",
            "o1-mini - Lighter reasoning model"
        ],
        "Features": [
            "Code generation from natural language",
            "Code explanation and documentation",
            "Bug detection and fixing",
            "Code refactoring suggestions",
            "Test generation",
            "Code review and best practices"
        ],
        "Subscription Requirements": [
            "GitHub Copilot Individual ($10/month)",
            "GitHub Copilot Business ($19/user/month)", 
            "GitHub Copilot Enterprise (Custom pricing)"
        ]
    }
    
    return capabilities


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 OpenCode Python SDK - GitHub Copilot Integration Example")
    print("=" * 60)
    main()
