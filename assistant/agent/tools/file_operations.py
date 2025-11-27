"""File reading tools for the assistant agent"""

import shutil
import yaml
from pathlib import Path
from typing import Optional


def read_file_tool(file_path: str) -> dict:
    """
    Read any file (examples, docs, source code, user's agent)
    
    Args:
        file_path: Path to file to read
    
    Returns:
        {"success": bool, "content": str, "message": str}
    """
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return {"success": False, "content": "", "message": f"File not found: {file_path}"}
        
        content = path.read_text()
        return {"success": True, "content": content, "message": f"Read {path.name} ({len(content)} chars)"}
    except Exception as e:
        return {"success": False, "content": "", "message": f"Error: {e}"}


def check_agent_compatibility_tool(agent_file_path: str) -> dict:
    """
    Check if user's agent is compatible with the SDK
    
    Args:
        agent_file_path: Path to the agent Python file
    
    Returns:
        {
            "compatible": bool,
            "agent_type": str (either "adk" or "custom"),
            "has_generate_content": bool,
            "has_runner": bool,
            "message": str
        }
    """
    agent_path = Path(agent_file_path).expanduser()
    
    if not agent_path.exists():
        return {
            "compatible": False,
            "agent_type": "unknown",
            "has_generate_content": False,
            "has_runner": False,
            "message": f"File not found: {agent_file_path}"
        }
    
    try:
        content = agent_path.read_text()
        
        # Check for ADK agent patterns
        has_adk_imports = 'from google.adk import' in content or 'import google.adk' in content
        has_runner = 'InMemoryRunner' in content or 'runner.run_async' in content
        
        # Check for custom agent patterns
        has_generate = 'def generate_content' in content
        
        if has_adk_imports and has_runner:
            return {
                "compatible": True,
                "agent_type": "adk",
                "has_generate_content": False,
                "has_runner": True,
                "message": "✓ Agent is compatible! Detected ADK agent with InMemoryRunner"
            }
        elif has_generate:
            return {
                "compatible": True,
                "agent_type": "custom",
                "has_generate_content": True,
                "has_runner": False,
                "message": "✓ Agent is compatible! Detected custom agent with generate_content() method"
            }
        else:
            return {
                "compatible": False,
                "agent_type": "unknown",
                "has_generate_content": False,
                "has_runner": False,
                "message": "Agent needs either:\n- ADK setup (Agent + InMemoryRunner + runner.run_async), OR\n- Custom agent with generate_content(prompt: str) method"
            }
    
    except Exception as e:
        return {
            "compatible": False,
            "agent_type": "unknown",
            "has_generate_content": False,
            "has_runner": False,
            "message": f"Error reading file: {e}"
        }


def check_eval_config_exists_tool(agent_directory: str) -> dict:
    """
    Check if eval_config.yaml exists in the agent directory
    
    Args:
        agent_directory: Path to agent project
    
    Returns:
        {
            "exists": bool,
            "path": str or None,
            "message": str
        }
    """
    try:
        dir_path = Path(agent_directory).expanduser()
        if not dir_path.exists():
            return {
                "exists": False,
                "path": None,
                "message": f"Directory not found: {agent_directory}"
            }
        
        config_path = dir_path / "eval_config.yaml"
        exists = config_path.exists()
        
        return {
            "exists": exists,
            "path": str(config_path) if exists else None,
            "message": "✓ Found eval_config.yaml" if exists else ""
        }
    except Exception as e:
        return {
            "exists": False,
            "path": None,
            "message": f"Error: {e}"
        }


def check_terraform_exists_tool(agent_directory: str) -> dict:
    """
    Check if terraform folder exists in the agent directory
    
    Args:
        agent_directory: Path to agent project
    
    Returns:
        {
            "exists": bool,
            "path": str or None,
            "message": str
        }
    """
    try:
        dir_path = Path(agent_directory).expanduser()
        if not dir_path.exists():
            return {
                "exists": False,
                "path": None,
                "message": f"Directory not found: {agent_directory}"
            }
        
        # Check for common terraform folder names
        for tf_dir in ["terraform", "infra", "tf"]:
            tf_path = dir_path / tf_dir
            if tf_path.exists() and tf_path.is_dir():
                return {
                    "exists": True,
                    "path": str(tf_path),
                    "message": f"✓ Found {tf_dir}/ directory"
                }
        
        return {
            "exists": False,
            "path": None,
            "message": ""
        }
    except Exception as e:
        return {
            "exists": False,
            "path": None,
            "message": f"Error: {e}"
        }


