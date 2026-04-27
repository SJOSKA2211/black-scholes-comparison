web: PYTHONPATH=apps/api python apps/api/scripts/deployment_check.py && PYTHONPATH=apps/api python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2

