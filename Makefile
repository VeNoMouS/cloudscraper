init:
	pip install pipenv -U
	pipenv install --dev

test:
	# This runs all of the tests, on both Python 2 and Python 3.
	detox

ci:
	pipenv run py.test -n 8 --boxed --junitxml=report.xml

flake8:
	pipenv run flake8 cloudscraper

coverage:
	pipenv run py.test --cov-config .coveragerc --verbose --cov-report term --cov-report xml --cov=cloudscraper tests
	pipenv run coveralls

publish:
	pip install 'twine>=1.5.0'
	python setup.py sdist bdist_wheel
	twine upload dist/*
	rm -fr build dist .egg cloudscraper.egg-info
