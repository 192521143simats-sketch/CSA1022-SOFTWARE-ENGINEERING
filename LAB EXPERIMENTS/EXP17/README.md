# EXP17

**Aim:** Push and pull Docker images using Docker Hub.

**Tools used:** Docker, Docker Hub, Nginx

## Outcome
Website and Dockerfile ready, plus a step-by-step command sheet with a screenshot checklist.

## Project files
All source files are in `static-site-image/`. Exact commands to run everything yourself are in `COMMANDS.md`.

## Screenshots (real output captured while building this)
1. `screenshots/01_files.png` - Static website and Dockerfile for the image
2. `screenshots/02_website.png` - The website that the image serves (http://localhost:8080)

Full command output: `terminal_transcript.txt`.

## What was actually run vs. what you must run yourself
**Run for real here (screenshots are genuine output):**
- Website + Dockerfile prepared; page rendered in Chrome

**NOT run here - you must run these on your own machine and take your own screenshots:**
- Everything involving Docker Hub: `build`, `login`, `tag`, `push`, `pull`, `run` (needs your Docker Hub account)

The build workspace used to prepare this had no access to Docker Hub, Kubernetes, Jenkins or your cloud accounts,
so no screenshots of those steps are included. I did not fake them; follow `COMMANDS.md` and capture them
(the `screenshots/TODO_YOUR_SCREENSHOTS.md` checklist lists each one).
