"""File reading and checking tools for the assistant agent"""

import os
from pathlib import Path


def list_directory_tool(directory_path: str, max_depth: int = 2) -> dict:
    """
    List contents of a directory to understand project structure
    
    Args:
        directory_path: Path to directory to explore
        max_depth: Maximum depth to recurse (default 2)
    
    Returns:
        {
            "success": bool,
            "structure": list of str (file/folder paths),
            "python_files": list of str (paths to .py files),
            "config_files": list of str (paths to .yaml, .json, .toml, .txt),
            "message": str
        }
    """
    try:
        path = Path(directory_path).expanduser()
        if not path.exists():
            return {
                "success": False,
                "structure": [],
                "python_files": [],
                "config_files": [],
                "message": f"Directory not found: {directory_path}"
            }
        
        if not path.is_dir():
            return {
                "success": False,
                "structure": [],
                "python_files": [],
                "config_files": [],
                "message": f"Path is not a directory: {directory_path}"
            }
        
        structure = []
        python_files = []
        config_files = []
        
        # Walk directory up to max_depth
        for root, dirs, files in os.walk(path):
            # Calculate current depth
            depth = str(root).count(os.sep) - str(path).count(os.sep)
            if depth > max_depth:
                dirs[:] = []  # Don't recurse deeper
                continue
            
            # Filter out common ignore patterns
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.venv', 'env']]
            
            indent = "  " * depth
            
            for dir_name in sorted(dirs):
                structure.append(f"{indent}{dir_name}/")
            
            for file_name in sorted(files):
                if file_name.startswith('.'):
                    continue
                    
                structure.append(f"{indent}{file_name}")
                file_path = Path(root) / file_name
                rel_path = str(file_path.relative_to(path))
                
                if file_name.endswith('.py'):
                    python_files.append(rel_path)
                elif file_name.endswith(('.yaml', '.yml', '.json', '.toml', '.txt', '.md')):
                    config_files.append(rel_path)
        
        message = f"Found {len(python_files)} Python files, {len(config_files)} config files"
        
        return {
            "success": True,
            "structure": structure[:100],  # Limit to first 100 entries
            "python_files": python_files,
            "config_files": config_files,
            "message": message
        }
    
    except Exception as e:
        return {
            "success": False,
            "structure": [],
            "python_files": [],
            "config_files": [],
            "message": f"Error: {e}"
        }


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
    Discovers and reads ALL Python files in the agent directory to check for required patterns
    
    Args:
        agent_file_path: Path to the agent Python file (can be absolute or relative)
    
    Returns:
        {
            "compatible": bool,
            "agent_type": str (either "adk" or "custom"),
            "has_generate_content": bool,
            "has_runner": bool,
            "files_checked": list of str,
            "message": str
        }
    """
    agent_path = Path(agent_file_path).expanduser()
    
    # If path is relative, try to resolve it from current working directory
    if not agent_path.is_absolute():
        agent_path = Path.cwd() / agent_path
    
    if not agent_path.exists():
        return {
            "compatible": False,
            "agent_type": "unknown",
            "has_generate_content": False,
            "has_runner": False,
            "files_checked": [],
            "message": f"File not found: {agent_file_path}\nResolved to: {agent_path}\nPlease provide the full path or ensure you're in the correct directory."
        }
    
    try:
        # Get the agent's project directory
        agent_dir = agent_path.parent
        
        # Find ALL Python files in the agent directory (recursively, max depth 4)
        all_py_files = []
        for depth in range(5):  # Search up to 4 levels deep
            if depth == 0:
                pattern = "*.py"
            else:
                pattern = "*/" * depth + "*.py"
            
            for py_file in agent_dir.glob(pattern):
                # Skip files in common ignore folders
                if any(part in py_file.parts for part in ['__pycache__', '.git', 'venv', '.venv', 'env', 
                                                           'node_modules', 'agent-evaluation-assistant',
                                                           'agent_evaluation_assistant', 'agent_evaluation_sdk']):
                    continue
                all_py_files.append(py_file)
        
        # Read all Python files
        files_checked = []
        all_content = []
        
        for py_file in all_py_files[:50]:  # Limit to first 50 files for performance
            try:
                content = py_file.read_text(errors='ignore')
                all_content.append(content)
                files_checked.append(str(py_file))
            except Exception:
                pass  # Skip files we can't read
        
        # Combine all content for checking
        combined_content = "\n".join(all_content)
        
        # Check for ADK agent patterns (FLEXIBLE matching)
        has_adk_imports = (
            'from google.adk import' in combined_content or 
            'import google.adk' in combined_content or
            'from google.adk.' in combined_content
        )
        has_agent_class = 'Agent(' in combined_content or 'Agent =' in combined_content
        has_runner = (
            'InMemoryRunner' in combined_content or 
            '.run_async(' in combined_content or
            'runner.run_async' in combined_content or
            'runner = ' in combined_content
        )
        
        # Check for custom agent patterns (FLEXIBLE matching)
        has_generate = (
            'def generate_content' in combined_content or
            'async def generate_content' in combined_content
        )
        
        files_msg = f" (scanned {len(files_checked)} Python files in project)"
        
        # More lenient ADK detection
        if has_adk_imports and (has_runner or has_agent_class):
            return {
                "compatible": True,
                "agent_type": "adk",
                "has_generate_content": False,
                "has_runner": True,
                "files_checked": files_checked,
                "message": f"✓ Agent is compatible! Detected ADK agent{files_msg}"
            }
        elif has_generate:
            return {
                "compatible": True,
                "agent_type": "custom",
                "has_generate_content": True,
                "has_runner": False,
                "files_checked": files_checked,
                "message": f"✓ Agent is compatible! Detected custom agent with generate_content() method{files_msg}"
            }
        else:
            return {
                "compatible": False,
                "agent_type": "unknown",
                "has_generate_content": False,
                "has_runner": False,
                "files_checked": files_checked,
                "message": f"Agent needs either:\n- ADK setup (Agent + InMemoryRunner + runner.run_async), OR\n- Custom agent with generate_content(prompt: str) method\n\nScanned {len(files_checked)} Python files in project directory"
            }
    
    except Exception as e:
        return {
            "compatible": False,
            "agent_type": "unknown",
            "has_generate_content": False,
            "has_runner": False,
            "files_checked": [],
            "message": f"Error scanning files: {e}"
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
        for tf_dir in ["terraform", "tf", "infrastructure", "infra"]:
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
