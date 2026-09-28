#!/usr/bin/env bash
set -e
python3 -m pip install -r requirements.txt
python3 collector/collector.py || true
python3 -m http.server 8000