def check_sdk_integration_tool(agent_file_path: str) -> dict:
    """
    Check if SDK is integrated in the agent file and validate the integration
    
    Args:
        agent_file_path: Path to agent file
    
    Returns:
        {
            "integrated": bool,
            "has_import": bool,
            "has_enable_evaluation": bool,
            "has_wrapper": bool,
            "has_flush": bool,
            "has_shutdown": bool,
            "has_tool_trace": bool,
            "missing_steps": list,
            "message": str
        }
    """
    try:
        path = Path(agent_file_path).expanduser()
        if not path.exists():
            return {
                "integrated": False,
                "has_import": False,
                "has_enable_evaluation": False,
                "has_wrapper": False,
                "has_flush": False,
                "has_shutdown": False,
                "has_tool_trace": False,
                "missing_steps": ["File not found"],
                "message": f"File not found: {agent_file_path}"
            }
        
        content = path.read_text()
        
        # Check for integration components
        has_import = 'from agent_evaluation_sdk import enable_evaluation' in content or 'import agent_evaluation_sdk' in content
        has_enable_evaluation = 'enable_evaluation(' in content
        has_wrapper = 'wrapper' in content and '= enable_evaluation(' in content
        has_flush = 'wrapper.flush()' in content or 'await wrapper.flush()' in content
        has_shutdown = 'wrapper.shutdown()' in content or 'await wrapper.shutdown()' in content
        has_tool_trace = '@wrapper.tool_trace' in content or 'wrapper.tool_trace(' in content
        
        # Determine what's missing
        missing_steps = []
        if not has_import:
            missing_steps.append("Import enable_evaluation")
        if not has_enable_evaluation:
            missing_steps.append("Call enable_evaluation()")
        if not has_wrapper:
            missing_steps.append("Store wrapper variable")
        if not has_flush:
            missing_steps.append("Add wrapper.flush()")
        if not has_shutdown:
            missing_steps.append("Add wrapper.shutdown()")
        
        integrated = has_import and has_enable_evaluation and has_wrapper
        
        if integrated:
            validation_msg = "✓ SDK integrated in this file"
            if not has_flush or not has_shutdown:
                validation_msg += "\n⚠️ Missing cleanup: " + ", ".join(missing_steps)
        else:
            validation_msg = ""
        
        return {
            "integrated": integrated,
            "has_import": has_import,
            "has_enable_evaluation": has_enable_evaluation,
            "has_wrapper": has_wrapper,
            "has_flush": has_flush,
            "has_shutdown": has_shutdown,
            "has_tool_trace": has_tool_trace,
            "missing_steps": missing_steps,
            "message": validation_msg
        }
    except Exception as e:
        return {
            "integrated": False,
            "has_import": False,
            "has_enable_evaluation": False,
            "has_wrapper": False,
            "has_flush": False,
            "has_shutdown": False,
            "has_tool_trace": False,
            "missing_steps": [],
            "message": f"Error: {e}"
        }


