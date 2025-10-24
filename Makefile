IMAGE_BASE_NAME = itspeetah/np-prime-numbers-caller
IMAGE_TAG := dev

BUILDX_PLATFORM = linux/amd64,linux/arm64
PRIME_NUMBERS_URI := http://dispatcher.default.svc.cluster.local/function/openfaas-fn/prime-numbers-invoked

DEV_PLATFORM = linux/arm64
DEV_PORT = 8081
LOCAL_URI=http://host.docker.internal:8080
CLUSTER_URI=http://dispatcher.default.svc.cluster.local/function/openfaas-fn/prime-numbers-invoked-INDEX
IMG_TAG_LOCAL=local
IMG_TAG_CLUSTER=dev

.PHONY: local cluster dev run

build:
	@echo "Building docker image..."
	docker buildx build --platform $(BUILDX_PLATFORM) --target function -t $(IMAGE_BASE_NAME):$(IMAGE_TAG) --build-arg PRIME_NUMBERS_URI=$(PRIME_NUMBERS_URI) .
	@echo "Done."

local: PRIME_NUMBERS_URI=$(LOCAL_URI)
local: IMAGE_TAG=$(IMG_TAG_LOCAL)
local: build

cluster: PRIME_NUMBERS_URI=$(CLUSTER_URI)
cluster: IMAGE_TAG=$(IMG_TAG_CLUSTER)
cluster: build

push:
	@echo "Pushing Docker imgage for function prime-numbers-caller..."
	docker image push $(IMAGE_BASE_NAME):$(IMAGE_TAG)
	@echo "Done."

push-local: IMAGE_TAG=$(IMG_TAG_LOCAL)
push-local: push

push-cluster: IMAGE_TAG=$(IMG_TAG_CLUSTER)
push-cluster: push

run:IMAGE_TAG=$(IMG_TAG_LOCAL)
run:
	docker run -d -p 8081:8080 $(IMAGE_BASE_NAME):$(IMAGE_TAG)

dev:BUILDX_PLATFORM=$(DEV_PLATFORM)
dev:
	$(MAKE) local
	$(MAKE) run

