#!/bin/bash
# shellcheck disable=SC1091

activate_env() {
	if [ -f "venv/bin/activate" ]; then
		echo "Virtual environment found. Activating..."
		source "venv/bin/activate"
	else
		echo "Error: Virtual environment not found at venv/bin/activate"
		exit 1
	fi
}

unit() {
	echo "Run unit tests..."
	python -m unittest discover tests.unit
}

backtest() {
	echo "Run backtest integration test..."
	python -m unittest discover tests.integration.backtest
}

live() {
	echo "Running live integration test..."
	python -m unittest discover tests.integration.live
}

options() {
	echo "Which tests would you like to run?"
	echo "1 - Unit"
	echo "2 - Backtest Integration"
	echo "3 - Live Integration"
}

# Main
while true; do
	activate_env
	options
	read -r option

	case $option in
	1)
		unit
		break
		;;
	2)
		backtest
		break
		;;
	3)
		live
		break
		;;
	*) echo "Please choose a different one." ;;
	esac
done
