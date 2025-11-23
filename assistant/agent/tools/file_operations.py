"""
File operation tools for the assistant agent
"""

import shutil
from pathlib import Path


def check_repo_exists_tool(repo_path: str) -> dict:
    """
    Check if agent-evaluation-assistant repository exists
    
    Args:
        repo_path: Path to check (use empty string to search from current location)
    
    Returns:
        {
            "exists": bool,
            "path": str or None,
            "message": str
        }
    """
    # Try to find repo
    if repo_path:
        check_path = Path(repo_path)
    else:
        # Search from typical locations
        check_path = Path.cwd()
    
    # Look for repo markers
    for _ in range(5):
        if (check_path / "sdk").exists() and (check_path / "terraform").exists():
            return {
                "exists": True,
                "path": str(check_path),
                "message": f"Repository found at: {check_path}"
            }
        check_path = check_path.parent
    
    return {
        "exists": False,
        "path": None,
        "message": "Repository not found. User needs to clone it."
    }


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


def copy_config_template_tool(
    repo_path: str,
    dest_path: str,
    enable_logging: bool,
    enable_tracing: bool,
    enable_metrics: bool,
    auto_collect: bool
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
    
    Returns:
        {
            "success": bool,
            "config_path": str,
            "message": str
        }
    """
    try:
        import yaml
        
        template_path = Path(repo_path) / "sdk/agent_evaluation_sdk/templates/eval_config.template.yaml"
        dest_file = Path(dest_path) / "eval_config.yaml"
        
        if not template_path.exists():
            return {
                "success": False,
                "config_path": None,
                "message": f"Template not found at: {template_path}"
            }
        
        # Read template
        with open(template_path) as f:
            config = yaml.safe_load(f)
        
        # Customize based on user preferences
        config['logging']['enabled'] = enable_logging
        config['tracing']['enabled'] = enable_tracing
        config['metrics']['enabled'] = enable_metrics
        config['dataset']['auto_collect'] = auto_collect
        
        # Write customized config
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        # Build summary
        enabled_services = []
        if enable_logging: enabled_services.append("Logging")
        if enable_tracing: enabled_services.append("Tracing")
        if enable_metrics: enabled_services.append("Metrics")
        
        return {
            "success": True,
            "config_path": str(dest_file),
            "message": f"✓ Created eval_config.yaml with: {', '.join(enabled_services)}. Dataset collection: {'ON' if auto_collect else 'OFF'}"
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
    agent_name: str,
    region: str
) -> dict:
    """
    Copy terraform module and create main.tf
    
    Args:
        repo_path: Path to agent-evaluation-assistant repository
        dest_path: Destination project directory
        project_id: GCP project ID
        agent_name: Agent name
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
        terraform_src = Path(repo_path) / "terraform"
        terraform_dest = Path(dest_path) / "terraform/modules/agent_evaluation"
        main_tf_path = Path(dest_path) / "terraform/main.tf"
        
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
  agent_name = "{agent_name}"
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


def read_agent_file_tool(agent_file_path: str) -> dict:
    """
    Read the contents of an agent file to verify integration
    
    Args:
        agent_file_path: Path to the agent Python file
    
    Returns:
        {
            "success": bool,
            "content": str,
            "message": str
        }
    """
    try:
        agent_path = Path(agent_file_path).expanduser()
        
        if not agent_path.exists():
            return {
                "success": False,
                "content": "",
                "message": f"File not found: {agent_file_path}"
            }
        
        content = agent_path.read_text()
        
        return {
            "success": True,
            "content": content,
            "message": f"✓ Successfully read {agent_path.name}"
        }
    
    except Exception as e:
        return {
            "success": False,
            "content": "",
            "message": f"Error reading file: {e}"
        }


def verify_integration_tool(agent_file_path: str, agent_type: str) -> dict:
    """
    Verify that SDK integration is correctly implemented
    
    Args:
        agent_file_path: Path to the agent Python file
        agent_type: Type of agent ("adk" or "custom")
    
    Returns:
        {
            "integrated": bool,
            "has_import": bool,
            "has_enable_evaluation": bool,
            "has_wrapper": bool,
            "has_tool_trace": bool,
            "missing_steps": list,
            "message": str
        }
    """
    try:
        agent_path = Path(agent_file_path).expanduser()
        
        if not agent_path.exists():
            return {
                "integrated": False,
                "has_import": False,
                "has_enable_evaluation": False,
                "has_wrapper": False,
                "has_tool_trace": False,
                "missing_steps": ["File not found"],
                "message": f"File not found: {agent_file_path}"
            }
        
        content = agent_path.read_text()
        
        # Check for required integration components
        has_import = 'from agent_evaluation_sdk import enable_evaluation' in content
        has_enable_evaluation = 'enable_evaluation(' in content
        has_wrapper = 'wrapper' in content
        has_tool_trace = '@wrapper.tool_trace' in content or 'wrapper.tool_trace' in content
        
        missing_steps = []
        if not has_import:
            missing_steps.append("Import enable_evaluation from agent_evaluation_sdk")
        if not has_enable_evaluation:
            missing_steps.append("Call enable_evaluation() to wrap the agent/runner")
        if not has_wrapper:
            missing_steps.append("Store the wrapper returned by enable_evaluation()")
        
        integrated = has_import and has_enable_evaluation and has_wrapper
        
        if integrated:
            message = "✓ SDK integration looks good!"
            if not has_tool_trace:
                message += " Note: No tool tracing detected - add @wrapper.tool_trace decorators to track tool calls."
        else:
            message = f"Integration incomplete. Missing: {', '.join(missing_steps)}"
        
        return {
            "integrated": integrated,
            "has_import": has_import,
            "has_enable_evaluation": has_enable_evaluation,
            "has_wrapper": has_wrapper,
            "has_tool_trace": has_tool_trace,
            "missing_steps": missing_steps,
            "message": message
        }
    
    except Exception as e:
        return {
            "integrated": False,
            "has_import": False,
            "has_enable_evaluation": False,
            "has_wrapper": False,
            "has_tool_trace": False,
            "missing_steps": [],
            "message": f"Error verifying integration: {e}"
        }


