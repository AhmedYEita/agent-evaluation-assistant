"""
Simple ADK Agent with Evaluation integration.
"""

import time
from pathlib import Path

from google.genai.adk import Agent

# Import the evaluation SDK
from agent_evaluation_sdk import enable_evaluation, EvaluationConfig


def create_agent():
    """Create and configure the agent with evaluation enabled."""
    # Load configuration
    config = EvaluationConfig.from_yaml(Path("eval_config.yaml"))

    # Create agent
    agent = Agent(
        model=config.agent.model,
        system_instruction=(
            "You are a helpful AI assistant with access to mock calculator and search tools. "
            "Provide clear, concise answers to user questions."
        ),
    )

    # Enable evaluation and get wrapper for tool tracing
    wrapper = enable_evaluation(
        agent=agent,
        project_id=config.project_id,
        agent_name=config.agent_name,
        config=config,
    )

    # Define tools with tracing
    @wrapper.tool_trace("search")
    def search_tool(query: str) -> str:
        """Search the web for information (mock implementation)."""
        # Simulate search API call
        time.sleep(0.5)
        return f"Search web for '{query}'"

    @wrapper.tool_trace("calculator")
    def calculator_tool(expression: str) -> str:
        """Evaluate mathematical expressions (mock implementation)."""
        # Simulate calculation
        time.sleep(0.2)
        return "Mock result: X"

    # Register tools with agent
    agent.add_tools([search_tool, calculator_tool])

    return agent, config


def main():
    """Run agent in interactive mode."""
    print("🚀 Loading configuration from eval_config.yaml...")
    print()

    agent, config = create_agent()

    print(f"   Project: {config.project_id}")
    print(f"   Agent: {config.agent_name}")
    print()
    print("=" * 70)
    print("Agent is ready! Try asking some questions.")
    print("Type 'quit' to exit.")
    print("=" * 70)
    print()

    # Interactive loop
    while True:
        try:
            user_input = input("You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\n👋 Goodbye!")
                break

            if not user_input:
                continue

            # Generate response
            print("Agent: ", end="", flush=True)
            response = agent.generate_content(user_input)

            # Print response
            if hasattr(response, "text"):
                print(response.text)
            else:
                print(response)

            print()

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print()

    print()
    print("=" * 70)
    print("📊 View your evaluation data:")
    print()
    print(
        f"Logs:       https://console.cloud.google.com/logs?project={config.project_id}"
    )
    print(
        f"Traces:     https://console.cloud.google.com/traces?project={config.project_id}"
    )
    print(
        f"Dashboards: https://console.cloud.google.com/monitoring/dashboards?project={config.project_id}"
    )

    # Show BigQuery dataset link if collection is enabled
    if config.dataset.auto_collect:
        print()
        print("📦 Dataset (collected interactions):")
        print(
            f"   https://console.cloud.google.com/bigquery?project={config.project_id}"
        )
        print(f"   → Navigate to: agent_evaluation.{config.agent_name}_eval_dataset")

    print("=" * 70)


if __name__ == "__main__":
    main()
