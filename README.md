# Local Runbook Agent · mimOE

A small **BYO Framework** agent that helps troubleshoot a fictional service using local Markdown runbooks and a model served by **mimOE Studio**. Python standard library only; no pip install, cloud inference, or framework dependency.

The model chooses a search query, Python executes one read-only tool, and the model uses the returned evidence to suggest checks. The agent never executes remediation commands.

```text
Question → local model chooses search terms → search_runbooks
         → retrieved Markdown → local model writes checklist + sources
```

## Quick start

Requires Python 3.10+ and mimOE Studio with a loaded instruction model.

1. Install [mimOE Studio](https://developer.mimik.com/mimOE-studio-early-access-download-v2). If the portal is unavailable, the [official Studio releases](https://github.com/mimik-mimOE/mimOE-Studio/releases) provide installers. Install its bundled runtime and connect.
2. In **mimOE → Models**, pull a small instruction model if none is installed, then click **Load**. Tested with `HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF`, Q4_K_M, registered as `smollm2-1.7b`.
3. Click the loaded model's **API** button. Copy the **Inference base URL**, model ID, and API key. Use the direct inference endpoint for this exercise.
4. Configure the shell and run:

```bash
export MIMOE_BASE_URL='http://127.0.0.1:8083/mimik-ai/openai/v1'
export MIMOE_MODEL='smollm2-1.7b'
# Enter the API key from Studio without including it in shell history:
read -r -s -p 'mimOE API key: ' MIMOE_API_KEY; echo  # bash
export MIMOE_API_KEY

python3 agent.py --check
python3 agent.py --trace \
  'Our queue backlog is growing and consumer lag is increasing. What should I check before scaling consumers?'
```

On macOS's default **zsh**, replace the `read` line with:

```zsh
read -r -s 'MIMOE_API_KEY?mimOE API key: '; echo
```

The default base URL is the one above. `MIMOE_MODEL` can be omitted if exactly one model is loaded. `--model MODEL_ID` overrides it. `.env.example` documents the variables; the script does **not** automatically load `.env` files. Keep credentials out of commits.

### Explore the underlying API

```bash
curl "$MIMOE_BASE_URL/models" \
  -H "Authorization: Bearer $MIMOE_API_KEY"

curl "$MIMOE_BASE_URL/chat/completions" \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $MIMOE_API_KEY" \
  -d '{"model":"smollm2-1.7b","messages":[{"role":"user","content":"Hello"}],"max_tokens":40,"stream":false}'
```

This uses OpenAI-compatible request and response fields, but the server is mimOE running on this device. An OpenAI account or cloud API key is not needed. In the tested runtime, `/models` was readable without authentication, while `/chat/completions` required the Studio API key.

## Example from a real local run

```text
[plan] model selected query
[tool] search_runbooks('queue backlog consumer lag')
[sources] queue-backlog.md, http-errors.md

1. Compare incoming message rate with consumer processing rate.
2. Check consumer error logs for repeated failures and retry loops.
3. Inspect dead-letter queue count. Preserve failed messages for investigation.
4. Check database latency and connection pool saturation before adding consumers.
5. If consumers are healthy and downstream capacity is available, ask the operator to consider scaling consumers gradually.

Retrieved sources: queue-backlog.md, http-errors.md
```

See [verification notes](docs/verification.md) for the environment, complete captured runs, and limitations.

## Implementation choices

- **Raw HTTP instead of a framework:** two model calls and one tool do not need a large dependency tree. The integration is easy to inspect and explain.
- **A bounded agent workflow:** the model selects the tool argument, the host validates the action, then the model sees the tool result. This is a narrow agent, not an autonomous incident responder.
- **Prompted JSON rather than native function calling:** this avoids requiring a `tools` capability from the chosen small model or endpoint. Only `{"tool":"search_runbooks","query":"..."}` is accepted. Invalid JSON or actions trigger a deterministic search using the original question; `--trace` reports that fallback.
- **Keyword retrieval:** rank bundled Markdown files by distinct matching terms, ignoring common stop words; return at most two files. Three short runbooks do not justify an embedding model or vector database.
- **Small local model:** SmolLM2 1.7B Q4_K_M is approximately 1.06 GB to download and keeps the demo lightweight. Model download requires internet; inference requests go to the local runtime.
- **Visible evidence:** the host always appends the filenames actually retrieved. This is provenance of the supplied context, not a guarantee that every generated statement is supported.

## Boundaries and limitations

- The tool reads only the project's `runbooks/*.md` and skips symlinks. Model-generated text is never used as a path or command.
- Only HTTP loopback endpoints are accepted. Proxy environment variables are ignored and redirects are rejected. There is no cloud fallback in the agent.
- Two model calls maximum, with bounded output tokens and a 120-second timeout per request. A search with no matching evidence stops before answer generation.
- All runbooks describe fictional systems. The agent has no access to real logs, metrics, or services and cannot diagnose a live incident.
- A small model can misunderstand the question or invent recommendations despite the prompt. This demo does not enforce claim-level grounding or treat generated advice as safe to execute.
- Lexical matching misses synonyms and non-English queries. A valid but poor model search query can retrieve irrelevant context or no context. The malformed-action fallback only addresses invalid output syntax.
- The bounded workflow has no persistent memory, iterative investigation, streaming UI, or remote tools. Those are outside this focused exercise.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Tests run offline and cover the request contract, action allowlist, retrieval, symlink exclusion, missing evidence, malformed-action fallback, redirect rejection, loopback restriction, and authentication errors. They do not replace a live mimOE smoke test.

## Troubleshooting

| Result | Check |
| --- | --- |
| Cannot reach mimOE | Start the runtime, connect Studio, and copy the API URL again. |
| No loaded models | Click **Load** in Model View; downloading a model alone is insufficient. |
| HTTP 401 / 403 | Set `MIMOE_API_KEY` from the model's **API** panel. |
| Selected model is not loaded | Use the exact ID from `python3 agent.py --check`. |
| Invalid model action in trace | The original question was used as the retrieval query; the fallback is explicit. |

## Development disclosure

Built with an AI coding assistant for implementation, documentation, and verification. The live demo was run against mimOE Studio's locally served model. The design choices, observed behavior, and remaining limitations are documented so they can be reviewed and explained.

References: [official inference add-on](https://github.com/mimik-mimOE/mimOE-addon-ai-foundation), [Studio releases](https://github.com/mimik-mimOE/mimOE-Studio/releases).
