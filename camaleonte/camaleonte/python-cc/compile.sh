#!/bin/bash

# Exit on error
set -e

# Check number of arguments
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <python_file.py> <venv_directory>"
  exit 1
fi

PYTHON_FILE="$1"
VENV_DIR="$2"

# Check if the Python file exists
if [ ! -f "$PYTHON_FILE" ]; then
  echo "Error: Python file '$PYTHON_FILE' does not exist."
  exit 2
fi

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR/bin" ]; then
  echo "Error: Virtual environment directory '$VENV_DIR' is invalid."
  exit 3
fi

# Activate the virtual environment
source "$VENV_DIR/bin/activate"

# Compile the Python file
nuitka client.py --standalone --onefile

echo "Compilation complete: $PYTHON_FILE"

# Deactivate the virtual environment
deactivate


