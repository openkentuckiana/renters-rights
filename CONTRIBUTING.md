# How to contribute

Thanks for taking the time to consider contributing to this project!

If you haven't already, come join the #code-for-kentuckiana channel in [Code for America's Slack](http://slack.codeforamerica.org).

## Testing

We're trying to maintain high test coverage on this project.
Please include Django test cases with your code.
You can run all tests by running `make test` from your command line.

## Submitting changes

Please send a [GitHub Pull Request to renters-rights](https://github.com/codeforkyana/renters-rights/pull/new/master) with a clear list of what you've done (read more about [pull requests](http://help.github.com/pull-requests/)). Please follow our coding conventions (below) and make sure all of your commits are atomic (one feature per commit).

Always write a clear log message for your commits. One-line messages are fine for small changes, but bigger changes should look like this:

    $ git commit -m "A brief summary of the commit
    > 
    > A paragraph describing what changed and its impact."

If you're a new contributor, add your name to CONTRIBUTORS.txt!

## Coding conventions

Start reading our code and you'll get the hang of it. We optimize for readability:

  * We use the [black](https://github.com/psf/black) code formatter (run `make format` or let the pre-commit hook format for you)
  * We use the Django test suite


(This document is based on https://github.com/opengovernment/opengovernment/blob/master/CONTRIBUTING.md)