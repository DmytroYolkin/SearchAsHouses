# Azure credit safety ($90, Azure for Students)
- Before any command that can spend credit (job submit, compute create, environment build, schedule create), say so and give a rough cost.
- Compute cluster min nodes 0. Never leave a compute instance running. No AKS, no managed online endpoints. Service images go to GHCR. The only ACR is the workspace registry for the training environment (#12, about $5/month); delete it when Azure spending stops.
- After Azure work, run `python searchashouses/azureml/setup/check_idle.py` once it exists.
- When the credit is checked, write the amount in .claude/context.md.
