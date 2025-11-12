"""Simple Agent with Evaluation integration.

This example shows how to integrate the evaluation SDK with any agent.
Replace MyAgent with your actual agent class - it just needs a generate_content() method.
"""

import time
from google import genai
from google.genai import types
from agent_evaluation_sdk import enable_evaluation


# Example: Your agent class (replace with your actual agent)
class MyAgent:
    """Simple agent wrapper - replace with your actual agent implementation."""
    
    def __init__(self, model, client, tools, tool_functions):
        self.model = model
        self.client = client
        self.tools = tools
        self.tool_functions = tool_functions

    def generate_content(self, prompt):
        """Required method: SDK wraps this to add observability."""
        response = self.client.models.generate_content(
            model=self.model,
            contents=[prompt],
            config=types.GenerateContentConfig(
                tools=self.tools,
                system_instruction="You are a helpful assistant. Provide concise, clear answers.",
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
                    system_instruction="You are a helpful assistant. Provide concise, clear answers.",
                ),
            )

        return response


def create_agent():
    """Create agent with evaluation - minimal integration."""
    # 1. Create your agent (as you normally would)
    client = genai.Client(
        vertexai=True, project="dt-ahmedyasser-sandbox-dev", location="us-central1"
    )

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
        model="gemini-2.5-flash", client=client, tools=tools, tool_functions={}
    )

    # 2. Enable evaluation (ONE LINE!)
    wrapper = enable_evaluation(
        agent, "dt-ahmedyasser-sandbox-dev", "my_agent", "eval_config.yaml"
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


def main():
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

    wrapper._shutdown()
    print("\n👋 Goodbye!")


if __name__ == "__main__":
    main()
