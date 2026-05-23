"""
Quoridor GUI - Pygame
Controls:
  - Click your pawn to select (green squares = valid moves)
  - Click a green square to move there
  - Press W to toggle wall placement mode
  - In wall mode: hover to preview, left-click to place
  - Right-click = rotate wall orientation (horizontal / vertical)
  - Z = undo, R = reset
"""

import pygame
import sys
import os
import threading
from game.board import GameState, Wall, BOARD_SIZE
from game.save_load import save_game, load_game, list_saves
from ai.opponents import AI_LEVELS

# ─── Layout ───────────────────────────────────────────────────────────────────
WINDOW_W, WINDOW_H = 920, 780
BOARD_X, BOARD_Y   = 40, 80
CELL  = 62
GAP   = 8
BOARD_PX = CELL * BOARD_SIZE + GAP * (BOARD_SIZE - 1)

# ─── Colors ───────────────────────────────────────────────────────────────────
C_BG        = (240, 237, 230)
C_BOARD     = (200, 178, 145)
C_CELL      = (230, 212, 180)
C_GOAL_P1   = (170, 215, 170)
C_GOAL_P2   = (215, 170, 170)
C_HIGHLIGHT = (100, 200, 100)
C_SELECTED  = (60,  170,  60)
C_WALL      = (75,   50,  20)
C_WALL_PRV  = (200, 150,  60)
C_WALL_BAD  = (200,  50,  50)
C_P1        = (50,  110, 200)
C_P2        = (200,  60,  50)
C_PANEL     = (248, 245, 240)
C_TEXT      = (35,   30,  25)
C_MUTED     = (130, 118, 105)
C_BTN       = (80,  120, 170)
C_BTN_H     = (55,   90, 140)
C_GREEN     = (50,  140,  80)
C_RED       = (160,  55,  40)
C_ORANGE    = (180, 110,  30)

FONT_BIG = FONT_MED = FONT_SM = None


# ─── Geometry helpers ─────────────────────────────────────────────────────────

def cell_rect(r, c):
    return pygame.Rect(BOARD_X + c*(CELL+GAP), BOARD_Y + r*(CELL+GAP), CELL, CELL)

def hwall_rect(r, c):
    return pygame.Rect(BOARD_X + c*(CELL+GAP), BOARD_Y + r*(CELL+GAP)+CELL, CELL*2+GAP, GAP)

def vwall_rect(r, c):
    return pygame.Rect(BOARD_X + c*(CELL+GAP)+CELL, BOARD_Y + r*(CELL+GAP), GAP, CELL*2+GAP)

def pos_to_cell(mx, my):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if cell_rect(r, c).collidepoint(mx, my):
                return (r, c)
    return None

def pos_to_wall(mx, my, horizontal):
    for r in range(BOARD_SIZE - 1):
        for c in range(BOARD_SIZE - 1):
            rect = hwall_rect(r, c) if horizontal else vwall_rect(r, c)
            if rect.inflate(6, 6).collidepoint(mx, my):
                return Wall(r, c, horizontal)
    return None


# ─── Button ───────────────────────────────────────────────────────────────────

class Button:
    def __init__(self, rect, label, color=None):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.base_color = color or C_BTN
        self.color = self.base_color
        self.hovered = False

    def update(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        self.color = C_BTN_H if self.hovered else self.base_color

    def draw(self, surf):
        pygame.draw.rect(surf, self.color, self.rect, border_radius=8)
        txt = FONT_SM.render(self.label, True, (255, 255, 255))
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event):
        return (event.type == pygame.MOUSEBUTTONDOWN
                and event.button == 1
                and self.rect.collidepoint(event.pos))


# ─── Menu screen ──────────────────────────────────────────────────────────────

