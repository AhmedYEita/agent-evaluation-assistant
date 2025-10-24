"""
Simple ADK Agent with Evaluation Integration

This example demonstrates how easy it is to add comprehensive evaluation
to an ADK agent with just a few lines of code.
"""

import os
from google.genai import types
from google.genai.adk import Agent

# Import the evaluation SDK - that's it!
from agent_evaluation_sdk import enable_evaluation


def main():
    # Get project ID from environment
    project_id = os.environ.get("GCP_PROJECT_ID")
    if not project_id:
        print("❌ Please set GCP_PROJECT_ID environment variable")
        print("   export GCP_PROJECT_ID='your-project-id'")
        return
    
    print("🚀 Creating ADK Agent with Evaluation...")
    print()
    
    # Step 1: Create your agent normally
    agent = Agent(
        model="gemini-2.0-flash-exp",
        system_instruction="""You are a helpful AI assistant that provides 
        clear, concise answers to user questions. Be friendly and informative.""",
    )
    
    # Step 2: Enable evaluation (this is the only addition!)
    enable_evaluation(
        agent=agent,
        project_id=project_id,
        agent_name="simple-adk-agent",
    )
    
    print()
    print("=" * 70)
    print("Agent is ready! Try asking some questions.")
    print("Type 'quit' to exit.")
    print("=" * 70)
    print()
    
    # Step 3: Use your agent normally - evaluation happens automatically!
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Generate response
            print("Agent: ", end="", flush=True)
            response = agent.generate_content(user_input)
            
            # Print response
            if hasattr(response, 'text'):
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
    print(f"Logs:       https://console.cloud.google.com/logs?project={project_id}")
    print(f"Traces:     https://console.cloud.google.com/traces?project={project_id}")
    print(f"Dashboards: https://console.cloud.google.com/monitoring/dashboards?project={project_id}")
    print()
    print("Export dataset:")
    print(f"  agent-eval export-dataset --project-id {project_id} \\")
    print(f"    --agent-name simple-adk-agent --output dataset.json")
    print("=" * 70)


if __name__ == "__main__":
    main()

