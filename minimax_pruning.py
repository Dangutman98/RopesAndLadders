import copy
import math
import time
from typing import List, Tuple, Optional, Dict, Set
from enum import Enum

class MinimaxPruning:
    """
    Advanced AI decision-making system using Minimax with Alpha-Beta pruning
    Specifically designed for strategic Snakes & Ladders gameplay
    """
    
    def __init__(self, max_depth: int = 5, time_limit: float = 3.0):
        """
        Initialize the AI system
        
        Args:
            max_depth: Maximum search depth for minimax algorithm
            time_limit: Maximum time allowed for thinking (seconds)
        """
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_evaluated = 0
        self.pruning_count = 0
        self.transposition_table = {}
        self.start_time = 0
        
        # Position history for oscillation prevention
        self.position_history = {}  # player -> list of recent positions
        self.max_history_length = 8  # Track last 8 positions
        
        # Strategic weights for evaluation
        self.DISTANCE_WEIGHT = 25
        self.LADDER_WEIGHT = 20
        self.ROPE_STRATEGIC_WEIGHT = 15
        self.ROPE_BLOCKING_WEIGHT = 30
        self.ROPE_USAGE_URGENCY = 25
        self.MOBILITY_WEIGHT = 3
        self.CENTER_CONTROL_WEIGHT = 2
        self.TURN_PENALTY = 0.1
        self.OSCILLATION_PENALTY = 15  # Penalty for returning to recent positions
        self.PROGRESS_BONUS = 10      # Bonus for making consistent progress
        
        # Game phase and patience parameters
        self.EARLY_GAME_TURNS = 8     # First 8 turns are "early game"
        self.MID_GAME_TURNS = 16      # Turns 8-16 are "mid game"
        self.PATIENCE_FACTOR = 0.2    # Reduce rope urgency by 80% in early game
        self.MID_GAME_FACTOR = 0.5    # Reduce rope urgency by 50% in mid game
        
    def clear_cache(self):
        """Clear the transposition table for fresh games"""
        self.transposition_table.clear()
        self.position_history.clear()
    
    def update_position_history(self, player, position):
        """Update position history for oscillation detection"""
        if player not in self.position_history:
            self.position_history[player] = []
        
        # Add new position
        self.position_history[player].append(position)
        
        # Keep only recent positions
        if len(self.position_history[player]) > self.max_history_length:
            self.position_history[player] = self.position_history[player][-self.max_history_length:]
    
    def get_game_phase(self, state):
        """
        Determine current game phase based on turn count and positions
        
        Returns:
            str: 'early', 'mid', or 'late'
        """
        if state.turn_count <= self.EARLY_GAME_TURNS:
            return 'early'
        elif state.turn_count <= self.MID_GAME_TURNS:
            return 'mid'
        else:
            return 'late'
    
    def get_patience_multiplier(self, state):
        """
        Get patience multiplier based on game phase
        
        Returns:
            float: Multiplier for rope urgency (lower = more patient)
        """
        phase = self.get_game_phase(state)
        
        if phase == 'early':
            return self.PATIENCE_FACTOR
        elif phase == 'mid':
            return self.MID_GAME_FACTOR
        else:
            return 1.0  # Full urgency in late game
    
    def get_oscillation_penalty(self, player, position):
        """Calculate penalty for returning to recent positions"""
        if player not in self.position_history:
            return 0
        
        recent_positions = self.position_history[player]
        if not recent_positions:
            return 0
        
        penalty = 0
        # Check how recently this position was visited
        for i, past_pos in enumerate(reversed(recent_positions)):
            if past_pos == position:
                # More recent visits get higher penalties
                recency_factor = (len(recent_positions) - i) / len(recent_positions)
                penalty += self.OSCILLATION_PENALTY * recency_factor
                break
        
        return penalty
    
    def get_progress_evaluation(self, state, player, new_position, old_position):
        """Evaluate if a move represents forward progress"""
        # Calculate distance improvement
        old_distance = state.manhattan_distance(old_position, state.prize_pos)
        new_distance = state.manhattan_distance(new_position, state.prize_pos)
        
        distance_improvement = old_distance - new_distance
        
        # Bonus for moves that reduce distance to prize
        if distance_improvement > 0:
            return self.PROGRESS_BONUS * distance_improvement
        elif distance_improvement < 0:
            # Penalty for moves that increase distance (unless strategic)
            return -self.PROGRESS_BONUS * abs(distance_improvement) * 0.5
        
        return 0
    
    def get_best_move(self, state, use_iterative_deepening: bool = True):
        """
        Get the best move for the current player
        
        Args:
            state: Current game state
            use_iterative_deepening: Whether to use iterative deepening search
            
        Returns:
            Best action dictionary
        """
        self.nodes_evaluated = 0
        self.pruning_count = 0
        
        print(f"🤖 AI {state.current_player.name} analyzing board...")
        
        if use_iterative_deepening:
            best_action = self._iterative_deepening_search(state)
        else:
            self.start_time = time.time()
            _, best_action = self._minimax(state, self.max_depth, -math.inf, math.inf, True, state.current_player)
        
        search_time = time.time() - self.start_time
        
        print(f"   📊 Analysis complete: {self.nodes_evaluated} nodes evaluated")
        print(f"   ✂️ Pruning efficiency: {self.pruning_count} branches pruned")
        print(f"   ⏱️ Search time: {search_time:.2f}s")
        print(f"   🧠 Cache entries: {len(self.transposition_table)}")
        
        # Update position history for the current player
        if best_action and best_action['type'].value == 'move':
            current_pos = state.player1_pos if state.current_player.name == "PLAYER1" else state.player2_pos
            new_pos = best_action['position']
            self.update_position_history(state.current_player, current_pos)
            
            # Log oscillation prevention info
            oscillation_penalty = self.get_oscillation_penalty(state.current_player, new_pos)
            if oscillation_penalty > 0:
                print(f"   🚫 Oscillation penalty applied: {oscillation_penalty:.1f}")
        
        return best_action if best_action else state.get_possible_actions()[0]
    
    def _iterative_deepening_search(self, state):
        """
        Perform iterative deepening search for better time management
        """
        best_action = None
        self.start_time = time.time()
        
        for depth in range(1, self.max_depth + 1):
            if time.time() - self.start_time > self.time_limit:
                break
                
            try:
                _, action = self._minimax(state, depth, -math.inf, math.inf, True, state.current_player)
                if action:
                    best_action = action
                    
                print(f"   🔍 Depth {depth} completed in {time.time() - self.start_time:.2f}s")
                
            except Exception as e:
                print(f"   ⚠️ Depth {depth} interrupted: {e}")
                break
        
        return best_action
    
    def _minimax(self, state, depth: int, alpha: float, beta: float, 
                maximizing_player: bool, target_player):
        """
        Minimax algorithm with Alpha-Beta pruning
        
        Args:
            state: Current game state
            depth: Current search depth
            alpha: Alpha value for pruning
            beta: Beta value for pruning
            maximizing_player: Whether current player is maximizing
            target_player: The player we're optimizing for
            
        Returns:
            Tuple of (evaluation_score, best_action)
        """
        self.nodes_evaluated += 1
        
        # Check time limit
        if time.time() - self.start_time > self.time_limit:
            return self._evaluate_state(state, target_player), None
        
        # Check transposition table
        state_hash = self._get_state_hash(state)
        if state_hash in self.transposition_table:
            cached_depth, cached_value, cached_action = self.transposition_table[state_hash]
            if cached_depth >= depth:
                return cached_value, cached_action
        
        # Terminal conditions
        if depth == 0 or state.is_game_over():
            value = self._evaluate_state(state, target_player)
            self.transposition_table[state_hash] = (depth, value, None)
            return value, None
        
        # Get and order actions for better pruning
        actions = self._order_actions(state, state.get_possible_actions())
        best_action = None
        
        if maximizing_player:
            max_eval = -math.inf
            
            for action in actions:
                try:
                    new_state = state.apply_action(action)
                    eval_score, _ = self._minimax(new_state, depth - 1, alpha, beta, False, target_player)
                    
                    if eval_score > max_eval:
                        max_eval = eval_score
                        best_action = action
                    
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        self.pruning_count += 1
                        break  # Alpha-Beta pruning
                        
                except ValueError:
                    continue
            
            self.transposition_table[state_hash] = (depth, max_eval, best_action)
            return max_eval, best_action
        
        else:
            min_eval = math.inf
            
            for action in actions:
                try:
                    new_state = state.apply_action(action)
                    eval_score, _ = self._minimax(new_state, depth - 1, alpha, beta, True, target_player)
                    
                    if eval_score < min_eval:
                        min_eval = eval_score
                        best_action = action
                    
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        self.pruning_count += 1
                        break  # Alpha-Beta pruning
                        
                except ValueError:
                    continue
            
            self.transposition_table[state_hash] = (depth, min_eval, best_action)
            return min_eval, best_action
    
    def _evaluate_state(self, state, player):
        """
        Comprehensive evaluation function that considers all game elements
        
        Args:
            state: Current game state
            player: Player to evaluate for
            
        Returns:
            Evaluation score (higher is better for the player)
        """
        # Terminal state evaluation
        if state.is_game_over():
            winner = state.get_winner()
            if winner == player:
                return 1000  # Win
            elif winner is not None:
                return -1000  # Loss
            else:
                return 0  # Draw
        
        # Get positions
        player_pos = state.player1_pos if player.name == "PLAYER1" else state.player2_pos
        opponent_pos = state.player2_pos if player.name == "PLAYER1" else state.player1_pos
        
        score = 0
        
        # 1. Distance to prize (most important factor)
        player_distance = state.manhattan_distance(player_pos, state.prize_pos)
        opponent_distance = state.manhattan_distance(opponent_pos, state.prize_pos)
        distance_score = (opponent_distance - player_distance) * self.DISTANCE_WEIGHT
        score += distance_score
        
        # 2. Ladder strategic evaluation
        ladder_score = self._evaluate_ladders(state, player, player_pos, opponent_pos)
        score += ladder_score
        
        # 3. Rope strategic evaluation
        rope_score = self._evaluate_ropes(state, player, player_pos, opponent_pos)
        score += rope_score
        
        # 4. Rope usage urgency (encourage using ropes when opponent is close)
        rope_urgency_score = self._evaluate_rope_urgency(state, player, opponent_distance)
        score += rope_urgency_score
        
        # 5. Mobility (more options = better)
        mobility_score = self._evaluate_mobility(state, player)
        score += mobility_score
        
        # 6. Board control (favor center positions early game)
        center_control_score = self._evaluate_center_control(state, player_pos, opponent_pos)
        score += center_control_score
        
        # 7. Turn penalty (encourage faster wins)
        turn_penalty = -state.turn_count * self.TURN_PENALTY
        score += turn_penalty
        
        # 8. Oscillation penalty (prevent getting stuck in loops)
        oscillation_penalty = self.get_oscillation_penalty(player, player_pos)
        score -= oscillation_penalty
        
        # 9. Progress evaluation (bonus for consistent forward movement)
        if player in self.position_history and self.position_history[player]:
            last_position = self.position_history[player][-1] if self.position_history[player] else player_pos
            progress_score = self.get_progress_evaluation(state, player, player_pos, last_position)
            score += progress_score
        
        return score
    
    def _evaluate_ladders(self, state, player, player_pos, opponent_pos):
        """Evaluate ladder positions and opportunities"""
        if not hasattr(state, 'ladders'):
            return 0
        
        ladder_score = 0
        
        for start_pos, end_pos in state.ladders:
            # Bonus if player is on a ladder base
            if player_pos == start_pos:
                ladder_advance = state.manhattan_distance(player_pos, state.prize_pos) - state.manhattan_distance(end_pos, state.prize_pos)
                if ladder_advance > 0:  # Ladder brings us closer to prize
                    ladder_score += ladder_advance * self.LADDER_WEIGHT
                else:
                    ladder_score += 5  # Small bonus even if not optimal
            
            # Penalty if opponent is on a ladder base
            if opponent_pos == start_pos:
                ladder_advance = state.manhattan_distance(opponent_pos, state.prize_pos) - state.manhattan_distance(end_pos, state.prize_pos)
                if ladder_advance > 0:
                    ladder_score -= ladder_advance * self.LADDER_WEIGHT
                else:
                    ladder_score -= 5
            
            # Bonus for being close to beneficial ladder bases
            if state.manhattan_distance(end_pos, state.prize_pos) < state.manhattan_distance(start_pos, state.prize_pos):
                distance_to_ladder = state.manhattan_distance(player_pos, start_pos)
                if distance_to_ladder <= 3:  # Within striking distance
                    ladder_score += (4 - distance_to_ladder) * 3
        
        return ladder_score
    
    def _evaluate_ropes(self, state, player, player_pos, opponent_pos):
        """Evaluate rope obstacles and their strategic value"""
        rope_score = 0
        
        for cells, rope_player, used in state.rope_obstacles:
            rope_head = cells[0]
            rope_tail = cells[-1]
            
            if rope_player == player:
                # Our rope - evaluate its effectiveness
                if not used:
                    # Unused rope - evaluate potential
                    opponent_to_head = state.manhattan_distance(opponent_pos, rope_head)
                    if opponent_to_head <= 2:  # Opponent is close to rope head
                        rope_score += self.ROPE_STRATEGIC_WEIGHT
                    
                    # Bonus if rope blocks opponent's path to prize
                    if self._rope_blocks_path(state, cells, opponent_pos, state.prize_pos):
                        rope_score += self.ROPE_BLOCKING_WEIGHT
                else:
                    # Used rope - small bonus for having used it effectively
                    rope_score += 5
            else:
                # Opponent's rope - evaluate threat
                if not used:
                    player_to_head = state.manhattan_distance(player_pos, rope_head)
                    if player_to_head <= 2:  # We're close to opponent's rope head
                        rope_score -= self.ROPE_STRATEGIC_WEIGHT
                    
                    # Penalty if rope blocks our path
                    if self._rope_blocks_path(state, cells, player_pos, state.prize_pos):
                        rope_score -= self.ROPE_BLOCKING_WEIGHT
        
        return rope_score
    
    def _evaluate_rope_urgency(self, state, player, opponent_distance):
        """Evaluate urgency of using remaining ropes with game phase awareness"""
        player_ropes = state.player1_rope_obstacles if player.name == "PLAYER1" else state.player2_rope_obstacles
        
        # Get patience multiplier based on game phase
        patience_multiplier = self.get_patience_multiplier(state)
        
        base_urgency = 0
        
        if player_ropes > 0 and opponent_distance <= 3:
            # Opponent is very close to winning - we should use ropes aggressively
            base_urgency = (4 - opponent_distance) * self.ROPE_USAGE_URGENCY
        elif player_ropes > 0 and opponent_distance <= 5:
            # Opponent is getting close - moderate urgency
            base_urgency = (6 - opponent_distance) * (self.ROPE_USAGE_URGENCY // 2)
        elif player_ropes > 1 and opponent_distance <= 7:
            # Still have multiple ropes and opponent is advancing
            base_urgency = (8 - opponent_distance) * (self.ROPE_USAGE_URGENCY // 3)
        
        # Apply patience multiplier (reduces urgency in early/mid game)
        return base_urgency * patience_multiplier
    
    def _evaluate_mobility(self, state, player):
        """Evaluate movement options available to player"""
        if state.current_player == player:
            moves = len(state.get_possible_moves())
            return moves * self.MOBILITY_WEIGHT
        return 0
    
    def _evaluate_center_control(self, state, player_pos, opponent_pos):
        """Evaluate control of center positions (more important early game)"""
        if state.turn_count > 20:  # Less important in late game
            return 0
        
        center_row, center_col = state.board_size // 2, state.board_size // 2
        
        player_center_distance = abs(player_pos[0] - center_row) + abs(player_pos[1] - center_col)
        opponent_center_distance = abs(opponent_pos[0] - center_row) + abs(opponent_pos[1] - center_col)
        
        return (opponent_center_distance - player_center_distance) * self.CENTER_CONTROL_WEIGHT
    
    def _rope_blocks_path(self, state, rope_cells, start_pos, end_pos):
        """Check if rope blocks direct path between two positions"""
        start_row, start_col = start_pos
        end_row, end_col = end_pos
        
        # Check if any rope cell is in the direct path
        for rope_row, rope_col in rope_cells:
            # Simple check: is rope cell between start and end?
            if (min(start_row, end_row) <= rope_row <= max(start_row, end_row) and
                min(start_col, end_col) <= rope_col <= max(start_col, end_col)):
                return True
        
        return False
    
    def _order_actions(self, state, actions):
        """Order actions for better alpha-beta pruning"""
        def action_priority(action):
            # Import ActionType locally to avoid circular imports
            from snakes_ladders_game import ActionType
            
            if action['type'] == ActionType.MOVE:
                # Prioritize moves that get closer to prize
                distance = state.manhattan_distance(action['position'], state.prize_pos)
                
                # Add oscillation penalty to move ordering
                oscillation_penalty = self.get_oscillation_penalty(state.current_player, action['position'])
                
                # Add progress evaluation
                current_pos = state.get_current_player_position()
                progress_bonus = -self.get_progress_evaluation(state, state.current_player, action['position'], current_pos)
                
                # Combine factors (lower score = higher priority)
                total_score = distance + (oscillation_penalty * 0.1) + (progress_bonus * 0.1)
                return total_score
            
            elif action['type'] == ActionType.PLACE_ROPE_OBSTACLE:
                # Prioritize rope placement based on strategic value and game phase
                cells = action['segment']
                head = cells[0]
                tail = cells[-1]
                opponent_pos = state.get_opponent_position()
                current_pos = state.get_current_player_position()
                
                # Get current player's remaining ropes
                player_ropes = state.player1_rope_obstacles if state.current_player.name == "PLAYER1" else state.player2_rope_obstacles
                
                # Distance from opponent to rope head
                rope_to_opponent = state.manhattan_distance(head, opponent_pos)
                opponent_to_prize = state.manhattan_distance(opponent_pos, state.prize_pos)
                
                # URGENT DEFENSIVE MODE: If opponent is very close to winning
                urgent_defense_bonus = 0
                if opponent_to_prize <= 3:  # Opponent is 3 or fewer moves from winning
                    # Prioritize ropes exactly 1 cell ahead of opponent toward prize
                    if rope_to_opponent == 1:
                        # Check if rope is in opponent's direction toward prize
                        opponent_row, opponent_col = opponent_pos
                        prize_row, prize_col = state.prize_pos
                        head_row, head_col = head
                        
                        # Is rope head between opponent and prize?
                        if ((opponent_row > prize_row and head_row < opponent_row) or  # Opponent moving up
                            (opponent_row < prize_row and head_row > opponent_row) or  # Opponent moving down
                            (opponent_col > prize_col and head_col < opponent_col) or  # Opponent moving left
                            (opponent_col < prize_col and head_col > opponent_col)):   # Opponent moving right
                            urgent_defense_bonus = -25  # VERY high priority for defensive rope
                
                # Normal distance optimization (when not in urgent defense mode)
                distance_bonus = 0
                if urgent_defense_bonus == 0:  # Only apply normal logic if not urgent defense
                    if 2 <= rope_to_opponent <= 4:
                        distance_bonus = -5  # Negative = higher priority
                    elif rope_to_opponent == 1:
                        distance_bonus = 5   # Reduced penalty when not urgent
                    elif rope_to_opponent > 6:
                        distance_bonus = 15  # Too far, likely irrelevant
                
                # Distance from rope to prize (ropes closer to prize are more blocking)
                rope_to_prize = min(
                    state.manhattan_distance(head, state.prize_pos),
                    state.manhattan_distance(tail, state.prize_pos)
                )
                
                # Bonus for ropes that block opponent's path to prize
                path_blocking_bonus = 0
                if self._rope_blocks_path(state, cells, opponent_pos, state.prize_pos):
                    path_blocking_bonus = -15  # Negative because lower is better priority
                
                # Penalty for ropes too close to current player (likely ineffective)
                self_distance_penalty = 0
                current_to_head = state.manhattan_distance(current_pos, head)
                if current_to_head <= 1:
                    self_distance_penalty = 20  # High penalty for placing rope next to self
                
                # Game phase patience penalty (makes rope placement less attractive in early game)
                # BUT: ignore patience when opponent is about to win!
                patience_penalty = 0
                if opponent_to_prize > 3:  # Only apply patience when not urgent
                    game_phase = self.get_game_phase(state)
                    if game_phase == 'early':
                        patience_penalty = 30  # Higher penalty in early game
                    elif game_phase == 'mid':
                        patience_penalty = 15  # Medium penalty in mid game
                
                # Rope conservation penalty (discourage using all ropes at once)
                conservation_penalty = 0
                if player_ropes > 1:  # If we have multiple ropes left
                    # Encourage saving at least one rope for later
                    conservation_penalty = (player_ropes - 1) * 8
                
                # Priority toward opponent's likely movement direction
                direction_bonus = 0
                if rope_to_opponent <= 3:  # Only consider if rope is reasonably close
                    opponent_to_prize = state.manhattan_distance(opponent_pos, state.prize_pos)
                    rope_to_prize_from_opponent = state.manhattan_distance(head, state.prize_pos)
                    if rope_to_prize_from_opponent < opponent_to_prize:
                        direction_bonus = -8  # Rope is between opponent and prize
                
                return (rope_to_opponent + distance_bonus + urgent_defense_bonus + rope_to_prize * 0.3 + 
                       path_blocking_bonus + self_distance_penalty + patience_penalty + 
                       conservation_penalty + direction_bonus)
            
            return 50  # Default priority
        
        return sorted(actions, key=action_priority)
    
    def _get_state_hash(self, state):
        """Generate a unique hash for the game state (for transposition table)"""
        # Create a simple hash based on key state components
        return (f"{state.player1_pos}_{state.player2_pos}_{state.player1_rope_obstacles}_"
                f"{state.player2_rope_obstacles}_{state.current_player.name}_{state.turn_count}_"
                f"{len(state.rope_obstacles)}_{state.game_phase.name}")


 