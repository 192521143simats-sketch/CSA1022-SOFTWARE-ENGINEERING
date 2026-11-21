# EXP19

**Aim:** CI/CD pipeline with GitHub Actions for a containerized Flask app: test, build, push, deploy.

**Tools used:** GitHub Actions, Docker, Docker Hub, Render

## Outcome
Flask app, tests, Dockerfile and `.github/workflows/ci-cd.yml`. Deployment link must come from your own cloud account.

## Project files
All source files are in `flask-cicd-pipeline/`. Exact commands to run everything yourself are in `COMMANDS.md`.

## Screenshots (real output captured while building this)
1. `screenshots/01_structure.png` - Repository contents
2. `screenshots/02_pytest.png` - Tests the pipeline will run (pass locally)
3. `screenshots/03_curl.png` - App responding locally
4. `screenshots/04_workflow_valid.png` - Workflow file is valid: test -> docker -> deploy

Full command output: `terminal_transcript.txt`.

## What was actually run vs. what you must run yourself
**Run for real here (screenshots are genuine output):**
- Unit tests pass
- App serves requests locally
- Workflow YAML validated

**NOT run here - you must run these on your own machine and take your own screenshots:**
- Workflow run on GitHub
- Docker Hub push and cloud deployment (needs your accounts and secrets)
- Deployment link

The build workspace used to prepare this had no access to Docker Hub, Kubernetes, Jenkins or your cloud accounts,
so no screenshots of those steps are included. I did not fake them; follow `COMMANDS.md` and capture them
(the `screenshots/TODO_YOUR_SCREENSHOTS.md` checklist lists each one).
