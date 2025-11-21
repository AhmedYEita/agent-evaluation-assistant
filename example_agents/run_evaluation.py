"""
Evaluation Testing Script

Runs the agent against the testing dataset and evaluates performance.
"""

import argparse
import asyncio
import sys
import yaml
from datetime import datetime, timezone

# Import evaluation SDK
from agent_evaluation_sdk import RegressionTester, EvaluationConfig
from pathlib import Path


def load_agent_config():
    """Load agent-specific configuration."""
    with open("agent_config.yaml") as f:
        return yaml.safe_load(f)


def main():
    """Run evaluation test on the agent."""
    parser = argparse.ArgumentParser(
        description="Run evaluation on agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--agent",
        choices=["custom", "adk"],
        default="custom",
        help="Which agent to evaluate (default: custom)",
    )
    
    args = parser.parse_args()

    print("🧪 Loading configuration and agent...")
    print()

    # Load configs
    eval_config = EvaluationConfig.from_yaml(Path("eval_config.yaml"))
    agent_config = load_agent_config()
    
    # Import and create agent based on selection
    if args.agent == "custom":
        from custom_agent import create_agent
        agent, wrapper = create_agent()
        print("   Using: Custom Agent")
        print(f"   Project: {agent_config.get('project_id', 'NOT_FOUND')}")
        print(f"   Agent: {agent_config.get('agent_name', 'NOT_FOUND')}")
    else:
        # For ADK agent, we need to run async
        print("   Using: ADK Agent")
        asyncio.run(run_adk_evaluation(agent_config))
        return
    print()

    # Run evaluation test
    tester = RegressionTester(
        project_id=agent_config['project_id'], 
        agent_name=agent_config['agent_name']
    )

    test_run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

    print(f"🔄 Running evaluation test: test_{test_run_timestamp}")
    print()

    results = tester.run_full_test(
        agent=agent,
        test_run_name=f"test_{test_run_timestamp}",
        only_reviewed=eval_config.regression.only_reviewed,
        limit=eval_config.regression.test_limit,
        dataset_table=eval_config.regression.dataset_table,
        metrics=eval_config.genai_eval.metrics,
        criteria=eval_config.genai_eval.criteria,
        thresholds=eval_config.genai_eval.thresholds,
    )

    # Cleanup
    wrapper.flush()
    wrapper.shutdown()

    if "error" not in results:
        print("\n✅ Evaluation test complete!")
        print()
        print("📊 Results saved to BigQuery:")
        print(f"   - Responses: {agent_config['agent_name']}_eval_{test_run_timestamp}")
        print(f"   - Metrics: {agent_config['agent_name']}_eval_{test_run_timestamp}_metrics")
        print()
        print("🔍 View results in BigQuery Console:")
        print(
            f"   https://console.cloud.google.com/bigquery?project={agent_config['project_id']}"
        )
        print("   → Dataset: agent_evaluation")
    else:
        print(f"\n❌ Error: {results['error']}")
        sys.exit(1)


