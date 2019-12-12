pep8-rules := E501,N806,W503,W504

init:
	pip install -r requirements.txt

test:
	# This runs all of the tests, on both Python 2 and Python 3.
	tox --parallel auto

watch:
	# This automatically selects and re-executes only tests affected by recent changes.
	ptw -- --testmon

retry:
	# This will retry failed tests on every file change.
	py.test -n auto --forked --looponfail

ci:
	py.test -n 8 --forked --junitxml=report.xml

lint:
	flake8 --ignore $(pep8-rules) cloudscraper tests

format:
	# Automatic reformatting
	autopep8 -aaa --ignore $(pep8-rules) --in-place --recursive cloudscraper tests

coverage:
	py.test --cov-config=.coveragerc --verbose --cov-report=term --cov-report=xml --cov=cloudscraper tests
	coveralls

clean:
	rm -fr build dist .egg cloudscraper.egg-info report.xml coverage.xml

build:
	make clean
	python3 setup.py sdist bdist_wheel --universal

publish:
	make build
	pip3 install 'twine>=1.5.0'
	twine upload dist/*
	make clean

publish_test:
	make build
	pip3 install 'twine>=1.5.0'
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*
	make clean
