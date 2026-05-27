"""
Quoridor Game Board - Core Logic
Handles game state, rules, wall placement, movement, and pathfinding.
"""

from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Set
import copy

BOARD_SIZE = 9

@dataclass
class Wall:
    """A wall segment. row,col = top-left corner of the 2-cell wall."""
    row: int
    col: int
    horizontal: bool  # True=horizontal, False=vertical

    def cells_blocked(self):
        """Returns the list of (row,col,direction) edges this wall blocks."""
        blocked = []
        if self.horizontal:
            # Blocks movement between row and row+1 for cols col and col+1
            blocked.append((self.row, self.col, 'S'))
            blocked.append((self.row, self.col + 1, 'S'))
            blocked.append((self.row + 1, self.col, 'N'))
            blocked.append((self.row + 1, self.col + 1, 'N'))
        else:
            # Blocks movement between col and col+1 for rows row and row+1
            blocked.append((self.row, self.col, 'E'))
            blocked.append((self.row + 1, self.col, 'E'))
            blocked.append((self.row, self.col + 1, 'W'))
            blocked.append((self.row + 1, self.col + 1, 'W'))
        return blocked

    def occupies(self):
        """Returns the two wall slots this wall occupies."""
        if self.horizontal:
            return [(self.row, self.col, True), (self.row, self.col + 1, True)]
        else:
            return [(self.row, self.col, False), (self.row + 1, self.col, False)]


@dataclass
class Player:
    row: int
    col: int
    walls: int
    player_id: int  # 0 or 1

    @property
    def goal_row(self):
        return BOARD_SIZE - 1 if self.player_id == 0 else 0

    def has_won(self):
        return self.row == self.goal_row


