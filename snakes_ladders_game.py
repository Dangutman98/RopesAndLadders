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
    
    def __init__(self, board_size: int = 11, max_ropes: int = 3):
        self.board_size = board_size
        self.max_ropes = max_ropes
        
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
                used_positions = self.get_rope_obstacle_positions()
                directions = {
                    'down': (1, 0),
                    'diagonal_right': (1, 1),
                    'diagonal_left': (1, -1)
                }
                for row in range(self.board_size):
                    for col in range(self.board_size):
                        start_pos = (row, col)
                        # Check if start position is valid
                        if (start_pos != self.player1_pos and 
                            start_pos != self.player2_pos and 
                            start_pos != self.prize_pos and
                            start_pos not in used_positions and
                            start_pos not in self.walls):
                            for dir_name, (dr, dc) in directions.items():
                                cells = [(row + dr * i, col + dc * i) for i in range(3)]
                                # All cells must be valid and not overlap with forbidden positions
                                valid = True
                                for cell in cells:
                                    r, c = cell
                                    if not (0 <= r < self.board_size and 0 <= c < self.board_size):
                                        valid = False
                                        break
                                    if (cell == self.player1_pos or cell == self.player2_pos or cell == self.prize_pos or cell in used_positions or cell in self.walls):
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
                    print(f"Player {self.current_player.name} climbed ladder from {start_pos} to {end_pos}")
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
        
        if action['type'] == ActionType.PLACE_ROPE_OBSTACLE:
            # Validate rope obstacle placement
            if self.get_current_player_rope_obstacles() <= 0:
                raise ValueError("No rope obstacles left to place")
            # Place rope obstacle (3-cell segment) with player info and used flag
            cells = action['segment']
            new_state.rope_obstacles.append((cells, new_state.current_player, False))
            if new_state.current_player == Player.PLAYER1:
                new_state.player1_rope_obstacles -= 1
            else:
                new_state.player2_rope_obstacles -= 1
            direction = action.get('direction', 'unknown')
            # Only print rope placement if not in a simulated Minimax state
            import inspect
            if not any('minimax' in frame.function or 'iterative_deepening' in frame.function for frame in inspect.stack()):
                print(f"Player {new_state.current_player.name} placed {direction} rope obstacle at {cells}")
        elif action['type'] == ActionType.MOVE:
            # Validate move
            if action['position'] not in self.get_possible_moves():
                raise ValueError(f"Invalid move: {action['position']} not in possible moves")
            # Apply move
            if new_state.current_player == Player.PLAYER1:
                new_state.player1_pos = action['position']
            else:
                new_state.player2_pos = action['position']
            # Check if player stepped on an opponent's unused rope (only at the head)
            stepped_on_opponent_rope = False
            rope_to_use = None
            for i, (cells, rope_player, used) in enumerate(new_state.rope_obstacles):
                if (action['position'] == cells[0] and 
                    not used and 
                    rope_player != new_state.current_player):  # Only opponent's unused rope triggers push-back
                    stepped_on_opponent_rope = True
                    rope_to_use = i
                    break
            if stepped_on_opponent_rope:
                # Mark rope as used
                cells, rope_player, used = new_state.rope_obstacles[rope_to_use]
                new_state.rope_obstacles[rope_to_use] = (cells, rope_player, True)
                # Push player from stepped cell to the last cell in the rope (tail)
                pushed_pos = cells[-1]  # Move directly to the rope's tail
                if new_state.current_player == Player.PLAYER1:
                    new_state.player1_pos = pushed_pos
                else:
                    new_state.player2_pos = pushed_pos
                print(f"Player {new_state.current_player.name} stepped on opponent's rope at {action['position']} and was pushed along the rope to {pushed_pos}")
            else:
                print(f"Player {new_state.current_player.name} moved to {action['position']}")
            # Check for ladder at new position (bottom of ladder)
            player_pos = new_state.player1_pos if new_state.current_player == Player.PLAYER1 else new_state.player2_pos
            for start_pos, end_pos in new_state.ladders:
                if player_pos == start_pos:
                    # Climb ladder
                    if new_state.current_player == Player.PLAYER1:
                        new_state.player1_pos = end_pos
                    else:
                        new_state.player2_pos = end_pos
                    print(f"Player {new_state.current_player.name} climbed ladder from {start_pos} to {end_pos}")
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