async def run_adk_evaluation(agent_config):
    """Run evaluation for ADK agent (async)."""
    from adk_agent import create_adk_agent
    from google.genai import types
    
    # Load eval config
    eval_config = EvaluationConfig.from_yaml(Path("eval_config.yaml"))
    
    agent, runner, wrapper, loaded_agent_config = create_adk_agent()
    
    print(f"   Project: {loaded_agent_config['project_id']}")
    print(f"   Agent: {loaded_agent_config['agent_name']}")
    print()

    # Create session
    session = await runner.session_service.create_session(
        app_name="adk_agent_app", user_id="eval_user"
    )

    # Create a wrapper that bridges sync to async
    class ADKAgentBridge:
        """Bridge to make ADK agent work with synchronous evaluation code."""
        
        def __init__(self, runner, session_id, loop):
            self.runner = runner
            self.session_id = session_id
            self.loop = loop
        
        def generate_content(self, prompt):
            """Synchronous wrapper that schedules async work in the event loop."""
            # Create a future for the result
            future = asyncio.run_coroutine_threadsafe(
                self._async_generate(prompt),
                self.loop
            )
            return future.result()
        
        async def _async_generate(self, prompt):
            """Async method to generate content."""
            content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
            response_text = ""
            async for event in self.runner.run_async(
                user_id="eval_user",
                session_id=self.session_id,
                new_message=content,
            ):
                if event.content.parts and event.content.parts[0].text:
                    response_text = event.content.parts[0].text
            
            # Return object with .text attribute
            class Response:
                def __init__(self, text):
                    self.text = text
            
            return Response(response_text)
    
    # Get the current event loop
    loop = asyncio.get_event_loop()
    
    # Create bridge
    agent_bridge = ADKAgentBridge(runner, session.id, loop)

    # Run evaluation test
    tester = RegressionTester(
        project_id=loaded_agent_config["project_id"], agent_name=loaded_agent_config["agent_name"]
    )

    test_run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

    print(f"🔄 Running evaluation test: test_{test_run_timestamp}")
    print()

    # Fetch test cases
    test_cases = tester.fetch_test_cases(only_reviewed=True, limit=None)
    
    if not test_cases:
        print("❌ No test cases found. Run the agent with --test to collect data first.")
        wrapper.flush()
        wrapper.shutdown()
        sys.exit(1)
    
    print(f"📋 Found {len(test_cases)} test cases")
    print()
    
    # Run agent on test cases manually (async version)
    print("🤖 Running agent on test cases...")
    
    # Generate test_run_id and timestamp
    test_run_id = f"test_{test_run_timestamp}"
    test_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        instruction = test_case["instruction"]
        reference = test_case.get("reference", "")
        
        print(f"   [{i}/{len(test_cases)}] Testing...")
        
        try:
            response = await agent_bridge._async_generate(instruction)
            response_text = response.text if response.text else "[EMPTY RESPONSE]"
            results.append({
                "test_run_id": test_run_id,
                "test_timestamp": test_timestamp,
                "instruction": instruction,
                "reference": reference,
                "response": response_text,
            })
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                "test_run_id": test_run_id,
                "test_timestamp": test_timestamp,
                "instruction": instruction,
                "reference": reference,
                "response": f"ERROR: {str(e)}",
            })
    
    print(f"✅ Completed {len(results)} test runs")
    
    # Use RegressionTester's built-in methods to save and evaluate
    from agent_evaluation_sdk.evaluation import GenAIEvaluator
    from google.cloud import bigquery
    from google.api_core.exceptions import NotFound
    
    # Create consistent table names
    response_table = f"{loaded_agent_config['project_id']}.agent_evaluation.{loaded_agent_config['agent_name']}_eval_{test_run_timestamp}"
    metrics_table = f"{response_table}_metrics"
    
    # Delete metrics table if it exists (to ensure clean schema)
    try:
        tester.bq_client.delete_table(metrics_table, not_found_ok=True)
        print(f"   Cleaned up old metrics table")
    except Exception:
        pass
    
    # Save responses
    print("💾 Saving responses...")
    # Manually save with our timestamp
    rows = [
        {**result, "test_run_name": f"test_{test_run_timestamp}", "agent_name": loaded_agent_config["agent_name"]}
        for result in results
    ]
    
    schema = [
        bigquery.SchemaField("test_run_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("test_run_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("test_timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("instruction", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("reference", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("response", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("context", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("error", "STRING", mode="NULLABLE"),
    ]
    
    try:
        table = bigquery.Table(response_table, schema=schema)
        tester.bq_client.create_table(table, exists_ok=True)
    except Exception as e:
        print(f"   Table exists or error: {e}")
    
    errors = tester.bq_client.insert_rows_json(response_table, rows)
    if errors:
        print(f"⚠️  Errors inserting rows: {errors}")
    else:
        print(f"✅ Responses saved: {response_table}")
    
    # Evaluate
    print("📈 Evaluating responses...")
    evaluator = GenAIEvaluator(project_id=loaded_agent_config["project_id"])
    eval_results = evaluator._evaluate(
        dataset=results,
        metrics=eval_config.genai_eval.metrics,
        criteria=eval_config.genai_eval.criteria,
        thresholds=eval_config.genai_eval.thresholds,
    )
    
    # Save metrics manually with correct schema
    print("💾 Saving metrics...")
    
    import json
    row = {
        "test_run_name": f"test_{test_run_timestamp}",
        "agent_name": loaded_agent_config["agent_name"],
        "test_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "dataset_size": eval_results.get("dataset_size", 0),
        "metrics": json.dumps(eval_results.get("metrics", {})),
        "criteria_scores": json.dumps(eval_results.get("criteria_scores", {})),
    }
    
    metrics_schema = [
        bigquery.SchemaField("test_run_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("test_timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("dataset_size", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("metrics", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("criteria_scores", "STRING", mode="NULLABLE"),
    ]
    
    try:
        metrics_table_obj = bigquery.Table(metrics_table, schema=metrics_schema)
        tester.bq_client.create_table(metrics_table_obj, exists_ok=True)
    except Exception as e:
        print(f"   Metrics table exists or error: {e}")
    
    errors = tester.bq_client.insert_rows_json(metrics_table, [row])
    if errors:
        print(f"⚠️  Errors inserting metrics: {errors}")
    else:
        print(f"✅ Metrics saved: {metrics_table}")
    
    # Cleanup
    wrapper.flush()
    wrapper.shutdown()
    
    print("\n✅ Evaluation test complete!")
    print()
    print("📊 Results saved to BigQuery:")
    print(f"   - Responses: {loaded_agent_config['agent_name']}_eval_{test_run_timestamp}")
    print(f"   - Metrics: {loaded_agent_config['agent_name']}_eval_{test_run_timestamp}_metrics")
    print()
    print("🔍 View results in BigQuery Console:")
    print(f"   https://console.cloud.google.com/bigquery?project={loaded_agent_config['project_id']}")
    print("   → Dataset: agent_evaluation")


if __name__ == "__main__":
    main()
