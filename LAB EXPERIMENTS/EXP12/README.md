# EXP12

**Aim:** Flask API -> Docker image -> Docker Hub -> Kubernetes Deployment + NodePort Service.

**Tools used:** Python Flask, Docker, Docker Hub, Kubernetes

## Outcome
Complete app, Dockerfile and Kubernetes manifests (`k8s/deployment.yaml`, `k8s/service.yaml`).

## Project files
All source files are in `flask-k8s-app/`. Exact commands to run everything yourself are in `COMMANDS.md`.

## Screenshots (real output captured while building this)
1. `screenshots/01_files_part1.png` - Project structure and app.py
2. `screenshots/01_files_part2.png` - Project structure and app.py
3. `screenshots/02_pytest.png` - API tests pass
4. `screenshots/03_curl.png` - Endpoints responding (running locally)
5. `screenshots/04_manifest_check.png` - Offline manifest consistency check

Full command output: `terminal_transcript.txt`.

## What was actually run vs. what you must run yourself
**Run for real here (screenshots are genuine output):**
- 6 pytest tests pass
- API endpoints exercised with curl
- Deployment/Service manifests cross-checked offline

**NOT run here - you must run these on your own machine and take your own screenshots:**
- `docker build`/`push`
- `kubectl apply` and accessing the API on NodePort 30007

The build workspace used to prepare this had no access to Docker Hub, Kubernetes, Jenkins or your cloud accounts,
so no screenshots of those steps are included. I did not fake them; follow `COMMANDS.md` and capture them
(the `screenshots/TODO_YOUR_SCREENSHOTS.md` checklist lists each one).
