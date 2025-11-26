"""
Simple GitHub Copilot Information Script

This script demonstrates basic connectivity to OpenCode server and provides
information about GitHub Copilot integration without requiring authentication.

Usage:
    python examples/copilot_info.py
"""

from opencode_ai import OpenCodeClient
import sys


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def main():
    """Display GitHub Copilot integration information."""
    
    print("🚀 OpenCode - GitHub Copilot Integration Info")
    
    # Connect to OpenCode server
    print_section("Connection Test")
    client = OpenCodeClient(base_url="http://localhost:4096")
    
    try:
        # Test connection
        config = client.get_config()
        print("✅ Successfully connected to OpenCode server")
        
        # Show path information
        path_info = client.get_path()
        if path_info:
            print(f"📁 Current directory: {getattr(path_info, 'directory', 'N/A')}")
    
    except Exception as e:
        print(f"❌ Error connecting to OpenCode: {e}")
        print("\n💡 Make sure OpenCode server is running:")
        print("   $ opencode")
        sys.exit(1)
    
    # GitHub Copilot Setup Instructions
    print_section("GitHub Copilot Setup")
    print("To use GitHub Copilot with OpenCode:\n")
    print("1. Ensure you have an active GitHub Copilot subscription")
    print("   https://github.com/features/copilot\n")
    print("2. Authenticate with GitHub Copilot:")
    print("   $ opencode auth login")
    print("   → Select 'GitHub Copilot'")
    print("   → Visit github.com/login/device")
    print("   → Enter the provided code\n")
    print("3. Enable desired models in GitHub settings:")
    print("   https://github.com/settings/copilot/features\n")
    print("4. Verify authentication:")
    print("   $ opencode auth list")
    
    # Available Models
    print_section("Available Models")
    print("When authenticated, GitHub Copilot provides:\n")
    
    models = [
        ("claude-sonnet-3.5", "Anthropic Claude", "Best for complex code tasks"),
        ("claude-haiku", "Anthropic Claude", "Fast, efficient"),
        ("gpt-4o", "OpenAI", "Advanced reasoning"),
        ("gpt-4o-mini", "OpenAI", "Fast, cost-effective"),
        ("o1", "OpenAI", "Reasoning model"),
        ("o1-mini", "OpenAI", "Lighter reasoning"),
    ]
    
    for model_id, provider, description in models:
        print(f"  github-copilot/{model_id:<20s}")
        print(f"    Provider: {provider}")
        print(f"    Use case: {description}\n")
    
    # Model Requirements
    print_section("Model Requirements")
    print("⚠️  Some models require specific subscription tiers:\n")
    print("  • Individual ($10/month) - Basic models")
    print("  • Pro+ ($19/month) - Claude, o1 models")
    print("  • Enterprise - All models + custom configuration\n")
    print("Some models need manual enablement in GitHub Copilot settings.")
    
    # Python SDK Usage
    print_section("Python SDK Usage")
    print("Example workflow:\n")
    print("```python")
    print("from opencode_ai import OpenCodeClient")
    print("")
    print("# Connect to server")
    print("client = OpenCodeClient()")
    print("")
    print("# Check configuration")
    print("config = client.get_config()")
    print("")
    print("# List sessions")
    print("sessions = client.list_sessions()")
    print("")
    print("# Subscribe to events (streaming)")
    print("for event in client.subscribe_events():")
    print("    print(event)")
    print("```")
    
    # Resources
    print_section("Additional Resources")
    print("📚 Documentation:")
    print("  • OpenCode Docs: https://opencode.ai/docs")
    print("  • SDK Guide: https://opencode.ai/docs/sdk")
    print("  • Providers: https://opencode.ai/docs/providers")
    print("  • GitHub Copilot Integration:")
    print("    packages/sdk/python/docs/github-copilot-integration.md\n")
    print("💬 Support:")
    print("  • Discord: https://discord.gg/opencode")
    print("  • GitHub: https://github.com/sst/opencode/issues")
    
    print("\n" + "=" * 60)
    print("✨ For interactive usage, use the OpenCode TUI: `opencode`")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
