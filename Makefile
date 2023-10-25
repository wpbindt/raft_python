image:
	docker build -t quorum .

mypy: image
	docker run -v $(CURDIR):/srv quorum mypy .

tests: image
	docker run -v $(CURDIR):/srv quorum python3 -m unittest discover .
