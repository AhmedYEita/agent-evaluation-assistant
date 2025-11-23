"""
Simple Config Validator
"""

import yaml


def validate_config_tool(config_content: str, config_type: str = "eval_config"):
    """
    Validate configuration files
    
    Returns:
        dict: {"valid": bool, "issues": list, "suggestions": list}
    """
    issues = []
    suggestions = []
    
    # Parse YAML
    try:
        config = yaml.safe_load(config_content)
    except yaml.YAMLError as e:
        return {
            "valid": False,
            "issues": [f"Invalid YAML: {e}"],
            "suggestions": []
        }
    
    if config_type == "eval_config":
        # Check required sections
        required = ["logging", "tracing", "metrics", "dataset", "genai_eval", "regression"]
        for section in required:
            if section not in config:
                issues.append(f"Missing section: {section}")
        
        # Check auto_collect warning
        if config.get("dataset", {}).get("auto_collect"):
            suggestions.append("Remember to set auto_collect: false after collecting data")
    
    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "suggestions": suggestions
    }
