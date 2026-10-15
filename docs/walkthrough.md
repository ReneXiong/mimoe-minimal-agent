# Short walkthrough

“I built a minimal coding agent that connects to mimOE Studio's local inference endpoint. It has one tool: persistent Bash. The model proposes a command, the host asks for approval, returns the actual output, and lets the model continue until it answers.”

1. Show the loaded model in Studio, then open its **API** panel.
2. Run `python3 agent.py --check` to show the local URL and model IDs.
3. In a disposable directory, ask it to create a text file and read it back. Inspect each command before approving it.
4. Show that the answer follows actual tool output.

“I used raw HTTP and Python's standard library so the integration is easy to inspect. The loop is inspired by DeepSeek Harness Minimal mode. I do not import the full framework: this exercise only needs a short prompt, history and a shell tool.”

“Tool actions use a small JSON protocol because native function calling is not assumed. Invalid output gets feedback, with a hard turn limit. Commands have a timeout and output limit. Bash keeps directory and variable state across calls.”

“SmolLM2 could issue a command but failed to finish the JSON protocol reliably in a live test. That exposed the difference between answering a prompt and reliably driving a tool loop. Model choice and recorded verification are part of the integration.”

“Approval is a human checkpoint, not a sandbox. The shell runs with OS permissions and can reach files and the network. I use a disposable directory for the demo. A production version would need OS-level isolation and a representative task evaluation.”
