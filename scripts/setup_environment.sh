#!/usr/bin/env bash
# Sets up a Python venv and installs requirements for local dev.

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "Done. Activate venv with: source .venv/bin/activate"
