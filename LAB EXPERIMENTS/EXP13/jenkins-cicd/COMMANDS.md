# EXP13

See `jenkins_setup.md` for installing Jenkins, creating the pipeline job and adding the GitHub webhook.

Replace `<dockerhub-username>` and `<server-ip>` in the Jenkinsfile first. If you have no cloud server, delete the `Deploy to cloud` stage (or replace its body with `docker run -d -p 5000:5000 $IMAGE:latest` to deploy on the Jenkins machine itself).
