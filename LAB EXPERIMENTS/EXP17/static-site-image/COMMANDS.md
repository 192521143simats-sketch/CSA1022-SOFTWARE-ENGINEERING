# EXP17 - Push and pull images using Docker Hub

Replace `<dockerhub-username>` with your Docker Hub user name (create a free account at hub.docker.com).

## Machine A (build and push)
```bash
cd static-site-image
docker build -t static-site:1.0 .                                   # 1. create the image
docker login                                                       # enter Docker Hub user + password/token
docker tag static-site:1.0 <dockerhub-username>/static-site:1.0    # 2. tag
docker push <dockerhub-username>/static-site:1.0                   #    push
```

## Machine B (another computer, or run `docker rmi` first on the same one)
```bash
docker pull <dockerhub-username>/static-site:1.0                   # 3. pull
docker run -d -p 8080:80 <dockerhub-username>/static-site:1.0      #    run
# open http://localhost:8080
```

## Submit
These commands plus a screenshot of each: build, login, tag, push, Docker Hub repo page, pull, run, browser.
