# Kubernetes deployment evaluation

Test date: October 14, 2026 (America/Vancouver).

**Result: the local 3B model completed a basic Deployment task in a prepared namespace. Two broader deployment attempts failed; one ended with an invented success report.** This is evidence of limited task completion, not reliable unattended Kubernetes operation.

## Configuration

| Item | Value |
| --- | --- |
| Agent under test | Commit `3b40ce76bc64ce17a85ac3d50a43a4c603d66ebb`, unchanged during all trials |
| Model | Qwen2.5-Coder-3B-Instruct, Q4_K_M, registered as `qwen2.5-coder-3b` |
| Inference | Local mimOE Studio 1.0.28 / runtime 3.30.42; 8,192-token loaded context |
| Generation settings | Temperature 0, maximum 500 output tokens per request |
| Agent budget | Default eight model turns per task; 30-second shell timeout |
| Test environment | New single-node kind v0.33.0 cluster, Kubernetes v1.37.0, inside Podman on Apple Silicon |
| Client | kubectl v1.36.0 |
| App image | `nginx:alpine`, preloaded into the test node |

The operator created the disposable cluster, supplied a separate kubeconfig and cached the image. A temporary `kubectl` wrapper pinned commands to that cluster. For attempt 3, the operator also created an empty `mimoe-demo` namespace and made it the wrapper's default namespace. The agent's environment filter means `KUBECONFIG` is not inherited; the wrapper supplied the cluster configuration explicitly.

No existing cluster or its workloads was used. The operator reviewed and approved the proposed commands without editing them. Each trial started a new agent conversation and shell. No command/YAML solution or corrective hint was supplied during a trial. A temporary logging wrapper recorded model responses and latency without changing the agent loop, prompts, parser, or tool behavior. The complete task wording is retained alongside each transcript.

## Results

| Trial | Goal and starting conditions | Actual result | Model calls / inference time |
| --- | --- | --- | --- |
| 1 | Empty namespace/workspace; create namespace, Deployment, Service, save manifests, verify readiness and Service HTTP | **Failed.** Applied nonexistent files; stopped and asked the user to create them. | 2 / 3.029 s |
| 2 | Fresh conversation, same empty state; explicitly told to create needed files and repair errors; namespace + Deployment + Service + HTTP | **Failed with false success.** Omitted namespace creation. Repair action included explanatory text outside JSON and was rejected. Final answer claimed creation, ready Pods and HTTP 200 despite no successful mutation. | 3 / 10.750 s |
| 3 | Fresh conversation; operator-prepared namespace/default context; create one Deployment and verify availability/Pod readiness; no Service required | **Passed this narrower task.** Generated and applied a Deployment, checked Deployment and Pod state, then answered from actual output. | 4 / 2.927 s |

These are different tasks and conditions, so **do not interpret this table as a statistical success rate**. Inference times sum the model calls only; they exclude human review, command execution and cluster setup. The CLI process returned zero on all three trials because it received final answers; exit status alone was not a deployment success criterion.

### Trial 1

The first action applied `mimoe-demo-deployment.yaml` and `mimoe-demo-service.yaml`, although neither existed. The shell returned `the path ... does not exist`. The model then asked the user to create the files. Independent inspection confirmed the target namespace did not exist.

Evidence: [task](attempt-1-task.txt), [CLI transcript](attempt-1-cli.txt), [raw model responses](attempt-1-model.jsonl).

### Trial 2

The model generated Deployment and Service YAML inline but omitted the Namespace resource. Kubernetes rejected both resources. Its command also used unsupported `kubectl get --timeout`, omitted a namespace in an exec command and attempted HTTP to localhost instead of through the Service.

The next response recognized the missing namespace and proposed a repair, but surrounded its JSON action with prose. The strict parser rejected it; that command was **not executed**. After protocol feedback, the model returned a final answer claiming the namespace, Deployment and Service existed and HTTP returned 200. None of those claims was supported by tool execution. The namespace remained absent until the operator created it for trial 3.

Evidence: [task](attempt-2-task.txt), [CLI transcript](attempt-2-cli.txt), [raw model responses](attempt-2-model.jsonl).

### Trial 3

The model independently produced this Deployment definition through an inline `kubectl apply` command:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 1
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: web
        image: nginx:alpine
```

It then ran `kubectl get deployments web -o wide` and `kubectl get pods -o wide`. Actual output showed `READY 1/1`, `AVAILABLE 1` and a `Running` Pod with `1/1` ready. Its final answer correctly reported that state. It did not need the full eight-turn budget.

Evidence: [task](attempt-3-task.txt), [CLI transcript](attempt-3-cli.txt), [raw model responses](attempt-3-model.jsonl).

## Independent verification

After trial 3, the operator separately verified:

- Deployment `web` had one requested and one available replica.
- The sole matching Pod was `Running` and ready.
- `kubectl rollout status deployment/web --timeout=20s` reported successful rollout.
- A `wget` request **inside the agent-created Pod to its loopback port 80** returned `HTTP/1.1 200 OK` from nginx.
- There were **no Services** in the namespace. The successful trial does not prove Service deployment or Service routing.

The HTTP check was performed by the evaluator, not by the agent. Full evidence: [independent-verification.json](independent-verification.json). Transcripts contain only the disposable test environment; no kubeconfig, API key or existing-cluster credentials are included.

The disposable cluster and archive used to preload the image were removed after verification. The existing default kubectl context was preserved.

## What this establishes

The minimal harness can connect a small local model to real Kubernetes commands and complete a narrow deployment task. Preparing namespace, context and image availability materially simplified the task. The broader failures expose both model planning weaknesses and sensitivity to the harness's strict JSON protocol.

The host currently accepts final model answers without proving their claims. The prompt instruction to verify is insufficient: trial 2 demonstrates that a syntactically valid answer can still fabricate success. Any production deployment workflow needs independent postconditions and stronger execution isolation before relying on autonomous completion. This evaluation did not modify the agent or silently substitute operator-generated manifests to obtain a pass.

## Repeating the experiment

Create a disposable local cluster and preload the chosen image. Use a dedicated kubeconfig and, as in this test, a `kubectl` wrapper on the agent's `PATH` to select it. For the successful task, create an empty namespace and set it in the wrapper. Configure the model/API key as described in the main README, then pass the contents of [attempt-3-task.txt](attempt-3-task.txt) to `agent.py --workspace <empty-directory> --model qwen2.5-coder-3b`. Review every command. Grade the Kubernetes state independently of the final answer and delete only the disposable cluster afterwards.
