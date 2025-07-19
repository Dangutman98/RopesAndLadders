#!/usr/bin/env python3
"""
Demonstration script to show verbose vs quiet logging modes
for the Ropes & Ladders game with Minimax AI.

This helps explain the core concept without all the detailed logs.
"""

from ropes_ladders_game import GameState, OptimizedMinimaxAgent
from minimax_pruning import MinimaxPruning

def demo_verbose_mode():
    """Demonstrate with full verbose logging"""
    print("=" * 60)
    print("🔊 VERBOSE MODE - Full detailed logging")
    print("=" * 60)
    
    # Create game with verbose=True (default)
    game = GameState(board_size=7, max_ropes=2, verbose=True)
    ai = MinimaxPruning(max_depth=3, verbose=True)
    
    # Get one AI move to show all the detailed output
    actions = game.get_possible_actions()
    if actions:
        print("\n🤖 AI is making a move...")
        best_action = ai.get_best_move(game)
        print(f"✅ AI chose: {best_action['description']}")

def demo_quiet_mode():
    """Demonstrate with minimal logging for cleaner explanation"""
    print("\n" + "=" * 60)
    print("🔇 QUIET MODE - Minimal logging for clean demonstration")
    print("=" * 60)
    
    # Create game with verbose=False
    game = GameState(board_size=7, max_ropes=2, verbose=False)
    ai = MinimaxPruning(max_depth=3, verbose=False)
    
    # Get one AI move with minimal output
    actions = game.get_possible_actions()
    if actions:
        print("\n🤖 AI is making a move (quiet mode)...")
        best_action = ai.get_best_move(game)
        print(f"✅ AI chose: {best_action['description']}")
        
        # Manually show key information without noise
        print(f"   📊 Nodes evaluated: {ai.nodes_evaluated}")
        print(f"   ✂️ Alpha-Beta prunings: {ai.pruning_count}")
        print(f"   🧠 Cached positions: {len(ai.transposition_table)}")

def explain_minimax_concept():
    """Explain the minimax algorithm in simple terms"""
    print("\n" + "=" * 60)
    print("🧠 MINIMAX ALGORITHM EXPLANATION")
    print("=" * 60)
    
    print("""
🎯 What is Minimax?
   • AI looks ahead several moves into the future
   • Assumes both players play optimally
   • Maximizes its own score, minimizes opponent's score

🌳 How it works:
   1. Generate a tree of all possible future game states
   2. Evaluate each leaf position with a scoring function
   3. Propagate scores back up the tree
   4. Choose the move leading to the best guaranteed outcome

✂️ Alpha-Beta Pruning:
   • Optimization that cuts unnecessary branches
   • If we find a move that's worse than what we already have,
     stop exploring that branch
   • Can reduce search space by 50-90%

⚡ Iterative Deepening:
   • Start with depth 1, then 2, then 3, etc.
   • Always have a "best move so far" even if time runs out
   • Deeper search = better play, but takes more time

🎲 In Ropes & Ladders:
   • Evaluates: distance to goal, ladder positions, rope threats
   • Considers: offensive moves, defensive rope placement
   • Plans: multi-step combinations of moves and rope usage
    """)

if __name__ == "__main__":
    print("🎮 Ropes & Ladders - Minimax AI Demonstration")
    
    # Show both modes
    demo_verbose_mode()
    demo_quiet_mode()
    
    # Explain the concept
    explain_minimax_concept()
    
    print("\n" + "=" * 60)
    print("💡 For your video demonstration:")
    print("   • Use quiet mode (verbose=False) for cleaner terminal")
    print("   • Manually explain key concepts without log noise")
    print("   • Show specific statistics when relevant")
    print("   • Focus on strategic decisions rather than debug output")
    print("=" * 60) 