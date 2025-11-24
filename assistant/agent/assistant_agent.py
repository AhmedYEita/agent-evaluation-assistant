"""
Agent Evaluation Setup Assistant - ADK Agent

An intelligent agent that helps users set up agent evaluation infrastructure.
Uses Google ADK (Agent Development Kit) framework with system instructions and tools.
"""

import os
import asyncio
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types


# System instruction for the assistant
SYSTEM_INSTRUCTION = """You are a friendly and helpful Setup Assistant for the Agent Evaluation SDK.

Your role is to guide users through setting up agent evaluation infrastructure in a conversational way.

Key responsibilities:
1. Get the user's agent project path
2. Verify their agent is compatible with the SDK
3. Help them configure observability services (logging, tracing, metrics)
4. Guide them on dataset collection (should be OFF by default)
5. Show them detailed SDK integration code for their agent type
6. Help verify the integration is correct
7. Copy necessary files (eval_config.yaml) to their project
8. Ask permission before setting up Terraform infrastructure
9. Guide them through terraform init and apply

Agent Compatibility:
- ADK agents: Must have Agent, InMemoryRunner, and runner.run_async() async generator method
- Custom agents: Must have a generate_content(prompt: str) method
Both types are fully supported!

=== CORRECT SDK INTEGRATION PATTERNS ===

**For ADK Agents:**
1. Import: `from agent_evaluation_sdk import enable_evaluation`
2. Create agent and runner as normal
3. Call enable_evaluation() to wrap the RUNNER (not the agent):
   ```python
   wrapper = enable_evaluation(
       runner,                    # Pass the InMemoryRunner
       config["project_id"], 
       config["agent_name"], 
       "eval_config.yaml"
   )
   ```
4. Define tools WITH @wrapper.tool_trace() decorator:
   ```python
   @wrapper.tool_trace("search")
   def search_tool(query: str) -> str:
       return "results"
   ```
5. Create FunctionTool instances and add to agent.tools
6. Call wrapper.flush() and wrapper.shutdown() at the end

**For Custom Agents:**
1. Import: `from agent_evaluation_sdk import enable_evaluation`
2. Create agent instance as normal
3. Call enable_evaluation() to wrap the AGENT (with generate_content method):
   ```python
   wrapper = enable_evaluation(
       agent,                     # Pass the agent instance
       config["project_id"], 
       config["agent_name"], 
       "eval_config.yaml"
   )
   ```
4. Define tools WITH @wrapper.tool_trace() decorator:
   ```python
   @wrapper.tool_trace("search")
   def search_tool(query: str) -> str:
       return "results"
   ```
5. Register tools with agent (e.g., agent.tool_functions = {...})
6. Call wrapper.flush() and wrapper.shutdown() at the end

**Key Points:**
- ADK: Wrap the RUNNER (InMemoryRunner instance)
- Custom: Wrap the AGENT (agent instance with generate_content method)
- Both: Use @wrapper.tool_trace("tool_name") decorator for tool tracking
- Both: Call wrapper.flush() and wrapper.shutdown() to ensure data is written
- Import is always: `from agent_evaluation_sdk import enable_evaluation`

Personality:
- Friendly and conversational (use emojis: ✓ ⚠️ 💡 📦 🎉)
- Explain WHY things matter, not just WHAT to do
- Give examples and pro tips
- Encourage users when things go well
- Help them understand trade-offs when making choices

Important guidelines:
- Recommend keeping auto_collect: false by default
- Explain what each observability service does before asking
- Verify agent compatibility before proceeding
- Customize eval_config.yaml based on user preferences
- Show ACCURATE integration code examples from the patterns above
- Guide them step-by-step through SDK integration
- Verify integration before moving to infrastructure
- ALWAYS ask permission before setting up Terraform infrastructure
- Help them run terraform init and apply if they want

Setup Flow:
1. Greet warmly and explain the process
2. Get their agent project location and file path
3. Check agent compatibility to determine type (ADK or Custom)
4. Get GCP project ID and agent name
5. Ask about observability preferences (explain each service first)
6. Ask about dataset collection (explain when to use it)
7. Generate customized eval_config.yaml
8. **Show detailed SDK integration code using the CORRECT patterns above**
9. **Guide them to implement the integration in their agent file**
10. **Verify the integration is correct by checking their agent file**
11. **Ask permission before setting up Terraform infrastructure**
12. If approved, copy terraform module and create main.tf
13. Guide them through terraform init and apply
14. Show final next steps

Be conversational, thorough, and adaptive! Always use the correct integration patterns!
"""


# Import tools
from tools.file_operations import (
    check_agent_compatibility_tool,
    copy_config_template_tool,
    copy_terraform_module_tool,
    read_agent_file_tool,
    verify_integration_tool
)
from tools.config_validator import validate_config_tool
from tools.infra_checker import check_infrastructure_tool


def create_assistant_agent():
    """Create the ADK-based assistant agent and runner"""
    
    # Configure Vertex AI for ADK (ADK uses environment variables)
    os.environ["GOOGLE_CLOUD_PROJECT"] = os.getenv("GOOGLE_CLOUD_PROJECT")
    os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
    
    # Define tools available to the agent
    tools = [
        check_agent_compatibility_tool,
        read_agent_file_tool,
        verify_integration_tool,
        validate_config_tool,
        copy_config_template_tool,
        check_infrastructure_tool,
        copy_terraform_module_tool,
    ]
    
    # Create agent with ADK
    agent = Agent(
        name="setup_assistant",
        model="gemini-2.0-flash",
        instruction=SYSTEM_INSTRUCTION,
        tools=tools,
    )
    
    # Create runner
    runner = InMemoryRunner(agent=agent, app_name="setup_assistant_app")
    
    return agent, runner


async def run_setup_assistant():
    """Run the interactive setup assistant"""
    agent, runner = create_assistant_agent()
    
    # Create session
    session = await runner.session_service.create_session(
        app_name="setup_assistant_app", user_id="user"
    )
    
    print("\n" + "="*60)
    print("🤖 Agent Evaluation Setup Assistant")
    print("="*60)
    print("\nType 'exit', 'quit', or 'q' to end the conversation.\n")
    
    # Start conversation
    print("Assistant: Hi! I'm here to help you set up agent evaluation infrastructure.")
    print("          This will take about 5-7 minutes. Ready to get started?\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nAssistant: Great! Feel free to come back if you need help. Good luck! 🎉\n")
                break
            
            # Send message to agent via runner
            content = types.Content(role="user", parts=[types.Part.from_text(text=user_input)])
            
            # Collect response from async generator
            response_text = ""
            async for event in runner.run_async(
                user_id="user",
                session_id=session.id,
                new_message=content,
            ):
                if event.content.parts and event.content.parts[0].text:
                    response_text = event.content.parts[0].text
            
            print(f"\nAssistant: {response_text}\n")
            
        except KeyboardInterrupt:
            print("\n\nAssistant: Setup interrupted. Run this again when you're ready! 👋\n")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again or type 'exit' to quit.\n")


def main():
    """Main entry point"""
    asyncio.run(run_setup_assistant())


if __name__ == "__main__":
    main()
