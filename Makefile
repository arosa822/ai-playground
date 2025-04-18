# Define variables
IMAGE_NAME = ai-playground
CONTAINER_NAME = ai-playground-container
QUAY_REPO = quay.io/arosa/ai-playground
PORT = 5000

# Build the Docker image
build:
	podman build -t $(IMAGE_NAME) .

tag:
	podman tag $(IMAGE_NAME) $(QUAY_REPO):latest

push: tag
	podman push $(QUAY_REPO):latest

# Run the Docker container
run:
	podman run --name $(CONTAINER_NAME) -p $(PORT):5000 $(IMAGE_NAME)

# Stop and remove the Docker container
clean:
	podman stop $(CONTAINER_NAME) || true
	podman rm $(CONTAINER_NAME) || true

# Rebuild and run the Docker container
rebuild: clean build run

# Deploy the application to OpenShift
deploy:
	oc apply -f deploy.yaml