class MenuScreen:
    def __init__(self, screen):
        self.screen   = screen
        self.sel_mode = None
        self.sel_ai   = 'Medium'
        self.btn_hvh  = Button((310, 260, 300, 50), "Human vs Human",    color=(60,100,160))
        self.btn_hvc  = Button((310, 325, 300, 50), "Human vs Computer", color=(60,100,160))
        self.btn_easy = Button((255, 415, 120, 42), "Easy",   color=(55,140,70))
        self.btn_med  = Button((390, 415, 120, 42), "Medium", color=(180,130,25))
        self.btn_hard = Button((525, 415, 120, 42), "Hard",   color=(170,50,45))
        self.btn_start= Button((330, 490, 260, 54), "Play Game", color=C_GREEN)

    def draw(self):
        s = self.screen
        s.fill(C_BG)
        t = FONT_BIG.render("QUORIDOR", True, C_TEXT)
        s.blit(t, t.get_rect(center=(460, 130)))
        sub = FONT_MED.render("Strategy Board Game  —  CSE472s", True, C_MUTED)
        s.blit(sub, sub.get_rect(center=(460, 180)))
        lbl = FONT_MED.render("Choose a game mode:", True, C_TEXT)
        s.blit(lbl, lbl.get_rect(center=(460, 228)))

        self.btn_hvh.base_color = (30,70,140) if self.sel_mode=='hvh' else (60,100,160)
        self.btn_hvc.base_color = (30,70,140) if self.sel_mode=='hvc' else (60,100,160)
        for b in [self.btn_hvh, self.btn_hvc]:
            b.draw(s)

        if self.sel_mode == 'hvc':
            al = FONT_MED.render("AI Difficulty:", True, C_TEXT)
            s.blit(al, al.get_rect(center=(460, 393)))
            for b, lv in zip([self.btn_easy,self.btn_med,self.btn_hard],['Easy','Medium','Hard']):
                if lv == self.sel_ai:
                    pygame.draw.rect(s,(255,255,255),b.rect.inflate(6,6),width=3,border_radius=10)
                b.draw(s)

        if self.sel_mode:
            self.btn_start.draw(s)

        hints = [
            "HOW TO PLAY:",
            "1. Click your pawn to select it — valid moves glow green",
            "2. Click a green square to move there",
            "3. Press W to enter Wall Mode — hover & click to place walls",
            "4. R = rotate wall  |  Z = undo  |  Right-click also rotates  |  Delete = reset",
        ]
        for i, h in enumerate(hints):
            col = C_TEXT if i == 0 else C_MUTED
            fnt = FONT_SM if i > 0 else FONT_SM
            hs = fnt.render(h, True, col)
            s.blit(hs, hs.get_rect(center=(460, 650 + i*22)))

        pygame.display.flip()

    def handle(self, event):
        mx, my = pygame.mouse.get_pos()
        for b in [self.btn_hvh,self.btn_hvc,self.btn_easy,self.btn_med,
                  self.btn_hard,self.btn_start]:
            b.update((mx, my))
        if self.btn_hvh.clicked(event):   self.sel_mode = 'hvh'
        if self.btn_hvc.clicked(event):   self.sel_mode = 'hvc'
        if self.btn_easy.clicked(event):  self.sel_ai = 'Easy'
        if self.btn_med.clicked(event):   self.sel_ai = 'Medium'
        if self.btn_hard.clicked(event):  self.sel_ai = 'Hard'
        if self.sel_mode and self.btn_start.clicked(event):
            return {'mode': self.sel_mode, 'ai': self.sel_ai}
        return None


# ─── Game screen ──────────────────────────────────────────────────────────────

