# EXP19 - CI/CD pipeline with GitHub Actions (Flask + Docker Hub + cloud deploy)

1. Push this folder to a new GitHub repo (see EXP14 for the git commands).
2. Add **repository secrets** (Settings -> Secrets and variables -> Actions):
   - `DOCKERHUB_USERNAME` - your Docker Hub user
   - `DOCKERHUB_TOKEN` - Docker Hub -> Account Settings -> Security -> New Access Token
   - `RENDER_DEPLOY_HOOK_URL` - on render.com create a *Web Service -> Existing image*
     `docker.io/<user>/flask-cicd:latest`, then copy its **Deploy Hook** URL
     (Heroku has no free tier now; Render, AWS App Runner or Azure Web Apps work the same way).
3. Push to `main` -> Actions tab -> the 3 jobs run -> open your Render URL.
4. Submit: `.github/workflows/ci-cd.yml` and the deployment link.
