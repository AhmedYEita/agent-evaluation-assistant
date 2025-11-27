"""File reading tools for the assistant agent"""

import shutil
import yaml
from pathlib import Path


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
