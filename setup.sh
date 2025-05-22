#!/usr/bin/env bash
set -euo pipefail

# Install system prerequisites
apt-get update
apt-get install -y curl

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies if package.json exists
if [ -f package.json ]; then
  npm install
fi
