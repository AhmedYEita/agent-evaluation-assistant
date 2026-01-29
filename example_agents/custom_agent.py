"""Custom Agent with Evaluation integration.

This example shows how to integrate the evaluation SDK with any agent.
Replace MyAgent with your actual agent class - it just needs a generate_content() method.
"""

import argparse
import time
import yaml
from google import genai
from google.genai import types
from agent_evaluation_sdk import enable_evaluation


# Test queries covering different aspects
TEST_QUERIES = [
    # Simple factual questions (no tools needed)
    "Explain what an API is",
    # Search tool queries
    "Look up best practices for REST APIs",
    # Calculator tool queries
    "What is 1024 divided by 16?",
    # Complex queries (may use tools)
    "What's the difference between a list and a tuple in Python?",
    # Edge cases
    "Thanks for your help",
]


# Example: Your agent class (replace with your actual agent implementation)
class MyAgent:
    """Simple agent wrapper - replace with your actual agent implementation."""

    def __init__(self, model, client, tools, tool_functions):
        self.model = model
        self.client = client
        self.tools = tools
        self.tool_functions = tool_functions
        self.system_instruction = (
            "You are a helpful assistant. Provide concise, clear answers."
        )

    def generate_content(self, prompt):
        """Required method: SDK wraps this to add observability."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                tools=self.tools,
                system_instruction=self.system_instruction,
            ),
        )

        # Handle tool calls (your agent's tool handling logic)
        if response.function_calls:
            call = response.function_calls[0]
            result = self.tool_functions[call.name](**dict(call.args))

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    prompt,
                    response.candidates[0].content,
                    types.Content(
                        role="function",
                        parts=[
                            types.Part.from_function_response(
                                name=call.name, response={"result": result}
                            )
                        ],
                    ),
                ],
                config=types.GenerateContentConfig(
                    tools=self.tools,
                    system_instruction=self.system_instruction,
                ),
            )

        return response


def load_agent_config():
    """Load agent configuration from YAML file."""
    with open("agent_config.yaml") as f:
        return yaml.safe_load(f)


def create_agent():
    """Create agent with evaluation - minimal integration."""
    # Load configuration
    config = load_agent_config()

    # 1. Create your agent (as you normally would)
    client = genai.Client(
        vertexai=True, project=config["project_id"], location=config["location"]
    )

    # Define tools
    tools = [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="search_tool",
                    description="Search the web for information",
                    parameters={
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query"}
                        },
                        "required": ["query"],
                    },
                ),
                types.FunctionDeclaration(
                    name="calculator_tool",
                    description="Evaluate mathematical expressions",
                    parameters={
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "Math expression",
                            }
                        },
                        "required": ["expression"],
                    },
                ),
            ]
        )
    ]

    agent = MyAgent(
        model=config["model"], client=client, tools=tools, tool_functions={}
    )

    # 2. Enable evaluation (ONE LINE!)
    wrapper = enable_evaluation(
        agent, config["project_id"], "custom_agent", "eval_config.yaml"
    )

    # 3. Define tools with tracing decorator
    @wrapper.tool_trace("search")
    def search_tool(query: str) -> str:
        time.sleep(0.5)
        return f"Mock search results for: {query}"

    @wrapper.tool_trace("calculator")
    def calculator_tool(expression: str) -> str:
        time.sleep(0.2)
        return "Mock result: 42"

    # 4. Register tools with agent
    agent.tool_functions = {
        "search_tool": search_tool,
        "calculator_tool": calculator_tool,
    }

    return agent, wrapper


def run_test_queries():
    """Run all test queries and collect responses."""
    print("=" * 70)
    print("Running Test Queries")
    print("=" * 70)
    print(f"\nTotal queries: {len(TEST_QUERIES)}")
    print("This will generate a dataset for evaluation.\n")

    agent, wrapper = create_agent()

    results = []
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[{i}/{len(TEST_QUERIES)}] Query: {query}")

        try:
            start = time.time()
            response = agent.generate_content(query)
            duration = (time.time() - start) * 1000

            response_text = (
                response.text if hasattr(response, "text") else str(response)
            )
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

        # Small delay to avoid rate limits
        time.sleep(1)

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


def run_interactive():
    """Run agent in interactive mode."""
    agent, wrapper = create_agent()

    print("Agent is ready! Type 'quit' to exit.\n")

    while True:
        try:
            user_input = input("You: ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                break
            if not user_input:
                continue

            response = agent.generate_content(user_input)
            print(f"Agent: {response.text}\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}\n")

    wrapper.shutdown()
    print("\n👋 Goodbye!")


def main():
    """Main entry point with CLI argument handling."""
    parser = argparse.ArgumentParser(
        description="Custom Agent with Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test queries instead of interactive mode",
    )

    args = parser.parse_args()

    if args.test:
        run_test_queries()
    else:
        run_interactive()


if __name__ == "__main__":
    main()
