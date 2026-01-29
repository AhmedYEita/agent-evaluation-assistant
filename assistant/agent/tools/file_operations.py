"""File reading and checking tools for the assistant agent"""

import os
from pathlib import Path
from typing import Optional


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
            
            rel_root = Path(root).relative_to(path)
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
    Reads the main agent file and follows local imports to check for required patterns
    
    Args:
        agent_file_path: Path to the agent Python file
    
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
    
    if not agent_path.exists():
        return {
            "compatible": False,
            "agent_type": "unknown",
            "has_generate_content": False,
            "has_runner": False,
            "files_checked": [],
            "message": f"File not found: {agent_file_path}"
        }
    
    try:
        # Track all files we've checked
        files_checked = [str(agent_path)]
        
        # Read main agent file
        content = agent_path.read_text()
        
        # Extract and read local imports
        import_contents = {}
        local_imports = _extract_local_imports(content)
        agent_dir = agent_path.parent
        
        for import_info in local_imports:
            import_path = _resolve_import_path(import_info, agent_dir)
            if import_path and import_path.exists():
                try:
                    import_contents[str(import_path)] = import_path.read_text()
                    files_checked.append(str(import_path))
                except Exception:
                    pass  # Skip files we can't read
        
        # Combine all content for checking
        all_content = content + "\n".join(import_contents.values())
        
        # Check for ADK agent patterns (in main file or imports)
        has_adk_imports = 'from google.adk import' in all_content or 'import google.adk' in all_content
        has_runner = 'InMemoryRunner' in all_content or 'runner.run_async' in all_content
        
        # Check for custom agent patterns (in main file or imports)
        has_generate = 'def generate_content' in all_content
        
        files_msg = f" (checked {len(files_checked)} file(s))" if len(files_checked) > 1 else ""
        
        if has_adk_imports and has_runner:
            return {
                "compatible": True,
                "agent_type": "adk",
                "has_generate_content": False,
                "has_runner": True,
                "files_checked": files_checked,
                "message": f"✓ Agent is compatible! Detected ADK agent with InMemoryRunner{files_msg}"
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
                "message": f"Agent needs either:\n- ADK setup (Agent + InMemoryRunner + runner.run_async), OR\n- Custom agent with generate_content(prompt: str) method\n\nChecked: {', '.join([Path(f).name for f in files_checked])}"
            }
    
    except Exception as e:
        return {
            "compatible": False,
            "agent_type": "unknown",
            "has_generate_content": False,
            "has_runner": False,
            "files_checked": [],
            "message": f"Error reading file: {e}"
        }


def _extract_local_imports(content: str) -> list:
    """Extract local import statements from Python code."""
    import re
    local_imports = []
    
    # Pattern 1: from .module import ... or from ..module import ...
    relative_imports = re.findall(r'from\s+(\.+[\w.]*)\s+import', content)
    local_imports.extend(relative_imports)
    
    # Pattern 2: from module import ... (where module doesn't start with known external packages)
    absolute_imports = re.findall(r'from\s+([\w.]+)\s+import', content)
    for imp in absolute_imports:
        # Filter out common external packages AND the AEA repo folder
        if not imp.split('.')[0] in ['os', 'sys', 'pathlib', 'typing', 'datetime', 'json', 'yaml', 
                                       're', 'asyncio', 'google', 'langchain', 'openai', 'anthropic',
                                       'requests', 'http', 'urllib', 'logging', 'argparse', 'functools',
                                       'itertools', 'collections', 'dataclasses', 'enum', 'abc',
                                       'agent_evaluation_sdk', 'agent_evaluation_assistant']:  # Skip AEA imports
            if '.' not in imp or len(imp.split('.')) <= 3:  # Likely local if short path
                local_imports.append(imp)
    
    # Pattern 3: import module (where module is likely local)
    simple_imports = re.findall(r'^import\s+([\w]+)', content, re.MULTILINE)
    for imp in simple_imports:
        if imp not in ['os', 'sys', 'pathlib', 'typing', 'datetime', 'json', 'yaml', 're', 'asyncio',
                       'agent_evaluation_sdk', 'agent_evaluation_assistant']:  # Skip AEA imports
            local_imports.append(imp)
    
    return local_imports


def _resolve_import_path(import_str: str, base_dir: Path) -> Optional[Path]:
    """Resolve an import string to an actual file path."""
    # Handle relative imports (., .., etc.)
    if import_str.startswith('.'):
        parts = import_str.lstrip('.').split('.')
        # For relative imports, start from base_dir
        current = base_dir
        for part in parts:
            if part:
                current = current / part
        
        # Try as .py file first
        if current.with_suffix('.py').exists():
            return current.with_suffix('.py')
        # Try as package (__init__.py)
        if (current / '__init__.py').exists():
            return current / '__init__.py'
    else:
        # Handle absolute imports (relative to base_dir)
        parts = import_str.split('.')
        
        # Skip if trying to import from AEA repo folders
        if parts[0] in ['agent_evaluation_assistant', 'agent_evaluation_sdk']:
            return None
        
        # Try as direct file
        file_path = base_dir / f"{parts[0]}.py"
        if file_path.exists():
            return file_path
        
        # Try as package
        package_path = base_dir / parts[0]
        if package_path.is_dir():
            # Skip if this is the AEA repo folder
            if package_path.name in ['agent_evaluation_assistant', 'agent_evaluation_sdk']:
                return None
                
            if len(parts) > 1:
                # Multi-level import: tools.calculator -> tools/calculator.py
                submodule = package_path / f"{parts[1]}.py"
                if submodule.exists():
                    return submodule
            # Try __init__.py
            init_path = package_path / '__init__.py'
            if init_path.exists():
                return init_path
    
    return None


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
