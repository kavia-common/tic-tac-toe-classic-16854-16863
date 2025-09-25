from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal
from uuid import uuid4

# In-memory storage for games; in production, replace with persistent storage
_GAMES: Dict[str, Dict] = {}


# PUBLIC_INTERFACE
class NewGameResponse(BaseModel):
    """Response model returned after starting a new game."""
    game_id: str = Field(..., description="Unique identifier for the new game.")
    board: List[List[Optional[Literal['X', 'O']]]] = Field(
        ..., description="3x3 board initialized with nulls."
    )
    next_player: Literal["X", "O"] = Field(..., description="Player who moves first.")
    status: Literal["in_progress", "won", "draw"] = Field(..., description="Current game status.")


# PUBLIC_INTERFACE
class MoveRequest(BaseModel):
    """Request model to make a move on the board."""
    row: int = Field(..., ge=0, le=2, description="Row index (0-2).")
    col: int = Field(..., ge=0, le=2, description="Column index (0-2).")
    player: Literal["X", "O"] = Field(..., description="Player making the move.")


# PUBLIC_INTERFACE
class GameStateResponse(BaseModel):
    """Response model representing current game state."""
    game_id: str = Field(..., description="Unique game identifier.")
    board: List[List[Optional[Literal['X', 'O']]]] = Field(..., description="3x3 board state.")
    next_player: Optional[Literal["X", "O"]] = Field(
        None, description="Next player if the game is still in progress; null otherwise."
    )
    status: Literal["in_progress", "won", "draw"] = Field(..., description="Current game status.")
    winner: Optional[Literal["X", "O"]] = Field(
        None, description="Winner of the game if status is 'won', otherwise null."
    )


def _new_board() -> List[List[Optional[str]]]:
    """Create a new 3x3 board."""
    return [[None for _ in range(3)] for _ in range(3)]


def _check_winner(board: List[List[Optional[str]]]) -> Optional[str]:
    """Check the board for a winner and return 'X' or 'O' if found, else None."""
    lines = []

    # Rows and columns
    for i in range(3):
        lines.append(board[i])  # row
        lines.append([board[0][i], board[1][i], board[2][i]])  # column

    # Diagonals
    lines.append([board[0][0], board[1][1], board[2][2]])
    lines.append([board[0][2], board[1][1], board[2][0]])

    for line in lines:
        if line[0] is not None and line.count(line[0]) == 3:
            return line[0]
    return None


def _is_draw(board: List[List[Optional[str]]]) -> bool:
    """Return True if the board is full and there is no winner."""
    for row in board:
        if any(cell is None for cell in row):
            return False
    return _check_winner(board) is None


def _get_status(board: List[List[Optional[str]]]) -> Literal["in_progress", "won", "draw"]:
    """Compute and return game status from board state."""
    if _check_winner(board):
        return "won"
    if _is_draw(board):
        return "draw"
    return "in_progress"


