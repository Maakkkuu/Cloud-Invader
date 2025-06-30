# Game constants

# Screen dimensions
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)  # Added missing PURPLE color
GRAY = (128, 128, 128)  # Added missing GRAY color
AWS_ORANGE = (255, 153, 0)
AWS_BLUE = (51, 153, 255)

# Game settings
PLAYER_SPEED = 5
PLAYER_COOLDOWN = 25  # Increased from 15 to slow down firing rate
INITIAL_CREDITS = 1000000  # 1 million AWS credits (back to original)
CREDIT_BURN_RATE = 10  # Base credits burned per second per enemy
HIT_PENALTY = 50000  # Credits lost when hit by enemy laser
LIVES_NAME = "AWS Credits"
PLAYER_NAME = "Starship Cirrus"

# Sprite dimensions
PLAYER_SPRITE_SIZE = (64, 64)
ENEMY_SPRITE_SIZE = (96, 96)  # Reverted from 192x192 back to 96x96 (normal size)

# Audio settings
ENABLE_AUDIO = True  # Set to False to disable all audio
MENU_MUSIC_VOLUME = 1.0  # Volume for menu music (100%)
ENEMY_SPEED = 2
ENEMY_SHOOT_CHANCE = 0.2  # Further reduced percentage chance per frame

# Power-up durations (in frames at 60fps)
S3_DURATION = 600  # 10 seconds
LOAD_BALANCER_DURATION = 900  # 15 seconds
AUTO_SCALING_DURATION = 1200  # 20 seconds

# Level system
CURRENT_LEVEL = 1
MAX_LEVELS = 4

# Level-specific settings
LEVEL_CONFIGS = {
    1: {
        'enemy_type': 'EC2',
        'enemy_sprite': 'assets/images/enemies/ec2.png',
        'background': 'assets/images/bg/level_one_bg.jpg',  # Updated to bg directory
        'enemy_speed': 2,
        'enemy_shoot_interval': 150,  # 2.5 seconds at 60fps
        'enemy_shoot_chance': 0.5,    # 50% chance when timer triggers
        'enemy_health': 1,
        'credit_burn_rate': 10
    },
    2: {
        'enemy_type': 'DynamoDB',
        'enemy_sprite': 'assets/images/enemies/dynamodb.png',
        'background': 'assets/images/bg/level_two_bg.png',  # Updated to bg directory
        'enemy_speed': 1,
        'enemy_shoot_interval': 0,    # DynamoDB doesn't use regular shooting
        'enemy_shoot_chance': 0.0,    # DynamoDB doesn't shoot normally, uses charge system
        'enemy_health': 5,  # Increased from 3 to 5 hits
        'credit_burn_rate': 25  # More expensive
    },
    3: {
        'enemy_type': 'Lambda',
        'enemy_sprite': 'assets/images/enemies/lambda.png',
        'background': 'assets/images/bg/level_three_bg.png',  # Updated to bg directory
        'enemy_speed': 1.5,
        'enemy_shoot_interval': 180,  # 3 seconds at 60fps
        'enemy_shoot_chance': 0.3,    # 30% chance when timer triggers (reduced from 70%)
        'enemy_health': 2,  # Medium toughness
        'credit_burn_rate': 15  # Moderate cost
    },
    4: {
        'enemy_type': 'CloudFormation',
        'enemy_sprite': 'assets/images/enemies/boss/cloudformation.png',
        'background': 'assets/images/bg/boss_bg.png',  # Assuming boss background is in bg directory
        'enemy_speed': 0.8,  # Increased speed for visible movement
        'enemy_shoot_interval': 180,  # 3 seconds at 60fps (changed from 300)
        'enemy_shoot_chance': 1.0,    # 100% chance for abilities (guaranteed every 3 seconds)
        'enemy_health': 300,  # Boss health (changed from 500)
        'credit_burn_rate': 100  # Expensive boss
    }
}

# Asteroid settings for DynamoDB
ASTEROID_SPRITES = [
    'assets/images/enemies/asteriods/asteriod_1.png',
    'assets/images/enemies/asteriods/asteriod_2.png',
    'assets/images/enemies/asteriods/asteriod_3.png',
    'assets/images/enemies/asteriods/asteriod_4.png'
]
ASTEROID_SPEED = 3  # Slow moving asteroids
DYNAMODB_CHARGE_TIME_MIN = 180  # 3 seconds at 60fps
DYNAMODB_CHARGE_TIME_MAX = 360  # 6 seconds at 60fps

# Boss level settings
BOSS_INTRO_DURATION = 420  # 7 seconds at 60fps (changed from 600)
BOSS_FADE_IN_DURATION = 420  # 7 seconds fade in (changed from 300)
BOSS_LASER_DURATION = 180  # 3 seconds laser beam (changed from 300)
BOSS_SIZE = (200, 150)  # Large boss sprite size
BOSS_MAX_HEALTH = 300  # Boss health for health bar (changed from 500)
BOSS_EXPLOSION_DURATION = 360  # 6 seconds explosion (changed from 600)
BOSS_HEALTH_BAR_WIDTH = 400
BOSS_HEALTH_BAR_HEIGHT = 20

# AWS Theme
ENEMY_NAMES = ["EC2", "DynamoDB"]  # Updated for multiple levels
LASER_NAME = "CloudShell Command"
