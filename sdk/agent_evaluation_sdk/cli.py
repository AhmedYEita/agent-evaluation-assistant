"""
CLI for Agent Evaluation Setup Assistant

This CLI provides quick validation and directs users to run the assistant locally.
"""

import argparse
import sys
from pathlib import Path


def setup_command(args):
    """Direct user to run the assistant locally"""
    print("\n" + "=" * 60)
    print("🤖 Agent Evaluation Setup Assistant")
    print("=" * 60 + "\n")

    print("The setup assistant is an interactive ADK agent that helps you")
    print("configure your agent evaluation infrastructure.\n")

    print("📋 Prerequisites:\n")
    print("  1. Clone the SDK repo (separate from your agent):")
    print("     cd ~/repos  # or wherever you keep repositories")
    print("     git clone https://github.com/yourorg/agent-evaluation-assistant")
    print("     cd agent-evaluation-assistant")
    print("     pip install -e ./sdk\n")

    print("  2. Run the interactive assistant:")
    print("     cd assistant/agent")
    print("     pip install -r requirements.txt")
    print("     python assistant_agent.py\n")

    print("The assistant will:")
    print("  • Get your agent project path")
    print("  • Verify your agent is compatible")
    print("  • Help you configure observability services")
    print("  • Generate customized config files in YOUR project")
    print("  • Copy terraform infrastructure to YOUR project")
    print("  • Show you how to integrate the SDK\n")

    print("💡 Keep the SDK repo separate from your agent project!")
    print("   ~/repos/agent-evaluation-assistant/  ← SDK (clone here)")
    print("   ~/repos/my-agent/                ← Your agent (existing)\n")


def validate_command(args):
    """Quick validation of existing setup"""
    print("\n" + "=" * 60)
    print("🔍 Setup Validation")
    print("=" * 60 + "\n")

    project_path = Path(args.project).expanduser().resolve()
    print(f"Checking: {project_path}\n")

    issues = []
    warnings = []

    # Check eval_config.yaml
    eval_config = project_path / "eval_config.yaml"
    if eval_config.exists():
        print("✓ eval_config.yaml found")
        try:
            import yaml

            with open(eval_config) as f:
                config = yaml.safe_load(f)
            print("✓ Valid YAML syntax")

            # Check if auto_collect is enabled
            if config.get("dataset", {}).get("auto_collect"):
                warnings.append(
                    "auto_collect is enabled - remember to disable after collecting data"
                )
        except Exception as e:
            issues.append(f"YAML error: {e}")
            print(f"✗ YAML error: {e}")
    else:
        issues.append("eval_config.yaml not found")
        print("✗ eval_config.yaml not found")

    # Check terraform module
    terraform_module = project_path / "terraform/modules/agent_evaluation"
    if terraform_module.exists():
        print("✓ Terraform module found")
    else:
        issues.append("Terraform module not found")
        print("✗ Terraform module not found")

    print()

    # Summary
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"  • {issue}")
        print()

    if warnings:
        print("⚠️  Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
        print()

    if not issues and not warnings:
        print("✓ Everything looks good! 🎉\n")

    # Next steps if issues
    if issues:
        print("💡 To fix these issues, run the setup assistant:")
        print("  cd assistant/agent && python assistant_agent.py\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Agent Evaluation Setup Assistant CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agent-eval-assistant setup              # Get instructions to run the assistant
  agent-eval-assistant validate           # Check your current setup
  agent-eval-assistant validate --project ~/my-agent  # Check specific directory
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser(
        "setup", help="Get instructions to run the interactive setup assistant"
    )
    setup_parser.set_defaults(func=setup_command)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate your existing setup configuration"
    )
    validate_parser.add_argument(
        "--project", default=".", help="Project directory to validate (default: current directory)"
    )
    validate_parser.set_defaults(func=validate_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
