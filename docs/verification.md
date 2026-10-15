# Verification

Tested October 14, 2026 (America/Vancouver), on an Apple Silicon Mac.

## Setup

- Studio 1.0.28, from mimik's official GitHub release. App signature identified mimik technology inc; notarization ticket was stapled.
- Bundled runtime 3.30.42 and AI Foundation 1.17.54, installed with Studio's bundled setup CLI.
- Runtime started with loopback-only HTTP binding and local discovery disabled.
- API panel showed `http://localhost:8083/mimik-ai/openai/v1` and a separate router URL. The agent uses direct inference, with `127.0.0.1` as the host.
- Model discovery worked without authentication; chat returned HTTP 401 until the Studio development API key was supplied. No cloud inference key was used.
- The portal download links returned a Page Not Found page during setup. The official Studio release was used instead.

## Reference design

Inspected DeepSeek Harness commit `571902028a75c64c1d767f4ae5fd099485f0ddf0` through GitHub CLI. Its current Minimal preset uses a short persona and persistent shell; dedicated text-file tools are disabled. Current upstream also supports image reading and compaction. This exercise implements the small text-only loop independently, not the full upstream framework.

Source: [pinned Minimal preset](https://github.com/deepseek-ai/deepseek-harness/blob/571902028a75c64c1d767f4ae5fd099485f0ddf0/packages/bundle/web-app/presets/minimal.patch.yml).

## Model selection and observed failure

SmolLM2 1.7B Q4_K_M was downloaded and loaded in Studio's Model View; the API panel was inspected. It succeeded in the earlier fixed runbook workflow, but in the revised general tool loop it issued one shell command and then repeatedly produced malformed action JSON. The host stopped after eight model turns with exit code 1. That is a failed harness smoke test, not successful verification.

The final minimal-loop demo uses the official `Qwen/Qwen2.5-Coder-3B-Instruct-GGUF` model, Q4_K_M (2,104,932,800-byte download), registered as `qwen2.5-coder-3b`. The model is served locally through mimOE.

## Live verification

Qwen initially wrapped valid actions in Markdown JSON fences. Strict parsing rejected the command, and a subsequent model answer claimed the result without a file being created. The directory was checked independently, exposing the false success. The parser now accepts exactly one enclosing JSON fence while retaining strict action validation. The final rerun executed the actual command `echo 'hello' > hello.txt && cat hello.txt`, returned exit code 0 and then produced a final answer. An independent read confirmed the file contents. This is why final model text alone is not treated as execution evidence.

See [live-runs.txt](live-runs.txt) for the captured final smoke test. Model commands were reviewed before approval and executed only in a disposable demo directory. Local absolute paths in the transcript are normalized to `<demo-workspace>`.

This tests the connection and a small file task. It does not establish general coding ability, reliable completion of arbitrary tasks or isolation from the rest of the computer.

## Automated verification

`python3 -m unittest discover -s tests -v`: 11 tests covering strict actions, feedback, rejected commands, loop limits, persistent shell directory/variables, exit status, timeouts, output limits, credential environment filtering, loopback validation, redirects and HTTP request/authentication behavior.

CI runs these offline. It does not install mimOE or claim to test local inference on GitHub's runners.

## Boundaries

The shell starts in the selected directory but is not sandboxed. Approval does not prevent an approved command from reaching other files or the network. The shell inherits a small environment allowlist, but can still read any disk credentials accessible to the OS user. Timeout cleanup is for ordinary child processes; commands can deliberately detach from a process group. Model-generated final answers are not independently checked by the host. Conversation history stays in memory without compaction, so long sessions can exceed the model context.
