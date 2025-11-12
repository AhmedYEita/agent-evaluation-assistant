"""ADK Agent example with evaluation integration."""

import warnings
import os

# Suppress warnings before any imports
warnings.filterwarnings("ignore", message=".*non-text parts.*")
warnings.filterwarnings("ignore", category=UserWarning, module="google.genai")

# Suppress gRPC/absl logging
os.environ["GRPC_VERBOSITY"] = "ERROR"
os.environ["GLOG_minloglevel"] = "2"

import asyncio
import time
from pathlib import Path
from google.adk import Agent  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.adk.sessions import Session  # noqa: E402
from google.adk.tools import FunctionTool  # noqa: E402
from google.genai import types  # noqa: E402
from agent_evaluation_sdk import enable_evaluation, EvaluationConfig  # noqa: E402


def create_adk_agent():
    """Create ADK agent with evaluation."""
    config = EvaluationConfig.from_yaml(Path("eval_config.yaml"))
    
    # Configure Vertex AI for ADK (ADK uses environment variables)
    os.environ["GOOGLE_CLOUD_PROJECT"] = config.project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
    
    # Create ADK agent first (without tools)
    agent = Agent(
        name=config.agent_name,
        model=config.agent.model,
        instruction="You are a helpful assistant. Provide concise, clear answers.",
    )
    
    # Create runner
    runner = InMemoryRunner(agent=agent, app_name="adk_agent_app")
    
    # Enable evaluation on runner (wraps runner.run_async which is an async generator)
    wrapper = enable_evaluation(runner, config.project_id, config.agent_name, "eval_config.yaml")
    
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


async def main():
    """Run test queries."""
    agent, runner, wrapper, config = create_adk_agent()
    
    test_queries = [
        "What is 2+2?",
        "Search for Python documentation",
        "Calculate 15 * 23",
        "Search for AI news and summarize",
        "What is 100 divided by 4?",
    ]
    
    # Create session
    session = await runner.session_service.create_session(
        app_name="adk_agent_app", user_id="test_user"
    )
    
    print("=" * 70)
    print("ADK Agent Test Queries")
    print("=" * 70)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n[{i}/{len(test_queries)}] Query: {query}")
        try:
            start = time.time()
            content = types.Content(role="user", parts=[types.Part.from_text(text=query)])
            
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
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Flush before shutdown to ensure all data is written
    wrapper.flush()
    wrapper.shutdown()
    
    print("\n" + "=" * 70)
    print("✅ Test complete!")
    print(f"📊 View traces: https://console.cloud.google.com/traces?project={config.project_id}")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
