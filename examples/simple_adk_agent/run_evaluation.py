"""
Evaluation Testing Script

This script runs your agent against the testing dataset and evaluates performance.

Usage:
    python run_evaluation.py
"""

import sys
from datetime import datetime

# Import agent creation from agent.py
from agent import create_agent

# Import evaluation SDK
from agent_evaluation_sdk import RegressionTester


def main():
    """Run evaluation test on the agent."""
    test_run_name = datetime.now().strftime("test_%Y%m%d_%H%M")

    print("🧪 Loading configuration and agent...")
    print()

    # Create agent (reuses the same agent from agent.py!)
    agent, config = create_agent()

    print(f"   Project: {config.project_id}")
    print(f"   Agent: {config.agent_name}")
    print(f"   Test Run: {test_run_name}")
    print()

    # Run evaluation test
    tester = RegressionTester(
        project_id=config.project_id, agent_name=config.agent_name
    )

    print(f"🔄 Running evaluation test: {test_run_name}")
    print()

    results = tester.run_full_test(
        agent=agent,
        test_run_name=test_run_name,
        only_reviewed=True,
        metrics=config.genai_eval.metrics,
        criteria=config.genai_eval.criteria,
        thresholds=config.genai_eval.thresholds,
    )

    if "error" not in results:
        print("\n✅ Evaluation test complete!")
        print()
        print("📊 Results saved to BigQuery:")
        timestamp = results.get("timestamp", "YYYYMMDD_HHMM")
        print(f"   - Test Run: {test_run_name}")
        print(f"   - Responses: {config.agent_name}_eval_{timestamp}")
        print(f"   - Metrics: {config.agent_name}_eval_{timestamp}_metrics")
        print()
        print("🔍 View results in BigQuery Console:")
        print(
            f"   https://console.cloud.google.com/bigquery?project={config.project_id}"
        )
        print("   → Dataset: agent_evaluation")
    else:
        print(f"\n❌ Error: {results['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
