"""Terraform and SDK folder operations for the assistant agent"""

import shutil
from pathlib import Path


def _find_repo_root(repo_path: Path) -> Path:
    """Find the repository root by looking for sdk/ and terraform/ directories."""
    check_path = repo_path.expanduser()
    for _ in range(5):  # Check up to 5 levels up
        if (check_path / "terraform").exists() and (check_path / "sdk").exists():
            return check_path
        if check_path.parent == check_path:  # Reached filesystem root
            break
        check_path = check_path.parent
    return repo_path.expanduser()


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
        repo = _find_repo_root(Path(repo_path))
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


def copy_sdk_folder_tool(repo_path: str, dest_path: str) -> dict:
    """
    Copy SDK folder to agent project directory
    
    Args:
        repo_path: Path to agent-evaluation-assistant repository root
        dest_path: Agent project root directory
        
    Returns:
        {
            "success": bool,
            "sdk_path": str,
            "copied": bool,
            "message": str
        }
    """
    try:
        repo = _find_repo_root(Path(repo_path))
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
        if sdk_dest.exists():
            return {
                "success": True,
                "sdk_path": str(sdk_dest),
                "copied": False,
                "message": f"✓ SDK folder already exists at: {sdk_dest}"
            }
        
        # Copy SDK folder
        shutil.copytree(sdk_src, sdk_dest)
        
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

