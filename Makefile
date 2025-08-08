init:
	rm -rf studytool/__pycache__
	rm -rf dist
	find tinyml -not -path "tinyml/slides/*" -delete

clean:
	find . -name "__pycache__" -exec rm -rf {} \;
	find . -name ".DS_Store" -exec rm -rf {} \;

commit:
	git commit -a -m "Update"
	git push origin

push:
	uv version --bump patch
	uv lock
	git commit -a -m "update"
	git push origin

publish:
	$(eval VERSION=$(shell uv version --short))
	git tag "v$(VERSION)"
	git push origin "v$(VERSION)"
	uv build
	@echo "Note: Set UV_PUBLISH_TOKEN environment variable with your PyPI token"
	uv publish --token $$UV_PUBLISH_TOKEN
