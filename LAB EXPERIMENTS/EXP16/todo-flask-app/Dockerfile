FROM python:3.12-slim

WORKDIR /app

# install dependencies first (better Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy the application code
COPY app.py .

EXPOSE 5000

# gunicorn is a production-grade server for Flask
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
