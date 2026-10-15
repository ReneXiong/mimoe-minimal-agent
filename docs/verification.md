# Verification record

Tested on October 14, 2026 (America/Vancouver), on an Apple Silicon Mac.

## Installed environment

| Component | Observed version / setting |
| --- | --- |
| mimOE Studio | 1.0.28, official aarch64 DMG |
| App signature | mimik technology inc; Developer ID signed, notarization ticket stapled |
| mimOE runtime | 3.30.42, bundled with Studio |
| AI Foundation add-on | 1.17.54, bundled |
| Model repository | HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF |
| Model file | smollm2-1.7b-instruct-q4_k_m.gguf |
| Download size | 1,055,609,536 bytes |
| Registered model ID | smollm2-1.7b |
| Loaded in | Studio Model View, GPU, 8K context |
| Inference base URL | http://127.0.0.1:8083/mimik-ai/openai/v1 |
| Runtime network | Started with loopback-only HTTP binding and local discovery disabled |

## Discovery and setup

The assignment's early-access portal URL and the current download link both returned a Page Not Found page during setup. The official `mimik-mimOE/mimOE-Studio` GitHub release provided the installer. No third-party binary source was used.

Studio initially reported that the runtime was missing. Its bundled `mimoe-setup` CLI installed the bundled runtime into the standard local runtime directory. The runtime was started and Studio connected to it. This release had no preinstalled model, so the model was pulled through mimOE, then loaded using the Studio UI.

The **API** button showed a direct inference URL and a separate traceable router URL. This demo uses direct inference. `/models` returned the loaded model without a key, but the first chat request returned HTTP 401. Using the development API key displayed in Studio fixed inference. No OpenAI cloud credential was used.

## Live checks

Complete command output is in [live-runs.txt](live-runs.txt). It contains only synthetic demo questions, model IDs and localhost URLs; no credentials.

| Check | Observed result |
| --- | --- |
| Model discovery | smollm2-1.7b returned by `/models` |
| Queue backlog | Model chose `queue backlog consumer lag`; retrieved queue-backlog.md and http-errors.md; produced relevant checklist; 0.94 s |
| Connection pool | Model chose `database connection pool exhausted timing out`; retrieved database-connections.md and http-errors.md; produced relevant checklist; 1.19 s |
| Unrelated question | Model chose `volcano geology`; no sources matched; stopped without answer-generation call |
| Missing API key | HTTP 401 surfaced with a configuration hint |

Timings are individual warm local runs, not a benchmark or a latency guarantee. Successful examples do not establish general answer quality or guarantee factual grounding.

## Automated checks

`python3 -m unittest discover -s tests -v`: **9 tests passed**. These cover the HTTP request shape and the host's control boundaries. CI runs these offline; it does not install Studio or claim to verify inference on GitHub's runner.

## Remaining limitations

SmolLM2 is a small instruction model. It can choose weak search terms, omit inline citations or generate advice that is not supported by the evidence. The host prints actual retrieved filenames but does not validate every claim. The tool itself is read-only and has no command-execution capability. The demo should be treated as an explainable prototype, not a production incident responder.
