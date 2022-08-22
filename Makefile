init:
	pip install -r requirements.txt

init-dev:
	make init
	pip install -r requirements-dev.txt

retry:
	# This will retry failed tests on every file change.
	py.test -n auto --forked --looponfail

test:
	py.test -n 8 --forked

lint:
	make lint-flake8
	make lint-black

lint-flake8:
	flake8 cloudscraper tests

lint-black:
	black cloudscraper tests --check --line-length=119

black:
	black cloudscraper tests --line-length=119

clean:
	rm -fr build dist .egg cloudscraper.egg-info report.xml coverage.xml

build:
	make clean
	python3 setup.py sdist bdist_wheel --universal
