#!/bin/bash

PYPROJECT="pyproject.toml"
TMPFILE="tmpfile.toml"

# Process the file: remove only the dependencies section under [project]
gsed '/\[project\]/,/^\[/{/dependencies = \[/,/]/d}' "$PYPROJECT" >"$TMPFILE"

# Fetch dependencies from pip freeze, excluding build-related tools
DEPENDENCIES=$(pip freeze | grep -Ev '^(setuptools|wheel|twine)' | awk '{printf "    \"%s\",\n", $0}')

# Remove trailing comma from the last dependency
DEPENDENCIES=$(echo "$DEPENDENCIES" | sed '$ s/,$//')

# Append the new dependencies to the end of the file
{
	cat "$TMPFILE"
	echo "dependencies = ["
	echo "$DEPENDENCIES"
	echo "]"
} >"$PYPROJECT"

# Cleanup temporary file
rm "$TMPFILE"

echo "Updated pyproject.toml with new dependencies."
