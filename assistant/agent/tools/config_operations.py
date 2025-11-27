"""Configuration management tools for the assistant agent"""

import yaml
from pathlib import Path


def _find_repo_root(repo_path: Path) -> Path:
    """Find the repository root by looking for sdk/ and terraform/ directories."""
    check_path = repo_path.expanduser()
    for _ in range(5):  # Check up to 5 levels up
        if (check_path / "sdk").exists() and (check_path / "terraform").exists():
            return check_path
        if check_path.parent == check_path:  # Reached filesystem root
            break
        check_path = check_path.parent
    return repo_path.expanduser()


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
        repo = _find_repo_root(Path(repo_path))
        template_path = repo / "sdk/agent_evaluation_sdk/templates/eval_config.template.yaml"
        dest_file = Path(dest_path).expanduser() / "eval_config.yaml"
        
        if not template_path.exists():
            return {
                "success": False,
                "config_path": None,
                "message": f"Template not found at: {template_path}. Please provide the ROOT path of agent-evaluation-assistant repository."
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
            config.pop('genai_eval', None)
            config.pop('regression', None)
        
        # Write customized config
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        with open(dest_file, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        # Build summary
        enabled_services = []
        if enable_logging:
            enabled_services.append("Logging")
        if enable_tracing:
            enabled_services.append("Tracing")
        if enable_metrics:
            enabled_services.append("Metrics")
        
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

