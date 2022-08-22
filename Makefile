init:
	python -m pip install -r requirements.txt

init-dev:
	make init
	python -m pip install -r requirements-dev.txt

retry:
	# This will retry failed tests on every file change.
	python -m py.test -n auto --forked --looponfail

test:
	python -m py.test -n 8 --forked

lint:
	make lint-flake8
	make lint-black

lint-flake8:
	python -m flake8 cloudscraper tests

lint-black:
	python -m black cloudscraper tests --check --line-length=119

black:
	python -m black cloudscraper tests --line-length=119

clean:
	rm -fr build dist .egg cloudscraper.egg-info report.xml coverage.xml

build:
	make clean
	python setup.py sdist bdist_wheel --universal
