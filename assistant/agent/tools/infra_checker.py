"""
Simple Infrastructure Checker
"""

from google.cloud import bigquery


def check_infrastructure_tool(project_id: str, agent_name: str):
    """
    Check if GCP infrastructure exists
    
    Returns:
        dict: {"exists": bool, "details": list, "errors": list}
    """
    details = []
    errors = []
    
    try:
        client = bigquery.Client(project=project_id)
        
        # Check dataset
        dataset_id = f"{project_id}.agent_evaluation"
        try:
            client.get_dataset(dataset_id)
            details.append(f"BigQuery dataset: {dataset_id}")
            
            # Check table
            table_id = f"{dataset_id}.{agent_name}_eval_dataset"
            try:
                table = client.get_table(table_id)
                details.append(f"Table: {agent_name}_eval_dataset ({table.num_rows} rows)")
            except Exception:
                errors.append(f"Table {agent_name}_eval_dataset not found")
                
        except Exception:
            errors.append("BigQuery dataset 'agent_evaluation' not found")
    
    except Exception as e:
        errors.append(f"Cannot access BigQuery: {e}")
    
    return {
        "exists": len(errors) == 0,
        "details": details,
        "errors": errors
    }