class OptimizedMinimaxAgent:
    """Enhanced AI agent with optimizations"""
    
    def __init__(self, max_depth: int = 4, time_limit: float = 5.0):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_evaluated = 0
        self.pruning_count = 0
        self.transposition_table = {}
        self.start_time = 0
        
    def clear_cache(self):
        """Clear transposition table"""
        self.transposition_table.clear()
    
    def order_actions(self, state: GameState, actions: List[Dict]) -> List[Dict]:
        """Order actions for better pruning (move ordering heuristic)"""
        def action_priority(action):
            if action['type'] == ActionType.MOVE:
                # Prioritize moves closer to prize
                distance = state.manhattan_distance(action['position'], state.prize_pos)
                return distance
            elif action['type'] == ActionType.PLACE_ROPE_OBSTACLE:
                # For 3-cell ropes, use head and tail
                cells = action['segment']
                head = cells[0]
                tail = cells[-1]
                opponent_pos = state.get_opponent_position()
                # Prioritize rope placement near opponent or in their path to prize
                rope_to_opponent = min(
                    state.manhattan_distance(head, opponent_pos),
                    state.manhattan_distance(tail, opponent_pos)
                )
                # Also consider blocking opponent's path to prize
                rope_to_prize = min(
                    state.manhattan_distance(head, state.prize_pos),
                    state.manhattan_distance(tail, state.prize_pos)
                )
                # Bonus if rope is directly between opponent and prize (in their path)
                opp_row, opp_col = opponent_pos
                prize_row, prize_col = state.prize_pos
                in_path = False
                for cell in cells:
                    # If rope cell is between opponent and prize in row or col
                    if (min(opp_row, prize_row) <= cell[0] <= max(opp_row, prize_row) and
                        min(opp_col, prize_col) <= cell[1] <= max(opp_col, prize_col)):
                        in_path = True
                        break
                path_bonus = -5 if in_path else 0  # Lower is better priority
                # Rope placement should be competitive with movement
                return rope_to_opponent + rope_to_prize * 0.5 + path_bonus
            else:
                return 50
        return sorted(actions, key=action_priority)
    
    def evaluate_state(self, state: GameState, player: Player) -> float:
        """Enhanced evaluation function (more aggressive rope use)"""
        if state.is_game_over():
            winner = state.get_winner()
            if winner == player:
                return 1000  # Win
            elif winner is not None:
                return -1000  # Loss
            else:
                return 0  # Draw
        # Get positions
        player_pos = (state.player1_pos if player == Player.PLAYER1 
                     else state.player2_pos)
        opponent_pos = (state.player2_pos if player == Player.PLAYER1 
                       else state.player1_pos)
        # Distance factors (closer to prize is much better)
        player_distance = state.manhattan_distance(player_pos, state.prize_pos)
        opponent_distance = state.manhattan_distance(opponent_pos, state.prize_pos)
        distance_score = (opponent_distance - player_distance) * 20  # Stronger weight
        # Ladder bonus
        ladder_bonus = 0
        if hasattr(state, 'ladders'):
            for start_pos, end_pos in state.ladders:
                # Bonus if player is on a ladder base
                if player_pos == start_pos:
                    # Extra bonus if ladder leads closer to prize
                    if state.manhattan_distance(end_pos, state.prize_pos) < player_distance:
                        ladder_bonus += 30
                    else:
                        ladder_bonus += 10
                # Bonus if ladder leads directly to the prize
                if end_pos == state.prize_pos and player_pos == start_pos:
                    ladder_bonus += 50
        # Rope strategic factors - evaluate rope placement effectiveness
        rope_score = 0
        player_ropes = (state.player1_rope_obstacles if player == Player.PLAYER1 
                       else state.player2_rope_obstacles)
        for cells, rope_player, used in state.rope_obstacles:
            rope_value = 0
            if rope_player == player:
                opponent_to_rope = min(
                    state.manhattan_distance(opponent_pos, cells[0]),
                    state.manhattan_distance(opponent_pos, cells[-1])
                )
                # Stronger reward for ropes close to opponent
                rope_value += max(0, 10 - 2 * opponent_to_rope)
                # Extra reward if rope is between opponent and prize
                for cell in cells:
                    if (min(opponent_pos[0], state.prize_pos[0]) <= cell[0] <= max(opponent_pos[0], state.prize_pos[0]) and
                        min(opponent_pos[1], state.prize_pos[1]) <= cell[1] <= max(opponent_pos[1], state.prize_pos[1])):
                        rope_value += 10
                        break
            else:
                player_to_rope = min(
                    state.manhattan_distance(player_pos, cells[0]),
                    state.manhattan_distance(player_pos, cells[-1])
                )
                rope_value -= max(0, 5 - player_to_rope)
            rope_score += rope_value
        # Encourage using ropes if opponent is close to prize and AI has ropes left
        if opponent_distance < 5 and player_ropes > 0:
            rope_score += (5 - opponent_distance) * 10
        # Penalize having unused ropes if opponent is very close to winning
        if opponent_distance <= 2 and player_ropes > 0:
            rope_score -= player_ropes * 20
        turn_penalty = -state.turn_count * 0.1
        center_row, center_col = state.board_size // 2, state.board_size // 2
        player_center_distance = abs(player_pos[0] - center_row) + abs(player_pos[1] - center_col)
        opponent_center_distance = abs(opponent_pos[0] - center_row) + abs(opponent_pos[1] - center_col)
        center_score = (opponent_center_distance - player_center_distance) * 2
        player_moves = len(state.get_possible_moves()) if state.current_player == player else 0
        mobility_score = player_moves * 1
        total_score = distance_score + ladder_bonus + rope_score + turn_penalty + center_score + mobility_score
        return total_score
    
    def minimax(self, state: GameState, depth: int, alpha: float, beta: float, 
                maximizing_player: bool, target_player: Player) -> Tuple[float, Optional[Dict]]:
        """Minimax with Alpha-Beta pruning and transposition table"""
        self.nodes_evaluated += 1
        
        # Check time limit
        if time.time() - self.start_time > self.time_limit:
            return self.evaluate_state(state, target_player), None
        
        # Check transposition table
        state_hash = state.get_state_hash()
        if state_hash in self.transposition_table:
            cached_depth, cached_value, cached_action = self.transposition_table[state_hash]
            if cached_depth >= depth:
                return cached_value, cached_action
        
        # Terminal conditions
        if depth == 0 or state.is_game_over():
            value = self.evaluate_state(state, target_player)
            self.transposition_table[state_hash] = (depth, value, None)
            return value, None
        
        actions = self.order_actions(state, state.get_possible_actions())
        best_action = None
        
        if maximizing_player:
            max_eval = -math.inf
            
            for action in actions:
                try:
                    new_state = state.apply_action(action)
                    eval_score, _ = self.minimax(new_state, depth - 1, alpha, beta, 
                                               False, target_player)
                    
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_action = action
                    
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        self.pruning_count += 1
                        break  # Alpha-Beta pruning
                        
                except ValueError as e:
                    continue
            
            # Cache result
            self.transposition_table[state_hash] = (depth, max_eval, best_action)
            return max_eval, best_action
        
        else:
            min_eval = math.inf
            
            for action in actions:
                try:
                    new_state = state.apply_action(action)
                    eval_score, _ = self.minimax(new_state, depth - 1, alpha, beta, 
                                               True, target_player)
                    
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_action = action
                    
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        self.pruning_count += 1
                        break  # Alpha-Beta pruning
                        
                except ValueError as e:
                    continue
            
            # Cache result
            self.transposition_table[state_hash] = (depth, min_eval, best_action)
            return min_eval, best_action
    
    def iterative_deepening(self, state: GameState) -> Dict:
        """Iterative deepening search"""
        best_action = None
        self.start_time = time.time()
        
        for depth in range(1, self.max_depth + 1):
            if time.time() - self.start_time > self.time_limit:
                break
                
            try:
                _, action = self.minimax(state, depth, -math.inf, math.inf, 
                                       True, state.current_player)
                if action:
                    best_action = action
                    
                print(f"   🔍 Depth {depth} completed in {time.time() - self.start_time:.2f}s")
                
            except Exception as e:
                print(f"   ⚠️ Depth {depth} interrupted: {e}")
                break
        
        return best_action
    
    def get_best_move(self, state: GameState, use_iterative_deepening: bool = True) -> Dict:
        """Get the best move using optimized search"""
        self.nodes_evaluated = 0
        self.pruning_count = 0
        
        print(f"🤖 AI {state.current_player.name} analyzing...")
        
        if use_iterative_deepening:
            best_action = self.iterative_deepening(state)
        else:
            self.start_time = time.time()
            _, best_action = self.minimax(state, self.max_depth, -math.inf, math.inf, 
                                         True, state.current_player)
        
        search_time = time.time() - self.start_time
        
        print(f"   📊 Analysis complete: {self.nodes_evaluated} nodes, "
              f"{self.pruning_count} pruned, {search_time:.2f}s")
        print(f"   🧠 Transposition table: {len(self.transposition_table)} entries")
        
        return best_action if best_action else state.get_possible_actions()[0]


