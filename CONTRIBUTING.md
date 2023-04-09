# Contributing guide

## Developing the mypy extension

Poetry will install the mypy extension in editable mode, but if you make changes in the extension,
then mypy might not seem to use them.
That happens due to caching.
So, in order to make all changes immediately available, disable caching in mypy with
```
mypy --cache-dir=/dev/null tests
```
