# Start from Python 3.10 base image
FROM python:3.10-slim-buster

# Install the necessary tools and libraries, curl
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    curl

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container
COPY . /usr/src/app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 80 available to the world outside this container
EXPOSE 80

# Run main.py when the container launches
CMD ["python", "main.py"]
