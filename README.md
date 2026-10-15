# mimOE minimal agent

A small command-line coding agent using mimOE Studio's local OpenAI-compatible API. Python standard library only. Inspired by DeepSeek Harness Minimal mode: a short system prompt, conversation history, one persistent Bash tool, and an agent loop.

```text
task -> local model -> bash command -> user approval -> result -> model -> ... -> answer
```

## Run

Requires macOS or Linux, Python 3.9+, Bash, and mimOE Studio with an instruction model loaded.

1. Install [mimOE Studio](https://developer.mimik.com/mimOE-studio-early-access-download-v2) and its bundled runtime. If the portal is unavailable, use the [official releases](https://github.com/mimik-mimOE/mimOE-Studio/releases).
2. In Model View, download a model if needed, click **Load**, then **API**. Copy the direct inference base URL, model ID and API key.
3. Configure your shell. For macOS zsh:

```zsh
export MIMOE_BASE_URL='http://127.0.0.1:8083/mimik-ai/openai/v1'
export MIMOE_MODEL='qwen2.5-coder-3b'
read -r -s 'MIMOE_API_KEY?mimOE API key: '; echo
export MIMOE_API_KEY
```

For Bash, use `read -r -s -p 'mimOE API key: ' MIMOE_API_KEY; echo` instead. `.env.example` documents the settings; the script does not load env files automatically.

```bash
python3 agent.py --check
mkdir -p /tmp/mimoe-demo
python3 agent.py --workspace /tmp/mimoe-demo \
  'Create hello.txt containing hello, then read it back to verify.'
```

Each command is displayed before execution. Enter `y` to run it; other answers decline. Omit the task to start an interactive session; `/exit` or Ctrl-D ends it. Shell variables, working directory and conversation history survive follow-up requests within the process. `--model` selects a loaded model; `--max-turns` sets the limit per task (default 8).

**Bash runs with your OS permissions. `--workspace` sets the starting directory; it is not a sandbox. Review commands and use a disposable directory.** The shell can access other files and the network. The inference API key and other inherited environment secrets are not passed to it, but this does not prevent access to credentials stored on disk.

## How it works

The model responds with one JSON action:

```json
{"tool":"bash","command":"ls"}
```

The host validates the action, asks for approval, executes it in a persistent Bash subprocess, and adds output and exit status to the conversation. The loop continues until the model returns:

```json
{"answer":"Created hello.txt and verified its contents."}
```

Malformed actions receive corrective feedback and consume a turn. Declined commands are not executed. A command timeout or output overflow terminates the shell process group and ends the session. Tool failures are returned to the model. Final answers are not verified by the host and can falsely claim success.

## Why this approach

- Raw HTTP makes the mimOE integration visible without framework setup. The base URL is local, not OpenAI's cloud API.
- Prompted JSON avoids depending on native function-calling support in the model. A single JSON code fence is accepted; the action schema remains strict. Smaller models may still fail the protocol.
- One Bash tool can inspect, edit and verify files. No separate editor, search stack, vector database, planning system or web interface is needed for this exercise.
- Inference accepts only loopback HTTP URLs, ignores proxy settings and rejects redirects. The shell has a separate capability boundary and is **not** network restricted.
- Each model request has a 120-second timeout and a 500-token output budget. Each command has a 30-second timeout and a 16,000-byte output limit. The default task budget is eight model turns. There is no context compaction or session persistence across restarts.

This borrows the minimal-loop concept, not the DeepSeek Harness implementation or its complete feature set. The [inspected upstream preset](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/web-app/presets/minimal.patch.yml) also includes capabilities such as image reading and context compaction. They are omitted here for the focused text-only assignment.

## Verify

```bash
python3 -m unittest discover -s tests -v
```

Tests cover approval rejection, action validation, tool feedback, turn limits, persistent shell state, timeout/output cleanup, credential environment filtering and the HTTP contract. They do not test general model competence. See [verification](docs/verification.md), [live run](docs/live-runs.txt), and the [short walkthrough](docs/walkthrough.md).

[Kubernetes evaluation](docs/kubernetes-evaluation/README.md): the 3B model completed a basic Deployment in a prepared namespace. Two broader tasks failed, including one false success report. All prompts, tool transcripts and independent checks are included.

Built with an AI coding assistant. The model runs locally through mimOE; no DeepSeek or OpenAI cloud API credential is required.