# Keep original MinimaxAgent for backward compatibility
MinimaxAgent = OptimizedMinimaxAgent


def test_game_logic():
    """Test the game logic implementation"""
    print("🔍 Testing Stage 2: Game Logic")
    print("="*60)
    
    # Create game state
    game_state = GameState(board_size=5, max_ropes=2)  # Smaller board for testing
    game_state.print_board()
    
    # Test possible moves
    print("\n🎯 Testing possible moves:")
    moves = game_state.get_possible_moves()
    print(f"✅ Player 1 possible moves: {moves}")
    
    # Test possible actions
    print("\n🎮 Testing possible actions:")
    actions = game_state.get_possible_actions()
    for i, action in enumerate(actions):
        print(f"   {i}: {action['description']}")
    
    # Test making a move
    print("\n🚶 Testing move action:")
    if moves:
        move_action = {'type': ActionType.MOVE, 'position': moves[0]}
        new_state = game_state.apply_action(move_action)
        new_state.print_board()
        
        # Test rope action
        print("\n🪢 Testing rope action:")
        rope_action = {'type': ActionType.PLACE_ROPE_OBSTACLE, 'segment': ((0,0), (1,1), (2,2)), 'direction': 'down'}
        newer_state = new_state.apply_action(rope_action)
        newer_state.print_board()
    
    print("\n🎉 Stage 2 Complete!")


