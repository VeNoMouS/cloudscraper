pep8-rules := E501,N806,W503,W504

init:
	pip install -r requirements.txt

test:
	# This runs all of the tests, on both Python 2 and Python 3.
	detox

ci:
	py.test -n 8 --boxed --junitxml=report.xml

flake8:
	flake8 --ignore $(pep8-rules) cloudscraper

autopep8:
	autopep8 -aaa --ignore $(pep8-rules) --in-place --recursive cloudscraper tests

coverage:
	py.test --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=cloudscraper tests
	coveralls

publish:
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -fr build dist .egg cloudscraper.egg-info
