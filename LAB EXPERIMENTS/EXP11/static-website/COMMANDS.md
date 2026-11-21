# EXP11 - commands to run on your computer (Docker Desktop must be running)

```bash
cd static-website

# 3. Build the image
docker build -t static-website .

# 4. Run the container (host port 8080 -> container port 80)
docker run -d --name my-site -p 8080:80 static-website

# 5. Open the website
#    http://localhost:8080   (or: curl http://localhost:8080)

# Useful checks / clean-up
docker images | grep static-website
docker ps
docker logs my-site
docker stop my-site && docker rm my-site
```
