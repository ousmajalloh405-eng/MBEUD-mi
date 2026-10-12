#!/bin/sh
set -eu

export API_URL="${API_URL:-http://127.0.0.1:8000}"

# The API stays local to the container; only Streamlit is exposed publicly.
uvicorn api.main:app --host 127.0.0.1 --port 8000 &
API_PID=$!

cleanup() {
    kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# Wait for the API before allowing the dashboard to make requests.
python - <<'PY'
import time
import urllib.request

url = "http://127.0.0.1:8000/health"
last_error = None

for _ in range(30):
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status == 200:
                break
    except Exception as exc:
        last_error = exc
    time.sleep(1)
else:
    raise SystemExit(f"API non prête après 30 secondes : {last_error}")
PY

exec streamlit run dashboard/app.py \
    --server.port="${PORT:-10000}" \
    --server.address=0.0.0.0 \
    --server.headless=true