def test_minimax_agent():
    """Test the Minimax agent"""
    print("🔍 Testing Stage 3: Minimax Algorithm")
    print("="*60)
    
    # Create game state
    game_state = GameState(board_size=5, max_ropes=2)
    ai_agent = OptimizedMinimaxAgent(max_depth=3, time_limit=2.0)
    
    print("🎮 Initial state:")
    game_state.print_board()
    
    # Test evaluation function
    print("\n📊 Testing evaluation function:")
    eval_score = ai_agent.evaluate_state(game_state, Player.PLAYER1)
    print(f"✅ Evaluation score for Player 1: {eval_score}")
    
    # Test AI decision making
    print("\n🤖 Testing AI decision making:")
    best_action = ai_agent.get_best_move(game_state)
    print(f"✅ AI chose action: {best_action}")
    
    # Apply the action
    new_state = game_state.apply_action(best_action)
    new_state.print_board()
    
    # Test a few more moves
    print("\n🎯 Testing multiple AI moves:")
    current_state = new_state
    for i in range(3):
        if not current_state.is_game_over():
            print(f"\n🎮 Move {i+2}:")
            best_action = ai_agent.get_best_move(current_state)
            print(f"🤖 AI chose: {best_action}")
            current_state = current_state.apply_action(best_action)
            current_state.print_board(use_colors=False)  # Disable colors for cleaner test output
    
    print("\n🎉 Stage 3 Complete!")


