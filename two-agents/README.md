# Two-agent local LLM demo

Minimal Python loop: two named agents exchange messages for **N** turns through a local **Ollama** endpoint. No Docker, no cloud APIs, no agent frameworks.

**Hardware target:** MacBook Pro Apple Silicon (M5), 32GB — a ~3B–7B instruct model is a comfortable default.

## 1. Install Ollama

- Download: [https://ollama.com](https://ollama.com)
- Confirm the server is up (default `http://localhost:11434`):

```bash
ollama --version
# If needed: ollama serve
```

LM Studio also works if you expose a compatible local OpenAI-style API; this demo talks to Ollama’s `/api/chat` by default.

## 2. Pull a model

Default in `config.json` is **`llama3.2`** (small instruct, fine on 32GB):

```bash
ollama pull llama3.2
```

Stronger option on this machine (~7B):

```bash
ollama pull qwen2.5:7b
```

Then run with `--model qwen2.5:7b` or change `model` in `config.json`.

## 3. Run the two-agent demo

No third-party Python packages — stdlib only (Python 3.10+).

```bash
cd two-agents
python3 converse.py
```

Useful overrides:

```bash
python3 converse.py --turns 5
python3 converse.py --model qwen2.5:7b --topic "Design a tiny retrieval experiment."
python3 converse.py --base-url http://localhost:11434 --config ./config.json
```

## 4. Change roles / prompts

Edit `config.json`:

| Field | Meaning |
| --- | --- |
| `agents[0].name` / `agents[1].name` | Display names (e.g. Proposer, Critic) |
| `agents[i].system_prompt` | Role instructions for that agent |
| `topic` | Opening seed message |
| `turns` | Full A↔B rounds |
| `model` | Ollama model tag |
| `ollama_base_url` | Endpoint (default `http://localhost:11434`) |

Placeholder roles today: **Proposer** + **Critic**. Swap the names and `system_prompt` strings when you settle on real roles — no code change required.

CLI flags (`--model`, `--turns`, `--topic`, `--base-url`, `--config`) override the config file for a single run.

## How it works

1. Load two agents from config.
2. Seed a shared transcript with `topic`.
3. For each turn: Proposer replies → Critic replies (both via Ollama `/api/chat`).
4. Each reply is appended to the shared transcript so both agents see the history.

That is the whole v1 loop.
