"""
File operation tools for the assistant agent
"""

import shutil
from pathlib import Path


def check_repo_exists_tool(repo_path: str = None) -> dict:
    """
    Check if agent-evaluation-assistant repository exists
    
    Args:
        repo_path: Optional path to check, otherwise searches from current location
    
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
            "has_generate_content": bool,
            "is_async": bool,
            "message": str
        }
    """
    agent_path = Path(agent_file_path).expanduser()
    
    if not agent_path.exists():
        return {
            "compatible": False,
            "has_generate_content": False,
            "is_async": False,
            "message": f"File not found: {agent_file_path}"
        }
    
    try:
        content = agent_path.read_text()
        
        has_generate = 'def generate_content' in content
        is_async = 'async def generate_content' in content
        
        if has_generate or is_async:
            agent_type = "async (ADK)" if is_async else "sync (custom)"
            return {
                "compatible": True,
                "has_generate_content": True,
                "is_async": is_async,
                "message": f"✓ Agent is compatible! Detected {agent_type} generate_content() method"
            }
        else:
            return {
                "compatible": False,
                "has_generate_content": False,
                "is_async": False,
                "message": "Agent needs a generate_content(prompt: str) method to work with SDK"
            }
    
    except Exception as e:
        return {
            "compatible": False,
            "has_generate_content": False,
            "is_async": False,
            "message": f"Error reading file: {e}"
        }


def copy_config_template_tool(
    repo_path: str,
    dest_path: str,
    enable_logging: bool = True,
    enable_tracing: bool = True,
    enable_metrics: bool = True,
    auto_collect: bool = False
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
    region: str = "us-central1"
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


