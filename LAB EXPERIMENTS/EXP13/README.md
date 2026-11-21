# EXP13

**Aim:** CI/CD pipeline with Jenkins: build the Docker image, run tests, deploy to the cloud, trigger on commits.

**Tools used:** Jenkins, Docker, GitHub webhooks, Python/pytest

## Outcome
App, Dockerfile, a complete declarative `Jenkinsfile` and a step-by-step `jenkins_setup.md`.

## Project files
All source files are in `jenkins-cicd/`. Exact commands to run everything yourself are in `COMMANDS.md`.

## Screenshots (real output captured while building this)
1. `screenshots/01_structure.png` - Sample app, Dockerfile and Jenkinsfile
2. `screenshots/02_pytest.png` - Pipeline 'Test' stage - passes locally
3. `screenshots/03_stages.png` - Stages declared in the Jenkinsfile

Full command output: `terminal_transcript.txt`.

## What was actually run vs. what you must run yourself
**Run for real here (screenshots are genuine output):**
- Sample app tests pass
- Jenkinsfile stages listed

**NOT run here - you must run these on your own machine and take your own screenshots:**
- Installing Jenkins and running the pipeline
- Cloud deployment and the GitHub webhook trigger
- The Jenkinsfile itself was not executed by Jenkins here (no Jenkins available), so expect to adjust small details such as credentials IDs

The build workspace used to prepare this had no access to Docker Hub, Kubernetes, Jenkins or your cloud accounts,
so no screenshots of those steps are included. I did not fake them; follow `COMMANDS.md` and capture them
(the `screenshots/TODO_YOUR_SCREENSHOTS.md` checklist lists each one).
