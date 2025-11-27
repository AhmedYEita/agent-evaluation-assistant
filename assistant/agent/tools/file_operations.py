"""File reading and checking tools for the assistant agent"""

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
