#!/bin/bash
# shellcheck disable=SC1091

TYPE=$1
ENV=$2

VENV="venv"

if [ -f "$VENV/bin/activate" ]; then
	echo "Virtual environment found. Activating..."
	source "$VENV/bin/activate"
else
	echo "Error: Virtual environment not found at $VENV/bin/activate"
	exit 1
fi

if [ "$TYPE" = "unit" ]; then
	echo "Run backtest integration test..."
	python -m unittest discover
elif [ "$TYPE" = "integration" ]; then
	if [ "$ENV" = "backtest" ]; then
		echo "Run backtest integration test..."
		python -m unittest discover tests.integration.backtest
	elif [ "$ENV" = "live" ]; then
		echo "Running live integration test..."
		python -m unittest discover tests.integration.live
	else
		echo "$ENV: is invalid"
	fi
else
	echo "$TYPE: is invalid"
fi
