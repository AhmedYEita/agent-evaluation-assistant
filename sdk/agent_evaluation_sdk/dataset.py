"""
Dataset collection for agent evaluation.
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from google.cloud import bigquery


class DatasetCollector:
    """Collects and stores agent interactions for evaluation datasets."""

    def __init__(
        self,
        project_id: str,
        agent_name: str,
        storage_location: Optional[str] = None,
        buffer_size: int = 10,
    ):
        """Initialize dataset collector.

        Args:
            project_id: GCP project ID
            agent_name: Name of the agent
            storage_location: BigQuery table (project.dataset.table)
            buffer_size: Number of interactions to buffer before writing to BigQuery
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
        self.buffer_size = buffer_size
        self._retry_counts: Dict[str, int] = {}  # Track retry counts per entry
        self._max_retries = 3  # Maximum retries before discarding

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
            "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            # Gen AI Evaluation Service fields
            "instruction": instruction,  # User's question/prompt
            "reference": response,  # Agent's response becomes the reference (ground truth)
            "context": None,  # Optional: can be populated from metadata
            "reviewed": False,  # Flag to track manual review status
            # Additional fields (JSON type in BigQuery - no need to json.dumps)
            "metadata": metadata if metadata else None,
            "trajectory": trajectory if trajectory else None,
        }

        # Add to buffer
        self.buffer.append(entry)

        # Flush if buffer is full
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> None:
        """Write buffered interactions to storage using load job (supports UPDATE/DELETE)."""
        if not self.buffer:
            return

        # Save current buffer and clear it immediately to avoid race conditions
        buffer_to_write = self.buffer
        self.buffer = []

        try:
            # Ensure table exists before writing
            self._ensure_table_exists()

            # Write to temporary JSONL file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp_file:
                for entry in buffer_to_write:
                    json.dump(entry, tmp_file)
                    tmp_file.write("\n")
                tmp_path = tmp_file.name

            try:
                # Load data using load job (not streaming, supports UPDATE/DELETE)
                job_config = bigquery.LoadJobConfig(
                    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
                    write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
                    schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
                )

                with open(tmp_path, "rb") as source_file:
                    load_job = self.bq_client.load_table_from_file(
                        source_file, self.storage_location, job_config=job_config
                    )

                # Wait for job to complete (with timeout)
                load_job.result(timeout=60)

                if load_job.errors:
                    print(f"Warning: Errors loading data to BigQuery: {load_job.errors}")
                else:
                    # Successfully loaded data
                    num_rows = len(buffer_to_write)
                    print(
                        f"✅ Wrote {num_rows} interaction(s) to "
                        f"BigQuery table: {self.storage_location}"
                    )

            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)

        except Exception as e:
            print(f"Warning: Failed to write dataset entries: {e}")
            # Re-add failed entries to buffer for retry (with retry limit)
            for entry in buffer_to_write:
                entry_id = entry.get("interaction_id", str(id(entry)))
                retry_count = self._retry_counts.get(entry_id, 0)
                if retry_count < self._max_retries:
                    self._retry_counts[entry_id] = retry_count + 1
                    self.buffer.append(entry)
                else:
                    print(
                        f"Warning: Discarding entry {entry_id} "
                        f"after {self._max_retries} failed retries"
                    )

    def _ensure_table_exists(self) -> None:
        """Create BigQuery table for test dataset if it doesn't exist."""
        # Ensure dataset exists first
        dataset_id = self.storage_location.split(".")[1]
        dataset_ref = f"{self.project_id}.{dataset_id}"

        try:
            self.bq_client.get_dataset(dataset_ref)
        except Exception:
            # Dataset doesn't exist, create it
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            try:
                self.bq_client.create_dataset(dataset, exists_ok=True)
                print(f"Created BigQuery dataset: {dataset_ref}")
            except Exception:
                pass  # Dataset might have been created by another process

        # Schema for test dataset (stores test cases with ground truth)
        schema = [
            bigquery.SchemaField("interaction_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("agent_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            # Test case fields
            bigquery.SchemaField("instruction", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("reference", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("context", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("reviewed", "BOOLEAN", mode="NULLABLE"),
            # Additional fields for debugging
            bigquery.SchemaField("metadata", "JSON", mode="NULLABLE"),
            bigquery.SchemaField("trajectory", "JSON", mode="NULLABLE"),
        ]

        table = bigquery.Table(self.storage_location, schema=schema)

        # Set clustering for better query performance
        table.clustering_fields = ["agent_name", "timestamp"]

        # Check if table exists before trying to create it
        table_exists = False
        try:
            self.bq_client.get_table(self.storage_location)
            table_exists = True
        except Exception:
            pass

        if not table_exists:
            try:
                self.bq_client.create_table(table, exists_ok=True)
                print(f"Created BigQuery table: {self.storage_location}")
            except Exception:
                pass  # Table might have been created by another process

    def _serialize(self, data: Any) -> str:
        """Serialize data to JSON string."""
        if isinstance(data, str):
            return data
        return json.dumps(data, default=str)
