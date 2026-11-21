# EXP18

**Aim:** Deploy a multi-container (frontend, backend, database) application on Kubernetes and scale it.

**Tools used:** Docker, Kubernetes (kubectl), Flask, Nginx, PostgreSQL

## Outcome
Three Dockerfiles/services, `docker-compose.yml` and Kubernetes YAML (Secret, 3 Deployments, 3 Services) ready to apply.

## Project files
All source files are in `multi-container-app/`. Exact commands to run everything yourself are in `COMMANDS.md`.

## Screenshots (real output captured while building this)
1. `screenshots/01_structure.png` - Project structure: frontend, backend, database and Kubernetes YAML
2. `screenshots/02_pytest.png` - Backend tests pass
3. `screenshots/03_backend_curl.png` - Backend API running locally
4. `screenshots/04_manifest_check.png` - Kubernetes manifests: selectors, replicas and services are consistent

Full command output: `terminal_transcript.txt`.

## What was actually run vs. what you must run yourself
**Run for real here (screenshots are genuine output):**
- Backend tests pass and API runs locally
- All Kubernetes YAML parsed and cross-checked (labels/selectors/ports)

**NOT run here - you must run these on your own machine and take your own screenshots:**
- `docker build`/`push`, `kubectl apply`, `kubectl scale`, and the Kubernetes dashboard screenshot
- PostgreSQL connectivity (backend was tested in in-memory mode only)

The build workspace used to prepare this had no access to Docker Hub, Kubernetes, Jenkins or your cloud accounts,
so no screenshots of those steps are included. I did not fake them; follow `COMMANDS.md` and capture them
(the `screenshots/TODO_YOUR_SCREENSHOTS.md` checklist lists each one).
