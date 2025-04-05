#!/usr/bin/env python
"""Command-line utility for managing MCP server daemons."""

import argparse
import logging
import sys
from typing import Dict, List, Optional

from ollama_mcp_discord.utils.daemon_manager import DaemonManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def print_status(status: Dict[str, Dict[str, str]]):
    """Print daemon status information.

    Args:
        status: Status dictionary from DaemonManager
    """
    for name, info in status.items():
        running = info.get("running", "false").lower() == "true"
        status_str = "RUNNING" if running else "STOPPED"

        # Add PID if available
        if "pid" in info:
            status_str += f" (PID: {info['pid']})"

        print(f"{name.upper()}: {status_str}")
        print(f"  Command: {info.get('command', 'N/A')} {info.get('args', '')}")
        print(f"  PID File: {info.get('pid_file', 'N/A')}")
        print(f"  Log File: {info.get('log_file', 'N/A')}")
        print()


def main(args: Optional[List[str]] = None):
    """Run the command-line utility.

    Args:
        args: Command-line arguments (defaults to sys.argv[1:])
    """
    parser = argparse.ArgumentParser(description="Manage MCP server daemons")
    parser.add_argument("--config", help="Path to daemon configuration file")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Status command
    status_parser = subparsers.add_parser("status", help="Get daemon status")
    status_parser.add_argument("name", nargs="?", help="Name of the daemon")

    # Start command
    start_parser = subparsers.add_parser("start", help="Start daemon(s)")
    start_parser.add_argument("name", nargs="?", help="Name of the daemon")

    # Stop command
    stop_parser = subparsers.add_parser("stop", help="Stop daemon(s)")
    stop_parser.add_argument("name", nargs="?", help="Name of the daemon")

    # Restart command
    restart_parser = subparsers.add_parser("restart", help="Restart daemon(s)")
    restart_parser.add_argument("name", nargs="?", help="Name of the daemon")

    # Parse arguments
    args = parser.parse_args(args)

    # Initialize daemon manager
    manager = DaemonManager(config_path=args.config)

    # Execute command
    if args.command == "status":
        if args.name:
            if args.name not in manager.daemons:
                print(f"Error: Daemon '{args.name}' not found")
                return 1
            status = {args.name: manager.daemons[args.name].get_status()}
        else:
            status = manager.get_status_all()
        print_status(status)

    elif args.command == "start":
        if args.name:
            if args.name not in manager.daemons:
                print(f"Error: Daemon '{args.name}' not found")
                return 1
            success = manager.start_daemon(args.name)
            if success:
                print(f"Started daemon: {args.name}")
            else:
                print(f"Failed to start daemon: {args.name}")
                return 1
        else:
            results = manager.start_all()
            for name, success in results.items():
                if success:
                    print(f"Started daemon: {name}")
                else:
                    print(f"Failed to start daemon: {name}")

    elif args.command == "stop":
        if args.name:
            if args.name not in manager.daemons:
                print(f"Error: Daemon '{args.name}' not found")
                return 1
            success = manager.stop_daemon(args.name)
            if success:
                print(f"Stopped daemon: {args.name}")
            else:
                print(f"Failed to stop daemon: {args.name}")
                return 1
        else:
            results = manager.stop_all()
            for name, success in results.items():
                if success:
                    print(f"Stopped daemon: {name}")
                else:
                    print(f"Failed to stop daemon: {name}")

    elif args.command == "restart":
        if args.name:
            if args.name not in manager.daemons:
                print(f"Error: Daemon '{args.name}' not found")
                return 1
            success = manager.restart_daemon(args.name)
            if success:
                print(f"Restarted daemon: {args.name}")
            else:
                print(f"Failed to restart daemon: {args.name}")
                return 1
        else:
            results = manager.restart_all()
            for name, success in results.items():
                if success:
                    print(f"Restarted daemon: {name}")
                else:
                    print(f"Failed to restart daemon: {name}")

    else:
        parser.print_help()

    return 0


if __name__ == "__main__":
    sys.exit(main())
