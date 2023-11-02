init:
	rm -rf studytool/__pycache__
	rm -rf dist
	find tinyml -not -path "tinyml/slides/*" -delete

push:
	poetry version patch
	poetry lock
	git commit -a -m "update"
	git push origin

publish:
	$(eval VERSION=$(shell poetry version --short))
	git tag "v$(VERSION)"
	git push origin "v$(VERSION)"
	poetry publish --build
