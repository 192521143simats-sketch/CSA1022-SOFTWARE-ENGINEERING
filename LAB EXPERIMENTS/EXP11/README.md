# EXP11

**Aim:** Create a static website, containerize it and serve it with Nginx using Docker.

**Tools used:** HTML, Dockerfile, Nginx, Docker

## Outcome
Complete project (`index.html`, `Dockerfile`, `.dockerignore`) ready to build and run with the 2 commands in `COMMANDS.md`.

## Project files
All source files are in `static-website/`. Exact commands to run everything yourself are in `COMMANDS.md`.

## Screenshots (real output captured while building this)
1. `screenshots/01_files.png` - Project files and the Dockerfile
2. `screenshots/02_validate.png` - Quick validation of index.html and Dockerfile
3. `screenshots/03_website.png` - The website (rendered in Chrome; this is what Nginx will serve at http://localhost:8080)

Full command output: `terminal_transcript.txt`.

## What was actually run vs. what you must run yourself
**Run for real here (screenshots are genuine output):**
- `index.html` created and parsed; Dockerfile checked
- Website rendered in headless Chrome (HD screenshot)

**NOT run here - you must run these on your own machine and take your own screenshots:**
- `docker build`, `docker run` and the browser screenshot at localhost:8080

The build workspace used to prepare this had no access to Docker Hub, Kubernetes, Jenkins or your cloud accounts,
so no screenshots of those steps are included. I did not fake them; follow `COMMANDS.md` and capture them
(the `screenshots/TODO_YOUR_SCREENSHOTS.md` checklist lists each one).
