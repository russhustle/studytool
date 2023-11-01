init:
	rm -rf studytool/__pycache__
	find tinyml -not -path "tinyml/slides/*" -delete

publish:
	poetry version patch
	poetry lock
	git commit -m -a "update"
	git push origin
	version=$(poetry version --short)
	git tag "v$version"
	git push origin "v$version"

	poetry publish --build
