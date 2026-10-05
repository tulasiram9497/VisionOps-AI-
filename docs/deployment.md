# Deployment

## Local development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd frontend && npm install
```

Then start the backend and frontend separately.

## Docker

```bash
docker compose up --build
```

This runs the backend on port 8000 and the frontend on port 3000. Note that direct webcam access from Docker may be limited on macOS and Windows. When that happens, run the backend locally on the host machine or use a video file input.
