# EXP12 - Flask API -> Docker -> Docker Hub -> Kubernetes

Replace `<dockerhub-username>` everywhere (also inside `k8s/deployment.yaml`).

```bash
cd flask-k8s-app

# 2-3. Containerize and build
docker build -t <dockerhub-username>/flask-api:v1 .
docker run -d -p 5000:5000 <dockerhub-username>/flask-api:v1 && curl localhost:5000/health

# 4. Push to Docker Hub
docker login
docker push <dockerhub-username>/flask-api:v1

# 5-6. Deploy to Kubernetes (Docker Desktop's Kubernetes, minikube or kind)
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl get pods
kubectl get svc flask-api-service

# Access through the NodePort
#   Docker Desktop / kind : http://localhost:30007
#   minikube              : minikube service flask-api-service --url
curl http://localhost:30007/api/students
```
