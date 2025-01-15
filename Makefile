all: test

uninstall:
	pip freeze | grep -v "^-e" | xargs pip uninstall -y

clean:
	rm -rf build dist
	find . -name '*.pyc' -exec rm \{\} \;

deps:
	pip install --upgrade pip twine wheel

install: deps
	@# `make install` installs the editable version of OpenFisca-France-Pension.
	@# This allows contributors to test as they code.
	pip install --editable .[dev] --upgrade

build: clean deps
	@# `make build` allows us to be be sure tests are run against the packaged version
	python setup.py sdist bdist_wheel
	find dist -name "*.whl" -exec pip install --upgrade {}[dev] \;

check-syntax-errors:
	python -m compileall -q .

format-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	autopep8 `git ls-files | grep "\.py$$"`

check-style:
	@# Do not analyse .gitignored files.
	@# `make` needs `$$` to output `$`. Ref: http://stackoverflow.com/questions/2382764.
	flake8 `git ls-files | grep "\.py$$" | grep -v openfisca_france_pension/variables/`

test: clean check-syntax-errors check-style
	openfisca test --country-package openfisca_france_pension tests
