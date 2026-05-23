# Quoridor Game
A complete Python/Pygame implementation of the Quoridor board game with AI opponents.

## Game Description
Quoridor is an abstract strategy board game played on a 9×9 grid. Each player has a pawn and 10 walls. The goal is to be the first to move your pawn to the opposite side of the board. On each turn, you either move your pawn one square (orthogonally) or place a 2-square wall to impede your opponent. The key constraint: walls can never completely block a player's path to their goal.

## Features
- **Human vs Human** local multiplayer
- **Human vs Computer** with 3 AI difficulty levels (Easy / Medium / Hard)
- Full Quoridor rule enforcement (jump over pawns, diagonal escapes, wall blocking validation)
- Valid move highlighting and wall placement preview
- **Undo** move at any time
- **Save / Load** game state (JSON)
- Win detection and victory screen
- Clean, responsive Pygame GUI

## Installation
### Requirements
- Python 3.8 or newer
- pygame

### Install dependencies
```bash
pip install pygame
```

### Run the game
```bash
python main.py
```

## Controls
| Action | Control |
|---|---|
| Select / move pawn | Left-click on your pawn, then click a highlighted square |
| Place a wall | Hover near the edge between cells (preview shown), then left-click |
| Rotate wall orientation | Right-click anywhere |
| Toggle Wall Mode | Click "Wall Mode" button in the side panel |
| Undo last move | Click "↩ Undo" |
| Save game | Click "💾 Save" |
| Load last save | Click "📂 Load" |
| Reset game | Click "↺ Reset" |

## Project Structure
```
quoridor/
├── main.py                # Entry point + Pygame GUI
├── game/
│   ├── board.py           # Core game logic, rules, pathfinding (BFS)
│   └── save_load.py       # Save/load game state to JSON
├── ai/
│   └── opponents.py       # Easy / Medium / Hard AI
├── saves/                 # Saved games (auto-created)
└── README.md
```

## AI Algorithm Explanation

### Easy AI
Selects a random valid action from all legal moves and wall placements. Suitable for beginners.

### Medium AI (Greedy Heuristic)
Uses a greedy strategy with two priorities:
1. **Win immediately** if possible.
2. **Place a wall** when the opponent is close (< 5 squares from goal) and the wall would significantly increase their path (net gain ≥ 2 squares).
3. Otherwise, **advance pawn** along the shortest path to goal using BFS.

### Hard AI (Minimax with Alpha-Beta Pruning)
Implements depth-3 minimax search with alpha-beta pruning:
- **Evaluation function**: `(opponent_path_length - own_path_length) × 10 + wall_advantage × 2`
- **Action ordering**: pawn moves first, then top-scoring wall placements (up to 6 candidates), which greatly speeds up alpha-beta cutoffs
- **Terminal detection**: immediate win/loss returns ±1000; depth-0 uses heuristic

The pathfinding (BFS) runs in O(N²) per call and is the main computational bottleneck. By limiting wall candidates and using alpha-beta pruning, the Hard AI achieves depth-3 search in interactive time.

## Assumptions
- 2-player mode only (as specified)
- Saves store only the most recent game state (not move history) for simplicity
- The Load button loads the most recently saved game
- Diagonal jumps are only available when a straight jump is blocked by a wall or board edge

## References
- Official Quoridor Rules — BoardGameGeek
- BFS Pathfinding: Introduction to Algorithms (Cormen et al.)
- Minimax/Alpha-Beta: Russell & Norvig, *Artificial Intelligence: A Modern Approach*
- Pygame Documentation: https://www.pygame.org/docs/

## Demo Video
*(Add YouTube/Drive link here)*

## Team Members
- Sama Gamal 2300371
- Ahmed Moataz 2301040
- Menna Osama 2300515
- Malak Mamdoh 2300428
