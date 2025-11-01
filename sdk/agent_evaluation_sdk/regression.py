"""
Regression testing utilities - run agent on test dataset and evaluate.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import bigquery


class RegressionTester:
    """Run regression tests on agent using historical test dataset."""

    def __init__(self, project_id: str, agent_name: str):
        """Initialize regression tester."""
        self.project_id = project_id
        self.agent_name = agent_name
        self.bq_client = bigquery.Client(project=project_id)

    def fetch_test_cases(
        self, only_reviewed: bool = True, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Fetch test cases from BigQuery."""
        table_name = f"{self.project_id}.agent_evaluation.{self.agent_name}_eval_dataset"
        query = f"""
            SELECT instruction, reference, context
            FROM `{table_name}`
        """

        if only_reviewed:
            query += " WHERE reviewed = TRUE"

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        print("📊 Fetching test cases...")
        results = self.bq_client.query(query).result()
        test_cases = [dict(row) for row in results]
        print(f"✅ Found {len(test_cases)} test cases")
        return test_cases

    def run_agent_on_tests(
        self, agent: Any, test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run agent on test cases and collect responses."""
        print(f"🤖 Running agent on {len(test_cases)} test cases...")
        results = []

        for i, test_case in enumerate(test_cases, 1):
            instruction = test_case["instruction"]
            reference = test_case["reference"]
            context = test_case.get("context")

            print(f"   [{i}/{len(test_cases)}] Testing...")

            try:
                response = agent.generate_content(instruction)
                response_text = response.text if hasattr(response, "text") else str(response)

                results.append(
                    {
                        "instruction": instruction,
                        "reference": reference,
                        "response": response_text,
                        "context": context,
                        "test_run_id": str(uuid.uuid4()),
                        "test_timestamp": datetime.utcnow().isoformat(),
                    }
                )

            except Exception as e:
                print(f"   ❌ Error: {e}")
                results.append(
                    {
                        "instruction": instruction,
                        "reference": reference,
                        "response": f"ERROR: {str(e)}",
                        "context": context,
                        "test_run_id": str(uuid.uuid4()),
                        "test_timestamp": datetime.utcnow().isoformat(),
                    }
                )

        print(f"✅ Completed {len(results)} test runs")
        return results

    def save_results(self, results: List[Dict[str, Any]], test_run_name: str) -> tuple[str, str]:
        """Save test results and metrics to BigQuery.

        Returns:
            Tuple of (response_table_name, metrics_table_name)
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        response_table = f"{self.project_id}.agent_evaluation.{self.agent_name}_eval_{timestamp}"
        metrics_table = f"{response_table}_metrics"

        # Save responses
        print("💾 Saving responses...")
        rows = [
            {**result, "test_run_name": test_run_name, "agent_name": self.agent_name}
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
        ]

        table = bigquery.Table(response_table, schema=schema)
        self.bq_client.create_table(table)
        self.bq_client.insert_rows_json(table, rows)
        print(f"✅ Responses saved: {response_table}")

        return response_table, metrics_table

    def save_metrics(
        self, test_run_name: str, eval_results: Dict[str, Any], metrics_table: str
    ) -> None:
        """Save evaluation metrics to BigQuery."""
        print("💾 Saving metrics...")

        row = {
            "test_run_name": test_run_name,
            "agent_name": self.agent_name,
            "test_timestamp": datetime.utcnow().isoformat(),
            "dataset_size": eval_results.get("dataset_size", 0),
            "metrics": eval_results.get("metrics", {}),
            "criteria_scores": eval_results.get("criteria_scores", {}),
        }

        schema = [
            bigquery.SchemaField("test_run_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("test_timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("dataset_size", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("metrics", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("criteria_scores", "JSON", mode="NULLABLE"),
        ]

        table = bigquery.Table(metrics_table, schema=schema)
        self.bq_client.create_table(table)
        self.bq_client.insert_rows_json(table, [row])
        print(f"✅ Metrics saved: {metrics_table}")

    def run_full_test(
        self,
        agent: Any,
        test_run_name: str,
        only_reviewed: bool = True,
        limit: Optional[int] = None,
        metrics: Optional[List[str]] = None,
        criteria: Optional[List[str]] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Run complete test: fetch, run, evaluate, save.

        This is the main method you should use.
        """
        from agent_evaluation_sdk.evaluation import GenAIEvaluator

        print("=" * 70)
        print(f"🧪 Running Test: {test_run_name}")
        print("=" * 70)

        # 1. Fetch test cases
        test_cases = self.fetch_test_cases(only_reviewed=only_reviewed, limit=limit)
        if not test_cases:
            return {"error": "No test cases found"}

        # 2. Run agent
        results = self.run_agent_on_tests(agent, test_cases)

        # 3. Save responses
        response_table, metrics_table = self.save_results(results, test_run_name)

        # 4. Evaluate
        print("📈 Evaluating responses...")
        evaluator = GenAIEvaluator(project_id=self.project_id)
        eval_results = evaluator._evaluate(
            dataset=results, metrics=metrics, criteria=criteria, thresholds=thresholds
        )

        # 5. Save metrics
        self.save_metrics(test_run_name, eval_results, metrics_table)

        # Summary
        print("\n" + "=" * 70)
        print("✅ Test Complete!")
        print("=" * 70)
        print(f"Test run: {test_run_name}")
        print(f"Test cases: {len(results)}")
        print(f"Responses: {response_table}")
        print(f"Metrics: {metrics_table}")
        print("\nMetrics Summary:")
        if "metrics" in eval_results:
            for metric, values in eval_results["metrics"].items():
                print(f"  {metric}: {values}")
        if "criteria_scores" in eval_results:
            print("Criteria:")
            for criterion, scores in eval_results["criteria_scores"].items():
                score_info = f"score={scores.get('score', 'N/A')}"
                if "pass_rate" in scores:
                    score_info += f", pass_rate={scores['pass_rate']}"
                print(f"  {criterion}: {score_info}")
        print("=" * 70)

        return {
            "test_run_name": test_run_name,
            "test_cases_count": len(results),
            "response_table": response_table,
            "metrics_table": metrics_table,
            "evaluation_results": eval_results,
        }
