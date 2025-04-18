# Define variables
IMAGE_NAME = ai-playground
CONTAINER_NAME = ai-playground-container
PORT = 5000

# Build the Docker image
build:
	podman build -t $(IMAGE_NAME) .

# Run the Docker container
run:
	podman run --name $(CONTAINER_NAME) -p $(PORT):5000 $(IMAGE_NAME)

# Stop and remove the Docker container
clean:
	podman stop $(CONTAINER_NAME) || true
	podman rm $(CONTAINER_NAME) || true

# Rebuild and run the Docker container
rebuild: clean build run
