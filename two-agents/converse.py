#!/usr/bin/env python3
"""Minimal two-agent conversation loop over a local Ollama endpoint."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path(__file__).with_name("config.json")


def load_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def chat(
    base_url: str,
    model: str,
    system_prompt: str,
    messages: list[dict[str, str]],
    timeout: float = 120.0,
) -> str:
    """Call Ollama /api/chat (non-streaming) and return assistant text."""
    payload = {
        "model": model,
        "stream": False,
        "messages": [{"role": "system", "content": system_prompt}, *messages],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise SystemExit(
            f"Could not reach Ollama at {base_url}: {exc}\n"
            "Is Ollama running? Try: ollama serve"
        ) from exc

    message = body.get("message") or {}
    content = message.get("content")
    if not content:
        raise SystemExit(f"Unexpected Ollama response: {body!r}")
    return content.strip()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run a short conversation between two local LLM agents via Ollama."
    )
    p.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help=f"Path to JSON config (default: {DEFAULT_CONFIG.name})",
    )
    p.add_argument("--model", help="Override model name (e.g. llama3.2, qwen2.5:7b)")
    p.add_argument(
        "--base-url",
        help="Override Ollama base URL (default from config: http://localhost:11434)",
    )
    p.add_argument("--turns", type=int, help="Number of full A↔B rounds")
    p.add_argument("--topic", help="Opening user topic / seed prompt")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    cfg = load_config(args.config)

    agents = cfg.get("agents") or []
    if len(agents) != 2:
        raise SystemExit("config.agents must contain exactly two agents")

    base_url = args.base_url or cfg.get("ollama_base_url") or "http://localhost:11434"
    model = args.model or cfg.get("model") or "llama3.2"
    turns = args.turns if args.turns is not None else int(cfg.get("turns") or 3)
    topic = args.topic or cfg.get("topic") or "Say hello and introduce your role."

    if turns < 1:
        raise SystemExit("--turns must be >= 1")

    a, b = agents[0], agents[1]
    transcript: list[dict[str, str]] = [{"role": "user", "content": topic}]

    print(f"Model: {model}")
    print(f"Endpoint: {base_url}")
    print(f"Agents: {a['name']} ↔ {b['name']}  ({turns} turn(s))")
    print(f"Topic: {topic}\n")
    print("=" * 60)

    for i in range(1, turns + 1):
        for agent in (a, b):
            reply = chat(base_url, model, agent["system_prompt"], transcript)
            labeled = f"[{agent['name']}] {reply}"
            print(f"\n--- Turn {i} · {agent['name']} ---\n{reply}\n")
            # Shared history: each agent sees prior messages as a flat chat log.
            transcript.append({"role": "assistant", "content": labeled})

    print("=" * 60)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
