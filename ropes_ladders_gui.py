import pygame
import sys
import math
import time
from typing import List, Tuple, Optional, Dict
from enum import Enum

# Import our existing game logic and new AI system
from ropes_ladders_game import GameState, Player, ActionType, OptimizedMinimaxAgent, Direction, GamePhase
from minimax_pruning import MinimaxPruning

# Initialize Pygame
pygame.init()

# Colors
class Colors:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (128, 128, 128)
    LIGHT_GRAY = (220, 220, 220)
    DARK_GRAY = (64, 64, 64)
    
    # Player colors
    BLUE = (52, 152, 219)
    RED = (231, 76, 60)
    LIGHT_BLUE = (174, 214, 241)
    LIGHT_RED = (245, 183, 177)
    
    # UI colors
    GREEN = (46, 204, 113)
    YELLOW = (241, 196, 15)
    ORANGE = (230, 126, 34)
    PURPLE = (155, 89, 182)
    
    # Board colors
    BOARD_LIGHT = (245, 245, 245)
    BOARD_DARK = (235, 235, 235)
    BOARD_BORDER = (189, 195, 199)
    PRIZE_COLOR = (255, 215, 0)
    
    # Button colors
    BUTTON_NORMAL = (52, 152, 219)
    BUTTON_HOVER = (41, 128, 185)
    BUTTON_PRESSED = (21, 67, 96)

class GameMode(Enum):
    MENU = "menu"
    GAME = "game"
    SETTINGS = "settings"
    GAME_OVER = "game_over"

