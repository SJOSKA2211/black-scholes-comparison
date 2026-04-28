web: python3 -m uvicorn --version || python3 -m pip install uvicorn[standard] && PYTHONPATH=apps/api python3 -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
