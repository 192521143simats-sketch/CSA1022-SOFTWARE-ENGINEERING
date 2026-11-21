# EXP16

**Aim:** Containerize a Python Flask To-Do application with Docker.

**Tools used:** Python, Flask, pytest, Docker, Docker Hub

## Outcome
Working Flask To-Do app + tests + Dockerfile (+ `.dockerignore`, `requirements.txt`). Submit the Dockerfile and your own container screenshots.

## Project files
All source files are in `todo-flask-app/`. Exact commands to run everything yourself are in `COMMANDS.md`.

## Screenshots (real output captured while building this)
1. `screenshots/01_files.png` - Flask To-Do project and Dockerfile
2. `screenshots/02_pytest.png` - Automated tests - all pass
3. `screenshots/03_api.png` - Testing the running app with curl
4. `screenshots/04_browser.png` - To-Do app in the browser (task 1 marked done)

Full command output: `terminal_transcript.txt`.

## What was actually run vs. what you must run yourself
**Run for real here (screenshots are genuine output):**
- 6 pytest tests pass
- App started and tested with real HTTP requests (add, toggle, list)
- UI screenshot from Chrome

**NOT run here - you must run these on your own machine and take your own screenshots:**
- `docker build`/`docker run` inside the container
- `docker push` to Docker Hub (needs your account)

The build workspace used to prepare this had no access to Docker Hub, Kubernetes, Jenkins or your cloud accounts,
so no screenshots of those steps are included. I did not fake them; follow `COMMANDS.md` and capture them
(the `screenshots/TODO_YOUR_SCREENSHOTS.md` checklist lists each one).
