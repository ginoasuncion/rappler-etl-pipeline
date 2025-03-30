# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn (production server)
RUN pip install gunicorn

# Make port 8080 available to the world outside the container
EXPOSE 8080

# Run the app with gunicorn on port 8080
CMD ["gunicorn", "-b", "0.0.0.0:8080", "main:app"]
