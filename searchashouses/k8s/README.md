# k8s

Kubernetes manifests for the local cluster, managed with kustomize. Commands run from `searchashouses/`.

## The local cluster (#2)
A k3d cluster (k3s in Docker), the same tool as in lab 3.1, defined in `k3d-cluster.yaml`. Needs Docker Desktop running.

| What | Value |
|---|---|
| Cluster / kubectl context | `searchashouses` / `k3d-searchashouses` |
| Nodes | 1 server (control plane) + 1 agent, k3s v1.31.5 |
| Kubernetes API | `https://127.0.0.1:6550` (this laptop only) |
| Ingress | `http://localhost:8080` -> built-in Traefik -> the gateway (#49) |
| Storage | StorageClass `local-path` (default), used by the index PersistentVolume (#51) and Postgres (#54) |

- Create: `k3d cluster create --config k8s/k3d-cluster.yaml`
- Check: `kubectl --context k3d-searchashouses get nodes`
- Stop/start: `k3d cluster stop searchashouses` / `k3d cluster start searchashouses`

## How deploy.yml reaches it (#57, #58)
The API listens on 127.0.0.1 only, so GitHub-hosted runners cannot reach it. `deploy.yml` runs on a **self-hosted runner on this laptop** with labels `self-hosted, k8s`, as the same user, so it uses `~/.kube/config` with the context `k3d-searchashouses`. The runner is started only while deploying. The repo is public, so self-hosted jobs only run on `push` to main or `workflow_dispatch`, and fork PRs never reach the runner (#57).
