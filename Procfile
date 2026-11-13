api: cd backend && uv run fastapi dev src/fastapi.py --port 4000
voice: cd backend && SERVICE_NAME=voice uv run fastapi dev src/fastapi.py --port 4001
mcp: cd mcp-server && uv run uvicorn src.main:app --port 4501 --reload
frontend: cd frontend && npm run dev
