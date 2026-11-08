"""Model Context Protocol (MCP) stdio server for Agentic Legal RAG."""

import json
import sys
from pathlib import Path
from typing import Any

from law2markdown.query import get_article, get_hierarchy, lookup_term, trace_references

TOOLS_DEFINITION = [
    {
        "name": "get_article",
        "description": (
            "法令識別子、条番号、項番号（任意）を指定して、"
            "該当条文または項の本文およびメタデータを取得します。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "law": {"type": "string", "description": "法令名または法令ID（例: 労働基準法）"},
                "article_num": {"type": "string", "description": "条番号（例: 1 または 第一条）"},
                "paragraph_num": {
                    "type": "integer",
                    "description": "（任意）特定項番号（例: 2 で第2項のみを取得）",
                },
            },
            "required": ["law", "article_num"],
        },
    },
    {
        "name": "get_hierarchy",
        "description": (
            "指定した条文が属する上位階層（編・章・節）および"
            "同一章・節に属する関連条文一覧を取得します。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "law": {"type": "string", "description": "法令名または法令ID"},
                "article_num": {"type": "string", "description": "条番号"},
            },
            "required": ["law", "article_num"],
        },
    },
    {
        "name": "trace_references",
        "description": (
            "指定した条文が参照している条文（outbound）または"
            "当該条文を参照している条文（inbound）をグラフ走査します。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "law": {"type": "string", "description": "法令名または法令ID"},
                "article_num": {"type": "string", "description": "条番号"},
                "direction": {
                    "type": "string",
                    "enum": ["outbound", "inbound", "both"],
                    "description": "走査方向（outbound: 参照先, inbound: 被参照元, both: 双方向）",
                    "default": "both",
                },
            },
            "required": ["law", "article_num"],
        },
    },
    {
        "name": "lookup_term",
        "description": (
            "指定した法令の用語定義レジストリから、"
            "専門用語の厳密な法的定義文および定義元条文を取得します。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "law": {"type": "string", "description": "法令名または法令ID"},
                "term": {
                    "type": "string",
                    "description": "調査対象の法的専門用語（例: 労働者, 賃金）",
                },
            },
            "required": ["law", "term"],
        },
    },
]


def handle_mcp_request(raw_json: str, kb_dir: str | Path = ".") -> str:
    """Process a single JSON-RPC 2.0 MCP request and return response string."""
    try:
        req = json.loads(raw_json)
    except Exception as e:
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {e}"},
            }
        )

    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "law2markdown-mcp", "version": "0.1.0"},
                },
            }
        )

    elif method == "tools/list":
        return json.dumps(
            {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": TOOLS_DEFINITION},
            }
        )

    elif method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        result_data: Any = None
        try:
            if tool_name == "get_article":
                result_data = get_article(
                    kb_dir=kb_dir,
                    law_title_or_id=args.get("law", ""),
                    article_num=args.get("article_num", ""),
                    paragraph_num=args.get("paragraph_num"),
                )
            elif tool_name == "get_hierarchy":
                result_data = get_hierarchy(
                    kb_dir=kb_dir,
                    law_title_or_id=args.get("law", ""),
                    article_num=args.get("article_num", ""),
                )
            elif tool_name == "trace_references":
                result_data = trace_references(
                    kb_dir=kb_dir,
                    law_title_or_id=args.get("law", ""),
                    article_num=args.get("article_num", ""),
                    direction=args.get("direction", "both"),
                )
            elif tool_name == "lookup_term":
                result_data = lookup_term(
                    kb_dir=kb_dir,
                    law_title_or_id=args.get("law", ""),
                    term=args.get("term", ""),
                )
            else:
                return json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": req_id,
                        "error": {"code": -32601, "message": f"Method/Tool not found: {tool_name}"},
                    }
                )

            # Format tool response
            if isinstance(result_data, dict) and result_data.get("body"):
                text_out = result_data["body"]
            else:
                text_out = json.dumps(result_data, ensure_ascii=False, indent=2)

            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": text_out}],
                        "structured": result_data,
                    },
                }
            )
        except Exception as e:
            return json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32000, "message": f"Execution error: {e}"},
                }
            )

    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Unknown method: {method}"},
        }
    )


def run_mcp_server(kb_dir: str | Path = ".") -> None:
    """Run MCP server over stdio."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = handle_mcp_request(line, kb_dir=kb_dir)
        sys.stdout.write(response + "\n")
        sys.stdout.flush()
