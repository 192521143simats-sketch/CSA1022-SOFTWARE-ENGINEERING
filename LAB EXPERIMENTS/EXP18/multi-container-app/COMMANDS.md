# EXP18 - Multi-container app on Kubernetes (frontend + backend + database)

Replace `<dockerhub-username>` in `k8s/20-backend.yaml` and `k8s/30-frontend.yaml`.

```bash
cd multi-container-app

# (optional) quick local test of all 3 containers
docker compose up --build            # open http://localhost:8080

# Build and push the two custom images
docker build -t <dockerhub-username>/notes-backend:v1  ./backend
docker build -t <dockerhub-username>/notes-frontend:v1 ./frontend
docker login
docker push <dockerhub-username>/notes-backend:v1
docker push <dockerhub-username>/notes-frontend:v1

# Deploy (Docker Desktop Kubernetes / minikube / kind)
kubectl apply -f k8s/
kubectl get pods,svc                       # monitor status
kubectl rollout status deployment/backend
kubectl logs deployment/backend

# open http://localhost:30080   (minikube: minikube service frontend --url)

# Scale the frontend to handle more load
kubectl scale deployment frontend --replicas=5
kubectl get pods -l app=frontend

# Dashboard screenshot
minikube dashboard        # or:  kubectl apply -f https://raw.githubusercontent.com/kubernetes/dashboard/v2.7.0/aio/deploy/recommended.yaml
```