def copy_config_template_tool(
    repo_path: str,
    dest_path: str,
    enable_logging: bool,
    enable_tracing: bool,
    enable_metrics: bool,
    auto_collect: bool,
    enable_evaluation: bool = False
) -> dict:
    """
    Copy and customize eval_config.yaml template
    
    Args:
        repo_path: Path to agent-evaluation-assistant repository
        dest_path: Destination directory for the config file
        enable_logging: Enable Cloud Logging
        enable_tracing: Enable Cloud Trace
        enable_metrics: Enable Cloud Monitoring
        auto_collect: Enable dataset auto-collection
        enable_evaluation: Enable Gen AI Evaluation (adds genai_eval and regression sections)
    
    Returns:
        {
            "success": bool,
            "config_path": str,
            "message": str
        }
    """
    try:
        repo = Path(repo_path).expanduser()
        
        # Try to find the repo root if a subdirectory was provided
        # Look for sdk/ directory going up the path
        check_path = repo
        for _ in range(5):  # Check up to 5 levels up
            if (check_path / "sdk").exists() and (check_path / "terraform").exists():
                repo = check_path
                break
            if check_path.parent == check_path:  # Reached filesystem root
                break
            check_path = check_path.parent
        
        template_path = repo / "sdk/agent_evaluation_sdk/templates/eval_config.template.yaml"
        dest_file = Path(dest_path).expanduser() / "eval_config.yaml"
        
        if not template_path.exists():
            return {
                "success": False,
                "config_path": None,
                "message": f"Template not found at: {template_path}. Please provide the ROOT path of agent-evaluation-assistant repository (should contain sdk/, terraform/, example_agents/ folders)."
            }
        
        # Read template
        with open(template_path) as f:
            config = yaml.safe_load(f)
        
        # Customize based on user preferences
        config['logging']['enabled'] = enable_logging
        config['tracing']['enabled'] = enable_tracing
        config['metrics']['enabled'] = enable_metrics
        config['dataset']['auto_collect'] = auto_collect
        
        # Conditionally include evaluation sections
        if not enable_evaluation:
            # Remove genai_eval and regression sections if not needed
            config.pop('genai_eval', None)
            config.pop('regression', None)
        
        # Write customized config
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        # Build summary
        enabled_services = []
        if enable_logging: enabled_services.append("Logging")
        if enable_tracing: enabled_services.append("Tracing")
        if enable_metrics: enabled_services.append("Metrics")
        
        summary = f"✓ Created eval_config.yaml with: {', '.join(enabled_services)}. Dataset collection: {'ON' if auto_collect else 'OFF'}"
        if enable_evaluation:
            summary += ". Gen AI Evaluation: Enabled"
        else:
            summary += ". Gen AI Evaluation: Disabled (can add later)"
        
        return {
            "success": True,
            "config_path": str(dest_file),
            "message": summary
        }
    
    except Exception as e:
        return {
            "success": False,
            "config_path": None,
            "message": f"Error creating config: {e}"
        }


def copy_terraform_module_tool(
    repo_path: str,
    dest_path: str,
    project_id: str,
    region: str
) -> dict:
    """
    Copy terraform module and create main.tf
    
    Args:
        repo_path: Path to agent-evaluation-assistant repository
        dest_path: Destination project directory
        project_id: GCP project ID
        region: GCP region
    
    Returns:
        {
            "success": bool,
            "terraform_path": str,
            "main_tf_created": bool,
            "message": str
        }
    """
    try:
        repo = Path(repo_path).expanduser()
        
        # Try to find the repo root if a subdirectory was provided
        # Look for terraform/ directory going up the path
        check_path = repo
        for _ in range(5):  # Check up to 5 levels up
            if (check_path / "terraform").exists() and (check_path / "sdk").exists():
                repo = check_path
                break
            if check_path.parent == check_path:  # Reached filesystem root
                break
            check_path = check_path.parent
        
        terraform_src = repo / "terraform"
        terraform_dest = Path(dest_path).expanduser() / "terraform/modules/agent_evaluation"
        main_tf_path = Path(dest_path).expanduser() / "terraform/main.tf"
        
        if not terraform_src.exists():
            return {
                "success": False,
                "terraform_path": None,
                "main_tf_created": False,
                "message": f"Terraform directory not found at: {terraform_src}. Please provide the ROOT path of agent-evaluation-assistant repository."
            }
        
        # Copy terraform module
        shutil.copytree(terraform_src, terraform_dest, dirs_exist_ok=True)
        
        # Create main.tf if it doesn't exist
        main_tf_created = False
        if not main_tf_path.exists():
            main_tf_content = f'''terraform {{
  required_version = ">= 1.0"
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 5.0"
    }}
  }}
}}

provider "google" {{
  project = "{project_id}"
  region  = "{region}"
}}

# Agent Evaluation Infrastructure
module "agent_evaluation" {{
  source = "./modules/agent_evaluation"
  
  project_id = "{project_id}"
  region     = "{region}"
}}
'''
            main_tf_path.parent.mkdir(parents=True, exist_ok=True)
            main_tf_path.write_text(main_tf_content)
            main_tf_created = True
        
        return {
            "success": True,
            "terraform_path": str(terraform_dest),
            "main_tf_created": main_tf_created,
            "message": f"✓ Copied terraform module. {'Created main.tf' if main_tf_created else 'main.tf already exists'}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "terraform_path": None,
            "main_tf_created": False,
            "message": f"Error copying terraform: {e}"
        }


