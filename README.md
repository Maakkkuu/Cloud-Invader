# Cloud Invaders

A Space Invaders/Shooter-style game with AWS themes, built with Python and Pygame.

## Game Description

Control the Starship Cirrus and destroy AWS service invaders before your credits run out. Each running service costs credits every second - manage your budget while defending the cloud!

## Controls
- **Arrow Keys**: Move ship left/right
- **Space**: Shoot laser
- **Enter**: Start game / Select menu option
- **Escape**: Quit game

## Installation & Running

```bash
# Clone my repository
git clone https://github.com/Maakkkuu/Cloud-Invader.git

# Change to the game directory
cd Cloud-Invader/

# Install Pygame
pip install pygame

# Run the game
python main.py
```

## Project Structure

```
cloud-invaders/
├── main.py              # Game entry point
├── src/
│   ├── game.py          # Main game logic
│   ├── menu.py          # Menu system
│   ├── sprites.py       # Game sprites
│   └── constants.py     # Game settings
└── assets/
    ├── images/          # Sprites and backgrounds
    └── audio/           # Sound effects and music
```

## AWS Theme

- **Starship Cirrus**: Your cloud-native spacecraft
- **AWS Credits**: Resource/health system
- **Service Enemies**: EC2, DynamoDB, Lambda, CloudFormation
- **Power-Ups**: S3, Load Balancer, Auto Scaling services

---

**Disclaimer**: The AWS resource costs in this game are fictional and not equivalent to real AWS pricing.

Defend the cloud and become the ultimate AWS Cloud Defender! 🚀☁️
