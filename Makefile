# Define variables
IMAGE_NAME = my-flask-app
CONTAINER_NAME = my-flask-app-container
PORT = 5000

# Build the Docker image
build:
	docker build -t $(IMAGE_NAME) .

# Run the Docker container
run:
	docker run --name $(CONTAINER_NAME) -p $(PORT):5000 $(IMAGE_NAME)

# Stop and remove the Docker container
clean:
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

# Rebuild and run the Docker container
rebuild: clean build run
