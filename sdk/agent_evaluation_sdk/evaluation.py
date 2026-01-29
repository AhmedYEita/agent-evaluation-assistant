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
        model_name: str = "gemini-2.5-flash",
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
        """Run evaluation on dataset using specified metrics and criteria.

        Args:
            dataset: List of test cases with instruction, reference, response
            metrics: List of metrics to compute (e.g., ["bleu", "rouge"])
            criteria: List of criteria for model-based evaluation
            thresholds: Optional dict of minimum scores for pass/fail (0-1 scale)

        Returns:
            Evaluation results dictionary
        """
        if not dataset:
            return {
                "dataset_size": 0,
                "metrics": {},
                "criteria_scores": {},
                "trajectory_stats": {},
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
            ]
        if thresholds is None:
            thresholds = {}

        print(f"📊 Evaluating {len(dataset)} interactions...")
        print(f"   Metrics: {', '.join(metrics)}")
        print(f"   Criteria: {', '.join(criteria)}")
        if thresholds:
            print(f"   Thresholds: {thresholds}")

        # Run automated metrics
        results: Dict[str, Any] = {
            "dataset_size": len(dataset),
            "metrics": {},
            "criteria_scores": {},
            "trajectory_stats": {},
        }

        # Calculate automated metrics
        for metric in metrics:
            metric_result = self._calculate_metric(dataset, metric)
            if "error" not in metric_result and metric in thresholds:
                metric_result = self._add_pass_rate(metric_result, thresholds[metric], metric)
            results["metrics"][metric] = metric_result

        # Run model-based criteria evaluation
        if criteria:
            results["criteria_scores"] = self._evaluate_criteria(dataset, criteria, thresholds)

        # Analyze trajectory data if available
        results["trajectory_stats"] = self._analyze_trajectories(dataset)

        return results

    def _calculate_metric(self, dataset: List[Dict[str, Any]], metric_name: str) -> Dict[str, Any]:
        """Calculate automated metric using Vertex AI Evaluation.

        Args:
            dataset: List of test cases with 'reference' and 'response' fields
            metric_name: Metric to calculate (e.g., "bleu", "rouge")

        Returns:
            Dictionary with metric scores
        """
        print(f"   Computing {metric_name.upper()} scores...")

        try:
            import pandas as pd
            from vertexai.preview.evaluation import EvalTask

            # Prepare evaluation dataset as DataFrame
            # Note: Vertex AI expects 'response' column for BLEU/ROUGE
            eval_data = [
                {
                    "reference": item.get("reference", ""),
                    "response": item.get("response", ""),
                }
                for item in dataset
            ]
            eval_dataset = pd.DataFrame(eval_data)

            # Run evaluation
            eval_task = EvalTask(dataset=eval_dataset, metrics=[metric_name])  # type: ignore[arg-type,list-item]
            result = eval_task.evaluate()

            # Extract scores
            return self._extract_metric_scores(result, metric_name, len(dataset))

        except ImportError:
            print("   ⚠️  vertexai.preview.evaluation not available")
            return self._error_response(
                "Vertex AI Evaluation SDK not installed", len(dataset), metric_name
            )
        except Exception as e:
            print(f"   ⚠️  {metric_name.upper()} calculation failed: {e}")
            return self._error_response(str(e), len(dataset), metric_name)

    def _extract_metric_scores(self, result: Any, metric_name: str, count: int) -> Dict[str, Any]:
        """Extract scores from Vertex AI evaluation result.

        Args:
            result: Vertex AI evaluation result object
            metric_name: Name of the metric
            count: Number of test cases

        Returns:
            Dictionary with extracted scores
        """
        if metric_name == "bleu":
            score = 0.0
            if hasattr(result, "summary_metrics") and result.summary_metrics:
                score = result.summary_metrics.get("bleu/mean", 0.0)
            elif hasattr(result, "metrics_table") and result.metrics_table is not None:
                try:
                    import pandas as pd

                    if isinstance(result.metrics_table, pd.DataFrame):
                        metrics_dict = result.metrics_table.to_dict("records")
                        scores_list = [
                            row.get("bleu", 0.0) for row in metrics_dict if "bleu" in row
                        ]
                        score = sum(scores_list) / len(scores_list) if scores_list else 0.0
                except Exception:
                    pass
            return {"score": round(score, 4), "count": count}

        elif metric_name == "rouge":
            if hasattr(result, "summary_metrics") and result.summary_metrics:
                # Try different possible key formats
                rouge_l = result.summary_metrics.get(
                    "rougeL/mean", result.summary_metrics.get("rouge_l_sum/mean", 0.0)
                )
                rouge_1 = result.summary_metrics.get(
                    "rouge1/mean", result.summary_metrics.get("rouge_1_sum/mean", 0.0)
                )
                rouge_2 = result.summary_metrics.get(
                    "rouge2/mean", result.summary_metrics.get("rouge_2_sum/mean", 0.0)
                )
                return {
                    "rougeL": round(rouge_l, 4),
                    "rouge1": round(rouge_1, 4),
                    "rouge2": round(rouge_2, 4),
                    "count": count,
                }
            return {"rougeL": 0.0, "rouge1": 0.0, "rouge2": 0.0, "count": count}

        return {"score": 0.0, "count": count}

    def _error_response(self, error_msg: str, count: int, metric_name: str = "") -> Dict[str, Any]:
        """Create error response dictionary matching metric's expected format.

        Args:
            error_msg: Error message
            count: Number of test cases
            metric_name: Metric name ("rouge" has special format, others use "score")

        Returns:
            Error response dictionary matching the metric's structure
        """
        if metric_name == "rouge":
            # ROUGE returns multiple sub-scores
            return {
                "rougeL": 0.0,
                "rouge1": 0.0,
                "rouge2": 0.0,
                "count": count,
                "error": error_msg,
            }
        # BLEU and other metrics return a single score
        return {"score": 0.0, "count": count, "error": error_msg}

    def _add_pass_rate(
        self, metric_result: Dict[str, Any], threshold: float, metric_name: str
    ) -> Dict[str, Any]:
        """Add pass rate to metric result based on threshold.

        Args:
            metric_result: Metric result dictionary
            threshold: Threshold value for pass/fail
            metric_name: Name of the metric

        Returns:
            Updated metric result with pass_rate
        """
        if metric_name == "rouge":
            score = metric_result.get("rougeL", 0.0)
        else:
            score = metric_result.get("score", 0.0)

        pass_rate = 1.0 if score >= threshold else 0.0
        return {**metric_result, "pass_rate": pass_rate}

    def _evaluate_criteria(
        self,
        dataset: List[Dict[str, Any]],
        criteria: List[str],
        thresholds: Optional[Dict[str, float]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Evaluate dataset using model-based criteria.

        Args:
            dataset: List of test cases with instruction, reference, response
            criteria: List of criteria names to evaluate
            thresholds: Optional dict of minimum scores for pass/fail

        Returns:
            Dictionary mapping criterion name to evaluation results
        """
        thresholds = thresholds or {}
        print(f"   Evaluating {len(criteria)} criteria using {self.model_name}...")

        try:
            from vertexai.preview.evaluation import EvalTask  # noqa: F401
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

        # Prepare evaluation dataset as DataFrame
        import pandas as pd

        eval_data = []
        for item in dataset:
            # Build enhanced context with trajectory info
            context = item.get("context", "")
            trajectory = item.get("trajectory")
            
            # If trajectory exists, add it to context for model-based evaluation
            if trajectory:
                import json
                try:
                    # Parse trajectory if it's a string
                    if isinstance(trajectory, str):
                        trajectory = json.loads(trajectory)
                    
                    # Format trajectory as readable text for the evaluator
                    if isinstance(trajectory, list) and len(trajectory) > 0:
                        tool_summary = []
                        for step in trajectory:
                            if isinstance(step, dict) and step.get("tool_name"):
                                tool_name = step["tool_name"]
                                duration = step.get("duration_ms", "?")
                                error = step.get("error")
                                status = " (FAILED)" if error else ""
                                tool_summary.append(f"- {tool_name} ({duration}ms){status}")
                        
                        if tool_summary:
                            trajectory_text = "Tool calls:\n" + "\n".join(tool_summary)
                            # Append trajectory to context
                            context = f"{context}\n\n{trajectory_text}" if context else trajectory_text
                except (json.JSONDecodeError, TypeError):
                    pass  # Skip if trajectory can't be parsed

            eval_data.append({
                "prompt": item.get("instruction", ""),
                "context": context,  # Now includes trajectory info
                "reference": item.get("reference", ""),
                "response": item.get("response", ""),
            })
        
        eval_dataset = pd.DataFrame(eval_data)

        valid_criteria = {
            "coherence",
            "fluency",
            "safety",
            "groundedness",
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

            results[criterion] = self._evaluate_single_criterion(
                eval_dataset, criterion, len(dataset), thresholds.get(criterion)
            )

        return results

    def _evaluate_single_criterion(
        self,
        eval_dataset: List[Dict[str, Any]],
        criterion: str,
        count: int,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Evaluate a single criterion using Vertex AI.

        Args:
            eval_dataset: Prepared evaluation dataset
            criterion: Criterion name to evaluate
            count: Number of test cases
            threshold: Optional threshold for pass/fail

        Returns:
            Evaluation result dictionary
        """
        try:
            from vertexai.preview.evaluation import EvalTask

            eval_task = EvalTask(dataset=eval_dataset, metrics=[criterion])  # type: ignore[arg-type,list-item]
            # Don't pass model parameter when dataset has 'response' column (BYOR mode)
            result = eval_task.evaluate()  # type: ignore[arg-type]

            # Extract and normalize score (Vertex AI uses 1-5 scale)
            raw_score = self._extract_raw_score(result, criterion)
            normalized_score = raw_score / 5.0 if raw_score > 1.0 else raw_score

            result_dict: Dict[str, Any] = {
                "score": round(normalized_score, 4),
                "count": count,
            }

            # Add pass rate if threshold is defined
            if threshold is not None:
                result_dict["pass_rate"] = self._calculate_pass_rate(result, criterion, threshold)

            status = "✓" if normalized_score >= (threshold or 0.0) else "✗"
            print(f"     {status} {criterion}: {normalized_score:.4f}")

            return result_dict

        except Exception as e:
            print(f"   ⚠️  {criterion} evaluation failed: {e}")
            return {"score": 0.0, "count": count, "error": str(e)}

    def _extract_raw_score(self, result: Any, criterion: str) -> float:
        """Extract raw score from Vertex AI result.

        Args:
            result: Vertex AI evaluation result
            criterion: Criterion name

        Returns:
            Raw score value
        """
        if hasattr(result, "summary_metrics") and result.summary_metrics:
            return float(result.summary_metrics.get(f"{criterion}/mean", 0.0))

        if hasattr(result, "metrics_table") and result.metrics_table is not None:
            # metrics_table is a DataFrame, convert to dict records
            try:
                import pandas as pd

                if isinstance(result.metrics_table, pd.DataFrame):
                    metrics_dict = result.metrics_table.to_dict("records")
                    scores_list = [
                        row.get(criterion, 0.0) for row in metrics_dict if criterion in row
                    ]
                    return sum(scores_list) / len(scores_list) if scores_list else 0.0
            except Exception:
                pass

        return 0.0

    def _calculate_pass_rate(self, result: Any, criterion: str, threshold: float) -> float:
        """Calculate pass rate based on threshold.

        Args:
            result: Vertex AI evaluation result
            criterion: Criterion name
            threshold: Threshold value

        Returns:
            Pass rate (0.0 to 1.0)
        """
        if hasattr(result, "metrics_table") and result.metrics_table is not None:
            try:
                import pandas as pd

                if isinstance(result.metrics_table, pd.DataFrame):
                    metrics_dict = result.metrics_table.to_dict("records")
                    per_sample_scores = [
                        (
                            row.get(criterion, 0.0) / 5.0
                            if row.get(criterion, 0.0) > 1.0
                            else row.get(criterion, 0.0)
                        )
                        for row in metrics_dict
                        if criterion in row
                    ]
                    if per_sample_scores:
                        passed = sum(1 for s in per_sample_scores if s >= threshold)
                        return round(passed / len(per_sample_scores), 4)
            except Exception:
                pass

        # Fallback: binary pass/fail based on average
        raw_score = self._extract_raw_score(result, criterion)
        normalized_score = raw_score / 5.0 if raw_score > 1.0 else raw_score
        return 1.0 if normalized_score >= threshold else 0.0

    def _analyze_trajectories(self, dataset: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze trajectory data from dataset.

        Args:
            dataset: List of test cases, may contain trajectory field

        Returns:
            Dictionary with trajectory statistics
        """
        import json

        trajectories_found = 0
        total_tool_calls = 0
        tool_counts: Dict[str, int] = {}
        tool_durations: Dict[str, List[float]] = {}
        interactions_with_tools = 0
        interactions_with_errors = 0

        for item in dataset:
            # Try to parse trajectory (might be JSON string or already parsed)
            trajectory = item.get("trajectory")
            if not trajectory:
                continue

            # Parse if it's a JSON string
            if isinstance(trajectory, str):
                try:
                    trajectory = json.loads(trajectory)
                except (json.JSONDecodeError, TypeError):
                    continue

            if not isinstance(trajectory, list) or len(trajectory) == 0:
                continue

            trajectories_found += 1
            has_tools = False

            for step in trajectory:
                if not isinstance(step, dict):
                    continue

                tool_name = step.get("tool_name")
                if tool_name:
                    has_tools = True
                    total_tool_calls += 1
                    tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

                    # Track duration
                    duration_ms = step.get("duration_ms")
                    if duration_ms is not None:
                        if tool_name not in tool_durations:
                            tool_durations[tool_name] = []
                        tool_durations[tool_name].append(duration_ms)

                    # Check for errors
                    if step.get("error"):
                        interactions_with_errors += 1

            if has_tools:
                interactions_with_tools += 1

        if trajectories_found == 0:
            return {
                "available": False,
                "message": "No trajectory data found in dataset"
            }

        # Calculate average durations
        avg_durations = {
            tool: round(sum(durations) / len(durations), 2)
            for tool, durations in tool_durations.items()
        }

        stats = {
            "available": True,
            "interactions_with_trajectory": trajectories_found,
            "interactions_with_tools": interactions_with_tools,
            "total_tool_calls": total_tool_calls,
            "avg_tools_per_interaction": round(total_tool_calls / interactions_with_tools, 2) if interactions_with_tools > 0 else 0,
            "tool_usage_counts": tool_counts,
            "avg_tool_duration_ms": avg_durations,
            "interactions_with_errors": interactions_with_errors,
        }

        print(f"\n🔧 Trajectory Analysis:")
        print(f"   Interactions with tools: {interactions_with_tools}/{trajectories_found}")
        print(f"   Total tool calls: {total_tool_calls}")
        if tool_counts:
            print(f"   Tool usage: {tool_counts}")
        if interactions_with_errors > 0:
            print(f"   ⚠️  Tool errors: {interactions_with_errors}")

        return stats