def test_performance():
    """Test performance optimizations"""
    print("🔍 Testing Stage 4: Performance Optimizations")
    print("="*60)
    
    print("🚀 Testing different difficulty levels:")
    difficulties = ["easy", "medium", "hard"]
    
    for difficulty in difficulties:
        print(f"\n🎯 Testing {difficulty.upper()} difficulty:")
        game_state = GameState(board_size=5, max_ropes=2)
        
        if difficulty == "easy":
            ai_agent = OptimizedMinimaxAgent(max_depth=2, time_limit=1.0)
        elif difficulty == "medium":
            ai_agent = OptimizedMinimaxAgent(max_depth=4, time_limit=2.0)
        else:  # hard
            ai_agent = OptimizedMinimaxAgent(max_depth=6, time_limit=3.0)
        
        start_time = time.time()
        best_action = ai_agent.get_best_move(game_state)
        end_time = time.time()
        
        print(f"   ⏱️ Time taken: {end_time - start_time:.2f} seconds")
        print(f"   🧠 Nodes evaluated: {ai_agent.nodes_evaluated}")
        print(f"   ✂️ Branches pruned: {ai_agent.pruning_count}")
        print(f"   💾 Cache entries: {len(ai_agent.transposition_table)}")
        print(f"   🎯 Best action: {best_action['description']}")
    
    print("\n🎉 Stage 4 Complete!")


