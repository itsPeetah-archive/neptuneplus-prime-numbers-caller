IMAGE := itspeetah/np-pnc-load:dev

.PHONY: build push up down all

all: build push down up

# DOCKER
build:
	docker buildx build --platform=linux/arm64,linux/amd64 -t $(IMAGE) .

push:
	docker push $(IMAGE)

up:
	kubectl apply -f dep.yaml

down:
	kubectl delete -f dep.yaml --ignore-not-found=true