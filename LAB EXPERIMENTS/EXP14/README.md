# EXP14

**Aim:** Continuous deployment of a Dockerized app with GitHub Actions.

**Tools used:** GitHub Actions, Docker, GHCR, Kubernetes (GKE)

## Outcome
App + Dockerfile + `.github/workflows/cd.yml` + Kubernetes manifest. Push to GitHub to run it.

## Project files
All source files are in `github-actions-cd/`. Exact commands to run everything yourself are in `COMMANDS.md`.

## Screenshots (real output captured while building this)
1. `screenshots/01_structure.png` - Repository: app, Dockerfile, workflow and Kubernetes manifest
2. `screenshots/02_pytest.png` - Tests that the pipeline runs (pass locally)
3. `screenshots/03_workflow_valid.png` - GitHub Actions workflow parses: test -> build-and-push -> deploy

Full command output: `terminal_transcript.txt`.

## What was actually run vs. what you must run yourself
**Run for real here (screenshots are genuine output):**
- Unit tests pass
- Workflow YAML validated (3 jobs in the right order)

**NOT run here - you must run these on your own machine and take your own screenshots:**
- Running the workflow on GitHub
- Cloud deployment (needs your GCP/AWS/Azure account and secrets)

The build workspace used to prepare this had no access to Docker Hub, Kubernetes, Jenkins or your cloud accounts,
so no screenshots of those steps are included. I did not fake them; follow `COMMANDS.md` and capture them
(the `screenshots/TODO_YOUR_SCREENSHOTS.md` checklist lists each one).
