"""
Dataset collection for agent evaluation.
"""

import json
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import bigquery


class DatasetCollector:
    """Collects and stores agent interactions for evaluation datasets."""

    def __init__(
        self,
        project_id: str,
        agent_name: str,
        sample_rate: float = 0.1,
        storage_location: Optional[str] = None,
    ):
        """Initialize dataset collector.

        Args:
            project_id: GCP project ID
            agent_name: Name of the agent
            sample_rate: Fraction of interactions to collect (0.0 to 1.0)
            storage_location: BigQuery table (project.dataset.table) or GCS bucket
        """
        self.project_id = project_id
        self.agent_name = agent_name
        self.sample_rate = sample_rate

        # Default storage location
        if storage_location is None:
            storage_location = f"{project_id}.agent_evaluation.{agent_name}_interactions"

        self.storage_location = storage_location

        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=project_id)

        # Create table if it doesn't exist
        self._ensure_table_exists()

        # In-memory buffer for batch writes
        self.buffer: List[Dict[str, Any]] = []
        self.buffer_size = 10  # Write every 10 samples

    def should_collect(self) -> bool:
        """Determine if this interaction should be collected based on sample rate."""
        return random.random() < self.sample_rate

    def add_interaction(
        self,
        interaction_id: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        trajectory: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add an interaction to the dataset.

        Args:
            interaction_id: Unique ID for this interaction
            input_data: User input/prompt
            output_data: Agent response
            metadata: Additional metadata (tokens, model, etc.)
            trajectory: List of intermediate steps (tool calls, reasoning, etc.)
        """
        if not self.should_collect():
            return

        # Create dataset entry
        entry = {
            "interaction_id": interaction_id,
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "input": self._serialize(input_data),
            "output": self._serialize(output_data),
            "metadata": metadata or {},
            "trajectory": trajectory or [],
        }

        # Add to buffer
        self.buffer.append(entry)

        # Flush if buffer is full
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """Write buffered interactions to storage."""
        if not self.buffer:
            return

        try:
            # Write to BigQuery
            table_ref = self.bq_client.get_table(self.storage_location)
            errors = self.bq_client.insert_rows_json(table_ref, self.buffer)

            if errors:
                print(f"Warning: Errors inserting rows to BigQuery: {errors}")

            # Clear buffer
            self.buffer = []

        except Exception as e:
            print(f"Warning: Failed to write dataset entries: {e}")

    def export_dataset(
        self,
        output_path: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> None:
        """Export collected interactions to a JSON file.

        Args:
            output_path: Path to output JSON file
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            limit: Maximum number of interactions to export
        """
        # Build query
        query = f"""
            SELECT *
            FROM `{self.storage_location}`
            WHERE agent_name = @agent_name
        """

        if start_date:
            query += " AND timestamp >= @start_date"
        if end_date:
            query += " AND timestamp <= @end_date"

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        # Execute query
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("agent_name", "STRING", self.agent_name),
            ]
        )

        if start_date:
            job_config.query_parameters.append(
                bigquery.ScalarQueryParameter("start_date", "STRING", start_date)
            )
        if end_date:
            job_config.query_parameters.append(
                bigquery.ScalarQueryParameter("end_date", "STRING", end_date)
            )

        query_job = self.bq_client.query(query, job_config=job_config)
        results = query_job.result()

        # Write to file
        interactions = [dict(row) for row in results]
        with open(output_path, "w") as f:
            json.dump(interactions, f, indent=2, default=str)

        print(f"Exported {len(interactions)} interactions to {output_path}")

    def _ensure_table_exists(self) -> None:
        """Create BigQuery table if it doesn't exist."""
        schema = [
            bigquery.SchemaField("interaction_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("input", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("output", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("trajectory", "JSON", mode="NULLABLE"),
        ]

        table = bigquery.Table(self.storage_location, schema=schema)

        # Set clustering for better query performance
        table.clustering_fields = ["agent_name", "timestamp"]

        try:
            self.bq_client.create_table(table)
            print(f"Created BigQuery table: {self.storage_location}")
        except Exception:
            # Table might already exist
            pass

    def _serialize(self, data: Any) -> str:
        """Serialize data to JSON string."""
        if isinstance(data, str):
            return data
        return json.dumps(data, default=str)
