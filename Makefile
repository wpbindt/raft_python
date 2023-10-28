.PHONY: tests mypy image
DOCKER_IMAGE := quorum

image:
	docker build -t ${DOCKER_IMAGE} .

mypy:
	docker run -v $(CURDIR):/srv ${DOCKER_IMAGE} mypy .

tests:
	docker run -v $(CURDIR):/srv ${DOCKER_IMAGE} python3 -m unittest discover tests
