"""ADK Agent example with evaluation integration."""

import os

import argparse
import asyncio
import time
import yaml
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import FunctionTool
from google.genai import types
from agent_evaluation_sdk import enable_evaluation


# Test queries covering different aspects
TEST_QUERIES = [
    # Simple factual questions (no tools needed)
    "What does HTTP stand for?",
    # Search tool queries
    "Search for the latest news about artificial intelligence",
    # Calculator tool queries
    "Compute 15 + 37 * 2",
    # Complex queries (may use tools)
    "Search for Python tutorials and tell me the top 3 topics",
    # Edge cases
    "Can you help me?",
]


def load_agent_config():
    """Load agent configuration from YAML file."""
    with open("agent_config.yaml") as f:
        return yaml.safe_load(f)


def create_adk_agent():
    """Create ADK agent with evaluation."""
    # Load configuration
    config = load_agent_config()

    # Configure Vertex AI for ADK (ADK uses environment variables)
    os.environ["GOOGLE_CLOUD_PROJECT"] = config["project_id"]
    os.environ["GOOGLE_CLOUD_LOCATION"] = config["location"]
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"

    # Create ADK agent first (without tools)
    agent = Agent(
        name="adk_agent",
        model=config["model"],
        instruction="You are a helpful assistant. Provide concise, clear answers.",
    )

    # Create runner
    runner = InMemoryRunner(agent=agent, app_name="adk_agent_app")

    # Enable evaluation on runner (wraps runner.run_async which is an async generator)
    wrapper = enable_evaluation(
        runner, config["project_id"], "adk_agent", "eval_config.yaml"
    )

    # Define mock tools WITH tracing decorator
    @wrapper.tool_trace("search")
    def search_tool(query: str) -> str:
        time.sleep(0.5)
        return f"Mock search results for: {query}"

    @wrapper.tool_trace("calculator")
    def calculator_tool(expression: str) -> str:
        time.sleep(0.2)
        return "Mock result: 42"

    # Create ADK tools with wrapped functions
    search = FunctionTool(search_tool)
    calculator = FunctionTool(calculator_tool)

    # Add tools to agent
    agent.tools = [search, calculator]

    return agent, runner, wrapper, config


async def run_test_queries():
    """Run test queries."""
    agent, runner, wrapper, config = create_adk_agent()

    # Create session
    session = await runner.session_service.create_session(
        app_name="adk_agent_app", user_id="test_user"
    )

    print("=" * 70)
    print("Running Test Queries")
    print("=" * 70)
    print(f"\nTotal queries: {len(TEST_QUERIES)}")
    print("This will generate a dataset for evaluation.\n")

    results = []
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] Query: {query}")
        try:
            start = time.time()
            content = types.Content(
                role="user", parts=[types.Part.from_text(text=query)]
            )

            # Collect response from async generator
            response_text = ""
            async for event in runner.run_async(
                user_id="test_user",
                session_id=session.id,
                new_message=content,
            ):
                if event.content.parts and event.content.parts[0].text:
                    response_text = event.content.parts[0].text

            duration = (time.time() - start) * 1000
            print(f"Response: {response_text[:100]}...")
            print(f"⏱️  {duration:.0f}ms")

            results.append(
                {
                    "query": query,
                    "response": response_text,
                    "duration_ms": duration,
                    "success": True,
                }
            )
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append(
                {
                    "query": query,
                    "response": None,
                    "duration_ms": 0,
                    "success": False,
                    "error": str(e),
                }
            )

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    avg_duration = (
        sum(r["duration_ms"] for r in results if r["success"]) / successful
        if successful > 0
        else 0
    )

    print(f"✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")
    print(f"⏱️  Average response time: {avg_duration:.0f}ms")

    # Flush before shutdown to ensure all data is written
    time.sleep(2)  # Give time for async operations to complete
    wrapper.flush()
    time.sleep(1)  # Give time for flush to complete
    wrapper.shutdown()

    print("\n" + "=" * 70)
    print("✅ Test complete! Dataset ready for evaluation.")
    print("📊 View data in GCP Console (Logs, Traces, BigQuery)")
    print("=" * 70)


async def run_interactive():
    """Run agent in interactive mode."""
    agent, runner, wrapper, config = create_adk_agent()

    # Create session
    session = await runner.session_service.create_session(
        app_name="adk_agent_app", user_id="interactive_user"
    )

    print("ADK Agent is ready! Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                break
            if not user_input:
                continue

            content = types.Content(
                role="user", parts=[types.Part.from_text(text=user_input)]
            )

            # Collect response from async generator
            response_text = ""
            async for event in runner.run_async(
                user_id="interactive_user",
                session_id=session.id,
                new_message=content,
            ):
                if event.content.parts and event.content.parts[0].text:
                    response_text = event.content.parts[0].text

            print(f"Agent: {response_text}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}\n")

    # Flush before shutdown to ensure all data is written
    wrapper.flush()
    wrapper.shutdown()
    print("\n👋 Goodbye!")


async def main():
    """Main entry point with CLI argument handling."""
    parser = argparse.ArgumentParser(
        description="ADK Agent with Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test queries instead of interactive mode",
    )

    args = parser.parse_args()

    if args.test:
        await run_test_queries()
    else:
        await run_interactive()


if __name__ == "__main__":
    asyncio.run(main())
