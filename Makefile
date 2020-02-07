IMAGE_NAME := docker_composer
VERSION := v2
REGISTRY_ADDR := jb6magic

push: tag
	docker push $(REGISTRY_ADDR)/$(IMAGE_NAME):$(VERSION)

tag: build
	docker tag $(IMAGE_NAME):$(VERSION) $(REGISTRY_ADDR)/$(IMAGE_NAME):$(VERSION)

build: Dockerfile
	docker build --rm -t $(IMAGE_NAME):$(VERSION) -f Dockerfile .
