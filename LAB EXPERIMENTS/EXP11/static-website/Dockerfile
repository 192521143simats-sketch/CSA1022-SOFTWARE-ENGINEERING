# Use the lightweight official Nginx image
FROM nginx:alpine

# Copy our website into the folder Nginx serves
COPY index.html /usr/share/nginx/html/index.html

# Nginx listens on port 80
EXPOSE 80

# nginx:alpine already starts Nginx in the foreground, so no CMD is needed
