#!/usr/bin/env python
"""
Standalone MCP Server for OpenFinance Contracts

This script runs the MCP server that provides tools and resources for
interacting with OpenFinance API contracts, including mock data generation
and correlation between different APIs.

Usage:
    python run_mcp_server.py [--specs-dir openfinance_specs] [--port 3000]
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.stdio import stdio_server

from app.mcp.openfinance_server import OpenFinanceMCPServer


async def main(specs_directory: str = "openfinance_specs") -> None:
    """Run the MCP server"""
    # Create MCP server instance
    mcp_server = OpenFinanceMCPServer(specs_directory)

    # Load contracts
    print("Loading OpenFinance contracts...")
    await mcp_server.load_contracts()

    # Get the MCP server
    server = mcp_server.get_server()

    # Run stdio server
    print("Starting MCP server on stdio...")
    print("Server ready to accept connections")

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run OpenFinance MCP Server")
    parser.add_argument(
        "--specs-dir",
        type=str,
        default="openfinance_specs",
        help="Directory containing OpenFinance specs",
    )

    args = parser.parse_args()

    try:
        asyncio.run(main(args.specs_dir))
    except KeyboardInterrupt:
        print("\nMCP server stopped")
    except Exception as e:
        print(f"Error running MCP server: {e}")
        sys.exit(1)
