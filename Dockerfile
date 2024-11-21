# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the requirements.txt file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app directory to the container
COPY . .

# Set the environment variable for Flask
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV DB_USER=flask_user
ENV DB_PASSWORD=root
ENV CLOUD_SQL_CONNECTION_NAME=module-challenge-incredicorp:us-central1:banking-db
ENV SECRET_KEY=your-secret-key

# Expose the port the app runs on
EXPOSE 8080

# Run the application with gunicorn (the recommended production WSGI server for Flask)
CMD ["gunicorn", "-b", "0.0.0.0:8080", "app:app"]
