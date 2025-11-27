"""
Agent Evaluation Setup Assistant - ADK Agent

An intelligent agent that helps users set up agent evaluation infrastructure.
Uses Google ADK (Agent Development Kit) framework with system instructions and tools.
"""

import os
import asyncio
from pathlib import Path
from google.adk import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types

# Import tools
from tools import (
    read_file_tool,
    check_agent_compatibility_tool,
    check_eval_config_exists_tool,
    check_terraform_exists_tool,
    check_sdk_integration_tool,
    copy_config_template_tool,
    copy_terraform_module_tool,
    copy_sdk_folder_tool,
    add_evaluation_config_tool,
    generate_evaluation_script_tool,
    validate_config_tool,
    check_infrastructure_tool,
)


def _load_system_instruction() -> str:
    """Load system instruction from prompt file."""
    prompt_file = Path(__file__).parent / "system_instruction.prompt"
    return prompt_file.read_text()


SYSTEM_INSTRUCTION = _load_system_instruction()


def create_assistant():
    """Create assistant agent"""
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise EnvironmentError(
            "GOOGLE_CLOUD_PROJECT environment variable not set.\n"
            "Set it with: export GOOGLE_CLOUD_PROJECT=your-project-id"
        )
    
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
    
    tools = [
        check_eval_config_exists_tool,
        check_terraform_exists_tool,
        check_agent_compatibility_tool,
        check_sdk_integration_tool,
        copy_config_template_tool,
        copy_terraform_module_tool,
        copy_sdk_folder_tool,
        read_file_tool,
        validate_config_tool,
        check_infrastructure_tool,
        add_evaluation_config_tool,
        generate_evaluation_script_tool,
    ]
    
    agent = Agent(
        name="setup_assistant",
        model="gemini-2.5-flash",
        instruction=SYSTEM_INSTRUCTION,
        tools=tools,
    )
    
    return agent, InMemoryRunner(agent=agent, app_name="setup_assistant")


async def run():
    """Run assistant"""
    agent, runner = create_assistant()
    session = await runner.session_service.create_session(app_name="setup_assistant", user_id="user")
    
    print("\n" + "="*60)
    print("🤖 Agent Evaluation Setup Assistant")
    print("="*60)
    print("\nType 'exit', 'quit', or 'q' to end.\n")
    print("Assistant: Hi! I help integrate the Agent Evaluation SDK into your agents.")
    print("          This includes configuration, code integration, and infrastructure setup.")
    print("          Ready to start?\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\nAssistant: Good luck! 🎉\n")
                break
            
            content = types.Content(role="user", parts=[types.Part.from_text(text=user_input)])
            
            response_text = ""
            async for event in runner.run_async(user_id="user", session_id=session.id, new_message=content):
                if event.content and hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            response_text = part.text
                            break
            
            if response_text:
                print(f"\nAssistant: {response_text}\n")
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Bye! 👋\n")
            break
        except Exception as e:
            print(f"\nError: {e}\nTry again or type 'exit'.\n")


if __name__ == "__main__":
    asyncio.run(run())
