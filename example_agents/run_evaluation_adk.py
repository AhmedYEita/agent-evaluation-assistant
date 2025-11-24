"""
Evaluation Testing Script for ADK Agent

Runs the ADK agent against the testing dataset and evaluates performance.
"""

import sys
import yaml
import asyncio
from datetime import datetime

# Import agent creation from adk_agent.py
from adk_agent import create_adk_agent

# Import evaluation SDK
from agent_evaluation_sdk import RegressionTester


async def main():
    """Run evaluation test on the ADK agent."""

    print("🧪 Loading configuration and ADK agent...")
    print()

    # Load configuration
    with open("agent_config.yaml") as f:
        agent_config = yaml.safe_load(f)
    
    with open("eval_config.yaml") as f:
        eval_config = yaml.safe_load(f)

    # Create ADK agent
    agent, runner, wrapper, config = create_adk_agent()

    print(f"   Project: {config['project_id']}")
    print(f"   Agent: adk_agent")
    print()

    # Run evaluation test
    tester = RegressionTester(
        project_id=config['project_id'],
        agent_name="adk_agent"
    )

    test_run_timestamp = datetime.now().strftime("%Y%m%d_%H%M")

    print(f"🔄 Running evaluation test: test_{test_run_timestamp}")
    print()

    # Note: For ADK agents with async runners, we need to use a sync wrapper
    # The regression tester will call agent.generate_content() which doesn't exist on runner
    # So we pass the agent directly
    results = tester.run_full_test(
        agent=agent,  # Pass the agent, not the runner
        test_run_name=f"test_{test_run_timestamp}",
        only_reviewed=eval_config.get('regression', {}).get('only_reviewed', True),
        limit=eval_config.get('regression', {}).get('test_limit'),
        metrics=eval_config.get('genai_eval', {}).get('metrics', ['bleu', 'rouge']),
        criteria=eval_config.get('genai_eval', {}).get('criteria', []),
        thresholds=eval_config.get('genai_eval', {}).get('thresholds', {}),
    )

    if "error" not in results:
        print("\n✅ Evaluation test complete!")
        print()
        print("📊 Results saved to BigQuery:")
        print(f"   - Responses: {results['response_table']}")
        print(f"   - Metrics: {results['metrics_table']}")
        print()
        print("🔍 View results in BigQuery Console:")
        print(
            f"   https://console.cloud.google.com/bigquery?project={config['project_id']}"
        )
        print("   → Dataset: agent_evaluation")
    else:
        print(f"\n❌ Error: {results['error']}")
        sys.exit(1)
    
    # Cleanup
    wrapper.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

