# EXP16 - commands to run on your computer

```bash
cd todo-flask-app

# Build and run locally
docker build -t todo-flask-app .
docker run -d --name todo -p 5000:5000 todo-flask-app
curl http://localhost:5000/health            # {"status":"ok"}
# open http://localhost:5000 in the browser, add / complete / delete tasks

# Push to Docker Hub (replace <dockerhub-username>)
docker login
docker tag todo-flask-app <dockerhub-username>/todo-flask-app:v1
docker push <dockerhub-username>/todo-flask-app:v1

docker stop todo && docker rm todo
```
