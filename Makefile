image:
	docker build -t quorum .

mypy:
	docker run -v $(CURDIR):/srv quorum mypy .

tests:
	docker run -v $(CURDIR):/srv quorum python3 -m unittest discover tests
