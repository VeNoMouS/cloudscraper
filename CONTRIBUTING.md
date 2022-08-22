# Contributing

## Issues

Issues are very valuable to this project.

  - Ideas are a valuable source of contributions others can make
  - Problems show where this project is lacking
  - With a question you show where contributors can improve the user
    experience

Thank you for creating them.

## Pull Requests

Pull requests are always welcome but getting from idea to merged PR will take a few steps!

### Local Dev Set Up

Installing the dev requirements should be all you need to get off your feet!

`pip install -r requirements-dev.txt`

From there, ensuring CICD tests will pass (ie running flake8 and black) can be done with the following commands:
- `black .` (adding the `-check` flag will prevent the code from being formatted)
- `flake8 .` (no output if no issues)


### PR Tenets

#### Does it state intent

You should be clear which problem you're trying to solve with your
contribution.

For example:

> Some Bug Fixes

Doesn't tell me anything about why you're doing that

> Fix broken test case for new changes within cloudflare's UI

Tells me the problem that you have found, and the pull request shows me
the action you have taken to solve it.

#### Is it of good quality

  - There is a singular and concise problem being solved by the PR
  - The PR is properly documented to the best of your ability
  - The code is passing all CICD tests
  - Attempts to avoid introducing bloat, tech debt, or out of scope features.
