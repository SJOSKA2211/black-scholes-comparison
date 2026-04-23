#!/bin/bash
cd apps/api
set -a
source .env
set +a
.venv/bin/python -m pytest tests/integration/ -m integration --cov=src --cov-branch --cov-append --cov-fail-under=100