class Game:
    """Main game class that handles game flow and player interactions"""
    
    def __init__(self, board_size: int = 11, max_ropes: int = 3):
        self.board_size = board_size
        self.max_ropes = max_ropes
        self.difficulty = "expert"
        self.reset_game()
    
    def reset_game(self):
        """Reset the game to initial state"""
        self.state = GameState(self.board_size, self.max_ropes)
        # Set AI parameters for expert only
        self.ai_agent = OptimizedMinimaxAgent(max_depth=8, time_limit=10.0)
        self.game_history = []
        self.move_history = []
    
    def print_game_info(self):
        """Print game information and rules"""
        print("\n" + "="*70)
        print("🎮 SNAKES & LADDERS - STRATEGIC EDITION")
        print("="*70)
        print("🎯 OBJECTIVE: Be the first player to reach the prize (*) at the top!")
        print("\n📋 RULES:")
        print("• 🎮 SETUP PHASE: Each player places rope obstacles on the board")
        print("• 🎲 MAIN GAME: MOVE one step (↑↓←→) OR use a ROPE to push opponent back")
        print("• 🧠 No luck involved - pure strategy and planning!")
        print("• 👥 Players start together and can occupy the same square")
        print("• 🪢 Each player starts with limited ropes - use them wisely!")
        print("• 🏆 First player to reach the prize wins!")
        print("\n🎨 BOARD SYMBOLS:")
        print("• 🎯 * = Prize (goal)")
        print("• 🔵 1 = Player 1 (Blue)")
        print("• 🔴 2 = Player 2 (Red)")
        print("• 🤝 1&2 = Both players on same square")
        print("• 🪢 R = Rope obstacle (blocks movement)")
        print("• 🧱 # = Wall (blocked)")
        print("• ⚪ . = Empty space")
        print(f"\n⚙️ CURRENT SETTINGS:")
        print(f"   📏 Board Size: {self.board_size}x{self.board_size}")
        print(f"   🪢 Ropes per Player: {self.max_ropes}")
        print(f"   🤖 AI Difficulty: {self.difficulty.upper()}")
        print("="*70)
    
    def get_human_action(self) -> Dict:
        """Get action from human player with enhanced interface"""
        actions = self.state.get_possible_actions()
        
        print(f"\n🎯 Your turn, Player {self.state.current_player.name}!")
        print(f"🎮 Current position: {self.state.get_current_player_position()}")
        print(f"🎯 Distance to prize: {self.state.manhattan_distance(self.state.get_current_player_position(), self.state.prize_pos)}")
        print(f"🪢 Ropes remaining: {self.state.get_current_player_ropes()}")
        
        print("\n📋 Available actions:")
        for i, action in enumerate(actions):
            if action['type'] == ActionType.MOVE:
                distance = self.state.manhattan_distance(action['position'], self.state.prize_pos)
                print(f"  {i}: 🚶 {action['description']} (distance to prize: {distance})")
            else:
                print(f"  {i}: 🪢 {action['description']}")
        
        while True:
            try:
                choice = input(f"\n🎯 Enter action number (0-{len(actions)-1}): ").strip()
                choice_idx = int(choice)
                
                if 0 <= choice_idx < len(actions):
                    return actions[choice_idx]
                else:
                    print(f"❌ Invalid choice! Please enter 0-{len(actions)-1}")
            except ValueError:
                print("❌ Please enter a valid number!")
            except KeyboardInterrupt:
                print("\n👋 Game interrupted by user!")
                exit(0)
    
    def play_game(self, mode: str = "human_vs_ai"):
        """Play the game with specified mode"""
        self.print_game_info()
        
        if mode == "human_vs_ai":
            print(f"\n🤖 Mode: Human vs AI ({self.difficulty.upper()})")
            print("🔵 You are Player 1 (Blue), AI is Player 2 (Red)")
        elif mode == "ai_vs_ai":
            print(f"\n🤖 Mode: AI vs AI ({self.difficulty.upper()})")
            print("🤖 Watch two AI agents compete!")
        elif mode == "human_vs_human":
            print("\n👥 Mode: Human vs Human")
            print("👥 Two human players take turns")
        
        game_start_time = time.time()
        
        # Game loop
        while not self.state.is_game_over():
            self.state.print_board()
            
            # Determine player type
            if mode == "ai_vs_ai":
                is_ai = True
            elif mode == "human_vs_human":
                is_ai = False
            else:  # human_vs_ai
                is_ai = (self.state.current_player == Player.PLAYER2)
            
            # Get and apply action
            if is_ai:
                action = self.ai_agent.get_best_move(self.state)
                print(f"🤖 AI chose: {action['description']}")
                
                if mode == "human_vs_ai":
                    input("📱 Press Enter to continue...")
                else:
                    time.sleep(0.5)  # Brief pause for AI vs AI
            else:
                action = self.get_human_action()
            
            # Apply action and record history
            self.game_history.append((self.state.current_player, action))
            self.move_history.append(f"Turn {self.state.turn_count + 1}: {self.state.current_player.name} - {action['description']}")
            self.state = self.state.apply_action(action)
        
        # Game over
        game_duration = time.time() - game_start_time
        self.display_game_results(game_duration)
    
    def display_game_results(self, game_duration: float):
        """Display enhanced final game results"""
        self.state.print_board()
        
        winner = self.state.get_winner()
        print("\n" + "="*70)
        print("🎉 GAME OVER!")
        print("="*70)
        
        if winner:
            if winner == Player.PLAYER1:
                print(f"🏆 Winner: Player 1 (Blue) 🔵")
            else:
                print(f"🏆 Winner: Player 2 (Red) 🔴")
        else:
            print("🤝 It's a draw!")
        
        print(f"\n📊 Game Statistics:")
        print(f"   ⏱️ Game duration: {game_duration:.1f} seconds")
        print(f"   🎯 Total turns: {self.state.turn_count}")
        print(f"   🪢 Player 1 ropes remaining: {self.state.player1_ropes}")
        print(f"   🪢 Player 2 ropes remaining: {self.state.player2_ropes}")
        print(f"   📏 Board size: {self.state.board_size}x{self.state.board_size}")
        print(f"   🤖 AI difficulty: {self.difficulty.upper()}")
        
        # Show game history summary
        print(f"\n📈 Game Summary:")
        move_count = {Player.PLAYER1: 0, Player.PLAYER2: 0}
        rope_count = {Player.PLAYER1: 0, Player.PLAYER2: 0}
        
        for player, action in self.game_history:
            if action['type'] == ActionType.MOVE:
                move_count[player] += 1
            else:
                rope_count[player] += 1
        
        print(f"   🔵 Player 1: {move_count[Player.PLAYER1]} moves, {rope_count[Player.PLAYER1]} ropes used")
        print(f"   🔴 Player 2: {move_count[Player.PLAYER2]} moves, {rope_count[Player.PLAYER2]} ropes used")
        
        # Show detailed move history for short games
        if len(self.move_history) <= 20:
            print(f"\n📜 Move History:")
            for i, move in enumerate(self.move_history[-10:], 1):  # Show last 10 moves
                print(f"   {len(self.move_history) - 10 + i}: {move}")
        
        print("="*70)
    
    def play_tournament(self, num_games: int = 5):
        """Play multiple games and track results with detailed statistics"""
        print(f"\n🏆 TOURNAMENT MODE - {num_games} Games")
        print(f"🤖 AI Difficulty: {self.difficulty.upper()}")
        print("="*70)
        
        wins = {Player.PLAYER1: 0, Player.PLAYER2: 0}
        total_turns = []
        total_durations = []
        
        for game_num in range(num_games):
            print(f"\n🎮 Game {game_num + 1}/{num_games}")
            print("-" * 40)
            
            self.reset_game()
            game_start = time.time()
            self.play_game("ai_vs_ai")
            game_duration = time.time() - game_start
            
            winner = self.state.get_winner()
            if winner:
                wins[winner] += 1
            
            total_turns.append(self.state.turn_count)
            total_durations.append(game_duration)
            
            if game_num < num_games - 1:
                input("\n📱 Press Enter for next game...")
        
        # Tournament results
        print(f"\n🏆 TOURNAMENT RESULTS")
        print("="*70)
        print(f"🔵 Player 1 wins: {wins[Player.PLAYER1]} ({wins[Player.PLAYER1]/num_games*100:.1f}%)")
        print(f"🔴 Player 2 wins: {wins[Player.PLAYER2]} ({wins[Player.PLAYER2]/num_games*100:.1f}%)")
        print(f"⏱️ Average game duration: {sum(total_durations) / len(total_durations):.1f} seconds")
        print(f"🎯 Average game length: {sum(total_turns) / len(total_turns):.1f} turns")
        print(f"⚡ Shortest game: {min(total_turns)} turns")
        print(f"🐌 Longest game: {max(total_turns)} turns")
        print(f"🤖 AI Difficulty: {self.difficulty.upper()}")
        print("="*70)