def copy_sdk_folder_tool(
    repo_path: str,
    dest_path: str
) -> dict:
    """
    Copy SDK folder to agent project directory
    
    Args:
        repo_path: Path to agent-evaluation-assistant repository root
        dest_path: Agent project root directory
        
    Returns:
        {
            "success": bool,
            "sdk_path": str,
            "copied": bool,  # True if just copied, False if already exists
            "message": str
        }
    """
    try:
        repo = Path(repo_path).expanduser()
        
        # Try to find the repo root if a subdirectory was provided
        check_path = repo
        for _ in range(5):  # Check up to 5 levels up
            if (check_path / "sdk").exists() and (check_path / "terraform").exists():
                repo = check_path
                break
            if check_path.parent == check_path:  # Reached filesystem root
                break
            check_path = check_path.parent
        
        sdk_src = repo / "sdk" / "agent_evaluation_sdk"
        sdk_dest = Path(dest_path).expanduser() / "agent_evaluation_sdk"
        
        if not sdk_src.exists():
            return {
                "success": False,
                "sdk_path": None,
                "copied": False,
                "message": f"SDK source not found at: {sdk_src}. Please provide the ROOT path of agent-evaluation-assistant repository."
            }
        
        # Check if SDK folder already exists
        copied = False
        if sdk_dest.exists():
            return {
                "success": True,
                "sdk_path": str(sdk_dest),
                "copied": False,
                "message": f"✓ SDK folder already exists at: {sdk_dest}"
            }
        
        # Copy SDK folder
        shutil.copytree(sdk_src, sdk_dest)
        copied = True
        
        return {
            "success": True,
            "sdk_path": str(sdk_dest),
            "copied": True,
            "message": f"✓ Copied SDK folder to: {sdk_dest}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "sdk_path": None,
            "copied": False,
            "message": f"Error copying SDK folder: {e}"
        }


def add_evaluation_config_tool(config_path: str) -> dict:
    """
    Add Gen AI Evaluation and Regression Testing sections to existing eval_config.yaml
    
    Args:
        config_path: Path to existing eval_config.yaml file
    
    Returns:
        {
            "success": bool,
            "message": str
        }
    """
    try:
        config_file = Path(config_path).expanduser()
        
        if not config_file.exists():
            return {
                "success": False,
                "message": f"Config file not found: {config_path}"
            }
        
        # Read existing config
        with open(config_file) as f:
            config = yaml.safe_load(f) or {}
        
        # Check if evaluation sections already exist
        if 'genai_eval' in config or 'regression' in config:
            return {
                "success": False,
                "message": "Evaluation sections (genai_eval/regression) already exist in config file"
            }
        
        # Add evaluation sections
        config['genai_eval'] = {
            'metrics': ['bleu', 'rouge'],
            'model_name': 'gemini-2.5-flash',
            'criteria': ['coherence', 'fluency', 'safety', 'groundedness'],
            'thresholds': {
                'bleu': 0.5,
                'rouge': 0.5,
                'coherence': 0.7,
                'fluency': 0.7,
                'safety': 0.9,
                'groundedness': 0.7
            }
        }
        
        config['regression'] = {
            'test_limit': None,
            'only_reviewed': True,
            'dataset_table': None
        }
        
        # Write updated config
        with open(config_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        return {
            "success": True,
            "message": "✓ Added Gen AI Evaluation and Regression Testing sections to eval_config.yaml"
        }
    
    except Exception as e:
        return {
            "success": False,
            "message": f"Error adding evaluation config: {e}"
        }


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
            script_content = f'''"""
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
from {agent_file_name.replace('.py', '') if agent_file_name else 'YOUR_AGENT_MODULE'} import create_adk_agent

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
        else:  # custom agent
            script_content = f'''"""
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
from {agent_file_name.replace('.py', '') if agent_file_name else 'YOUR_AGENT_MODULE'} import YOUR_AGENT_FUNCTION_OR_CLASS

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
