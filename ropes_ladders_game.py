import copy
import math
import random
import time
from typing import List, Tuple, Optional, Dict, Set
from enum import Enum

class Player(Enum):
    """Enum representing the two players in the game"""
    PLAYER1 = 1
    PLAYER2 = 2

class ActionType(Enum):
    """Enum representing the types of actions players can take"""
    MOVE = "move"
    PLACE_ROPE = "place_rope"
    PLACE_ROPE_OBSTACLE = "place_rope_obstacle"

class GamePhase(Enum):
    """Enum representing the different phases of the game"""
    PLAYING = "playing"
    FINISHED = "finished"

class Direction(Enum):
    """Enum representing the four movement directions"""
    UP = (-1, 0)
    DOWN = (1, 0)
    LEFT = (0, -1)
    RIGHT = (0, 1)

class GameState:
    """Represents the complete state of the game at any point"""
    
    def __init__(self, board_size: int = 11, max_ropes: int = 3, verbose: bool = True):
        self.board_size = board_size
        self.max_ropes = max_ropes
        self.verbose = verbose
        
        # Initialize player positions
        self.player1_pos = (board_size - 1, board_size // 2)  # Bottom-center
        self.player2_pos = (board_size - 1, board_size // 2)  # Bottom-center (same as player 1)
        self.prize_pos = (0, board_size // 2)  # Middle top cell
        
        # Initialize rope counts
        self.player1_ropes = max_ropes
        self.player2_ropes = max_ropes
        
        # Initialize rope obstacles (placed during setup)
        self.player1_rope_obstacles = max_ropes
        self.player2_rope_obstacles = max_ropes
        self.rope_obstacles = []  # List of (cells, player, used)
        
        # Initialize walls (can be added dynamically)
        self.walls = set()
        
        # Initialize ladders (placed during setup)
        self.ladders = []  # List of (start_pos, end_pos)
        self._place_random_ladders()
        
        # Game state
        self.current_player = Player.PLAYER1
        self.turn_count = 0
        self.game_phase = GamePhase.PLAYING
        
        if self.verbose:
            print(f"Game initialized:")
            print(f"   Board size: {board_size}x{board_size}")
            print(f"   Player 1 starts at: {self.player1_pos}")
            print(f"   Player 2 starts at: {self.player2_pos}")
            print(f"   Prize location: {self.prize_pos}")
            print(f"   Each player has {max_ropes} rope obstacles to place during the game")
            print(f"   Game starts immediately - no setup phase!")
    
    def get_state_hash(self) -> str:
        """Generate a unique hash for this game state for transposition table"""
        def rope_str(r):
            cells = r[0]
            player = r[1]
            used = r[2]
            cell_str = ",".join([f"{c[0]}_{c[1]}" for c in cells])
            return f"{cell_str}-{player.value}-{used}"
        rope_obstacles_str = "_".join(sorted([rope_str(r) for r in self.rope_obstacles]))
        return f"{self.player1_pos}_{self.player2_pos}_{self.player1_ropes}_{self.player2_ropes}_{self.current_player.value}_{self.turn_count}_{rope_obstacles_str}_{self.game_phase.value}"
    
    def is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within board bounds and not blocked by walls"""
        row, col = pos
        return (0 <= row < self.board_size and 
                0 <= col < self.board_size and 
                pos not in self.walls)
    
    def is_on_rope_obstacle(self, pos: Tuple[int, int]) -> bool:
        """Check if position is on a rope obstacle (any of the 3 cells)"""
        for cells, player, used in self.rope_obstacles:
            if pos in cells:
                return True
        return False
    
    def get_rope_obstacle_positions(self) -> Set[Tuple[int, int]]:
        """Get all positions that are part of rope obstacles (all 3 cells)"""
        positions = set()
        for cells, player, used in self.rope_obstacles:
            positions.update(cells)
        return positions
    
    def get_current_player_position(self) -> Tuple[int, int]:
        """Get current player's position"""
        return (self.player1_pos if self.current_player == Player.PLAYER1 
                else self.player2_pos)
    
    def get_opponent_position(self) -> Tuple[int, int]:
        """Get opponent's position"""
        return (self.player2_pos if self.current_player == Player.PLAYER1 
                else self.player1_pos)
    
    def get_current_player_ropes(self) -> int:
        """Get current player's remaining ropes"""
        return (self.player1_ropes if self.current_player == Player.PLAYER1 
                else self.player2_ropes)
    
    def get_current_player_rope_obstacles(self) -> int:
        """Get current player's remaining rope obstacles to place"""
        return (self.player1_rope_obstacles if self.current_player == Player.PLAYER1 
                else self.player2_rope_obstacles)
    
    def manhattan_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> int:
        """Calculate Manhattan distance between two positions"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])
    
    def is_game_over(self) -> bool:
        """Check if game is over (someone reached the prize)"""
        if self.game_phase != GamePhase.PLAYING:
            return False
        return (self.player1_pos == self.prize_pos or 
                self.player2_pos == self.prize_pos)
    

    
    def get_winner(self) -> Optional[Player]:
        """Get winner if game is over"""
        if self.player1_pos == self.prize_pos:
            return Player.PLAYER1
        elif self.player2_pos == self.prize_pos:
            return Player.PLAYER2
        return None
    
    def get_possible_moves(self) -> List[Tuple[int, int]]:
        """Get all valid move positions for current player"""
        current_pos = self.get_current_player_position()
        moves = []
        
        for direction in Direction:
            new_pos = (current_pos[0] + direction.value[0], 
                      current_pos[1] + direction.value[1])
            if self.is_valid_position(new_pos):
                moves.append(new_pos)
        
        return moves
    
    def get_possible_actions(self) -> List[Dict]:
        """Get all possible actions for current player"""
        actions = []
        
        if self.game_phase == GamePhase.PLAYING:
            # Movement actions
            for move_pos in self.get_possible_moves():
                actions.append({
                    'type': ActionType.MOVE,
                    'position': move_pos,
                    'description': f"Move to {move_pos}"
                })
            
            # Rope placement actions - available throughout the game
            if self.get_current_player_rope_obstacles() > 0:
                # Get current player's existing rope positions to prevent overlap
                current_player_rope_positions = set()
                for cells, rope_player, used in self.rope_obstacles:
                    if rope_player == self.current_player:
                        current_player_rope_positions.update(cells)
                
                directions = {
                    'down': (1, 0),
                    'diagonal_right': (1, 1),
                    'diagonal_left': (1, -1)
                }
                for row in range(self.board_size):
                    for col in range(self.board_size):
                        start_pos = (row, col)
                        # Check if start position is valid (only restrict prize and walls)
                        if (start_pos != self.prize_pos and
                            start_pos not in self.walls):
                            for dir_name, (dr, dc) in directions.items():
                                cells = [(row + dr * i, col + dc * i) for i in range(3)]
                                # All cells must be within board bounds and not overlap with forbidden positions
                                valid = True
                                for cell in cells:
                                    r, c = cell
                                    if not (0 <= r < self.board_size and 0 <= c < self.board_size):
                                        valid = False
                                        break
                                    # Restrict prize position, walls, current player's own rope positions, and current player positions
                                    if (cell == self.prize_pos or cell in self.walls or 
                                        cell in current_player_rope_positions or
                                        cell == self.player1_pos or cell == self.player2_pos):
                                        valid = False
                                        break
                                if valid:
                                    actions.append({
                                        'type': ActionType.PLACE_ROPE_OBSTACLE,
                                        'segment': tuple(cells),
                                        'direction': dir_name,
                                        'description': f"Place rope {dir_name.upper()} from {start_pos}"
                                    })
        return actions
    
    def check_rope_trigger(self, position):
        """Check if a player stepping on a position triggers an opponent's rope"""
        for i, (cells, rope_player, used) in enumerate(self.rope_obstacles):
            if (position == cells[0] and 
                not used and 
                rope_player != self.current_player):  # Only opponent's unused rope triggers push-back
                # Mark rope as used
                self.rope_obstacles[i] = (cells, rope_player, True)
                # Push player from stepped cell to the last cell in the rope (tail)
                pushed_pos = cells[-1]  # Move directly to the rope's tail
                if self.current_player == Player.PLAYER1:
                    self.player1_pos = pushed_pos
                else:
                    self.player2_pos = pushed_pos
                if self.verbose:
                    print(f"Player {self.current_player.name} stepped on opponent's rope at {position} and was pushed along the rope to {pushed_pos}")
                return True, pushed_pos
        return False, position
    
    def climb_ladders_if_on_base(self):
        """If the current player is on a ladder base, climb to the top (repeat if chained)."""
        climbed = False
        while True:
            player_pos = self.player1_pos if self.current_player == Player.PLAYER1 else self.player2_pos
            found = False
            for start_pos, end_pos in self.ladders:
                if player_pos == start_pos:
                    if self.current_player == Player.PLAYER1:
                        self.player1_pos = end_pos
                    else:
                        self.player2_pos = end_pos
                    if self.verbose:
                        print(f"Player {self.current_player.name} climbed ladder from {start_pos} to {end_pos}")
                    
                    # Check if landing position triggers a rope
                    rope_triggered, final_pos = self.check_rope_trigger(end_pos)
                    if rope_triggered:
                        # Check if rope tail is also on a ladder base (for chaining)
                        pass  # The rope trigger already moved the player
                    
                    found = True
                    climbed = True
                    break
            if not found:
                break
        return climbed

    def apply_action(self, action: Dict) -> 'GameState':
        """Apply action and return new game state"""
        new_state = copy.deepcopy(self)
        # At the start of the turn, climb ladders if on base
        new_state.climb_ladders_if_on_base()
        
        if action['type'] == ActionType.MOVE:
            # Validate move
            if action['position'] not in self.get_possible_moves():
                raise ValueError(f"Invalid move: {action['position']} not in possible moves")
            # Apply move
            if new_state.current_player == Player.PLAYER1:
                new_state.player1_pos = action['position']
            else:
                new_state.player2_pos = action['position']
            # Check if player stepped on an opponent's unused rope (only at the head)
            rope_triggered, final_pos = new_state.check_rope_trigger(action['position'])
            if rope_triggered:
                # Check for ladder at pushed position (rope tail)
                player_pos = new_state.player1_pos if new_state.current_player == Player.PLAYER1 else new_state.player2_pos
                for start_pos, end_pos in new_state.ladders:
                    if player_pos == start_pos:
                        # Climb ladder
                        if new_state.current_player == Player.PLAYER1:
                            new_state.player1_pos = end_pos
                        else:
                            new_state.player2_pos = end_pos
                        if new_state.verbose:
                            print(f"Player {new_state.current_player.name} climbed ladder from {start_pos} to {end_pos}")
                        
                        # Check if landing position from ladder also triggers a rope
                        rope_triggered_again, final_pos_2 = new_state.check_rope_trigger(end_pos)
                        break
            
            # After handling rope trigger, check for ladders based on final position  
            final_pos = final_pos if rope_triggered else action['position']
            new_state.climb_ladders_if_on_base()
            
        elif action['type'] == ActionType.PLACE_ROPE_OBSTACLE:
            cells = action['segment']
            direction = action['direction']
            # Add new rope obstacle
            player_ropes = new_state.player1_rope_obstacles if new_state.current_player == Player.PLAYER1 else new_state.player2_rope_obstacles
            if player_ropes > 0:
                new_state.rope_obstacles.append((cells, new_state.current_player, False))
                if new_state.current_player == Player.PLAYER1:
                    new_state.player1_rope_obstacles -= 1
                else:
                    new_state.player2_rope_obstacles -= 1
        
        else:
            # Handle other action types
            pass
        
        # Check if someone won
        if new_state.player1_pos == new_state.prize_pos:
            new_state.winner = Player.PLAYER1
            return new_state
        elif new_state.player2_pos == new_state.prize_pos:
            new_state.winner = Player.PLAYER2
            return new_state
        
        # Check for ladders again after rope placement for current player
        for start_pos, end_pos in new_state.ladders:
            # Check current player position
            current_pos = new_state.player1_pos if new_state.current_player == Player.PLAYER1 else new_state.player2_pos
            if current_pos == start_pos:
                # Climb ladder  
                if new_state.current_player == Player.PLAYER1:
                    new_state.player1_pos = end_pos
                else:
                    new_state.player2_pos = end_pos
                if new_state.verbose:
                    print(f"Player {new_state.current_player.name} climbed ladder from {start_pos} to {end_pos}")
                
                # Check if landing position from ladder triggers a rope
                rope_triggered_from_ladder, final_pos_3 = new_state.check_rope_trigger(end_pos)
                break
        # Switch player and increment turn
        new_state.current_player = (Player.PLAYER2 if new_state.current_player == Player.PLAYER1 
                                   else Player.PLAYER1)
        new_state.turn_count += 1
        # After switching, climb ladders for the new player
        new_state.climb_ladders_if_on_base()
        return new_state
    
    def print_board(self, use_colors: bool = True):
        """Print current board state with optional colors"""
        if use_colors:
            # ANSI color codes
            RED = '\033[91m'
            BLUE = '\033[94m'
            GREEN = '\033[92m'
            YELLOW = '\033[93m'
            RESET = '\033[0m'
            BOLD = '\033[1m'
        else:
            RED = BLUE = GREEN = YELLOW = RESET = BOLD = ''
        
        print(f"\n{BOLD}{'='*60}{RESET}")
        print(f"{BOLD}🎮 Turn {self.turn_count} | Current Player: {BLUE if self.current_player == Player.PLAYER1 else RED}{self.current_player.name}{RESET}")
        print(f"{BOLD}🪢 Player 1 Ropes Left: {BLUE}{self.player1_rope_obstacles}{RESET} | Player 2 Ropes Left: {RED}{self.player2_rope_obstacles}{RESET}")
        print(f"{BOLD}{'='*60}{RESET}")
        
        for row in range(self.board_size):
            line = ""
            for col in range(self.board_size):
                pos = (row, col)
                if pos == self.prize_pos:
                    line += f" {YELLOW}*{RESET} "
                elif pos == self.player1_pos and pos == self.player2_pos:
                    line += f"{BLUE}1{RESET}&{RED}2{RESET}"
                elif pos == self.player1_pos:
                    line += f" {BLUE}1{RESET} "
                elif pos == self.player2_pos:
                    line += f" {RED}2{RESET} "
                elif self.is_on_rope_obstacle(pos):
                    line += f" {BOLD}R{RESET} "
                elif pos in self.walls:
                    line += f" {BOLD}#{RESET} "
                else:
                    line += " . "
            print(line)
        print(f"{BOLD}{'='*60}{RESET}")

    def _place_random_ladders(self):
        directions = [  # (row_delta, col_delta)
            (1, 0),    # up
            (1, 1),    # up-right
            (1, -1),   # up-left
        ]
        attempts = 0
        while len(self.ladders) < 3 and attempts < 100:
            attempts += 1
            length = random.randint(2, 4)
            dir_idx = random.randint(0, 2)
            d_row, d_col = directions[dir_idx]
            start_row = random.randint(0, self.board_size - length - 1)
            start_col = random.randint(0, self.board_size - 1)
            # For diagonals, ensure col stays in bounds
            if d_col == 1:
                if start_col > self.board_size - length - 1:
                    continue
            elif d_col == -1:
                if start_col < length:
                    continue
            # Compute end position
            end_row = start_row + d_row * (length - 1)
            end_col = start_col + d_col * (length - 1)
            if not (0 <= end_row < self.board_size and 0 <= end_col < self.board_size):
                continue
            start_pos = (start_row, start_col)
            end_pos = (end_row, end_col)
            # Ensure base is always the cell with the highest row (bottom-most), top is lowest row (top-most)
            if start_pos[0] > end_pos[0]:
                base, top = start_pos, end_pos
            else:
                base, top = end_pos, start_pos
            # Check for overlap with players, prize, ropes, or other ladders
            ladder_cells = [(start_row + d_row * i, start_col + d_col * i) for i in range(length)]
            forbidden = set([self.player1_pos, self.player2_pos, self.prize_pos])
            forbidden.update(self.get_rope_obstacle_positions())
            for l in self.ladders:
                forbidden.add(l[0])
                forbidden.add(l[1])
            if any(cell in forbidden for cell in ladder_cells):
                continue
            self.ladders.append((base, top))


# Import the new MinimaxPruning AI system
from minimax_pruning import MinimaxPruning

# Keep original MinimaxAgent for backward compatibility
class OptimizedMinimaxAgent:
    """Wrapper for backward compatibility - uses new MinimaxPruning system"""
    
    def __init__(self, max_depth: int = 5, time_limit: float = 3.0, verbose: bool = True):
        self.ai = MinimaxPruning(max_depth=max_depth, time_limit=time_limit, verbose=verbose)
        self.max_depth = max_depth
        self.time_limit = time_limit
        
    def clear_cache(self):
        """Clear transposition table"""
        self.ai.clear_cache()
    
    def get_best_move(self, state: GameState, use_iterative_deepening: bool = True) -> Dict:
        """Get the best move using the new AI system"""
        return self.ai.get_best_move(state, use_iterative_deepening)
    
    @property
    def nodes_evaluated(self):
        return self.ai.nodes_evaluated
    
    @property
    def pruning_count(self):
        return self.ai.pruning_count
    
    @property
    def transposition_table(self):
        return self.ai.transposition_table


# Keep original MinimaxAgent for backward compatibility
MinimaxAgent = OptimizedMinimaxAgent 