# Initialize FastAPI with Ocean Professional theme metadata for docs
app = FastAPI(
    title="Tic-Tac-Toe API",
    description=(
        "Modern, minimal Tic-Tac-Toe API following the Ocean Professional theme.\n\n"
        "Play by starting a new game, making moves, and checking the game state."
    ),
    version="1.0.0",
    contact={"name": "Tic-Tac-Toe Backend", "url": "https://example.com"},
    terms_of_service="https://example.com/terms",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def custom_openapi():
    """
    Generate a custom OpenAPI schema that reflects Ocean Professional theme via metadata.
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Tic-Tac-Toe API",
        version="1.0.0",
        description="Modern, minimal Tic-Tac-Toe API. Ocean Professional theme.",
        routes=app.routes,
    )
    # Tag definitions with descriptions (grouping)
    openapi_schema["tags"] = [
        {"name": "Health", "description": "Service health checks."},
        {"name": "Game", "description": "Tic-Tac-Toe game lifecycle and moves."},
    ]
    # Add theme metadata (non-standard) to guide docs styling (informational)
    openapi_schema["x-theme"] = {
        "name": "Ocean Professional",
        "primary": "#2563EB",
        "secondary": "#F59E0B",
        "success": "#F59E0B",
        "error": "#EF4444",
        "background": "#f9fafb",
        "surface": "#ffffff",
        "text": "#111827",
        "gradient": "from-blue-500/10 to-gray-50",
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# PUBLIC_INTERFACE
@app.get("/", summary="Health Check", tags=["Health"])
def health_check():
    """
    Health check endpoint to verify service availability.
    Returns a simple JSON message.
    """
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/games",
    summary="Start New Game",
    description="Creates a new Tic-Tac-Toe game with an empty 3x3 board. 'X' moves first.",
    response_model=NewGameResponse,
    tags=["Game"],
    responses={
        201: {"description": "Game created successfully."}
    },
)
def start_new_game():
    """
    Start a new game of Tic-Tac-Toe.

    Returns:
        NewGameResponse: Contains the game_id, initial board, next player, and status.
    """
    game_id = str(uuid4())
    board = _new_board()
    next_player = "X"
    _GAMES[game_id] = {
        "board": board,
        "next_player": next_player,
        "winner": None,
        "status": "in_progress",
    }
    return JSONResponse(
        status_code=201,
        content=NewGameResponse(
            game_id=game_id,
            board=board,
            next_player=next_player,
            status="in_progress",
        ).model_dump(),
    )


# PUBLIC_INTERFACE
@app.get(
    "/games/{game_id}",
    summary="Get Game State",
    description="Retrieve the current game state, including board, next player, and status.",
    response_model=GameStateResponse,
    tags=["Game"],
    responses={
        404: {"description": "Game not found."}
    },
)
def get_game_state(game_id: str):
    """
    Get the current state of a specific game.

    Parameters:
        game_id (str): Unique identifier of the game.

    Returns:
        GameStateResponse: Current board, next player (if applicable), status, and winner if any.
    """
    game = _GAMES.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")

    board = game["board"]
    winner = _check_winner(board)
    status = _get_status(board)
    next_player = None if status != "in_progress" else game["next_player"]

    return GameStateResponse(
        game_id=game_id,
        board=board,
        next_player=next_player,
        status=status,
        winner=winner,
    )


# PUBLIC_INTERFACE
@app.post(
    "/games/{game_id}/moves",
    summary="Make a Move",
    description=(
        "Make a move for a given player at (row, col). Validates turn order, bounds, and cell availability. "
        "Updates the game state and returns the updated board and status."
    ),
    response_model=GameStateResponse,
    tags=["Game"],
    responses={
        400: {"description": "Invalid move or game state."},
        404: {"description": "Game not found."},
    },
)
def make_move(game_id: str, move: MoveRequest):
    """
    Make a move for the specified player.

    Parameters:
        game_id (str): The game identifier.
        move (MoveRequest): The move details including row, col, and player.

    Returns:
        GameStateResponse: Updated game state after the move.
    """
    game = _GAMES.get(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found.")

    board = game["board"]
    status = _get_status(board)
    if status != "in_progress":
        raise HTTPException(status_code=400, detail=f"Game is already {status}.")

    if move.player != game["next_player"]:
        raise HTTPException(status_code=400, detail=f"It is {game['next_player']}'s turn.")

    r, c = move.row, move.col
    if board[r][c] is not None:
        raise HTTPException(status_code=400, detail="Cell is already occupied.")

    # Apply move
    board[r][c] = move.player

    # Compute new status and winner
    winner = _check_winner(board)
    if winner:
        game["winner"] = winner
        game["status"] = "won"
        game["next_player"] = None
    elif _is_draw(board):
        game["status"] = "draw"
        game["next_player"] = None
    else:
        game["status"] = "in_progress"
        game["next_player"] = "O" if move.player == "X" else "X"

    return GameStateResponse(
        game_id=game_id,
        board=board,
        next_player=game["next_player"],
        status=game["status"],
        winner=game.get("winner"),
    )
