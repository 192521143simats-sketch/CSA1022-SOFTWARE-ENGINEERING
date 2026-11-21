# Jenkins setup (Step 1 and Step 4)

## Install Jenkins locally with Docker
```bash
docker run -d --name jenkins -p 8081:8080 -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts-jdk17
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword   # unlock password
```
Open http://localhost:8081 -> install suggested plugins. Also install: **Docker Pipeline, GitHub, SSH Agent**.
(Jenkins needs the `docker` CLI and Python inside; easiest is to run it on a Linux VM or use a custom image.)

## Create the pipeline job
1. New Item -> *Pipeline* -> name `jenkins-demo`.
2. Pipeline -> *Pipeline script from SCM* -> Git -> your repository URL -> branch `main` -> Script Path `Jenkinsfile`.
3. Add credentials: `dockerhub-creds` (username/password) and `deploy-ssh` (SSH private key).

## Trigger builds on every commit / pull request (Step 4)
1. Job -> Configure -> Build Triggers -> tick **GitHub hook trigger for GITScm polling**.
2. GitHub repo -> Settings -> Webhooks -> Add webhook:
   Payload URL `http://<public-jenkins-url>/github-webhook/`, content type `application/json`, events *Push* and *Pull requests*.
   (On a laptop use `ngrok http 8081` to get a public URL.)
3. Push a commit -> a build starts automatically.
