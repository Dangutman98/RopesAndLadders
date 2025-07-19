# 🎮 Snakes & Ladders with Smart AI

A modern twist on the classic Snakes & Ladders game featuring intelligent AI with strategic rope placement mechanics.

### 🎯 **Game Mechanics**
- **Interactive GUI** with modern pygame interface
- **Strategic rope placement** - players can place ropes to push opponents back
- **Smart ladders** - climb up instantly when stepping on ladder base
- **No luck involved** - pure strategy and skill!

### 🤖 **Advanced AI System**
- **MinimaxPruning Algorithm** with Alpha-Beta pruning
- **Intelligent rope placement** with game phase awareness
- **Adaptive strategy** - patient in early game, aggressive when threatened
- **Optimized performance** with transposition tables and iterative deepening

### 🎮 **Game Modes**
- **Human vs AI** - Challenge the intelligent opponent
- **AI vs AI** - Watch two AIs compete strategically
- **Human vs Human** - Play against friends locally

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pygame library

### Installation
```
# Clone the repository
git clone https://github.com/yourusername/SnakesAndLadders2.git
cd SnakesAndLadders2

# Install dependencies
pip install pygame

# Run the game
python snakes_ladders_gui.py
```

## 🎯 How to Play

### **Objective**
Be the first player to reach the prize (⭐) at the top of the board!

### **Controls**
- **Movement**: Click on adjacent cells to move your player
- **Rope Placement**: Click "Place Rope" and select rope type and position
- **Strategic Timing**: Use ropes wisely - you have limited rope obstacles!

### **Game Elements**
- 🔵 **Player 1** (Blue) - Human player
- 🔴 **Player 2** (Red) - AI opponent  
- ⭐ **Prize** - Goal position at the top
- 🆙 **Ladders** - Climb up when stepped on
- 🎗️ **Ropes** - Push opponents back when triggered
- 🧱 **Walls** - Blocked positions

## 🧠 AI Strategy

The AI uses a sophisticated strategy system:

### **Game Phase Awareness**
- **Early Game**: Focuses on movement, conserves ropes
- **Mid Game**: Moderate rope usage, strategic positioning
- **Late Game**: Aggressive rope placement when threatened

### **Smart Rope Placement**
- **Optimal Distance**: Places ropes 2-4 cells from opponent normally
- **Urgent Defense**: Places ropes 1 cell ahead when opponent is about to win
- **Path Blocking**: Prioritizes ropes that block opponent's path to prize
- **Conservation**: Avoids using all ropes at once

### **Advanced Features**
- **Alpha-Beta Pruning**: Eliminates poor moves early
- **Transposition Tables**: Caches evaluated positions
- **Iterative Deepening**: Searches deeper when time allows
- **Oscillation Prevention**: Avoids getting stuck in movement loops

## 📁 Project Structure

```
SnakesAndLadders2/
├── snakes_ladders_gui.py      # Main GUI application
├── snakes_ladders_game.py     # Core game logic and AI wrapper
├── minimax_pruning.py         # Advanced AI implementation
├── README.md                  # This file
└── .gitignore                 # Git ignore rules
```

## 🔧 Technical Details

### **Core Classes**
- **`GameState`**: Manages board state, player positions, and game rules
- **`MinimaxPruning`**: Advanced AI with strategic decision making
- **`OptimizedMinimaxAgent`**: Wrapper for backward compatibility
- **`SnakesLaddersGUI`**: Pygame-based graphical interface

### **AI Configuration**
- **Search Depth**: 5 levels (configurable)
- **Time Limit**: 3 seconds per move
- **Evaluation Weights**: Optimized for strategic play
- **Performance**: ~1000 nodes evaluated per move

### **Performance Metrics**
- **Average AI Response**: 0.3-0.5 seconds
- **Pruning Efficiency**: 50+ branches pruned per search
- **Memory Usage**: Optimized with transposition tables

## 🤝 Contributing

Feel free to contribute improvements:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- Built with **Python** and **pygame**
- AI implementation uses **Minimax algorithm** with **Alpha-Beta pruning**
- Inspired by classic Snakes & Ladders with modern strategic elements

---

*Enjoy strategic gameplay with intelligent AI!* 🎮🤖 
