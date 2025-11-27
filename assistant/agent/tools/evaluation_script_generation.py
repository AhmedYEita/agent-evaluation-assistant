"""Evaluation script generation tools for running evaluation tests

This module generates run_evaluation.py script templates for both ADK and custom agents.
The generated scripts allow users to run evaluation tests against their agents.
"""

from pathlib import Path
from typing import Optional


def generate_evaluation_script_tool(
    agent_directory: str,
    agent_type: str,
    agent_name: str,
    agent_file_name: Optional[str] = None
) -> dict:
    """
    Generate run_evaluation.py script template based on agent type
    
    Args:
        agent_directory: Path to agent project directory
        agent_type: "adk" or "custom"
        agent_name: Name of the agent
        agent_file_name: Optional agent file name (e.g., "my_agent.py")
    
    Returns:
        {
            "success": bool,
            "script_path": str,
            "message": str
        }
    """
    try:
        dest_dir = Path(agent_directory).expanduser()
        script_path = dest_dir / "run_evaluation.py"
        
        if script_path.exists():
            return {
                "success": False,
                "script_path": str(script_path),
                "message": "run_evaluation.py already exists. Please rename or delete it first."
            }
        
        if agent_type == "adk":
            script_content = _generate_adk_script(agent_name, agent_file_name)
        else:  # custom agent
            script_content = _generate_custom_script(agent_name, agent_file_name)
        
        # Write script
        dest_dir.mkdir(parents=True, exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return {
            "success": True,
            "script_path": str(script_path),
            "message": f"✓ Created run_evaluation.py template for {agent_type} agent. Please customize the TODO sections."
        }
    
    except Exception as e:
        return {
            "success": False,
            "script_path": None,
            "message": f"Error generating evaluation script: {e}"
        }


def _generate_adk_script(agent_name: str, agent_file_name: Optional[str]) -> str:
    """Generate ADK agent evaluation script template."""
    module_name = agent_file_name.replace('.py', '') if agent_file_name else 'YOUR_AGENT_MODULE'
    
    return f'''"""
Evaluation Testing Script for ADK Agent

Runs your ADK agent against the testing dataset and evaluates performance.

CUSTOMIZE THIS SCRIPT:
1. Update the import statement below to match your agent structure
2. Update the agent creation code to match how you initialize your agent
3. Ensure your agent uses InMemoryRunner with run_async() method
"""

import sys
import yaml
import asyncio
from datetime import datetime, timezone
from google.genai import types

# TODO: Update this import to match your agent structure
# Examples:
#   from my_agent import create_adk_agent
#   from agents.core import build_adk_agent
#   from src.agent_factory import create_agent
from {module_name} import create_adk_agent

# Import evaluation SDK
from agent_evaluation_sdk import RegressionTester, GenAIEvaluator


async def main():
    """Run evaluation test on the ADK agent."""

    print("🧪 Loading configuration and ADK agent...")
    print()

    # TODO: Update config file paths if your config files have different names or locations
    # Examples:
    #   config_path = "config/agent_config.yaml"
    #   config_path = "settings/my_config.yaml"
    #   config_path = Path(__file__).parent / "config.yaml"
    with open("agent_config.yaml") as f:
        agent_config = yaml.safe_load(f)
    
    with open("eval_config.yaml") as f:
        eval_config = yaml.safe_load(f)

    # TODO: Customize this to match your agent creation pattern
    # Your function should return: (agent, runner, config, wrapper)
    # Examples:
    #   agent, runner, config, wrapper = create_adk_agent()
    #   agent, runner, config, wrapper = build_adk_agent(config_path="config.yaml")
    #   agent, runner, config, wrapper = initialize_agent(agent_config)
    agent, runner, config, wrapper = create_adk_agent()

    # TODO: Update these print statements if your config structure is different
    # The config dict might have different keys, or project_id might be accessed differently
    # Examples:
    #   print(f"   Project: {{config.get('gcp_project')}}")
    #   print(f"   Project: {{agent_config['project_id']}}")
    print(f"   Project: {{config['project_id']}}")
    print(f"   Agent: {agent_name}")
    print()

    # Run evaluation test
    tester = RegressionTester(
        project_id=config['project_id'],
        agent_name="{agent_name}"
    )

    test_run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

    print(f"🔄 Running evaluation test: test_{{test_run_timestamp}}")
    print()

    # Fetch test cases
    test_cases = tester.fetch_test_cases(
        only_reviewed=eval_config.get('regression', {{}}).get('only_reviewed', True),
        limit=eval_config.get('regression', {{}}).get('test_limit')
    )
    
    if not test_cases:
        print("❌ No test cases found. Run the agent with --test to collect data first.")
        wrapper.flush()
        wrapper.shutdown()
        sys.exit(1)
    
    print(f"📋 Found {{len(test_cases)}} test cases")
    print()
    
    # TODO: Update app_name to match the app_name used when creating InMemoryRunner
    # The app_name MUST match what was used in: InMemoryRunner(agent=agent, app_name="...")
    # Check your agent creation code to find the correct app_name value
    # Common values: "adk_agent_app", "your_app_name", or from config
    app_name = config.get('app_name', 'adk_agent_app')  # Update this to match your runner's app_name
    
    # Run agent on test cases
    print("🤖 Running agent on test cases...")
    
    test_run_id = f"test_{{test_run_timestamp}}"
    test_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        instruction = test_case["instruction"]
        reference = test_case.get("reference", "")
        
        print(f"   [{{i}}/{{len(test_cases)}}] Testing...")
        
        try:
            # TODO: Update user_id if you need a different identifier for evaluation runs
            # This is used for session creation and run_async calls
            user_id = "eval_user"  # Change if needed
            
            # Create a fresh session for each test case to avoid session expiration issues
            session = await runner.session_service.create_session(
                app_name=app_name, user_id=user_id
            )
            
            # TODO: Customize content creation if your agent expects different message format
            # Some agents might need different Content structure or additional metadata
            content = types.Content(role="user", parts=[types.Part.from_text(text=instruction)])
            response_text = ""
            
            # TODO: Customize response extraction if your agent returns different event structure
            # Some agents might return responses in different format or multiple parts
            # Examples:
            #   - Check for event.content.parts[0].function_call instead of text
            #   - Concatenate multiple text parts: response_text += part.text
            #   - Handle different event types or structures
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=content,
            ):
                if event.content.parts and event.content.parts[0].text:
                    response_text = event.content.parts[0].text
            
            # TODO: Customize empty response handling if needed
            # Some agents might return empty responses intentionally or use different indicators
            if not response_text or response_text.strip() == "":
                response_text = "[EMPTY RESPONSE]"
            
            results.append({{
                "test_run_id": test_run_id,
                "test_timestamp": test_timestamp,
                "instruction": instruction,
                "reference": reference,
                "response": response_text,
                "context": test_case.get("context"),
                "error": None,
            }})
        except Exception as e:
            print(f"   ❌ Error: {{e}}")
            results.append({{
                "test_run_id": test_run_id,
                "test_timestamp": test_timestamp,
                "instruction": instruction,
                "reference": reference,
                "response": f"ERROR: {{str(e)}}",
                "context": test_case.get("context"),
                "error": str(e),
            }})
    
    print(f"✅ Completed {{len(results)}} test runs")
    
    # Save using RegressionTester methods (uses new table naming)
    response_table, metrics_table = tester.save_results(results, test_run_id)
    
    # Evaluate
    print("📈 Evaluating responses...")
    evaluator = GenAIEvaluator(project_id=config["project_id"])
    eval_results = evaluator._evaluate(
        dataset=results,
        metrics=eval_config.get('genai_eval', {{}}).get('metrics', ['bleu', 'rouge']),
        criteria=eval_config.get('genai_eval', {{}}).get('criteria', []),
        thresholds=eval_config.get('genai_eval', {{}}).get('thresholds', {{}}),
    )
    
    # Save metrics
    tester.save_metrics(test_run_id, eval_results, metrics_table)
    
    # Cleanup
    wrapper.flush()
    wrapper.shutdown()
    
    print("\\n✅ Evaluation test complete!")
    print()
    print("📊 Results saved to BigQuery:")
    print(f"   - Responses: {{response_table}}")
    print(f"   - Metrics: {{metrics_table}}")
    print()
    print("🔍 View results in BigQuery Console:")
    print(f"   https://console.cloud.google.com/bigquery?project={{config['project_id']}}")
    print("   → Dataset: agent_evaluation")


if __name__ == "__main__":
    asyncio.run(main())
'''


def _generate_custom_script(agent_name: str, agent_file_name: Optional[str]) -> str:
    """Generate custom agent evaluation script template."""
    module_name = agent_file_name.replace('.py', '') if agent_file_name else 'YOUR_AGENT_MODULE'
    
    return f'''"""
Evaluation Testing Script

Runs your agent against the testing dataset and evaluates performance.

CUSTOMIZE THIS SCRIPT:
1. Update the import statement below to match your agent structure
2. Update the get_agent() function to match how you initialize your agent
3. Ensure your agent has a generate_content(prompt: str) method
"""

import sys
import yaml
from datetime import datetime

# TODO: Update this import to match your agent structure
# Examples:
#   from my_agent import create_agent
#   from agents.core import MyAgent
#   from src.agent_factory import build_agent
#   from agent import AgentClass
from {module_name} import YOUR_AGENT_FUNCTION_OR_CLASS

# Import evaluation SDK
from agent_evaluation_sdk import RegressionTester


def get_agent():
    """
    TODO: Customize this function to create your agent instance.
    
    Your agent must have a generate_content(prompt: str) method.
    
    Examples:
    
    # If you have a factory function:
    agent = create_agent(config_path="config.yaml")
    return agent
    
    # If you have a class:
    agent = MyAgent(project_id="...", model="...")
    return agent
    
    # If you need to load config first:
    # TODO: Update config file path if different
    with open("agent_config.yaml") as f:
        config = yaml.safe_load(f)
    agent = build_agent(config)
    return agent
    
    # If your agent needs initialization:
    agent = initialize_agent()
    agent.setup()
    return agent
    """
    # REPLACE THIS with your agent creation code
    agent = YOUR_AGENT_FUNCTION_OR_CLASS()
    return agent


def main():
    """Run evaluation test on the agent."""

    print("🧪 Loading configuration and agent...")
    print()

    # TODO: Update config file paths if your config files have different names or locations
    # Examples:
    #   config_path = "config/agent_config.yaml"
    #   config_path = "settings/my_config.yaml"
    #   config_path = Path(__file__).parent / "config.yaml"
    with open("agent_config.yaml") as f:
        agent_config = yaml.safe_load(f)
    
    with open("eval_config.yaml") as f:
        eval_config = yaml.safe_load(f)

    # Create your agent
    print("🤖 Initializing agent...")
    agent = get_agent()
    
    # Wrap with evaluation SDK (if not already wrapped)
    # TODO: If you already wrapped your agent during creation, skip this entire block
    # TODO: Update project_id and agent_name access if your config structure is different
    # Examples:
    #   project_id = agent_config.get('gcp_project_id')
    #   agent_name = agent_config.get('name')
    from agent_evaluation_sdk import enable_evaluation
    wrapper = enable_evaluation(
        agent,
        agent_config['project_id'],
        agent_config['agent_name'],
        "eval_config.yaml"  # TODO: Update if eval_config.yaml is in a different location
    )

    # Run evaluation test
    tester = RegressionTester(
        project_id=agent_config['project_id'],
        agent_name="{agent_name}"
    )

    test_run_timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    print(f"🔄 Running evaluation test: test_{{test_run_timestamp}}")
    print()

    results = tester.run_full_test(
        agent=agent,
        test_run_name=f"test_{{test_run_timestamp}}",
        only_reviewed=eval_config.get('regression', {{}}).get('only_reviewed', True),
        limit=eval_config.get('regression', {{}}).get('test_limit'),
        metrics=eval_config.get('genai_eval', {{}}).get('metrics', ['bleu', 'rouge']),
        criteria=eval_config.get('genai_eval', {{}}).get('criteria', []),
        thresholds=eval_config.get('genai_eval', {{}}).get('thresholds', {{}}),
    )

    if "error" not in results:
        print("\\n✅ Evaluation test complete!")
        print()
        print("📊 Results saved to BigQuery:")
        print(f"   - Responses: {{results['response_table']}}")
        print(f"   - Metrics: {{results['metrics_table']}}")
        print()
        print("🔍 View results in BigQuery Console:")
        print(
            f"   https://console.cloud.google.com/bigquery?project={{agent_config['project_id']}}"
        )
        print("   → Dataset: agent_evaluation")
    else:
        print(f"\\n❌ Error: {{results['error']}}")
        sys.exit(1)
    
    # Cleanup
    wrapper.shutdown()


if __name__ == "__main__":
    main()
'''

