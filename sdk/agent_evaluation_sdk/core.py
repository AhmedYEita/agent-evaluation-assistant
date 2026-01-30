"""Core evaluation wrapper for agents with automatic instrumentation."""

import asyncio
import atexit
import functools
import inspect
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Callable, Dict

from agent_evaluation_sdk.config import EvaluationConfig
from agent_evaluation_sdk.dataset import DatasetCollector
from agent_evaluation_sdk.logging import CloudLogger
from agent_evaluation_sdk.metrics import CloudMetrics
from agent_evaluation_sdk.tracing import CloudTracer


class EvaluationWrapper:
    """Wraps ADK agents with evaluation capabilities. Supports all ADK methods automatically."""

    def __init__(self, agent: Any, config: EvaluationConfig):
        self.agent = agent
        self.config = config
        self.logger = (
            CloudLogger(config.project_id, config.agent_name, config.logging.level)
            if config.logging.enabled
            else None
        )
        self.tracer = (
            CloudTracer(config.project_id, config.agent_name) if config.tracing.enabled else None
        )
        self.metrics = (
            CloudMetrics(config.project_id, config.agent_name) if config.metrics.enabled else None
        )
        self.dataset_collector = (
            DatasetCollector(
                config.project_id,
                config.agent_name,
                config.dataset.storage_location,
                config.dataset.buffer_size,
            )
            if config.dataset.auto_collect
            else None
        )

        self._trace_context = threading.local()
        max_workers = getattr(config, "executor_workers", 4)
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="eval_bg_")
        self._shutdown_called = False
        self._original_methods: Dict[str, Callable] = {}
        self._tool_traces = threading.local()  # Track tool calls for trajectories per thread
        atexit.register(self._shutdown)
        self._wrap_agent()

        print(f"✅ Evaluation enabled for agent: {config.agent_name}")
        print(f"   - Logging: {'Enabled' if config.logging.enabled else 'Disabled'}")
        print(f"   - Tracing: {'Enabled' if config.tracing.enabled else 'Disabled'}")
        print(f"   - Metrics: {'Enabled' if config.metrics.enabled else 'Disabled'}")
        print(f"   - Dataset: {'Enabled' if config.dataset.auto_collect else 'Disabled'}")

    def _wrap_agent(self) -> None:
        methods = [
            m for m in ["generate_content", "run_async", "run", "invoke"] if hasattr(self.agent, m)
        ]
        if not methods:
            raise ValueError(
                "Agent must have at least one of: generate_content, run, run_async, or invoke"
            )

        # Check if agent is a Pydantic model
        try:
            from pydantic import BaseModel

            is_pydantic = isinstance(self.agent, BaseModel)
        except ImportError:
            is_pydantic = False

        for method_name in methods:
            original = getattr(self.agent, method_name)
            # Check if it's an async generator function
            is_async_gen = inspect.isasyncgenfunction(original)
            if method_name == "run_async" or asyncio.iscoroutinefunction(original):
                wrapper = (
                    self._wrap_async_generator(original)
                    if is_async_gen
                    else self._wrap_async_method(original)
                )
            else:
                wrapper = self._wrap_sync_method(original)
            self._original_methods[method_name] = original

            # Use object.__setattr__ to bypass Pydantic validation for Pydantic models
            if is_pydantic:
                object.__setattr__(self.agent, method_name, wrapper)
            else:
                setattr(self.agent, method_name, wrapper)

    def _wrap_async_generator(self, original_method: Callable) -> Callable:
        """Wrap an async generator method (e.g., runner.run_async)."""

        @functools.wraps(original_method)
        async def wrapped(*args, **kwargs):
            interaction_id = str(uuid.uuid4())
            
            # Initialize trajectory tracking for this interaction
            if self.config.logging.include_trajectories:
                self._tool_traces.traces = []
            
            # Extract input from new_message Content object
            input_data = ""
            if kwargs.get("new_message"):
                msg = kwargs["new_message"]
                if hasattr(msg, "parts") and msg.parts:
                    input_data = " ".join(
                        part.text for part in msg.parts if hasattr(part, "text") and part.text
                    )
                elif hasattr(msg, "text"):
                    input_data = msg.text
            elif args:
                input_data = str(args[0])

            trace_id, parent_span_id = None, None
            if self.tracer:
                trace_id = self.tracer.generate_trace_id()
                parent_span_id = uuid.uuid4().hex[:16]
                # Set trace context BEFORE calling the generator so tools can access it
                self._trace_context.context = (trace_id, parent_span_id)

            try:
                start = time.time()
                final_response = None

                async for item in original_method(*args, **kwargs):
                    final_response = item
                    yield item

                duration_ms = (time.time() - start) * 1000
                output_data = self._extract_output(final_response) if final_response else ""
                metadata = self._extract_metadata(final_response) if final_response else {}

                # Get trajectory if tracking is enabled
                trajectory = None
                if self.config.logging.include_trajectories and hasattr(self._tool_traces, 'traces'):
                    trajectory = self._tool_traces.traces if self._tool_traces.traces else None

                if not self._shutdown_called:
                    self._submit_observability(
                        trace_id,
                        parent_span_id,
                        interaction_id,
                        input_data,
                        output_data,
                        duration_ms,
                        metadata,
                        start,
                        trajectory=trajectory,
                    )
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                error_msg = str(e)
                if not self._shutdown_called:
                    self._submit_observability(
                        trace_id,
                        parent_span_id,
                        interaction_id,
                        input_data,
                        f"ERROR: {error_msg}",
                        duration_ms,
                        {"error": True, "error_type": type(e).__name__},
                        start,
                        is_error=True,
                    )
                raise
            finally:
                if self.tracer:
                    self._trace_context.context = None

        return wrapped

    def _wrap_async_method(self, original_method: Callable) -> Callable:
        @functools.wraps(original_method)
        async def wrapped(*args, **kwargs):
            interaction_id = str(uuid.uuid4())

            # Initialize trajectory tracking for this interaction
            if self.config.logging.include_trajectories:
                self._tool_traces.traces = []

            input_data = (
                args[0]
                if args
                else kwargs.get("prompt")
                or kwargs.get("input")
                or kwargs.get("message")
                or kwargs.get("new_message")
                or ""
            )

            trace_id, parent_span_id = None, None
            if self.tracer:
                trace_id = self.tracer.generate_trace_id()
                parent_span_id = uuid.uuid4().hex[:16]
                self._trace_context.context = (trace_id, parent_span_id)

            try:
                start = time.time()
                response = await original_method(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000

                output_data = self._extract_output(response)
                metadata = self._extract_metadata(response)

                # Get trajectory if tracking is enabled
                trajectory = None
                if self.config.logging.include_trajectories and hasattr(
                    self._tool_traces, "traces"
                ):
                    trajectory = self._tool_traces.traces if self._tool_traces.traces else None
                    self._last_trajectory = trajectory.copy() if trajectory else None

                if not self._shutdown_called:
                    self._submit_observability(
                        trace_id,
                        parent_span_id,
                        interaction_id,
                        input_data,
                        output_data,
                        duration_ms,
                        metadata,
                        start,
                        trajectory=trajectory,
                    )

                return response
            except Exception as e:
                duration_ms = (time.time() - start) * 1000
                error_msg = str(e)
                if not self._shutdown_called:
                    self._submit_observability(
                        trace_id,
                        parent_span_id,
                        interaction_id,
                        input_data,
                        f"ERROR: {error_msg}",
                        duration_ms,
                        {"error": True, "error_type": type(e).__name__},
                        start,
                        is_error=True,
                    )
                raise
            finally:
                if self.tracer:
                    self._trace_context.context = None

        return wrapped

    def _wrap_sync_method(self, original_method: Callable) -> Callable:
        @functools.wraps(original_method)
        def wrapped(*args, **kwargs):
            interaction_id = str(uuid.uuid4())

            # Initialize trajectory tracking for this interaction
            if self.config.logging.include_trajectories:
                self._tool_traces.traces = []

            input_data = (
                args[0]
                if args
                else kwargs.get("prompt") or kwargs.get("input") or kwargs.get("message") or ""
            )

            trace_id, parent_span_id = None, None
            if self.tracer:
                trace_id = self.tracer.generate_trace_id()
                parent_span_id = uuid.uuid4().hex[:16]
                self._trace_context.context = (trace_id, parent_span_id)

            try:
                start = time.time()
                response = original_method(*args, **kwargs)
                duration_ms = (time.time() - start) * 1000

                output_data = self._extract_output(response)
                metadata = self._extract_metadata(response)

                # Get trajectory if tracking is enabled
                trajectory = None
                if self.config.logging.include_trajectories and hasattr(
                    self._tool_traces, "traces"
                ):
                    trajectory = self._tool_traces.traces if self._tool_traces.traces else None
                    self._last_trajectory = trajectory.copy() if trajectory else None

                if not self._shutdown_called:
                    self._submit_observability(
                        trace_id,
                        parent_span_id,
                        interaction_id,
                        input_data,
                        output_data,
                        duration_ms,
                        metadata,
                        start,
                        trajectory=trajectory,
                    )

                return response
            finally:
                if self.tracer:
                    self._trace_context.context = None

        return wrapped

    def _submit_observability(
        self,
        trace_id,
        parent_span_id,
        interaction_id,
        input_data,
        output_data,
        duration_ms,
        metadata,
        start,
        is_error=False,
        trajectory=None,
    ):
        def safe_submit(func, *args):
            try:
                self._executor.submit(func, *args)
            except RuntimeError:
                pass

        if self.tracer and trace_id:
            safe_submit(
                self._send_trace_spans,
                trace_id,
                parent_span_id,
                interaction_id,
                input_data,
                output_data,
                start,
                start + duration_ms / 1000,
                start,
                start,
            )

        if self.logger and self.config.logging.include_trajectories:
            safe_submit(
                self._send_log, interaction_id, input_data, output_data, duration_ms, metadata
            )

        if self.metrics:
            safe_submit(self._send_metrics, duration_ms, metadata, is_error)

        if self.dataset_collector:
            safe_submit(self._send_dataset, interaction_id, input_data, output_data, metadata, trajectory)

    def _send_trace_spans(
        self,
        trace_id,
        parent_span_id,
        interaction_id,
        input_data,
        output_data,
        llm_start,
        llm_end,
        extract_start,
        extract_end,
    ):
        try:
            query_preview, response_preview = str(input_data)[:200], str(output_data)[:200]
            attrs = {
                "interaction_id": interaction_id,
                "query": query_preview,
                "response": response_preview,
                "input_length": len(str(input_data)),
                "output_length": len(str(output_data)),
            }
            self.tracer._send_span(
                trace_id, parent_span_id, "agent.generate_content", llm_start, extract_end, attrs
            )
            self.tracer._send_span(
                trace_id,
                uuid.uuid4().hex[:16],
                "llm.generate",
                llm_start,
                llm_end,
                {"query": query_preview},
                parent_span_id,
            )
            self.tracer._send_span(
                trace_id,
                uuid.uuid4().hex[:16],
                "processing.extract",
                extract_start,
                extract_end,
                {},
                parent_span_id,
            )
        except Exception as e:
            print(f"Warning: Failed to send trace spans: {e}")

    def _send_log(self, interaction_id, input_data, output_data, duration_ms, metadata):
        try:
            self.logger.log_interaction(
                interaction_id, input_data, output_data, duration_ms, metadata
            )
        except Exception as e:
            print(f"Warning: Failed to send log: {e}")

    def _send_metrics(self, duration_ms, metadata, is_error=False):
        try:
            if is_error:
                error_type = metadata.get("error_type", "UnknownError")
                self.metrics.record_error(error_type)
            else:
                self.metrics.record_latency(duration_ms)
                self.metrics.record_success()
                if metadata.get("input_tokens") and metadata.get("output_tokens"):
                    self.metrics.record_token_count(
                        metadata["input_tokens"], metadata["output_tokens"]
                    )
        except Exception as e:
            print(f"Warning: Failed to send metrics: {e}")

    def _send_dataset(self, interaction_id, input_data, output_data, metadata, trajectory=None):
        try:
            self.dataset_collector.add_interaction(
                interaction_id, input_data, output_data, metadata, trajectory
            )
        except Exception as e:
            print(f"Warning: Failed to add dataset entry: {e}")

    def _extract_output(self, response):
        if isinstance(response, str):
            return response
        if hasattr(response, "text"):
            return response.text
        # Handle ADK event objects (events have content.parts)
        if hasattr(response, "content"):
            content = response.content
            if hasattr(content, "parts") and content.parts:
                # Extract text from all text parts
                texts = []
                for part in content.parts:
                    if hasattr(part, "text") and part.text:
                        texts.append(part.text)
                if texts:
                    return " ".join(texts)
            if isinstance(content, str):
                return content
            return getattr(content, "text", "")
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content"):
                if hasattr(candidate.content, "parts"):
                    return " ".join(
                        part.text for part in candidate.content.parts if hasattr(part, "text")
                    )
                return getattr(candidate.content, "text", "")
        if isinstance(response, dict):
            for key in ["output", "response", "text", "content", "message"]:
                if key in response:
                    return str(response[key])
        return str(response)

    def _extract_metadata(self, response):
        metadata = {}
        if hasattr(response, "usage_metadata"):
            usage = response.usage_metadata
            metadata["input_tokens"] = getattr(usage, "prompt_token_count", None)
            metadata["output_tokens"] = getattr(usage, "candidates_token_count", None)
            metadata["total_tokens"] = getattr(usage, "total_token_count", None)
        if isinstance(response, dict) and "metadata" in response:
            metadata.update(response["metadata"])
        if hasattr(response, "prompt_token_count"):
            metadata["input_tokens"] = response.prompt_token_count
        if hasattr(response, "candidates_token_count"):
            metadata["output_tokens"] = response.candidates_token_count
        if hasattr(response, "total_token_count"):
            metadata["total_tokens"] = response.total_token_count
        if hasattr(response, "model"):
            metadata["model"] = response.model
        elif isinstance(response, dict) and "model" in response:
            metadata["model"] = response["model"]
        return {k: v for k, v in metadata.items() if v is not None}

    def flush(self):
        if self.dataset_collector:
            self.dataset_collector.flush()

    def shutdown(self):
        """Public method for graceful shutdown.

        Flushes pending data and shuts down background threads.
        """
        if self._shutdown_called:
            return
        self._shutdown_called = True
        try:
            self._executor.shutdown(wait=True, timeout=10.0)
            self.flush()
        except Exception:
            pass

    def _shutdown(self):
        """Private method for internal use (atexit, __del__)."""
        self.shutdown()

    def tool_trace(self, tool_name):
        def decorator(func):
            @functools.wraps(func)
            def wrapped(*args, **kwargs):
                trace_context = getattr(self._trace_context, "context", None)
                start = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start) * 1000
                    
                    # Add to trajectory if tracking is enabled
                    if self.config.logging.include_trajectories and hasattr(self._tool_traces, 'traces'):
                        tool_entry = {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "duration_ms": round(duration_ms, 2),
                            "timestamp": time.time()
                        }
                        self._tool_traces.traces.append(tool_entry)
                    
                    # Send to tracer if available
                    if self.tracer and trace_context and not self._shutdown_called:
                        trace_id, parent_span_id = trace_context
                        try:
                            self._executor.submit(
                                self._send_tool_span,
                                trace_id,
                                parent_span_id,
                                tool_name,
                                start,
                                time.time(),
                                None,
                            )
                        except RuntimeError:
                            pass
                    return result
                    
                except Exception as e:
                    duration_ms = (time.time() - start) * 1000
                    
                    # Add error to trajectory if tracking is enabled
                    if self.config.logging.include_trajectories and hasattr(self._tool_traces, 'traces'):
                        tool_entry = {
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "duration_ms": round(duration_ms, 2),
                            "timestamp": time.time(),
                            "error": str(e)
                        }
                        self._tool_traces.traces.append(tool_entry)
                    
                    # Send error to tracer if available
                    if self.tracer and trace_context and not self._shutdown_called:
                        trace_id, parent_span_id = trace_context
                        try:
                            self._executor.submit(
                                self._send_tool_span,
                                trace_id,
                                parent_span_id,
                                tool_name,
                                start,
                                time.time(),
                                e,
                            )
                        except RuntimeError:
                            pass
                    raise

            return wrapped

        return decorator

    def _send_tool_span(
        self, trace_id, parent_span_id, tool_name, start_time, end_time, error=None
    ):
        try:
            attrs = (
                {
                    "error": True,
                    "error.type": type(error).__name__,
                    "error.message": str(error)[:256],
                }
                if error
                else {}
            )
            self.tracer._send_span(
                trace_id,
                uuid.uuid4().hex[:16],
                f"tool.{tool_name}",
                start_time,
                end_time,
                attrs,
                parent_span_id,
            )
        except Exception as e:
            print(f"Warning: Failed to send tool span: {e}")

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to the wrapped agent."""
        return getattr(self.agent, name)

    def __del__(self):
        try:
            self._shutdown()
        except Exception:
            pass


def enable_evaluation(agent, project_id, agent_name, config_path=None):
    if config_path:
        config = EvaluationConfig.from_yaml(Path(config_path))
        config.project_id = project_id
        config.agent_name = agent_name
    else:
        config = EvaluationConfig.default(project_id=project_id, agent_name=agent_name)
    return EvaluationWrapper(agent, config)
