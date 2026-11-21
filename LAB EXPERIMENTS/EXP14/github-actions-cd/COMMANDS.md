# EXP14 - Continuous Deployment with GitHub Actions

```bash
# 1. Push this folder to a NEW GitHub repository
cd github-actions-cd
git init -b main && git add . && git commit -m "Dockerized app with CD workflow"
git remote add origin https://github.com/<you>/ci-demo.git
git push -u origin main
```

## One-time GitHub setup
- Repo -> Settings -> Actions -> General -> Workflow permissions -> **Read and write**.
- For the image: the workflow pushes to **GitHub Container Registry** (ghcr.io) using the built-in `GITHUB_TOKEN` - no extra secret.
- For the `deploy` job (GKE) add these secrets (Settings -> Secrets and variables -> Actions):
  `GCP_SA_KEY` (service-account JSON), `GKE_CLUSTER`, `GKE_LOCATION`.
  *No cloud account?* Delete the `deploy` job - build+push alone still demonstrates CI/CD.
  AWS ECS / Azure AKS also work: swap the last job for `aws-actions/amazon-ecs-deploy-task-definition` or `azure/k8s-deploy`.

## 4. Test the pipeline
```bash
# change something, e.g. the message in app.py
git commit -am "Change greeting" && git push
# GitHub -> Actions tab: watch test -> build-and-push -> deploy turn green
```