class GameState:
    """Complete game state for Quoridor."""

    def __init__(self):
        self.players = [
            Player(0, BOARD_SIZE // 2, 10, 0),   # P1: top center, goal = row 8
            Player(BOARD_SIZE - 1, BOARD_SIZE // 2, 10, 1),  # P2: bottom center, goal = row 0
        ]
        self.walls: List[Wall] = []
        self.current_player = 0
        self.winner: Optional[int] = None
        self.move_history: List[dict] = []  # for undo
        self._blocked_edges: Set[Tuple] = set()  # cache

    def copy(self):
        return copy.deepcopy(self)

    # ─── Edge / movement helpers ─────────────────────────────────────────────

    def _compute_blocked_edges(self):
        blocked = set()
        for w in self.walls:
            for edge in w.cells_blocked():
                blocked.add(edge)
        return blocked

    def is_blocked(self, row, col, direction):
        """Is movement from (row,col) in given direction blocked by a wall?"""
        edges = self._compute_blocked_edges()
        return (row, col, direction) in edges

    def in_bounds(self, row, col):
        return 0 <= row < BOARD_SIZE and 0 <= col < BOARD_SIZE

    DELTAS = {'N': (-1, 0), 'S': (1, 0), 'E': (0, 1), 'W': (0, -1)}
    OPPOSITE = {'N': 'S', 'S': 'N', 'E': 'W', 'W': 'E'}

    def get_pawn_moves(self, player_id: int) -> List[Tuple[int, int]]:
        """Return all valid destination squares for the given player's pawn."""
        p = self.players[player_id]
        opp = self.players[1 - player_id]
        moves = []

        for d, (dr, dc) in self.DELTAS.items():
            nr, nc = p.row + dr, p.col + dc
            if not self.in_bounds(nr, nc):
                continue
            if self.is_blocked(p.row, p.col, d):
                continue
            # Square occupied by opponent?
            if nr == opp.row and nc == opp.col:
                # Try to jump over
                jr, jc = nr + dr, nc + dc
                if self.in_bounds(jr, jc) and not self.is_blocked(nr, nc, d):
                    moves.append((jr, jc))
                else:
                    # Can't jump straight — try diagonal jumps
                    for sd, (sdr, sdc) in self.DELTAS.items():
                        if sd == d or sd == self.OPPOSITE[d]:
                            continue
                        diag_r, diag_c = nr + sdr, nc + sdc
                        if self.in_bounds(diag_r, diag_c) and not self.is_blocked(nr, nc, sd):
                            moves.append((diag_r, diag_c))
            else:
                moves.append((nr, nc))

        return list(set(moves))

    # ─── Wall placement ───────────────────────────────────────────────────────

    def _wall_slot_taken(self, wall: Wall) -> bool:
        """Check if this wall overlaps any existing wall."""
        new_slots = set(wall.occupies())
        for w in self.walls:
            for slot in w.occupies():
                if slot in new_slots:
                    return True
        # Also check center-cross conflict (horizontal + vertical sharing anchor)
        # Two walls cross if one horizontal at (r,c) and one vertical at (r,c)
        for w in self.walls:
            if w.horizontal != wall.horizontal:
                # They cross if they share the same anchor cell in opposite orientation
                if w.horizontal and not wall.horizontal:
                    # existing horiz (wr,wc), new vert (r,c):
                    # cross if wall crosses: wr==r and c==wc or c==wc+1 checked by slots above
                    pass
        return False

    def _walls_cross(self, w1: Wall, w2: Wall) -> bool:
        if w1.horizontal == w2.horizontal:
            return False
        # Horizontal w_h and vertical w_v cross if:
        # w_h.row == w_v.row and w_h.col == w_v.col  (same anchor, different orientation)
        wh = w1 if w1.horizontal else w2
        wv = w1 if not w1.horizontal else w2
        return wh.row == wv.row and wh.col == wv.col

    def can_place_wall(self, wall: Wall) -> bool:
        """Check if wall placement is legal (no overlap, no complete blockage)."""
        if self.players[self.current_player].walls <= 0:
            return False
        # Bounds check: walls go on edges between cells, so max index is BOARD_SIZE-2
        if wall.horizontal:
            if not (0 <= wall.row <= BOARD_SIZE - 2 and 0 <= wall.col <= BOARD_SIZE - 2):
                return False
        else:
            if not (0 <= wall.row <= BOARD_SIZE - 2 and 0 <= wall.col <= BOARD_SIZE - 2):
                return False

        # Check overlap with existing walls
        if self._wall_slot_taken(wall):
            return False
        # Check crossing
        for w in self.walls:
            if self._walls_cross(w, wall):
                return False

        # Temporarily place wall and check pathfinding
        self.walls.append(wall)
        valid = self._both_players_have_path()
        self.walls.pop()
        return valid

    def _both_players_have_path(self) -> bool:
        for pid in range(2):
            if not self._has_path(pid):
                return False
        return True

    def _has_path(self, player_id: int) -> bool:
        """BFS to check if player can reach their goal row."""
        p = self.players[player_id]
        goal_row = p.goal_row
        start = (p.row, p.col)
        visited = {start}
        queue = deque([start])
        blocked = self._compute_blocked_edges()

        while queue:
            r, c = queue.popleft()
            if r == goal_row:
                return True
            for d, (dr, dc) in self.DELTAS.items():
                nr, nc = r + dr, c + dc
                if self.in_bounds(nr, nc) and (nr, nc) not in visited:
                    if (r, c, d) not in blocked:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
        return False

    def shortest_path(self, player_id: int) -> int:
        """BFS shortest path length to goal for given player. Returns inf if blocked."""
        p = self.players[player_id]
        goal_row = p.goal_row
        start = (p.row, p.col)
        visited = {start: 0}
        queue = deque([(start, 0)])
        blocked = self._compute_blocked_edges()

        while queue:
            (r, c), dist = queue.popleft()
            if r == goal_row:
                return dist
            for d, (dr, dc) in self.DELTAS.items():
                nr, nc = r + dr, c + dc
                if self.in_bounds(nr, nc) and (nr, nc) not in visited:
                    if (r, c, d) not in blocked:
                        visited[(nr, nc)] = dist + 1
                        queue.append(((nr, nc), dist + 1))
        return float('inf')

    def get_valid_walls(self) -> List[Wall]:
        """Return all legal wall placements for current player."""
        walls = []
        for r in range(BOARD_SIZE - 1):
            for c in range(BOARD_SIZE - 1):
                for horiz in [True, False]:
                    w = Wall(r, c, horiz)
                    if self.can_place_wall(w):
                        walls.append(w)
        return walls

    # ─── Actions ─────────────────────────────────────────────────────────────

    def move_pawn(self, row: int, col: int):
        """Move current player's pawn. Returns True if successful."""
        moves = self.get_pawn_moves(self.current_player)
        if (row, col) not in moves:
            return False

        snapshot = self._snapshot()
        p = self.players[self.current_player]
        p.row, p.col = row, col
        self.move_history.append({'type': 'move', 'snapshot': snapshot})

        if p.has_won():
            self.winner = self.current_player
        else:
            self.current_player = 1 - self.current_player
        return True

    def place_wall(self, wall: Wall) -> bool:
        """Place wall for current player. Returns True if successful."""
        if not self.can_place_wall(wall):
            return False

        snapshot = self._snapshot()
        self.walls.append(wall)
        self.players[self.current_player].walls -= 1
        self.move_history.append({'type': 'wall', 'snapshot': snapshot})
        self.current_player = 1 - self.current_player
        return True

    # ─── Undo / redo ─────────────────────────────────────────────────────────

    def _snapshot(self):
        return {
            'players': copy.deepcopy(self.players),
            'walls': copy.deepcopy(self.walls),
            'current_player': self.current_player,
            'winner': self.winner,
        }

    def undo(self) -> bool:
        if not self.move_history:
            return False
        snap = self.move_history.pop()['snapshot']
        self.players = snap['players']
        self.walls = snap['walls']
        self.current_player = snap['current_player']
        self.winner = snap['winner']
        return True

    def is_game_over(self) -> bool:
        return self.winner is not None

    def get_all_valid_actions(self):
        """Returns list of all valid actions: ('move', r, c) or ('wall', Wall)"""
        actions = []
        for r, c in self.get_pawn_moves(self.current_player):
            actions.append(('move', r, c))
        if self.players[self.current_player].walls > 0:
            for w in self.get_valid_walls():
                actions.append(('wall', w))
        return actions
