mypy:
	@poetry run mypy src/$FOLDER_NAME/* tests/*

flake8:
	@poetry run flake8 src/$FOLDER_NAME/* tests/*

lint: mypy flake8

test: unit_test

unit_test:
	@poetry run pytest tests/unit -xvvs

shell:
	@poetry run ipython

install_git_hooks:
	@ln -s `pwd`/.hooks/pre-push .git/hooks/pre-push