def get_custom_settings():
    """Get custom game settings from user"""
    print("\n⚙️ CUSTOM SETTINGS")
    print("="*50)
    
    try:
        board_size = int(input("📏 Board size (3-15, default 7): ") or "7")
        board_size = max(3, min(15, board_size))
        
        max_ropes = int(input("🪢 Max ropes per player (0-10, default 2): ") or "2")
        max_ropes = max(0, min(10, max_ropes))
        
        print("\n🤖 AI Difficulty Options:")
        print("1. Easy (depth 2, 1s thinking)")
        print("2. Medium (depth 4, 3s thinking)")
        print("3. Hard (depth 6, 5s thinking)")
        print("4. Expert (depth 8, 10s thinking)")
        
        diff_choice = input("Choose difficulty (1-4, default 2): ") or "2"
        difficulty_map = {"1": "easy", "2": "medium", "3": "hard", "4": "expert"}
        difficulty = difficulty_map.get(diff_choice, "medium")
        
        print(f"\n✅ Settings configured:")
        print(f"   📏 Board: {board_size}x{board_size}")
        print(f"   🪢 Ropes: {max_ropes} per player")
        print(f"   🤖 AI: {difficulty.upper()}")
        
        return board_size, max_ropes, difficulty
        
    except ValueError:
        print("❌ Invalid input! Using default settings.")
        return 7, 2, "medium"


