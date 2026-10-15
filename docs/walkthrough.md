# Two-minute walkthrough

## What I built

“I built a local runbook assistant using the BYO Framework approach. You describe an operational symptom, the model chooses search terms, a Python tool searches fictional Markdown runbooks, and the model uses the returned text to produce a checklist. Inference runs through mimOE Studio's local OpenAI-compatible endpoint.”

## Show the connection

1. Open Studio's Model View and show the loaded SmolLM2 model.
2. Click **API** and explain the inference base URL, model ID, and local authentication. Avoid exposing a customized API key in a recording.
3. Run `python3 agent.py --check`.

## Show the workflow

```bash
python3 agent.py --trace 'Our queue backlog is growing and consumer lag is increasing. What should I check before scaling consumers?'
```

“The trace distinguishes model planning from tool execution. The tool is ordinary Python. The second model call receives actual retrieved text. The host lists the files retrieved, even when the model omits citations.”

## Why these choices

“I used the standard library because this exercise only needs two HTTP calls for planning and synthesis, plus model discovery. A framework would add setup without much value here. Keyword search is sufficient for three tiny runbooks. I used validated JSON actions so the demo doesn't depend on native function calling support in this model.”

## What I learned

“The supplied portal URL returned a Page Not Found page, so I located the signed installer in the official GitHub releases. Studio 1.0.28 needed its runtime installed, and the model had to be downloaded separately. I verified the API settings using the model's API panel. Model discovery worked without authentication, but inference returned 401 until I supplied the panel's development API key.”

## Limits and next step

“This is a bounded, read-only agent. It does not inspect a real service or execute fixes. A small model can still generate unsupported advice. The next improvement would be an evaluated set of representative questions and claim-level citation checks. I would add embeddings only if the runbook collection outgrew lexical retrieval.”
