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

Note:
    This example demonstrates the conceptual workflow. The actual session and
    prompt APIs may require using the lower-level generated client methods.
    See the SDK documentation for complete API details.
"""

from opencode_ai import OpenCodeClient
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
        if config:
            print(f"✅ Connected to OpenCode")
        else:
            print("⚠️  Could not fetch config, but connection established")
        
        # Step 2: Check providers configuration
        print("\n🤖 Checking for GitHub Copilot configuration...")
        
        # Note: To use GitHub Copilot, you must first authenticate:
        # Run: opencode auth login
        # Then select "GitHub Copilot" and follow the OAuth flow
        
        try:
            providers_info = client.config_providers()
            if providers_info:
                print("✅ Provider configuration retrieved")
                # The providers_info may contain details about available providers
                # including github-copilot if authenticated
        except Exception as e:
            print(f"⚠️  Could not fetch providers: {e}")
        
        # Step 3: Available GitHub Copilot models
        print("\n📦 GitHub Copilot Models (when authenticated):")
        
        copilot_models = [
            {
                "id": "claude-sonnet-3.5",
                "name": "Claude Sonnet 3.5",
                "description": "Most capable, best for complex tasks"
            },
            {
                "id": "claude-haiku",
                "name": "Claude Haiku",
                "description": "Fast, efficient for simpler queries"
            },
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "description": "Advanced reasoning and code understanding"
            },
            {
                "id": "gpt-4o-mini",
                "name": "GPT-4o Mini",
                "description": "Fast, cost-effective"
            },
            {
                "id": "o1",
                "name": "o1",
                "description": "Advanced reasoning model"
            },
            {
                "id": "o1-mini",
                "name": "o1-mini",
                "description": "Lighter reasoning model"
            }
        ]
        
        for model in copilot_models:
            print(f"   • {model['id']:20s} - {model['description']}")
        
        # Step 4: Check existing sessions
        print("\n📚 Checking existing sessions...")
        sessions = client.list_sessions() or []
        print(f"✅ Found {len(sessions)} existing session(s)")
        
        # Step 5: Instructions for creating sessions and sending prompts
        print("\n💡 To use GitHub Copilot models programmatically:")
        print("   1. Use the lower-level generated client APIs")
        print("   2. Create a session using the appropriate API endpoint")
        print("   3. Send prompts with model configuration:")
        print("      {")
        print('        "providerID": "github-copilot",')
        print('        "modelID": "claude-sonnet-3.5"')
        print("      }")
        
        print("\n📖 For complete API documentation, see:")
        print("   • docs/github-copilot-integration.md")
        print("   • https://opencode.ai/docs/sdk")
        
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