def main():
    """Main function to run the game"""
    print("🎮 Welcome to Strategic Snakes & Ladders!")
    print("🚀 Enhanced with AI Minimax Algorithm & Alpha-Beta Pruning")
    
    while True:
        print("\n🎮 MAIN MENU")
        print("="*40)
        print("1. 🔵 Human vs AI")
        print("2. 🤖 AI vs AI")
        print("3. 👥 Human vs Human")
        print("4. 🏆 AI Tournament (5 games)")
        print("5. ⚙️ Custom Settings")
        print("6. 🧪 Run Tests")
        print("7. 👋 Exit")
        
        try:
            choice = input("\n🎯 Enter your choice (1-7): ").strip()
            
            if choice == "1":
                game = Game()
                game.play_game("human_vs_ai")
            elif choice == "2":
                game = Game()
                game.play_game("ai_vs_ai")
            elif choice == "3":
                game = Game()
                game.play_game("human_vs_human")
            elif choice == "4":
                game = Game()
                game.play_tournament(5)
            elif choice == "5":
                board_size, max_ropes, difficulty = get_custom_settings()
                game = Game(board_size, max_ropes, difficulty)
                
                print("\n🎯 Choose game mode:")
                print("1. Human vs AI")
                print("2. AI vs AI")
                print("3. Human vs Human")
                print("4. Tournament")
                
                mode_choice = input("Enter mode (1-4, default 1): ") or "1"
                mode_map = {"1": "human_vs_ai", "2": "ai_vs_ai", "3": "human_vs_human", "4": "tournament"}
                
                if mode_choice == "4":
                    game.play_tournament(5)
                else:
                    mode = mode_map.get(mode_choice, "human_vs_ai")
                    game.play_game(mode)
                    
            elif choice == "6":
                run_all_tests()
            elif choice == "7":
                print("👋 Thanks for playing Strategic Snakes & Ladders!")
                print("🎮 Created with ❤️ using Python & Minimax AI")
                break
            else:
                print("❌ Invalid choice! Please enter 1-7.")
                
        except KeyboardInterrupt:
            print("\n👋 Thanks for playing Strategic Snakes & Ladders!")
            print("🎮 Created with ❤️ using Python & Minimax AI")
            break
        except Exception as e:
            print(f"❌ An error occurred: {e}")
            print("🔄 Please try again.")
            
        # Ask if user wants to play again
        try:
            play_again = input("\n🎮 Play another game? (y/n, default y): ").strip().lower()
            if play_again == 'n' or play_again == 'no':
                print("👋 Thanks for playing Strategic Snakes & Ladders!")
                print("🎮 Created with ❤️ using Python & Minimax AI")
                break
        except KeyboardInterrupt:
            print("\n👋 Thanks for playing Strategic Snakes & Ladders!")
            print("🎮 Created with ❤️ using Python & Minimax AI")
            break


def run_all_tests():
    """Run all test functions"""
    print("\n🧪 RUNNING ALL TESTS")
    print("="*70)
    
    # Test Stage 1: Foundation
    print("🔍 Testing Stage 1: Core Game Foundation")
    print("="*60)
    
    game_state = GameState(board_size=7, max_ropes=2)
    game_state.print_board()
    
    print(f"✅ Current player position: {game_state.get_current_player_position()}")
    print(f"✅ Opponent position: {game_state.get_opponent_position()}")
    print(f"✅ Current player ropes: {game_state.get_current_player_ropes()}")
    print(f"✅ Distance to prize: {game_state.manhattan_distance(game_state.get_current_player_position(), game_state.prize_pos)}")
    print(f"✅ Is game over: {game_state.is_game_over()}")
    print(f"✅ Winner: {game_state.get_winner()}")
    
    print("\n🎉 Stage 1 Complete!")
    
    # Test Stage 2: Game Logic
    print("\n\n")
    test_game_logic()
    
    # Test Stage 3: Minimax Algorithm
    print("\n\n")
    test_minimax_agent()
    
    # Test Stage 4: Performance
    print("\n\n")
    test_performance()
    
    print("\n🎉 All tests completed successfully!")
    print("🚀 System is ready for gameplay!")


# Test the foundation and game logic
if __name__ == "__main__":
    main() 