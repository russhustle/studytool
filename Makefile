init:
	rm -rf studytool/__pycache__
	rm -rf dist
	find tinyml -not -path "tinyml/slides/*" -delete

commit:
	git commit -a -m "Update"
	git push origin

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
