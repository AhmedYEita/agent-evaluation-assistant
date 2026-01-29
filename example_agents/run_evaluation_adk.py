"""
Evaluation Testing Script for ADK Agent

Runs the ADK agent against the testing dataset and evaluates performance.
"""

import sys
import uuid
import yaml
import asyncio
from datetime import datetime, timezone
from google.genai import types

# Import agent creation from adk_agent.py
from adk_agent import create_adk_agent

# Import evaluation SDK
from agent_evaluation_sdk import RegressionTester, GenAIEvaluator


async def main():
    """Run evaluation test on the ADK agent."""

    print("🧪 Loading configuration and ADK agent...")
    print()

    # Load configuration
    with open("eval_config.yaml") as f:
        eval_config = yaml.safe_load(f)

    # Create ADK agent
    agent, runner, wrapper, config = create_adk_agent()

    print(f"   Project: {config['project_id']}")
    print("   Agent: adk_agent")
    print()

    # Run evaluation test
    tester = RegressionTester(project_id=config["project_id"], agent_name="adk_agent")

    test_run_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")

    print(f"🔄 Running evaluation test: test_{test_run_timestamp}")
    print()

    # Fetch test cases
    test_cases = tester.fetch_test_cases(
        only_reviewed=eval_config.get("regression", {}).get("only_reviewed", True),
        limit=eval_config.get("regression", {}).get("test_limit"),
    )

    if not test_cases:
        print(
            "❌ No test cases found. Run the agent with --test to collect data first."
        )
        wrapper.flush()
        wrapper.shutdown()
        sys.exit(1)

    print(f"📋 Found {len(test_cases)} test cases")
    print()

    # Create session for evaluation
    session = await runner.session_service.create_session(
        app_name="adk_agent_app", user_id="eval_user"
    )

    # Run agent on test cases
    print("🤖 Running agent on test cases...")

    test_run_name = f"test_{test_run_timestamp}"
    test_timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    results = []
    for i, test_case in enumerate(test_cases, 1):
        instruction = test_case["instruction"]
        reference = test_case.get("reference", "")

        print(f"   [{i}/{len(test_cases)}] Testing...")

        try:
            content = types.Content(
                role="user", parts=[types.Part.from_text(text=instruction)]
            )
            response_text = ""

            async for event in runner.run_async(
                user_id="eval_user",
                session_id=session.id,
                new_message=content,
            ):
                if event.content.parts and event.content.parts[0].text:
                    response_text = event.content.parts[0].text

            # Ensure response is not empty
            if not response_text or response_text.strip() == "":
                response_text = "[EMPTY RESPONSE]"

            results.append(
                {
                    "test_run_id": str(uuid.uuid4()),  # Unique ID for this test case
                    "test_timestamp": test_timestamp,
                    "instruction": instruction,
                    "reference": reference,
                    "response": response_text,
                    "context": test_case.get("context"),
                    "error": None,
                }
            )
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(
                {
                    "test_run_id": str(uuid.uuid4()),  # Unique ID for this test case
                    "test_timestamp": test_timestamp,
                    "instruction": instruction,
                    "reference": reference,
                    "response": f"ERROR: {str(e)}",
                    "context": test_case.get("context"),
                    "error": str(e),
                }
            )

    print(f"✅ Completed {len(results)} test runs")

    # Save using RegressionTester methods (uses new table naming)
    response_table, metrics_table = tester.save_results(results, test_run_name)

    # Evaluate
    print("📈 Evaluating responses...")
    evaluator = GenAIEvaluator(project_id=config["project_id"])
    eval_results = evaluator._evaluate(
        dataset=results,
        metrics=eval_config.get("genai_eval", {}).get("metrics", ["bleu", "rouge"]),
        criteria=eval_config.get("genai_eval", {}).get("criteria", []),
        thresholds=eval_config.get("genai_eval", {}).get("thresholds", {}),
    )

    # Save metrics
    tester.save_metrics(test_run_name, eval_results, metrics_table)

    # Cleanup
    wrapper.flush()
    wrapper.shutdown()

    print("\n✅ Evaluation test complete!")
    print()
    print("📊 Results saved to BigQuery:")
    print(f"   - Responses: {response_table}")
    print(f"   - Metrics: {metrics_table}")
    print()
    print("🔍 View results in BigQuery Console:")
    print(
        f"   https://console.cloud.google.com/bigquery?project={config['project_id']}"
    )
    print("   → Dataset: agent_evaluation")


if __name__ == "__main__":
    asyncio.run(main())
