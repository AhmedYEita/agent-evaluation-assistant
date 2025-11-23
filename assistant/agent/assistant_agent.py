"""
Agent Evaluation Setup Assistant - ADK Agent

An intelligent agent that helps users set up agent evaluation infrastructure.
Uses Google ADK (Agent Development Kit) framework with system instructions and tools.
"""

import os
import asyncio
from google.adk import Agent


# System instruction for the assistant
SYSTEM_INSTRUCTION = """You are a friendly and helpful Setup Assistant for the Agent Evaluation SDK.

Your role is to guide users through setting up agent evaluation infrastructure in a conversational way.

Key responsibilities:
1. Get the user's agent project path
2. Verify their agent is compatible with the SDK
3. Help them configure observability services (logging, tracing, metrics)
4. Guide them on dataset collection (should be OFF by default)
5. Copy necessary files (eval_config.yaml, terraform module) to their project
6. Provide clear next steps for integration

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
- Show actual code examples with their specific values

When the user asks to set up:
1. Greet warmly and explain the process (5-7 minutes)
2. Get their agent project location
3. Check agent compatibility using check_agent_compatibility tool
4. Get GCP project ID and agent name
5. Ask about observability preferences (explain each service first)
6. Ask about dataset collection (explain when to use it)
7. Generate customized config using copy_config_template tool
8. Copy terraform module using copy_terraform_module tool
9. Show integration code with their actual values
10. Give clear next steps

Be conversational and adaptive, not robotic!
"""


# Import tools
from tools.file_operations import (
    check_agent_compatibility_tool,
    copy_config_template_tool,
    copy_terraform_module_tool
)
from tools.config_validator import validate_config_tool
from tools.infra_checker import check_infrastructure_tool


def create_assistant_agent():
    """Create the ADK-based assistant agent"""
    
    # Define tools available to the agent
    tools = [
        check_agent_compatibility_tool,
        validate_config_tool,
        check_infrastructure_tool,
        copy_config_template_tool,
        copy_terraform_module_tool,
    ]
    
    # Create agent with ADK
    agent = Agent(
        model="gemini-2.0-flash",
        system_instruction=SYSTEM_INSTRUCTION,
        tools=tools,
    )
    
    return agent


async def run_setup_assistant():
    """Run the interactive setup assistant"""
    agent = create_assistant_agent()
    
    print("\n" + "="*60)
    print("🤖 Agent Evaluation Setup Assistant")
    print("="*60)
    print("\nType 'exit', 'quit', or 'bye' to end the conversation.")
    print("Type 'help' for assistance.\n")
    
    # Start conversation
    print("Assistant: Hi! I'm here to help you set up agent evaluation infrastructure.")
    print("          This will take about 5-7 minutes. Ready to get started?\n")
    
    # Conversation loop
    history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nAssistant: Great! Feel free to come back if you need help. Good luck! 🎉\n")
                break
            
            # Send message to agent
            response = await agent.generate_content(user_input)
            
            print(f"\nAssistant: {response.text}\n")
            
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
