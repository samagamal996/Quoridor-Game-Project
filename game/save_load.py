"""
Game save/load functionality using JSON.
"""

import json
import os
from datetime import datetime
from game.board import GameState, Wall, Player, BOARD_SIZE

SAVES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'saves')


def save_game(state: GameState, filename: str = None) -> str:
    os.makedirs(SAVES_DIR, exist_ok=True)
    if filename is None:
        filename = f"quoridor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = os.path.join(SAVES_DIR, filename)

    data = {
        'players': [
            {'row': p.row, 'col': p.col, 'walls': p.walls, 'player_id': p.player_id}
            for p in state.players
        ],
        'walls': [
            {'row': w.row, 'col': w.col, 'horizontal': w.horizontal}
            for w in state.walls
        ],
        'current_player': state.current_player,
        'winner': state.winner,
    }

    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    return path


def load_game(path: str) -> GameState:
    with open(path, 'r') as f:
        data = json.load(f)

    state = GameState.__new__(GameState)
    state.players = [
        Player(p['row'], p['col'], p['walls'], p['player_id'])
        for p in data['players']
    ]
    state.walls = [
        Wall(w['row'], w['col'], w['horizontal'])
        for w in data['walls']
    ]
    state.current_player = data['current_player']
    state.winner = data['winner']
    state.move_history = []
    return state


def list_saves():
    os.makedirs(SAVES_DIR, exist_ok=True)
    files = [f for f in os.listdir(SAVES_DIR) if f.endswith('.json')]
    return sorted(files, reverse=True)