class GameScreen:
    def __init__(self, screen, mode, ai_level='Medium'):
        self.screen    = screen
        self.mode      = mode
        self.ai_level  = ai_level
        self.state     = GameState()
        self.ai        = AI_LEVELS[ai_level]() if mode == 'hvc' else None

        self.selected  = None   # selected pawn cell
        self.moves     = []     # highlighted valid moves
        self.wall_mode = False
        self.wall_horiz= True
        self.preview   = None

        self.msg       = ""
        self.msg_timer = 0
        self.ai_busy   = False

        self.btn_wall  = Button((730, 130, 150, 40), "W: Wall Mode",  color=C_ORANGE)
        self.btn_undo  = Button((730, 185, 150, 38), "Z: Undo",        color=C_BTN)
        self.btn_save  = Button((730, 235, 150, 38), "Save",          color=C_BTN)
        self.btn_load  = Button((730, 285, 150, 38), "Load",          color=C_BTN)
        self.btn_reset = Button((730, 345, 150, 38), "Reset Game",     color=C_RED)
        self.btn_menu  = Button((730, 395, 150, 38), "Main Menu",     color=(90,90,100))

        self._maybe_ai()

    # ── AI ────────────────────────────────────────────────────────────────────

    def _maybe_ai(self):
        if (self.mode == 'hvc'
                and self.state.current_player == 1
                and not self.state.is_game_over()
                and not self.ai_busy):
            self.ai_busy = True
            self.msg = "AI is thinking..."
            threading.Thread(target=self._ai_turn, daemon=True).start()

    def _ai_turn(self):
        action = self.ai.choose_action(self.state)
        if action:
            if action[0] == 'move':
                self.state.move_pawn(action[1], action[2])
            else:
                self.state.place_wall(action[1])
        self.ai_busy = False
        self.msg = ""

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle(self, event):
        # Win screen buttons
        if self.state.is_game_over():
            return self._handle_win(event)

        mx, my = pygame.mouse.get_pos()
        for b in [self.btn_wall,self.btn_undo,self.btn_save,
                  self.btn_load,self.btn_reset,self.btn_menu]:
            b.update((mx, my))

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_w:
                self._toggle_wall_mode()
            if event.key == pygame.K_z:
                self._undo()
            if event.key == pygame.K_r:
                # R = rotate wall orientation
                self.wall_horiz = not self.wall_horiz
                mx2, my2 = pygame.mouse.get_pos()
                self.preview = pos_to_wall(mx2, my2, self.wall_horiz)
                ori = "Horizontal" if self.wall_horiz else "Vertical"
                self.show_msg(f"Wall rotated: {ori}")
            if event.key == pygame.K_DELETE or event.key == pygame.K_F5:
                self._reset()

        # Side buttons
        if self.btn_wall.clicked(event):  self._toggle_wall_mode()
        if self.btn_undo.clicked(event):  self._undo()
        if self.btn_save.clicked(event):  self._save()
        if self.btn_load.clicked(event):  self._load()
        if self.btn_reset.clicked(event): self._reset()
        if self.btn_menu.clicked(event):  return 'menu'

        # Wall preview on mouse move
        if event.type == pygame.MOUSEMOTION and self.wall_mode and not self.ai_busy:
            self.preview = pos_to_wall(mx, my, self.wall_horiz)

        # Board interaction
        if event.type == pygame.MOUSEBUTTONDOWN and not self.ai_busy:
            if event.button == 3:
                self.wall_horiz = not self.wall_horiz
                self.preview = pos_to_wall(mx, my, self.wall_horiz)
            elif event.button == 1:
                if self.wall_mode:
                    self._place_wall(mx, my)
                else:
                    self._click_board(mx, my)

        return None

    def _toggle_wall_mode(self):
        self.wall_mode = not self.wall_mode
        self.selected  = None
        self.moves     = []
        self.preview   = None
        if self.wall_mode:
            self.show_msg("WALL MODE: hover to preview, click to place, W to exit")
        else:
            self.show_msg("MOVE MODE: click your pawn to select it")

    def _click_board(self, mx, my):
        """Handle a left-click in move mode."""
        cell = pos_to_cell(mx, my)
        if cell is None:
            # Clicked outside board — deselect
            self.selected = None
            self.moves    = []
            return

        r, c = cell
        p = self.state.players[self.state.current_player]

        if r == p.row and c == p.col:
            # Clicked own pawn → select and show valid moves
            self.selected = cell
            self.moves    = self.state.get_pawn_moves(self.state.current_player)
            if not self.moves:
                self.show_msg("No valid moves available!")
            return

        if (r, c) in self.moves:
            # Clicked a valid destination → move pawn
            self.state.move_pawn(r, c)
            self.selected = None
            self.moves    = []
            self._maybe_ai()
            return

        # Clicked somewhere else → deselect
        self.selected = None
        self.moves    = []

    def _place_wall(self, mx, my):
        w = pos_to_wall(mx, my, self.wall_horiz)
        if w is None:
            self.show_msg("Click on the gap between cells to place a wall")
            return
        if not self.state.place_wall(w):
            self.show_msg("Invalid! Wall would block a player's path.")
        else:
            self.preview = None
            self._maybe_ai()

    def _undo(self):
        if self.state.undo():
            self.selected = None
            self.moves    = []
        else:
            self.show_msg("Nothing to undo!")

    def _save(self):
        save_game(self.state)
        self.show_msg("Game saved!")

    def _load(self):
        saves = list_saves()
        if not saves:
            self.show_msg("No saved games found!")
            return
        try:
            path = os.path.join(os.path.dirname(__file__), 'saves', saves[0])
            self.state    = load_game(path)
            self.selected = None
            self.moves    = []
            self.show_msg(f"Loaded: {saves[0]}")
        except Exception:
            self.show_msg("Failed to load save!")

    def _reset(self):
        self.state     = GameState()
        self.selected  = None
        self.moves     = []
        self.wall_mode = False
        self.preview   = None
        self.msg       = ""
        self._maybe_ai()

    def show_msg(self, text, frames=130):
        self.msg       = text
        self.msg_timer = frames

    def _handle_win(self, event):
        mx, my = pygame.mouse.get_pos()
        if hasattr(self, '_wa'):
            self._wa.update((mx, my))
            self._wm.update((mx, my))
            if self._wa.clicked(event): return 'restart'
            if self._wm.clicked(event): return 'menu'
        return None

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self):
        self.screen.fill(C_BG)
        self._draw_board()
        self._draw_panel()
        self._draw_msg()
        if self.msg_timer > 0:
            self.msg_timer -= 1
            if self.msg_timer == 0 and not self.ai_busy:
                self.msg = ""
        if self.state.is_game_over():
            self._draw_win_overlay()
        pygame.display.flip()

    def _draw_board(self):
        s = self.screen
        bg = pygame.Rect(BOARD_X-12, BOARD_Y-12, BOARD_PX+24, BOARD_PX+24)
        pygame.draw.rect(s, C_BOARD, bg, border_radius=12)

        for c in range(BOARD_SIZE):
            pygame.draw.rect(s, C_GOAL_P1, cell_rect(BOARD_SIZE-1, c), border_radius=4)
            pygame.draw.rect(s, C_GOAL_P2, cell_rect(0, c), border_radius=4)

        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                color = (C_SELECTED if self.selected==(r,c)
                         else C_HIGHLIGHT if (r,c) in self.moves
                         else C_CELL)
                pygame.draw.rect(s, color, cell_rect(r,c), border_radius=4)

        # Labels
        for i in range(BOARD_SIZE):
            cx = BOARD_X + i*(CELL+GAP) + CELL//2
            lb = FONT_SM.render(str(i+1), True, C_MUTED)
            s.blit(lb, lb.get_rect(center=(cx, BOARD_Y+BOARD_PX+16)))
            lb2 = FONT_SM.render(chr(65+i), True, C_MUTED)
            s.blit(lb2, lb2.get_rect(center=(BOARD_X-18, BOARD_Y+i*(CELL+GAP)+CELL//2)))

        # Placed walls
        for w in self.state.walls:
            rect = hwall_rect(w.row,w.col) if w.horizontal else vwall_rect(w.row,w.col)
            pygame.draw.rect(s, C_WALL, rect, border_radius=3)

        # Preview
        if self.wall_mode and self.preview and not self.ai_busy:
            valid = self.state.can_place_wall(self.preview)
            color = C_WALL_PRV if valid else C_WALL_BAD
            rect = (hwall_rect(self.preview.row,self.preview.col) if self.preview.horizontal
                    else vwall_rect(self.preview.row,self.preview.col))
            surf = pygame.Surface((rect.width,rect.height), pygame.SRCALPHA)
            surf.fill((*color, 180))
            s.blit(surf, rect.topleft)

        # Pawns
        for pid, p in enumerate(self.state.players):
            cr = cell_rect(p.row, p.col)
            cx, cy = cr.center
            col = C_P1 if pid==0 else C_P2
            pygame.draw.circle(s, col, (cx,cy), CELL//2-5)
            pygame.draw.circle(s, (255,255,255), (cx,cy), CELL//2-5, 2)
            lbl = FONT_SM.render(f"P{pid+1}", True, (255,255,255))
            s.blit(lbl, lbl.get_rect(center=(cx,cy)))

        # "click me" hint
        if not self.wall_mode and not self.selected and not self.ai_busy:
            p = self.state.players[self.state.current_player]
            cr = cell_rect(p.row, p.col)
            hint = FONT_SM.render("click!", True, C_MUTED)
            s.blit(hint, (cr.right+4, cr.centery-7))

    def _draw_panel(self):
        s = self.screen
        panel = pygame.Rect(715, 70, 185, 590)
        pygame.draw.rect(s, C_PANEL, panel, border_radius=10)
        pygame.draw.rect(s, (200,190,180), panel, width=1, border_radius=10)

        cp = self.state.current_player
        col = C_P1 if cp==0 else C_P2
        turn = FONT_MED.render(f"Player {cp+1}'s turn", True, col)
        s.blit(turn, turn.get_rect(center=(807, 97)))

        self.btn_wall.base_color = C_ORANGE if self.wall_mode else C_BTN
        self.btn_wall.label = "W: Move Mode" if self.wall_mode else "W: Wall Mode"

        for b in [self.btn_wall,self.btn_undo,self.btn_save,
                  self.btn_load,self.btn_reset,self.btn_menu]:
            b.draw(s)

        for pid, p in enumerate(self.state.players):
            col = C_P1 if pid==0 else C_P2
            y = 460 + pid*60
            nm = FONT_MED.render(f"Player {pid+1}", True, col)
            s.blit(nm, (730, y))
            wl = FONT_SM.render(f"Walls left: {p.walls}", True, C_TEXT)
            s.blit(wl, (730, y+24))

        mode_str = "Human vs Human" if self.mode=='hvh' else f"vs AI ({self.ai_level})"
        ml = FONT_SM.render(mode_str, True, C_MUTED)
        s.blit(ml, ml.get_rect(center=(807, 600)))

        ori = "Horizontal" if self.wall_horiz else "Vertical"
        ol = FONT_SM.render(f"Wall: {ori}  |  R key or right-click", True, C_MUTED)
        s.blit(ol, ol.get_rect(center=(807, 620)))

        # Goal labels on board
        p1g = FONT_SM.render("P1 goal →", True, (80,140,80))
        s.blit(p1g, (BOARD_X+BOARD_PX+4, BOARD_Y+BOARD_PX-10))
        p2g = FONT_SM.render("P2 goal →", True, (140,80,80))
        s.blit(p2g, (BOARD_X+BOARD_PX+4, BOARD_Y+4))

    def _draw_msg(self):
        if not self.msg:
            return
        surf = FONT_SM.render(self.msg, True, C_TEXT)
        rect = surf.get_rect(center=(370, 48))
        bg = rect.inflate(24, 12)
        pygame.draw.rect(self.screen, C_PANEL, bg, border_radius=8)
        pygame.draw.rect(self.screen, (190,180,170), bg, width=1, border_radius=8)
        self.screen.blit(surf, rect)

    def _draw_win_overlay(self):
        s = self.screen
        ov = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
        ov.fill((0,0,0,150))
        s.blit(ov, (0,0))

        card = pygame.Rect(185, 240, 550, 240)
        pygame.draw.rect(s, C_PANEL, card, border_radius=16)

        w = self.state.winner
        col = C_P1 if w==0 else C_P2
        title = FONT_BIG.render(f"Player {w+1} Wins!", True, col)
        s.blit(title, title.get_rect(center=(460, 305)))
        sub = FONT_MED.render("Reached the opposite side!", True, C_MUTED)
        s.blit(sub, sub.get_rect(center=(460, 355)))

        self._wa = Button((210, 400, 200, 50), "Play Again", color=C_GREEN)
        self._wm = Button((510, 400, 200, 50), "Main Menu",  color=(90,90,100))
        self._wa.draw(s)
        self._wm.draw(s)


# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    global FONT_BIG, FONT_MED, FONT_SM
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Quoridor")
    clock = pygame.time.Clock()

    try:
        FONT_BIG = pygame.font.SysFont("Georgia", 40, bold=True)
        FONT_MED = pygame.font.SysFont("Arial", 20)
        FONT_SM  = pygame.font.SysFont("Arial", 14)
    except Exception:
        FONT_BIG = pygame.font.Font(None, 46)
        FONT_MED = pygame.font.Font(None, 26)
        FONT_SM  = pygame.font.Font(None, 19)

    screen_name = 'menu'
    menu = MenuScreen(screen)
    game = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if screen_name == 'menu':
                result = menu.handle(event)
                if result:
                    game = GameScreen(screen, result['mode'], result['ai'])
                    screen_name = 'game'

            elif screen_name == 'game':
                result = game.handle(event)
                if result == 'menu':
                    menu = MenuScreen(screen)
                    screen_name = 'menu'
                elif result == 'restart':
                    game = GameScreen(screen, game.mode, game.ai_level)

        if screen_name == 'menu':
            menu.draw()
        elif screen_name == 'game':
            game.draw()

        clock.tick(60)


if __name__ == '__main__':
    main()
