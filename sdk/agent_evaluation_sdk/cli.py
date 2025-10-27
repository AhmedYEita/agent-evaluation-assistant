"""
CLI tool for agent evaluation management.
"""

import argparse
import sys


def export_dataset(args):
    """Export collected dataset to JSON file."""
    from agent_evaluation_sdk.dataset import DatasetCollector

    collector = DatasetCollector(
        project_id=args.project_id,
        agent_name=args.agent_name,
    )

    collector.export_dataset(
        output_path=args.output,
        start_date=args.start_date,
        end_date=args.end_date,
        limit=args.limit,
    )


def view_logs(args):
    """View recent logs for an agent."""
    import subprocess

    filter_expr = f'resource.labels.agent_name="{args.agent_name}"'

    cmd = [
        "gcloud", "logging", "read",
        filter_expr,
        f"--project={args.project_id}",
        f"--limit={args.limit}",
        "--format=json",
    ]

    subprocess.run(cmd)


def view_dashboard(args):
    """Open Cloud Monitoring dashboard for an agent."""
    import subprocess

    cmd = [
        "gcloud", "monitoring", "dashboards", "list",
        f'--filter=displayName:"{args.agent_name}"',
        f"--project={args.project_id}",
    ]

    subprocess.run(cmd)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agent Evaluation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Export dataset command
    export_parser = subparsers.add_parser(
        "export-dataset",
        help="Export collected interactions to JSON file"
    )
    export_parser.add_argument("--project-id", required=True, help="GCP project ID")
    export_parser.add_argument("--agent-name", required=True, help="Agent name")
    export_parser.add_argument("--output", required=True, help="Output JSON file path")
    export_parser.add_argument("--start-date", help="Start date (ISO format)")
    export_parser.add_argument("--end-date", help="End date (ISO format)")
    export_parser.add_argument("--limit", type=int, help="Max number of interactions")
    export_parser.set_defaults(func=export_dataset)

    # View logs command
    logs_parser = subparsers.add_parser(
        "logs",
        help="View recent logs for an agent"
    )
    logs_parser.add_argument("--project-id", required=True, help="GCP project ID")
    logs_parser.add_argument("--agent-name", required=True, help="Agent name")
    logs_parser.add_argument("--limit", type=int, default=50, help="Number of log entries")
    logs_parser.set_defaults(func=view_logs)

    # View dashboard command
    dashboard_parser = subparsers.add_parser(
        "dashboard",
        help="List dashboards for an agent"
    )
    dashboard_parser.add_argument("--project-id", required=True, help="GCP project ID")
    dashboard_parser.add_argument("--agent-name", required=True, help="Agent name")
    dashboard_parser.set_defaults(func=view_dashboard)

    # Parse and execute
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()