class RopesLaddersGUI:
    def __init__(self):
        # Screen settings
        self.SCREEN_WIDTH = 1200
        self.SCREEN_HEIGHT = 800
        self.BOARD_SIZE = 11
        self.CELL_SIZE = 45
        self.BOARD_OFFSET_X = 75
        self.BOARD_OFFSET_Y = 50
        
        # Game state
        self.game_state = GameState(self.BOARD_SIZE, max_ropes=3, verbose=False)
        self.game_mode = GameMode.MENU
        self.selected_cell = None
        self.possible_moves = []
        self.possible_rope_segments = []
        self.dragging = False
        self.drag_start = None
        self.current_segment = []
        
        # AI - Use new MinimaxPruning system for enhanced strategic play
        self.ai_agent = MinimaxPruning(verbose=True)
        self.ai_thinking = False
        self.ai_start_time = 0
        self.ai_vs_ai_mode = False
        self.ai_vs_ai_paused = False
        self.ai_auto_delay = 1.5  # Slightly longer delay so players can see moves
        self.last_ai_move_time = 0
        
        # Game modes
        self.human_vs_ai = True  # True for Human vs AI, False for AI vs AI
        
        # Rope placement mode
        self.rope_placement_mode = False
        self.available_rope_actions = []
        
        # UI
        self.buttons = []
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 18)
        
        # Initialize screen
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption("Ropes & Ladders - Strategic Edition")
        
        # Disable debug output during AI simulation
        self.debug_output = True
    
    def create_button(self, x: int, y: int, width: int, height: int, text: str, 
                     action: str, color: Tuple[int, int, int] = Colors.BUTTON_NORMAL) -> Dict:
        """Create a button dictionary"""
        return {
            'rect': pygame.Rect(x, y, width, height),
            'text': text,
            'action': action,
            'color': color,
            'hover': False
        }
    
    def draw_button(self, button: Dict):
        """Draw a button with hover effects"""
        color = Colors.BUTTON_HOVER if button['hover'] else button['color']
        pygame.draw.rect(self.screen, color, button['rect'])
        pygame.draw.rect(self.screen, Colors.BLACK, button['rect'], 2)
        
        # Button text
        text_surface = self.font.render(button['text'], True, Colors.WHITE)
        text_rect = text_surface.get_rect(center=button['rect'].center)
        self.screen.blit(text_surface, text_rect)
    
    def draw_main_menu(self):
        """Draw the main menu"""
        self.screen.fill(Colors.WHITE)
        
        # Title
        title_text = self.title_font.render("Ropes & Ladders", True, Colors.DARK_GRAY)
        subtitle_text = self.font.render("Strategic Edition with AI", True, Colors.GRAY)
        
        title_rect = title_text.get_rect(center=(self.SCREEN_WIDTH // 2, 150))
        subtitle_rect = subtitle_text.get_rect(center=(self.SCREEN_WIDTH // 2, 190))
        
        self.screen.blit(title_text, title_rect)
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Menu buttons
        self.buttons = []
        button_width = 300
        button_height = 60
        button_x = (self.SCREEN_WIDTH - button_width) // 2
        start_y = 280
        
        menu_options = [
            ("Human vs AI", "start_human_vs_ai"),
            ("AI vs AI", "start_ai_vs_ai"),
            ("Human vs Human", "start_human_vs_human"),
            ("Exit", "exit")
        ]
        
        for i, (text, action) in enumerate(menu_options):
            y = start_y + i * (button_height + 20)
            button = self.create_button(button_x, y, button_width, button_height, text, action)
            self.buttons.append(button)
            self.draw_button(button)
        
        # Current settings display
        settings_y = start_y + len(menu_options) * (button_height + 20) + 40
        settings_text = [
            f"Board Size: {self.BOARD_SIZE}x{self.BOARD_SIZE}",
            f"Ropes per Player: {self.game_state.max_ropes}",
            f"AI: MinimaxPruning (Depth: {self.ai_agent.max_depth})"
        ]
        
        for i, text in enumerate(settings_text):
            text_surface = self.small_font.render(text, True, Colors.GRAY)
            text_rect = text_surface.get_rect(center=(self.SCREEN_WIDTH // 2, settings_y + i * 25))
            self.screen.blit(text_surface, text_rect)
    
    def draw_board(self):
        """Draw the game board"""
        if not self.game_state:
            return
        
        # Board background
        board_rect = pygame.Rect(self.BOARD_OFFSET_X, self.BOARD_OFFSET_Y, self.BOARD_SIZE * self.CELL_SIZE, self.BOARD_SIZE * self.CELL_SIZE)
        pygame.draw.rect(self.screen, Colors.BOARD_BORDER, board_rect)
        pygame.draw.rect(self.screen, Colors.BOARD_LIGHT, board_rect, 3)
        
        # Draw grid
        for row in range(self.BOARD_SIZE):
            for col in range(self.BOARD_SIZE):
                x = self.BOARD_OFFSET_X + col * self.CELL_SIZE
                y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE
                
                # Alternate colors for checkerboard pattern
                color = Colors.BOARD_LIGHT if (row + col) % 2 == 0 else Colors.BOARD_DARK
                cell_rect = pygame.Rect(x, y, self.CELL_SIZE, self.CELL_SIZE)
                pygame.draw.rect(self.screen, color, cell_rect)
                pygame.draw.rect(self.screen, Colors.BOARD_BORDER, cell_rect, 1)
                
                # Draw coordinates and cell number (if cell is large enough)
                if self.CELL_SIZE > 40:
                    coord_text = self.small_font.render(f"{row},{col}", True, Colors.LIGHT_GRAY)
                    self.screen.blit(coord_text, (x + 2, y + 2))
                    cell_num = row * self.BOARD_SIZE + col
                    num_text = self.small_font.render(str(cell_num), True, Colors.DARK_GRAY)
                    num_rect = num_text.get_rect(bottomright=(x + self.CELL_SIZE - 2, y + self.CELL_SIZE - 2))
                    self.screen.blit(num_text, num_rect)
        
        # Draw ladders
        if hasattr(self.game_state, 'ladders'):
            for start_pos, end_pos in self.game_state.ladders:
                s_row, s_col = start_pos
                e_row, e_col = end_pos
                length = max(abs(e_row - s_row), abs(e_col - s_col)) + 1
                d_row = (e_row - s_row) // (length - 1) if length > 1 else 0
                d_col = (e_col - s_col) // (length - 1) if length > 1 else 0
                # Compute all ladder cells
                cells = [(s_row + i * d_row, s_col + i * d_col) for i in range(length)]
                # Draw rails
                for offset in [-0.25, 0.25]:
                    rail_points = []
                    for i, (row, col) in enumerate(cells):
                        x = self.BOARD_OFFSET_X + (col + offset) * self.CELL_SIZE + self.CELL_SIZE // 2
                        y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2
                        rail_points.append((x, y))
                    pygame.draw.lines(self.screen, Colors.BLACK, False, rail_points, 4)
                # Draw rungs
                for i in range(length):
                    row, col = cells[i]
                    x1 = self.BOARD_OFFSET_X + (col - 0.25) * self.CELL_SIZE + self.CELL_SIZE // 2
                    x2 = self.BOARD_OFFSET_X + (col + 0.25) * self.CELL_SIZE + self.CELL_SIZE // 2
                    y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2
                    pygame.draw.line(self.screen, Colors.BLACK, (x1, y), (x2, y), 3)

        # Draw prize
        prize_row, prize_col = self.game_state.prize_pos
        prize_x = self.BOARD_OFFSET_X + prize_col * self.CELL_SIZE + self.CELL_SIZE // 2
        prize_y = self.BOARD_OFFSET_Y + prize_row * self.CELL_SIZE + self.CELL_SIZE // 2
        
        pygame.draw.circle(self.screen, Colors.PRIZE_COLOR, (prize_x, prize_y), self.CELL_SIZE // 3)
        pygame.draw.circle(self.screen, Colors.ORANGE, (prize_x, prize_y), self.CELL_SIZE // 3, 3)
        
        # Prize text
        prize_text = self.font.render("P", True, Colors.ORANGE)
        prize_rect = prize_text.get_rect(center=(prize_x, prize_y))
        self.screen.blit(prize_text, prize_rect)
        
        # Draw rope obstacles
        self.draw_rope_obstacles()
        
        # Draw players
        self.draw_players()
        
        # Highlight possible moves
        self.highlight_possible_moves()
        
        # Draw drag and drop
        self.draw_drag_and_drop()
    
    def draw_players(self):
        """Draw player pieces on the board"""
        if not self.game_state:
            return
        
        # Player 1
        p1_row, p1_col = self.game_state.player1_pos
        p1_x = self.BOARD_OFFSET_X + p1_col * self.CELL_SIZE + self.CELL_SIZE // 4
        p1_y = self.BOARD_OFFSET_Y + p1_row * self.CELL_SIZE + self.CELL_SIZE // 2
        
        pygame.draw.circle(self.screen, Colors.BLUE, (p1_x, p1_y), self.CELL_SIZE // 6)
        pygame.draw.circle(self.screen, Colors.WHITE, (p1_x, p1_y), self.CELL_SIZE // 6, 2)
        
        # Player 1 number
        p1_text = self.small_font.render("1", True, Colors.WHITE)
        p1_rect = p1_text.get_rect(center=(p1_x, p1_y))
        self.screen.blit(p1_text, p1_rect)
        
        # Player 2
        p2_row, p2_col = self.game_state.player2_pos
        p2_x = self.BOARD_OFFSET_X + p2_col * self.CELL_SIZE + 3 * self.CELL_SIZE // 4
        p2_y = self.BOARD_OFFSET_Y + p2_row * self.CELL_SIZE + self.CELL_SIZE // 2
        
        pygame.draw.circle(self.screen, Colors.RED, (p2_x, p2_y), self.CELL_SIZE // 6)
        pygame.draw.circle(self.screen, Colors.WHITE, (p2_x, p2_y), self.CELL_SIZE // 6, 2)
        
        # Player 2 number
        p2_text = self.small_font.render("2", True, Colors.WHITE)
        p2_rect = p2_text.get_rect(center=(p2_x, p2_y))
        self.screen.blit(p2_text, p2_rect)
    
    def draw_rope_obstacles(self):
        """Draw rope obstacles on the board (3-cell segments with diagonal support and player colors)"""
        if not self.game_state or not hasattr(self.game_state, 'rope_obstacles'):
            return
        
        for i, (cells, player, used) in enumerate(self.game_state.rope_obstacles):
            # Calculate pixel positions for all cells
            points = []
            for row, col in cells:
                x = self.BOARD_OFFSET_X + col * self.CELL_SIZE + self.CELL_SIZE // 2
                y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2
                points.append((x, y))
            # Choose color based on player and used status
            if used:
                rope_color = (128, 128, 128)  # Grey
                rope_dark = (96, 96, 96)     # Darker grey
            elif player == Player.PLAYER1:
                rope_color = (52, 152, 219)  # Blue
                rope_dark = (41, 128, 185)   # Darker blue
            else:  # PLAYER2
                rope_color = (231, 76, 60)   # Red
                rope_dark = (192, 57, 43)    # Darker red
            # Draw rope as a thick polyline through all cells
            rope_thickness = 8
            pygame.draw.lines(self.screen, rope_dark, False, points, rope_thickness)
            pygame.draw.lines(self.screen, rope_color, False, points, rope_thickness - 2)
            # Draw rope head (first cell) with special marker
            head_x, head_y = points[0]
            head_radius = 10
            pygame.draw.circle(self.screen, rope_dark, (head_x, head_y), head_radius)
            pygame.draw.circle(self.screen, rope_color, (head_x, head_y), head_radius - 2)
            if not used:
                pygame.draw.circle(self.screen, Colors.WHITE, (head_x, head_y), 4)
            else:
                pygame.draw.circle(self.screen, Colors.BLACK, (head_x, head_y), 3)
            # Draw rope tail (last cell)
            tail_x, tail_y = points[-1]
            end_radius = 6
            pygame.draw.circle(self.screen, rope_dark, (tail_x, tail_y), end_radius)
            pygame.draw.circle(self.screen, rope_color, (tail_x, tail_y), end_radius - 2)
    
    def draw_drag_and_drop(self):
        """Draw drag and drop visual feedback"""
        if not self.dragging or not self.drag_start:
            return
        
        # Draw a semi-transparent rope being dragged
        rope_width = self.CELL_SIZE // 3
        rope_height = self.CELL_SIZE // 8
        rope_rect = pygame.Rect(self.drag_start[0] - rope_width // 2, 
                               self.drag_start[1] - rope_height // 2, 
                               rope_width, rope_height)
        
        # Create a surface with alpha for transparency
        rope_surface = pygame.Surface((rope_width, rope_height), pygame.SRCALPHA)
        rope_surface.fill((139, 69, 19, 128))  # Brown with alpha
        self.screen.blit(rope_surface, rope_rect)
    
    def highlight_possible_moves(self):
        """Highlight possible moves for current player"""
        if not self.game_state:
            return
            
        # Don't highlight when AI is thinking
        if self.ai_thinking:
            return
        
        # Determine if current player is human
        is_human_turn = True
        if self.ai_vs_ai_mode:
            is_human_turn = False  # AI vs AI - no human players
        elif self.human_vs_ai and self.game_state.current_player == Player.PLAYER2:
            is_human_turn = False  # Human vs AI - Player 2 is AI
        
        # Only highlight for human players
        if not is_human_turn:
            return
        
        # If in rope placement mode, highlight rope placement positions
        if self.rope_placement_mode:
            for action in self.available_rope_actions:
                cells = action['segment']
                for i, (row, col) in enumerate(cells):
                    x = self.BOARD_OFFSET_X + col * self.CELL_SIZE
                    y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE
                    
                    # Draw thick orange border for rope placement positions
                    # Head (first cell) gets special highlighting
                    if i == 0:  # Head of rope
                        highlight_rect = pygame.Rect(x + 2, y + 2, self.CELL_SIZE - 4, self.CELL_SIZE - 4)
                        pygame.draw.rect(self.screen, Colors.ORANGE, highlight_rect, 5)
                        # Add inner highlight for better visibility
                        inner_rect = pygame.Rect(x + 5, y + 5, self.CELL_SIZE - 10, self.CELL_SIZE - 10)
                        pygame.draw.rect(self.screen, Colors.ORANGE, inner_rect, 2)
                        # Draw white dot to indicate head
                        center_x = x + self.CELL_SIZE // 2
                        center_y = y + self.CELL_SIZE // 2
                        pygame.draw.circle(self.screen, Colors.WHITE, (center_x, center_y), 5)
                    else:  # Body/tail of rope
                        highlight_rect = pygame.Rect(x + 2, y + 2, self.CELL_SIZE - 4, self.CELL_SIZE - 4)
                        pygame.draw.rect(self.screen, Colors.YELLOW, highlight_rect, 3)
            return
        
        for action in self.possible_moves:
            if action['type'] == ActionType.MOVE:
                row, col = action['position']
                x = self.BOARD_OFFSET_X + col * self.CELL_SIZE
                y = self.BOARD_OFFSET_Y + row * self.CELL_SIZE
                
                # Highlight cell with thick border
                highlight_rect = pygame.Rect(x + 2, y + 2, self.CELL_SIZE - 4, self.CELL_SIZE - 4)
                pygame.draw.rect(self.screen, Colors.GREEN, highlight_rect, 5)
                # Add inner highlight for better visibility
                inner_rect = pygame.Rect(x + 5, y + 5, self.CELL_SIZE - 10, self.CELL_SIZE - 10)
                pygame.draw.rect(self.screen, Colors.GREEN, inner_rect, 2)
            

    
    def draw_info_panel(self):
        """Draw the information panel"""
        if not self.game_state:
            return
        
        panel_x = self.BOARD_OFFSET_X + self.BOARD_SIZE * self.CELL_SIZE + 30
        panel_y = self.BOARD_OFFSET_Y
        
        # Game info - only playing phase now
        # Determine if current player is human or AI
        is_human_turn = True
        if self.human_vs_ai and self.game_state.current_player == Player.PLAYER2:
            is_human_turn = False
        elif self.ai_vs_ai_mode:
            is_human_turn = False
        
        current_player_text = f"Current Player: {self.game_state.current_player.name}"
        if self.ai_vs_ai_mode:
            current_player_text += " (AI)"
        elif not is_human_turn:
            current_player_text += " (AI)"
        else:
            current_player_text += " (YOU)"
        
        # Player labels based on game type
        if self.human_vs_ai:
            p1_label = "Player 1: (Human)"
            p2_label = "Player 2: (AI)"
        elif self.ai_vs_ai_mode:
            p1_label = "Player 1: (AI)"
            p2_label = "Player 2: (AI)"
        else:  # human_vs_human
            p1_label = "Player 1: (Human)"
            p2_label = "Player 2: (Human)"
        
        info_lines = [
            f"Turn: {self.game_state.turn_count}",
            "",
            current_player_text,
            "",
            p1_label,
            f"   Position: {self.game_state.player1_pos}",
            f"   Ropes left: {self.game_state.player1_rope_obstacles}",
            f"   Distance: {self.game_state.manhattan_distance(self.game_state.player1_pos, self.game_state.prize_pos)}",
            "",
            p2_label,
            f"   Position: {self.game_state.player2_pos}",
            f"   Ropes left: {self.game_state.player2_rope_obstacles}",
            f"   Distance: {self.game_state.manhattan_distance(self.game_state.player2_pos, self.game_state.prize_pos)}",
        ]
        
        for i, line in enumerate(info_lines):
            if line.strip():  # Non-empty lines
                color = Colors.BLUE if "Player 1" in line else Colors.RED if "Player 2" in line else Colors.DARK_GRAY
                if "Current Player" in line:
                    color = Colors.BLUE if self.game_state.current_player == Player.PLAYER1 else Colors.RED
                
                text_surface = self.small_font.render(line, True, color)
                self.screen.blit(text_surface, (panel_x, panel_y + i * 25))
        
        # Action buttons for human players
        if not self.ai_thinking:
            self.draw_action_buttons(panel_x, panel_y + len(info_lines) * 25 + 30)
    
    def draw_action_buttons(self, x: int, y: int):
        """Draw action buttons for human players"""
        # Don't show action buttons if AI is thinking
        if self.ai_thinking:
            return
            
        # Determine if current player is human
        is_human_turn = True
        if self.ai_vs_ai_mode:
            is_human_turn = False  # AI vs AI - no human players
        elif self.human_vs_ai and self.game_state.current_player == Player.PLAYER2:
            is_human_turn = False  # Human vs AI - Player 2 is AI
        
        # Only show buttons for human players
        if not is_human_turn:
            return
        
        # Clear ALL buttons to avoid conflicts with menu buttons
        self.buttons = []
        
        button_width = 180
        button_height = 35
        
        # Check if it's human's turn
        is_human_turn = True
        if self.ai_vs_ai_mode:
            is_human_turn = False  # AI vs AI - no human players
        elif self.human_vs_ai and self.game_state.current_player == Player.PLAYER2:
            is_human_turn = False  # Human vs AI - Player 2 is AI
        
        if is_human_turn:
            # Human turn instructions
            your_turn_text = self.small_font.render("YOUR TURN:", True, Colors.GREEN)
            self.screen.blit(your_turn_text, (x, y))
            y += 25
            
            # Show rope placement mode instructions
            if self.rope_placement_mode:
                rope_mode_text = self.small_font.render("Placing rope:", True, Colors.ORANGE)
                self.screen.blit(rope_mode_text, (x, y))
                y += 20
                
                instruction_text = self.small_font.render("Click orange cells to place rope", True, Colors.DARK_GRAY)
                self.screen.blit(instruction_text, (x, y))
                y += 20
                
                cancel_text = self.small_font.render("(Click anywhere else to cancel)", True, Colors.GRAY)
                self.screen.blit(cancel_text, (x, y))
                y += 30
            
            else:
                # Move buttons
                move_actions = [action for action in self.possible_moves if action['type'] == ActionType.MOVE]
                if move_actions:
                    move_text = self.small_font.render("Click green cells to move", True, Colors.DARK_GRAY)
                    self.screen.blit(move_text, (x, y))
                    y += 20
            
                # Rope placement buttons
                rope_actions = [action for action in self.possible_moves if action['type'] == ActionType.PLACE_ROPE_OBSTACLE]
                if rope_actions:
                    rope_header = self.small_font.render("Place Ropes:", True, Colors.DARK_GRAY)
                    self.screen.blit(rope_header, (x, y))
                    y += 25
                    
                    # Group actions by direction
                    directions = {}
                    for action in rope_actions:
                        direction = action.get('direction', 'unknown')
                        if direction not in directions:
                            directions[direction] = []
                        directions[direction].append(action)
                    
                    # Create buttons for each direction
                    for direction, actions in directions.items():
                        if direction == 'down':
                            button_text = "Down"
                            button_color = Colors.PURPLE
                        elif direction == 'diagonal_right':
                            button_text = "Diag-Right"
                            button_color = Colors.ORANGE
                        elif direction == 'diagonal_left':
                            button_text = "Diag-Left"
                            button_color = Colors.YELLOW
                        else:
                            button_text = direction.title()
                            button_color = Colors.GRAY
                        
                        rope_button = self.create_button(x, y, button_width, button_height - 5, 
                                                       button_text, 
                                                       f"rope_{direction}", button_color)
                        rope_button['is_action_button'] = True
                        rope_button['rope_actions'] = actions
                        self.buttons.append(rope_button)
                        self.draw_button(rope_button)
                        y += button_height + 5
                    
                    rope_info = self.small_font.render("(Head = white dot = danger!)", True, Colors.RED)
                    self.screen.blit(rope_info, (x, y))
                    y += 30
        else:
            # AI turn indicator
            ai_text = self.small_font.render("AI is thinking...", True, Colors.PURPLE)
            self.screen.blit(ai_text, (x, y))
            y += 40
        
        # Back to menu button
        menu_button = self.create_button(x, y + 50, button_width, button_height, 
                                       "Back to Menu", "back_to_menu", Colors.GRAY)
        menu_button['is_action_button'] = True
        self.buttons.append(menu_button)
        self.draw_button(menu_button)
        
        # Exit button
        exit_button = self.create_button(x, y + 100, button_width, button_height, 
                                       "Exit Game", "exit", Colors.RED)
        exit_button['is_action_button'] = True
        self.buttons.append(exit_button)
        self.draw_button(exit_button)
    
    def draw_ai_thinking(self):
        """Draw AI thinking indicator"""
        if self.ai_thinking:
            if self.ai_vs_ai_mode:
                # Only show a generic message, no countdown
                thinking_text = self.font.render("AI is thinking...", True, Colors.PURPLE)
            else:
                thinking_text = self.font.render("AI is thinking...", True, Colors.PURPLE)
            
            thinking_rect = thinking_text.get_rect(center=(self.SCREEN_WIDTH // 2, 50))
            
            # Background for visibility
            bg_rect = thinking_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, Colors.WHITE, bg_rect)
            pygame.draw.rect(self.screen, Colors.PURPLE, bg_rect, 2)
            
            self.screen.blit(thinking_text, thinking_rect)
    
    def draw_game_mode_indicator(self):
        """Draw game mode indicator and stop/resume/exit buttons for AI vs AI"""
        # Always show Exit button in top right
        exit_button = self.create_button(self.SCREEN_WIDTH - 130, 15, 100, 35, "Exit", "exit", Colors.RED)
        exit_button['is_action_button'] = True
        self.buttons.append(exit_button)
        self.draw_button(exit_button)
        if self.ai_vs_ai_mode:
            mode_text = self.small_font.render("AI vs AI Mode - Watch the AIs compete!", True, Colors.DARK_GRAY)
            mode_rect = mode_text.get_rect(center=(self.SCREEN_WIDTH // 2, 25))
            self.screen.blit(mode_text, mode_rect)
            if self.ai_vs_ai_paused:
                # Draw Resume button
                resume_button = self.create_button(self.SCREEN_WIDTH - 250, 15, 100, 35, "Resume", "stop_ai", Colors.GREEN)
                resume_button['is_action_button'] = True
                self.buttons.append(resume_button)
                self.draw_button(resume_button)
            else:
                # Draw Stop button at top right (next to Exit)
                stop_button = self.create_button(self.SCREEN_WIDTH - 250, 15, 100, 35, "Stop", "stop_ai", Colors.RED)
                stop_button['is_action_button'] = True
                self.buttons.append(stop_button)
                self.draw_button(stop_button)

    # Add a paused state to the GUI
    def pause_ai_vs_ai(self):
        self.ai_vs_ai_paused = True
    def resume_ai_vs_ai(self):
        self.ai_vs_ai_paused = False

    # In __init__, add: self.ai_vs_ai_paused = False
    # In process_ai_turn, add a check:
    # if self.game_type == "ai_vs_ai" and getattr(self, 'ai_vs_ai_paused', False): return
    # In handle_button_click, handle 'stop_ai' to pause and show exit/resume options

    def draw_game_over(self):
        """Draw game over screen"""
        # Semi-transparent overlay
        overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(Colors.BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Game over panel
        panel_width = 400
        panel_height = 400
        panel_x = (self.SCREEN_WIDTH - panel_width) // 2
        panel_y = (self.SCREEN_HEIGHT - panel_height) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, Colors.WHITE, panel_rect)
        pygame.draw.rect(self.screen, Colors.DARK_GRAY, panel_rect, 3)
        
        # Winner announcement
        winner = self.game_state.get_winner()
        if winner:
            winner_text = f"Player {winner.value} Wins!"
            color = Colors.BLUE if winner == Player.PLAYER1 else Colors.RED
        else:
            winner_text = "It's a Draw!"
            color = Colors.GRAY
        
        winner_surface = self.title_font.render(winner_text, True, color)
        winner_rect = winner_surface.get_rect(center=(panel_x + panel_width // 2, panel_y + 80))
        self.screen.blit(winner_surface, winner_rect)
        
        # Game statistics
        stats_y = panel_y + 150
        stats = [
            f"Total turns: {self.game_state.turn_count}",
            f"Rope obstacles placed: {len(self.game_state.rope_obstacles)}"
        ]
        
        for i, stat in enumerate(stats):
            stat_surface = self.font.render(stat, True, Colors.DARK_GRAY)
            stat_rect = stat_surface.get_rect(center=(panel_x + panel_width // 2, stats_y + i * 35))
            self.screen.blit(stat_surface, stat_rect)
        
        # Buttons
        self.buttons = []
        button_width = 120
        button_height = 40
        
        # Row 1: Play Again and Main Menu
        play_again_button = self.create_button(panel_x + 30, panel_y + panel_height - 100, 
                                             button_width, button_height, "Play Again", "play_again")
        menu_button = self.create_button(panel_x + panel_width - 150, panel_y + panel_height - 100, 
                                       button_width, button_height, "Main Menu", "back_to_menu")
        
        # Row 2: Exit button (centered)
        exit_button = self.create_button(panel_x + (panel_width - button_width) // 2, panel_y + panel_height - 50, 
                                       button_width, button_height, "Exit Game", "exit", Colors.RED)
        
        self.buttons.extend([play_again_button, menu_button, exit_button])
        
        for button in self.buttons:
            self.draw_button(button)
    
    def start_new_game(self):
        """Start a new game"""
        self.game_state = GameState(self.BOARD_SIZE, max_ropes=3, verbose=False)
        self.possible_moves = self.game_state.get_possible_actions()
        self.game_mode = GameMode.GAME
        self.cell_size = self.CELL_SIZE
        
        # Clear AI agent cache and position history for fresh start
        self.ai_agent.clear_cache()
    

    
    def handle_board_click(self, pos: Tuple[int, int]):
        """Handle clicks on the game board"""
        if not self.game_state or self.ai_thinking:
            return
        
        mouse_x, mouse_y = pos
        
        # Check if click is within board
        if (mouse_x < self.BOARD_OFFSET_X or mouse_x > self.BOARD_OFFSET_X + self.BOARD_SIZE * self.CELL_SIZE or
            mouse_y < self.BOARD_OFFSET_Y or mouse_y > self.BOARD_OFFSET_Y + self.BOARD_SIZE * self.CELL_SIZE):
            return
        
        # Convert to board coordinates
        col = (mouse_x - self.BOARD_OFFSET_X) // self.CELL_SIZE
        row = (mouse_y - self.BOARD_OFFSET_Y) // self.CELL_SIZE
        target_pos = (row, col)
        
        # Handle rope placement mode
        if self.rope_placement_mode:
            # Find rope action that starts at clicked position
            for action in self.available_rope_actions:
                if action['segment'][0] == target_pos:  # Check if head of rope is at clicked position
                    self.execute_action(action)
                    # Exit rope placement mode
                    self.rope_placement_mode = False
                    self.available_rope_actions = []
                    print(f"Placed rope at {target_pos}")
                    return
            
            # If no valid rope placement found, exit rope placement mode
            self.rope_placement_mode = False
            self.available_rope_actions = []
            print("Cancelled rope placement")
            return
        
        # Handle regular movement
        move_action = None
        for action in self.possible_moves:
            if action['type'] == ActionType.MOVE and action['position'] == target_pos:
                move_action = action
                break
        
        if move_action:
            self.execute_action(move_action)
    
    def execute_action(self, action: Dict):
        """Execute a game action"""
        self.game_state = self.game_state.apply_action(action)
        self.possible_moves = self.game_state.get_possible_actions()
        
        # Update game mode - always in playing phase now
        self.game_mode = GameMode.GAME
        
        # Check if game is over
        if self.game_state.is_game_over():
            self.game_mode = GameMode.GAME_OVER
        
        # Start AI turn if needed
        self.check_ai_turn()
    
    def check_ai_turn(self):
        """Check if it's AI's turn and start AI thinking"""
        if self.game_state.is_game_over():
            return
        
        is_ai_turn = False
        
        if self.ai_vs_ai_mode:
            is_ai_turn = True
        elif self.human_vs_ai and self.game_state.current_player == Player.PLAYER2:
            is_ai_turn = True
        
        # Only start AI thinking if it's actually an AI turn and we're not already thinking
        if is_ai_turn and not self.ai_thinking:
            self.ai_thinking = True
            # Reset timers for new AI turn
            self.last_ai_move_time = 0
            # AI will think in the next frame to keep UI responsive
    
    def process_ai_turn(self, dt: float):
        """Process AI turn (called once per frame when AI is thinking)"""
        if not self.ai_thinking:
            return
        
        # Pause AI moves if AI vs AI is paused
        if self.ai_vs_ai_mode and self.ai_vs_ai_paused:
            return
        
        # Add delay for human vs AI mode so human can see what's happening
        if self.human_vs_ai:
            self.last_ai_move_time += dt
            if self.last_ai_move_time < self.ai_auto_delay:
                return  # Still waiting
            self.last_ai_move_time = 0
        
        # Add delay for AI vs AI mode so user can watch the moves
        elif self.ai_vs_ai_mode:
            self.last_ai_move_time += dt
            if self.last_ai_move_time < self.ai_auto_delay:
                return  # Still waiting
            # Reset timer for next turn
            self.last_ai_move_time = 0
        
        # Get AI move
        action = self.ai_agent.get_best_move(self.game_state)
        
        # Execute the action
        self.execute_action(action)
        
        self.ai_thinking = False
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_mouse_click(event.pos)
            
            elif event.type == pygame.MOUSEMOTION:
                self.handle_mouse_motion(event.pos)
        
        return True
    
    def handle_mouse_click(self, pos: Tuple[int, int]):
        """Handle mouse clicks"""
        
        # Check button clicks
        for button in self.buttons:
            if button['rect'].collidepoint(pos):
                
                self.handle_button_click(button['action'])
                return
        
        # Handle board clicks in game mode
        if self.game_mode == GameMode.GAME:
            self.handle_board_click(pos)
    
    def handle_mouse_motion(self, pos: Tuple[int, int]):
        """Handle mouse motion for hover effects"""
        for button in self.buttons:
            button['hover'] = button['rect'].collidepoint(pos)
    
    def handle_button_click(self, action: str):
        """Handle button clicks"""
        
        if action == "start_human_vs_ai":
            self.human_vs_ai = True
            self.ai_vs_ai_mode = False
            self.start_new_game()
        
        elif action == "start_ai_vs_ai":
            self.human_vs_ai = False
            self.ai_vs_ai_mode = True
            self.start_new_game()
        
        elif action == "start_human_vs_human":
            self.human_vs_ai = False  # Both players are human
            self.ai_vs_ai_mode = False
            self.start_new_game()
        
        elif action == "back_to_menu":
            self.game_mode = GameMode.MENU
        
        elif action == "play_again":
            self.start_new_game()
        
        elif action == "exit":
            pygame.quit()
            sys.exit()
        
        # Rope placement actions
        elif action.startswith("rope_"):
            direction = action.split("_", 1)[1]  # Get direction after "rope_"
            # Find the button that was clicked to get the associated actions
            for button in self.buttons:
                if button.get('action') == action and 'rope_actions' in button:
                    # Enter rope placement mode
                    self.rope_placement_mode = True
                    self.available_rope_actions = button['rope_actions']
                    print(f"Entering rope placement mode for {direction} - {len(self.available_rope_actions)} options available")
                    return
        
        # Stop AI vs AI button
        elif action == "stop_ai":
            if self.ai_vs_ai_mode:
                if self.ai_vs_ai_paused:
                    self.resume_ai_vs_ai()
                else:
                    self.pause_ai_vs_ai()
        


    def update(self):
        """Update game state"""
        # Calculate delta time
        dt = pygame.time.get_ticks() / 1000.0  # Convert to seconds
        
        # Process AI turn if needed
        if self.ai_thinking:
            self.process_ai_turn(dt)
        
        # Check for new AI turns
        if self.game_mode == GameMode.GAME:
            self.check_ai_turn()
    
    def draw(self):
        """Draw everything"""
        self.screen.fill(Colors.WHITE)
        
        if self.game_mode == GameMode.MENU:
            self.draw_main_menu()
        
        elif self.game_mode == GameMode.GAME:
            self.draw_board()
            self.draw_info_panel()
            self.draw_ai_thinking()
            self.draw_game_mode_indicator()
        
        elif self.game_mode == GameMode.GAME_OVER:
            self.draw_board()
            self.draw_info_panel()
            self.draw_game_over()
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            pygame.time.delay(10) # Reduced delay for smoother updates
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = RopesLaddersGUI()
    game.run() 