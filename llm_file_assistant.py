"""Command-line resume assistant that lets an OpenAI model call local file tools."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable
from typing import Any

from openai import OpenAI, OpenAIError

from fs_tools import list_files, read_file, search_in_file, write_file


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Extract text and metadata from a PDF, TXT, or DOCX resume.",
            "parameters": {
                "type": "object",
                "properties": {"filepath": {"type": "string"}},
                "required": ["filepath"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files directly inside a directory, optionally filtered by extension.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory": {"type": "string"},
                    "extension": {"type": ["string", "null"]},
                },
                "required": ["directory"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write UTF-8 text to a file, creating parent directories.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["filepath", "content"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_in_file",
            "description": "Search a resume for a case-insensitive keyword and return surrounding context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string"},
                    "keyword": {"type": "string"},
                },
                "required": ["filepath", "keyword"],
                "additionalProperties": False,
            },
        },
    },
]

Tool = Callable[..., Any]
TOOLS: dict[str, Tool] = {
    "read_file": read_file,
    "list_files": list_files,
    "write_file": write_file,
    "search_in_file": search_in_file,
}


def run_assistant(
    query: str,
    client: OpenAI,
    model: str,
    max_tool_rounds: int = 8,
) -> str:
    """Send a query and execute the model's requested tools until it responds."""
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": (
                "You are a helpful resume-file assistant. Use the provided file "
                "tools whenever the user asks you to inspect, find, or create files. "
                "For requests about all resumes in a folder, list the folder and "
                "read relevant files. Summarize tool results accurately, and state "
                "when a file operation fails. Do not claim an operation succeeded "
                "unless its tool result confirms success."
            ),
        },
        {"role": "user", "content": query},
    ]

    for round_index in range(max_tool_rounds + 1):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )
        message = response.choices[0].message
        if not message.tool_calls:
            return message.content or ""
        if round_index == max_tool_rounds:
            break

        messages.append(message.model_dump(exclude_none=True))
        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
                tool = TOOLS[tool_name]
                result = tool(**arguments)
            except (json.JSONDecodeError, KeyError, TypeError) as exc:
                result = {"success": False, "error": f"Invalid tool call: {exc}"}
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError(
        f"The assistant exceeded the limit of {max_tool_rounds} tool rounds."
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Ask an OpenAI model to work with local resume files."
    )
    parser.add_argument(
        "query",
        nargs="*",
        help='Request, for example: "Find resumes mentioning Python in resumes"',
    )
    parser.add_argument(
        "--model",
        default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        help="OpenAI model name (default: OPENAI_MODEL or gpt-4o-mini)",
    )
    args = parser.parse_args()
    query = " ".join(args.query).strip()
    if not query:
        query = input("What would you like to do with your resume files? ").strip()
    if not query:
        print("Please provide a request.", file=sys.stderr)
        return 2
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "Set the OPENAI_API_KEY environment variable before running.",
            file=sys.stderr,
        )
        return 2

    try:
        answer = run_assistant(query, OpenAI(), args.model)
    except (OpenAIError, RuntimeError) as exc:
        print(f"Assistant request failed: {exc}", file=sys.stderr)
        return 1
    print(answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
