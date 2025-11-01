"""
Dataset collection for agent evaluation.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from google.cloud import bigquery


class DatasetCollector:
    """Collects and stores agent interactions for evaluation datasets."""

    def __init__(
        self,
        project_id: str,
        agent_name: str,
        storage_location: Optional[str] = None,
    ):
        """Initialize dataset collector.

        Args:
            project_id: GCP project ID
            agent_name: Name of the agent
            storage_location: BigQuery table (project.dataset.table) or GCS bucket
        """
        self.project_id = project_id
        self.agent_name = agent_name

        # Default storage location
        if storage_location is None:
            storage_location = f"{project_id}.agent_evaluation.{agent_name}_eval_dataset"

        self.storage_location = storage_location

        # Initialize BigQuery client
        self.bq_client = bigquery.Client(project=project_id)

        # Create table if it doesn't exist
        self._ensure_table_exists()

        # In-memory buffer for batch writes
        self.buffer: List[Dict[str, Any]] = []
        self.buffer_size = 10  # Write every 10 samples

    def add_interaction(
        self,
        interaction_id: str,
        input_data: Any,
        output_data: Any,
        metadata: Optional[Dict[str, Any]] = None,
        trajectory: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Add an interaction to the test dataset.

        The agent's response is stored as the reference (ground truth).
        Users can review and update the reference in BigQuery if needed.

        Args:
            interaction_id: Unique ID for this interaction
            input_data: User input/prompt
            output_data: Agent response (saved as reference/ground truth)
            metadata: Additional metadata (tokens, model, etc.)
            trajectory: List of intermediate steps (tool calls, reasoning, etc.)
        """
        # Serialize input and output
        instruction = self._serialize(input_data)
        response = self._serialize(output_data)

        # Create dataset entry (Gen AI Evaluation Service compatible)
        entry = {
            "interaction_id": interaction_id,
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            # Gen AI Evaluation Service fields
            "instruction": instruction,  # User's question/prompt
            "reference": response,  # Agent's response becomes the reference (ground truth)
            "context": None,  # Optional: can be populated from metadata
            "reviewed": False,  # Flag to track manual review status
            # Additional debugging fields
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

    def _ensure_table_exists(self) -> None:
        """Create BigQuery table for test dataset if it doesn't exist."""
        # Schema for test dataset (stores test cases with ground truth)
        schema = [
            bigquery.SchemaField("interaction_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            # Test case fields
            bigquery.SchemaField("instruction", "STRING", mode="REQUIRED"),  # User query/prompt
            bigquery.SchemaField(
                "reference", "STRING", mode="REQUIRED"
            ),  # Ground truth (agent's response, can be updated after review)
            bigquery.SchemaField("context", "STRING", mode="NULLABLE"),  # Optional context
            bigquery.SchemaField("reviewed", "BOOLEAN", mode="NULLABLE"),  # Manual review flag
            # Additional fields for debugging
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
