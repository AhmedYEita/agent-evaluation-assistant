"""
ADK Agent with Custom Configuration

This example shows how to use a custom configuration file for more control
over evaluation behavior.
"""

import os
from google.genai.adk import Agent
from agent_evaluation_sdk import enable_evaluation


def main():
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        print("❌ Please set GCP_PROJECT_ID environment variable")
        return
    
    print("🚀 Creating ADK Agent with Custom Evaluation Config...")
    print()
    
    # Create agent
    agent = Agent(
        model="gemini-2.0-flash-exp",
        system_instruction="You are a customer support agent for a tech company.",
    )
    
    # Enable evaluation with custom config
    enable_evaluation(
        agent=agent,
        project_id=project_id,
        agent_name="customer-support-agent",
        config_path="eval_config.yaml",  # Use custom config
    )
    
    print()
    print("Customer Support Agent Ready!")
    print()
    
    # Example interactions
    test_queries = [
        "How do I reset my password?",
        "What are your business hours?",
        "I'm having trouble logging in",
        "Can you help me with billing?",
    ]
    
    for query in test_queries:
        print(f"User: {query}")
        response = agent.generate_content(query)
        print(f"Agent: {response.text}")
        print()


if __name__ == "__main__":
    main()

