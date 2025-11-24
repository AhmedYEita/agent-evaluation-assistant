"""
Regression testing utilities

Runs the agent on a test dataset and evaluates performance.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud import bigquery
from google.cloud.exceptions import Conflict


class RegressionTester:
    """Run regression tests on agent using historical test dataset."""

    def __init__(self, project_id: str, agent_name: str):
        """Initialize regression tester.

        Args:
            project_id: GCP project ID
            agent_name: Name of the agent (used for table naming)
        """
        self.project_id = project_id
        self.agent_name = self._validate_name(agent_name)
        self.bq_client = bigquery.Client(project=project_id)

    def _validate_name(self, name: str) -> str:
        """Validate and sanitize agent name for BigQuery table naming.

        Args:
            name: Agent name to validate

        Returns:
            Validated agent name

        Raises:
            ValueError: If name contains invalid characters
        """
        # Validate BigQuery table names: letters, numbers, underscores, hyphens, and spaces only
        if not name.replace("_", "").replace("-", "").replace(" ", "").isalnum():
            raise ValueError(
                f"Invalid agent name: '{name}'. "
                f"Must contain only letters, numbers, underscores, hyphens, and spaces."
            )
        # Sanitize name: replace hyphens and spaces with underscores
        return name.replace("-", "_").replace(" ", "_")

    def fetch_test_cases(
        self,
        only_reviewed: bool = True,
        limit: Optional[int] = None,
        dataset_table: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch test cases from BigQuery.

        Args:
            only_reviewed: If True, only fetch reviewed test cases
            limit: Optional limit on number of test cases to fetch
            dataset_table: Optional custom BigQuery table name (overrides default)

        Returns:
            List of test cases with instruction, reference, and context
        """
        # Determine table name: use custom if provided, otherwise use default naming
        if dataset_table:
            table_name = dataset_table
        else:
            table_name = f"{self.project_id}.agent_evaluation.{self.agent_name}_eval_dataset"

        # Use parameterized query to prevent SQL injection
        query = """
            SELECT instruction, reference, context
            FROM `{table_name}`
            {where_clause}
            ORDER BY timestamp DESC
            {limit_clause}
        """.format(
            table_name=table_name,
            where_clause="WHERE reviewed = TRUE" if only_reviewed else "",
            limit_clause=f"LIMIT {int(limit)}" if limit else "",
        )

        print("📊 Fetching test cases...")
        try:
            results = self.bq_client.query(query).result()
            test_cases = [dict(row) for row in results]
            print(f"✅ Found {len(test_cases)} test cases")
            return test_cases
        except Exception as e:
            print(f"❌ Error fetching test cases: {e}")
            return []

    def run_agent_on_tests(
        self, agent: Any, test_cases: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run agent on test cases and collect responses.

        Args:
            agent: ADK agent instance
            test_cases: List of test cases to run

        Returns:
            List of results with responses
        """
        print(f"🤖 Running agent on {len(test_cases)} test cases...")
        results = []

        for i, test_case in enumerate(test_cases, 1):
            instruction = test_case.get("instruction", "")
            reference = test_case.get("reference", "")
            context = test_case.get("context")

            print(f"   [{i}/{len(test_cases)}] Testing...")

            try:
                response = agent.generate_content(instruction)
                response_text = response.text if hasattr(response, "text") else str(response)
                error = None

                # Ensure response is not empty
                if not response_text or response_text.strip() == "":
                    response_text = "[EMPTY RESPONSE]"
                    error = "Agent returned empty response"

            except Exception as e:
                print(f"   ❌ Error: {e}")
                response_text = f"ERROR: {str(e)}"
                error = str(e)

            results.append(
                {
                    "instruction": instruction,
                    "reference": reference,
                    "response": response_text,
                    "context": context,
                    "test_run_id": str(uuid.uuid4()),
                    "test_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
                    "error": error,
                }
            )

        print(f"✅ Completed {len(results)} test runs")
        return results

    def save_results(self, results: List[Dict[str, Any]], test_run_name: str) -> tuple[str, str]:
        """Save test results to BigQuery.

        Args:
            results: List of test results to save
            test_run_name: Name of the test run

        Returns:
            Tuple of (response_table_name, metrics_table_name)

        Raises:
            Exception: If saving fails
        """
        # Use fixed table names
        response_table = f"{self.project_id}.agent_evaluation.{self.agent_name}_eval_run"
        metrics_table = f"{self.project_id}.agent_evaluation.{self.agent_name}_eval_metrics"

        print("💾 Saving responses...")
        
        # Add timestamp to each row
        timestamp = datetime.utcnow().isoformat()
        rows = [
            {
                **result,
                "test_run_name": test_run_name,
                "agent_name": self.agent_name,
                "test_timestamp": timestamp
            }
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

        # Create table if it doesn't exist
        try:
            table = bigquery.Table(response_table, schema=schema)
            table.clustering_fields = ["agent_name", "test_timestamp"]
            self.bq_client.create_table(table, exists_ok=True)
            print(f"   ✓ Table ready: {response_table}")
        except Conflict:
            # Table already exists, which is fine
            pass
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            raise

        try:
            errors = self.bq_client.insert_rows_json(response_table, rows)
            if errors:
                print(f"⚠️  Errors inserting rows: {errors}")
            else:
                print(f"✅ Responses saved: {response_table} ({len(rows)} rows)")
        except Exception as e:
            print(f"❌ Error inserting rows: {e}")
            raise

        return response_table, metrics_table

    def save_metrics(
        self, test_run_name: str, eval_results: Dict[str, Any], metrics_table: str
    ) -> None:
        """Save evaluation metrics to BigQuery.

        Args:
            test_run_name: Name of the test run
            eval_results: Evaluation results dictionary
            metrics_table: BigQuery table name for metrics

        Raises:
            Exception: If saving fails
        """
        import json

        print("💾 Saving metrics...")

        row = {
            "test_run_name": test_run_name,
            "agent_name": self.agent_name,
            "test_timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "dataset_size": eval_results.get("dataset_size", 0),
            "metrics": json.dumps(eval_results.get("metrics", {})),
            "criteria_scores": json.dumps(eval_results.get("criteria_scores", {})),
        }

        schema = [
            bigquery.SchemaField("test_run_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("test_timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("dataset_size", "INTEGER", mode="NULLABLE"),
            bigquery.SchemaField("metrics", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("criteria_scores", "STRING", mode="NULLABLE"),
        ]

        # Create table if it doesn't exist
        try:
            table = bigquery.Table(metrics_table, schema=schema)
            table.clustering_fields = ["agent_name", "test_timestamp"]
            self.bq_client.create_table(table, exists_ok=True)
            print(f"   ✓ Table ready: {metrics_table}")
        except Conflict:
            # Table already exists, which is fine
            pass
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            raise

        try:
            errors = self.bq_client.insert_rows_json(metrics_table, [row])
            if errors:
                print(f"⚠️  Errors inserting metrics: {errors}")
            else:
                print(f"✅ Metrics saved: {metrics_table}")
        except Exception as e:
            print(f"❌ Error inserting metrics: {e}")
            raise

    def run_full_test(
        self,
        agent: Any,
        test_run_name: str,
        only_reviewed: bool = True,
        limit: Optional[int] = None,
        dataset_table: Optional[str] = None,
        metrics: Optional[List[str]] = None,
        criteria: Optional[List[str]] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Run complete regression test: fetch, run, evaluate, save.

        This is the main method for running regression tests.

        Args:
            agent: ADK agent instance to test
            test_run_name: Name for this test run
            only_reviewed: If True, only use reviewed test cases
            limit: Optional limit on number of test cases
            dataset_table: Optional custom BigQuery table name
            metrics: List of metrics to compute (e.g., ["bleu", "rouge"])
            criteria: List of criteria for evaluation
            thresholds: Optional dict of minimum scores for pass/fail

        Returns:
            Dictionary with test results and metadata
        """
        from agent_evaluation_sdk.evaluation import GenAIEvaluator

        print("=" * 70)
        print(f"🧪 Running Test: {test_run_name}")
        print("=" * 70)

        # 1. Fetch test cases
        test_cases = self.fetch_test_cases(
            only_reviewed=only_reviewed, limit=limit, dataset_table=dataset_table
        )
        if not test_cases:
            print("❌ No test cases found")
            return {"error": "No test cases found"}

        # 2. Run agent on test cases
        results = self.run_agent_on_tests(agent, test_cases)

        # 3. Save responses to BigQuery
        try:
            response_table, metrics_table = self.save_results(results, test_run_name)
        except Exception as e:
            print(f"❌ Failed to save results: {e}")
            return {"error": f"Failed to save results: {e}"}

        # 4. Evaluate responses
        print("📈 Evaluating responses...")
        evaluator = GenAIEvaluator(project_id=self.project_id)
        eval_results = evaluator._evaluate(
            dataset=results, metrics=metrics, criteria=criteria, thresholds=thresholds
        )

        # 5. Save metrics to BigQuery
        try:
            self.save_metrics(test_run_name, eval_results, metrics_table)
        except Exception as e:
            print(f"⚠️  Failed to save metrics: {e}")

        # Print summary
        self._print_summary(test_run_name, results, response_table, metrics_table, eval_results)

        return {
            "test_run_name": test_run_name,
            "test_cases_count": len(results),
            "response_table": response_table,
            "metrics_table": metrics_table,
            "evaluation_results": eval_results,
        }

    def _print_summary(
        self,
        test_run_name: str,
        results: List[Dict[str, Any]],
        response_table: str,
        metrics_table: str,
        eval_results: Dict[str, Any],
    ) -> None:
        """Print test summary.

        Args:
            test_run_name: Name of the test run
            results: Test results
            response_table: BigQuery table name for responses
            metrics_table: BigQuery table name for metrics
            eval_results: Evaluation results
        """
        print("\n" + "=" * 70)
        print("✅ Test Complete!")
        print("=" * 70)
        print(f"Test run: {test_run_name}")
        print(f"Test cases: {len(results)}")
        print(f"\nBigQuery Tables (appended):")
        print(f"  Responses: {response_table}")
        print(f"  Metrics: {metrics_table}")

        print("\nMetrics Summary:")
        if "metrics" in eval_results:
            for metric, values in eval_results["metrics"].items():
                print(f"  {metric}: {values}")

        if "criteria_scores" in eval_results:
            print("\nCriteria:")
            for criterion, scores in eval_results["criteria_scores"].items():
                score_info = f"score={scores.get('score', 'N/A')}"
                if "pass_rate" in scores:
                    score_info += f", pass_rate={scores['pass_rate']}"
                print(f"  {criterion}: {score_info}")

        print("\n💡 Query your results:")
        print(f"   SELECT * FROM `{response_table}` WHERE test_run_name = '{test_run_name}'")
        print(f"   SELECT * FROM `{metrics_table}` WHERE test_run_name = '{test_run_name}'")
        print("=" * 70)
