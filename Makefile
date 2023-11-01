init:
	rm -rf studytool/__pycache__
	find tinyml -not -path "tinyml/slides/*" -delete

publish:
	poetry version patch
	poetry lock
	git commit -a -m "update"
	git push origin
	$(eval VERSION=$(shell poetry version --short))
	git tag "v$(VERSION)"
	git push origin "v$(VERSION)"
	poetry publish --build
