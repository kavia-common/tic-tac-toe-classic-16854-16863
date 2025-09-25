# Tic-Tac-Toe Backend API

Modern, minimal FastAPI backend implementing a Tic-Tac-Toe game following the "Ocean Professional" theme.

## Run

- Install dependencies:
  pip install -r requirements.txt

- Start server:
  uvicorn src.api.main:app --host 0.0.0.0 --port 3001 --reload

Docs:
- OpenAPI JSON: /openapi.json
- Swagger UI: /docs
- ReDoc: /redoc

## Endpoints

- GET /              Health check
- POST /games        Start a new game (X goes first)
- GET /games/{id}    Get game state
- POST /games/{id}/moves  Make a move: { "row": 0..2, "col": 0..2, "player": "X"|"O" }

Notes:
- In-memory storage for simplicity; replace with persistent store for production.
- Includes basic validation and clear error responses.
