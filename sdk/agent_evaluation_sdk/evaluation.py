"""
Gen AI Evaluation Service integration.
"""

from typing import Any, Dict, List, Optional

from google.cloud import aiplatform


class GenAIEvaluator:
    """Run evaluations using Gen AI Evaluation Service."""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-1.5-flash",
    ):
        """Initialize evaluator.

        Args:
            project_id: GCP project ID
            location: GCP region
            model_name: Model to use for model-based evaluation
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

        # Initialize Vertex AI
        aiplatform.init(project=project_id, location=location)

    def _evaluate(
        self,
        dataset: List[Dict[str, Any]],
        metrics: Optional[List[str]] = None,
        criteria: Optional[List[str]] = None,
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        """Internal evaluation logic.

        Expects dataset with: instruction, reference, response fields.

        Args:
            dataset: List of test cases with instruction, reference, response
            metrics: List of metrics to compute (e.g., ["bleu", "rouge"])
            criteria: List of criteria for pointwise evaluation
            thresholds: Optional dict of minimum scores for pass/fail (0-1 scale)

        Returns:
            Evaluation results dictionary
        """
        if not dataset:
            return {
                "dataset_size": 0,
                "metrics": {},
                "criteria_scores": {},
                "error": "Empty dataset",
            }

        if metrics is None:
            metrics = ["bleu", "rouge"]
        if criteria is None:
            criteria = [
                "coherence",
                "fluency",
                "safety",
                "groundedness",
                "fulfillment",
            ]
        if thresholds is None:
            thresholds = {}

        print(f"📊 Evaluating {len(dataset)} interactions...")
        print(f"   Metrics: {', '.join(metrics)}")
        print(f"   Criteria: {', '.join(criteria)}")
        if thresholds:
            print(f"   Thresholds: {thresholds}")

        # Run automated metrics
        results = {
            "dataset_size": len(dataset),
            "metrics": {},
            "criteria_scores": {},
        }

        # Calculate BLEU if requested
        if "bleu" in metrics:
            bleu_scores = self._calculate_bleu(dataset)
            # Add pass rate if threshold is defined
            if "bleu" in thresholds and bleu_scores.get("score"):
                bleu_scores["pass_rate"] = (
                    1.0 if bleu_scores["score"] >= thresholds["bleu"] else 0.0
                )
            results["metrics"]["bleu"] = bleu_scores

        # Calculate ROUGE if requested
        if "rouge" in metrics:
            rouge_scores = self._calculate_rouge(dataset)
            # Add pass rate if threshold is defined (uses rougeL as primary metric)
            if "rouge" in thresholds and rouge_scores.get("rougeL"):
                rouge_scores["pass_rate"] = (
                    1.0 if rouge_scores["rougeL"] >= thresholds["rouge"] else 0.0
                )
            results["metrics"]["rouge"] = rouge_scores

        # Run pointwise evaluation for criteria
        if criteria:
            criteria_results = self._evaluate_criteria(dataset, criteria, thresholds)
            results["criteria_scores"] = criteria_results

        return results

    def _calculate_bleu(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate BLEU scores using Vertex AI Evaluation.

        Args:
            dataset: List of test cases with 'reference' and 'response' fields

        Returns:
            Dictionary with BLEU scores
        """
        print("   Computing BLEU scores...")

        try:
            from vertexai.preview.evaluation import EvalTask

            # Prepare evaluation dataset
            eval_dataset = []
            for item in dataset:
                eval_dataset.append(
                    {
                        "reference": item.get("reference", ""),
                        "prediction": item.get("response", ""),
                    }
                )

            # Create evaluation task
            eval_task = EvalTask(
                dataset=eval_dataset,
                metrics=["bleu"],
            )

            # Run evaluation
            result = eval_task.evaluate()

            # Extract BLEU score from results
            # Vertex AI returns a DataFrame-like structure
            if hasattr(result, "summary_metrics"):
                bleu_score = result.summary_metrics.get("bleu/mean", 0.0)
            else:
                # Fallback: calculate from row metrics
                bleu_scores = [
                    row.get("bleu", 0.0) for row in result.metrics_table if "bleu" in row
                ]
                bleu_score = sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0.0

            return {
                "score": round(bleu_score, 4),
                "count": len(dataset),
            }

        except ImportError:
            print("   ⚠️  vertexai.preview.evaluation not available")
            return {
                "score": 0.0,
                "count": len(dataset),
                "error": "Vertex AI Evaluation SDK not installed",
            }
        except Exception as e:
            print(f"   ⚠️  BLEU calculation failed: {e}")
            return {
                "score": 0.0,
                "count": len(dataset),
                "error": str(e),
            }

    def _calculate_rouge(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate ROUGE scores using Vertex AI Evaluation.

        Args:
            dataset: List of test cases with 'reference' and 'response' fields

        Returns:
            Dictionary with ROUGE scores (rouge1, rouge2, rougeL)
        """
        print("   Computing ROUGE scores...")

        try:
            from vertexai.preview.evaluation import EvalTask

            # Prepare evaluation dataset
            eval_dataset = []
            for item in dataset:
                eval_dataset.append(
                    {
                        "reference": item.get("reference", ""),
                        "prediction": item.get("response", ""),
                    }
                )

            # Create evaluation task
            eval_task = EvalTask(
                dataset=eval_dataset,
                metrics=["rouge"],
            )

            # Run evaluation
            result = eval_task.evaluate()

            # Extract ROUGE scores
            rouge_results = {}
            if hasattr(result, "summary_metrics"):
                rouge_results["rougeL"] = round(result.summary_metrics.get("rougeL/mean", 0.0), 4)
                rouge_results["rouge1"] = round(result.summary_metrics.get("rouge1/mean", 0.0), 4)
                rouge_results["rouge2"] = round(result.summary_metrics.get("rouge2/mean", 0.0), 4)
            else:
                # Fallback: default values
                rouge_results = {"rougeL": 0.0, "rouge1": 0.0, "rouge2": 0.0}

            rouge_results["count"] = len(dataset)
            return rouge_results

        except ImportError:
            print("   ⚠️  vertexai.preview.evaluation not available")
            return {
                "rougeL": 0.0,
                "rouge1": 0.0,
                "rouge2": 0.0,
                "count": len(dataset),
                "error": "Vertex AI Evaluation SDK not installed",
            }
        except Exception as e:
            print(f"   ⚠️  ROUGE calculation failed: {e}")
            return {
                "rougeL": 0.0,
                "rouge1": 0.0,
                "rouge2": 0.0,
                "count": len(dataset),
                "error": str(e),
            }

    def _evaluate_criteria(
        self,
        dataset: List[Dict[str, Any]],
        criteria: List[str],
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Evaluate dataset against criteria using model-based evaluation.

        Args:
            dataset: List of test cases with instruction, reference, response
            criteria: List of criteria names to evaluate
            thresholds: Optional dict of minimum scores for pass/fail

        Returns:
            Dictionary mapping criterion name to evaluation results
        """
        if thresholds is None:
            thresholds = {}

        print(f"   Evaluating {len(criteria)} criteria using {self.model_name}...")

        try:
            from vertexai.preview.evaluation import EvalTask

            # Prepare evaluation dataset
            eval_dataset = []
            for item in dataset:
                eval_dataset.append(
                    {
                        "prompt": item.get("instruction", ""),
                        "context": item.get("context", ""),
                        "reference": item.get("reference", ""),
                        "response": item.get("response", ""),
                    }
                )

            # Map criteria to Vertex AI metric names
            valid_criteria = {
                "coherence",
                "fluency",
                "safety",
                "groundedness",
                "fulfillment",
                "instruction_following",
                "verbosity",
            }

            results = {}

            for criterion in criteria:
                if criterion not in valid_criteria:
                    print(f"   ⚠️  Unknown criterion: {criterion}")
                    results[criterion] = {
                        "score": 0.0,
                        "count": len(dataset),
                        "error": f"Unknown criterion: {criterion}",
                    }
                    continue

                try:
                    # Create evaluation task for this criterion
                    eval_task = EvalTask(
                        dataset=eval_dataset,
                        metrics=[criterion],
                    )

                    # Run evaluation
                    result = eval_task.evaluate(model=self.model_name)

                    # Extract score (Vertex AI typically returns 1-5 scale)
                    if hasattr(result, "summary_metrics"):
                        raw_score = result.summary_metrics.get(f"{criterion}/mean", 0.0)
                    else:
                        # Fallback: calculate from row metrics
                        scores = [
                            row.get(criterion, 0.0)
                            for row in result.metrics_table
                            if criterion in row
                        ]
                        raw_score = sum(scores) / len(scores) if scores else 0.0

                    # Normalize to 0-1 scale if needed (Vertex AI uses 1-5)
                    normalized_score = raw_score / 5.0 if raw_score > 1.0 else raw_score

                    result_dict = {
                        "score": round(normalized_score, 4),
                        "count": len(dataset),
                    }

                    # Calculate pass rate if threshold is defined
                    if criterion in thresholds:
                        # For per-sample scores, calculate actual pass rate
                        if hasattr(result, "metrics_table"):
                            per_sample_scores = [
                                (
                                    row.get(criterion, 0.0) / 5.0
                                    if row.get(criterion, 0.0) > 1.0
                                    else row.get(criterion, 0.0)
                                )
                                for row in result.metrics_table
                                if criterion in row
                            ]
                            if per_sample_scores:
                                passed = sum(
                                    1 for s in per_sample_scores if s >= thresholds[criterion]
                                )
                                result_dict["pass_rate"] = round(passed / len(per_sample_scores), 4)
                        else:
                            # Fallback: binary pass/fail based on average
                            result_dict["pass_rate"] = (
                                1.0 if normalized_score >= thresholds[criterion] else 0.0
                            )

                    results[criterion] = result_dict

                    status = "✓" if normalized_score >= thresholds.get(criterion, 0.0) else "✗"
                    print(f"     {status} {criterion}: {normalized_score:.4f}")

                except Exception as e:
                    print(f"   ⚠️  {criterion} evaluation failed: {e}")
                    results[criterion] = {
                        "score": 0.0,
                        "count": len(dataset),
                        "error": str(e),
                    }

            return results

        except ImportError:
            print("   ⚠️  vertexai.preview.evaluation not available")
            return {
                criterion: {
                    "score": 0.0,
                    "count": len(dataset),
                    "error": "Vertex AI Evaluation SDK not installed",
                }
                for criterion in criteria
            }
        except Exception as e:
            print(f"   ⚠️  Criteria evaluation failed: {e}")
            return {
                criterion: {
                    "score": 0.0,
                    "count": len(dataset),
                    "error": str(e),
                }
                for criterion in criteria
            }

    # Note: export_results() removed - results are saved to BigQuery by RegressionTester
