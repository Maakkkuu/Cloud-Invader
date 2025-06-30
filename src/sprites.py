import pygame
import random
import os
from src.constants import *

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        
        # Try to load sprite images
        sprite_path = "assets/images/ship/starship_cirrus.png"
        shadow_path = "assets/images/ship/starship_cirrus_shadow.png"
        s3_path = "assets/images/ship/s3_powered_player_ship.png"
        
        if os.path.exists(sprite_path):
            self.normal_image = pygame.image.load(sprite_path)
            self.normal_image = pygame.transform.scale(self.normal_image, PLAYER_SPRITE_SIZE)
        else:
            # Create the normal Starship Cirrus player ship (fallback)
            self.normal_image = pygame.Surface(PLAYER_SPRITE_SIZE)
            self.normal_image.fill(AWS_ORANGE)
            
            # Add AWS logo-like design
            center_x, center_y = PLAYER_SPRITE_SIZE[0] // 2, PLAYER_SPRITE_SIZE[1] // 2
            pygame.draw.polygon(self.normal_image, AWS_BLUE, [
                (center_x, center_y - 15), 
                (center_x + 20, center_y), 
                (center_x, center_y + 15), 
                (center_x - 20, center_y)
            ])
        
        # Load shadow sprite
        if os.path.exists(shadow_path):
            self.shadow_image = pygame.image.load(shadow_path)
            self.shadow_image = pygame.transform.scale(self.shadow_image, PLAYER_SPRITE_SIZE)
        else:
            # Create shadow fallback (darker version of normal sprite)
            self.shadow_image = self.normal_image.copy()
            shadow_overlay = pygame.Surface(PLAYER_SPRITE_SIZE)
            shadow_overlay.fill((0, 0, 0))
            shadow_overlay.set_alpha(150)  # Semi-transparent black
            self.shadow_image.blit(shadow_overlay, (0, 0))
        
        # Load S3 powered sprite
        if os.path.exists(s3_path):
            self.s3_image = pygame.image.load(s3_path)
            self.s3_image = pygame.transform.scale(self.s3_image, PLAYER_SPRITE_SIZE)
        else:
            # Create S3 fallback (green tinted version)
            self.s3_image = self.normal_image.copy()
            s3_overlay = pygame.Surface(PLAYER_SPRITE_SIZE)
            s3_overlay.fill((0, 255, 0))
            s3_overlay.set_alpha(100)
            self.s3_image.blit(s3_overlay, (0, 0))
        
        self.image = self.normal_image.copy()
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH // 2 - PLAYER_SPRITE_SIZE[0] // 2
        self.rect.y = SCREEN_HEIGHT - PLAYER_SPRITE_SIZE[1] - 10
        self.speed = PLAYER_SPEED
        self.credits = INITIAL_CREDITS
        self.cooldown = 0
        self.cooldown_time = PLAYER_COOLDOWN
        
        # Invincibility system with glitching effect
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 120  # 2 seconds at 60fps
        self.glitch_timer = 0
        self.use_shadow = False  # Toggle between normal and shadow
        
        # Power-up system
        self.s3_power = False
        self.s3_timer = 0
        self.s3_duration = 300  # 5 seconds at 60fps
        
        self.load_balancer_power = False
        self.load_balancer_timer = 0
        self.load_balancer_duration = 600  # 10 seconds at 60fps

    def update(self):
        # Handle S3 power-up
        if self.s3_power:
            self.s3_timer -= 1
            if self.s3_timer <= 0:
                self.s3_power = False
        
        # Handle Load Balancer power-up
        if self.load_balancer_power:
            self.load_balancer_timer -= 1
            if self.load_balancer_timer <= 0:
                self.load_balancer_power = False
        
        # Handle invincibility with glitching effect
        if self.invincible or self.s3_power:
            if self.invincible:
                self.invincible_timer -= 1
                self.glitch_timer += 1
                
                # Toggle between normal and shadow sprites every 8 frames for glitching effect
                if self.glitch_timer % 8 == 0:
                    self.use_shadow = not self.use_shadow
                    
                # Apply the appropriate sprite
                if self.use_shadow:
                    self.image = self.shadow_image.copy()
                else:
                    self.image = self.s3_image.copy() if self.s3_power else self.normal_image.copy()
                
                # End invincibility
                if self.invincible_timer <= 0:
                    self.invincible = False
                    self.use_shadow = False
            else:
                # S3 power without invincibility glitch
                self.image = self.s3_image.copy()
        else:
            # Use normal sprite when no special effects
            self.image = self.normal_image.copy()
            
        # Decrease cooldown timer
        if self.cooldown > 0:
            self.cooldown -= 1
            
        # Get keyboard input (only if not invincible)
        if not self.invincible:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and self.rect.left > 0:
                self.rect.x -= self.speed
            if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
                self.rect.x += self.speed
        else:
            # Limited movement during invincibility (50% speed)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] and self.rect.left > 0:
                self.rect.x -= self.speed // 2
            if keys[pygame.K_RIGHT] and self.rect.right < SCREEN_WIDTH:
                self.rect.x += self.speed // 2
            
    def shoot(self):
        # Cannot shoot while invincible (but can shoot with S3 power)
        if self.invincible and not self.s3_power:
            return []
            
        if self.cooldown == 0:
            self.cooldown = self.cooldown_time
            
            # Load Balancer: Shotgun spread
            if self.load_balancer_power:
                lasers = []
                # Create 5 lasers in a spread pattern
                for i in range(5):
                    angle_offset = (i - 2) * 15  # -30, -15, 0, 15, 30 degrees
                    laser_x = self.rect.centerx + (i - 2) * 10  # Spread horizontally too
                    laser = Laser(laser_x, self.rect.top, -10)
                    # Add slight horizontal movement for spread effect
                    laser.speed_x = (i - 2) * 2  # -4, -2, 0, 2, 4 horizontal speed
                    lasers.append(laser)
                return lasers
            else:
                # Normal single laser
                return [Laser(self.rect.centerx, self.rect.top, -10)]
        return []
        
    def take_hit(self):
        """Handle player being hit - activate invincibility"""
        # S3 power provides immunity to hits
        if self.s3_power:
            return False
            
        if not self.invincible:  # Only take damage if not already invincible
            self.invincible = True
            self.invincible_timer = self.invincible_duration
            self.glitch_timer = 0
            self.use_shadow = False
            return True  # Hit was processed
        return False  # Hit was ignored due to invincibility
    
    def activate_power_up(self, power_type):
        """Activate a power-up"""
        if power_type == 's3':
            self.s3_power = True
            self.s3_timer = self.s3_duration
        elif power_type == 'load_balancer':
            self.load_balancer_power = True
            self.load_balancer_timer = self.load_balancer_duration
        # Auto scaling is handled externally by the game

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, level=1, stationary=False):
        super().__init__()
        
        self.level = level
        self.config = LEVEL_CONFIGS[level]
        self.health = self.config['enemy_health']
        self.max_health = self.health
        self.stationary = stationary  # For boss-spawned stationary enemies
        self.boss_level_mode = False  # Flag for boss level behavior
        
        # Shooting timer system
        self.shoot_timer = 0
        self.shoot_interval = self.config['enemy_shoot_interval']
        # Add some randomness to initial timer so enemies don't all shoot at once
        if self.shoot_interval > 0:
            self.shoot_timer = random.randint(0, self.shoot_interval)
        
        # Load appropriate sprite based on level
        sprite_path = self.config['enemy_sprite']
        if os.path.exists(sprite_path):
            self.image = pygame.image.load(sprite_path)
            self.image = pygame.transform.scale(self.image, ENEMY_SPRITE_SIZE)
        else:
            # Create generated sprite (fallback)
            self.image = pygame.Surface(ENEMY_SPRITE_SIZE)
            color = AWS_ORANGE if level == 1 else (153, 50, 204)  # Purple for DynamoDB
            self.image.fill(color)
            
            # Add service text
            try:
                font = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 20)
            except:
                font = pygame.font.SysFont(None, 24)
            text = font.render(self.config['enemy_type'], False, WHITE)
            text_rect = text.get_rect(center=(ENEMY_SPRITE_SIZE[0]//2, ENEMY_SPRITE_SIZE[1]//2))
            self.image.blit(text, text_rect)
        
        self.original_image = self.image.copy()  # Store original for damage effects
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 1  # 1 for right, -1 for left
        self.speed = self.config['enemy_speed']
    
    def set_boss_level_mode(self, boss_mode=True):
        """Set whether this enemy should use boss level movement (horizontal only)"""
        self.boss_level_mode = boss_mode
        
    def update(self):
        # Only move if not stationary
        if not self.stationary:
            # Horizontal movement only
            self.rect.x += self.speed * self.direction
            
            # Handle edge collision for all enemies (both normal and boss level)
            if self.rect.left <= 0:
                self.rect.left = 0           # Keep within left boundary
                self.direction = 1           # Change direction to right
            elif self.rect.right >= SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH  # Keep within right boundary
                self.direction = -1          # Change direction to left
            
            # Movement behavior depends on boss level mode
            if self.boss_level_mode:
                # BOSS LEVEL: Lock Y position for horizontal-only movement
                if not hasattr(self, 'spawn_y'):
                    self.spawn_y = self.rect.y
                # Force Y position to stay at spawn height
                self.rect.y = self.spawn_y
            # For normal levels, no additional Y movement (horizontal only)
        
        # Update shooting timer
        if self.shoot_interval > 0:
            self.shoot_timer += 1
        
    def shoot(self):
        # Timer-based shooting for EC2
        if self.level == 1 and self.shoot_interval > 0:
            if self.shoot_timer >= self.shoot_interval:
                self.shoot_timer = 0  # Reset timer
                # Add some randomness to next shot interval (±25%)
                variance = int(self.shoot_interval * 0.25)
                self.shoot_timer = -random.randint(-variance, variance)
                
                # Check if this enemy should shoot (50% chance)
                if random.random() < self.config['enemy_shoot_chance']:
                    return Laser(self.rect.centerx, self.rect.bottom, 5)
        return None
        
    def take_damage(self):
        """Handle taking damage and return True if enemy is destroyed"""
        self.health -= 1
        
        # Visual damage effect - make sprite more transparent/red
        if self.health > 0:
            damage_ratio = 1 - (self.health / self.max_health)
            # Create damage effect by tinting red
            self.image = self.original_image.copy()
            red_overlay = pygame.Surface(ENEMY_SPRITE_SIZE)
            red_overlay.fill((255, 0, 0))
            red_overlay.set_alpha(int(100 * damage_ratio))
            self.image.blit(red_overlay, (0, 0))
            
        return self.health <= 0

class DynamoDBEnemy(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, level=2)
        self.charge_timer = 0
        self.charge_time = random.randint(DYNAMODB_CHARGE_TIME_MIN, DYNAMODB_CHARGE_TIME_MAX)
        self.is_charging = False
        
    def update(self):
        super().update()
        
        # Handle charging system
        self.charge_timer += 1
        if self.charge_timer >= self.charge_time:
            self.is_charging = True
            
    def shoot_asteroids(self):
        """Shoot multiple asteroids when fully charged"""
        if self.is_charging:
            self.is_charging = False
            self.charge_timer = 0
            self.charge_time = random.randint(DYNAMODB_CHARGE_TIME_MIN, DYNAMODB_CHARGE_TIME_MAX)
            
            # Shoot 2-4 asteroids
            asteroids = []
            num_asteroids = random.randint(2, 4)
            for i in range(num_asteroids):
                # Spread asteroids across the enemy width
                offset_x = (i - num_asteroids/2) * 20
                asteroid = Asteroid(self.rect.centerx + offset_x, self.rect.bottom)
                asteroids.append(asteroid)
            return asteroids
        return []

class Asteroid(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        
        # Randomly choose an asteroid sprite
        sprite_path = random.choice(ASTEROID_SPRITES)
        if os.path.exists(sprite_path):
            self.image = pygame.image.load(sprite_path)
            self.image = pygame.transform.scale(self.image, (32, 32))  # Smaller than enemies
        else:
            # Fallback asteroid
            self.image = pygame.Surface((32, 32))
            self.image.fill((139, 69, 19))  # Brown color
            
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.speed = ASTEROID_SPEED
        
        # Add some random horizontal drift
        self.drift = random.uniform(-1, 1)
        
    def update(self):
        self.rect.y += self.speed
        self.rect.x += self.drift
        
        # Remove if it goes off screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, power_type):
        super().__init__()
        self.power_type = power_type
        
        # Load power-up sprites
        power_up_images = {
            's3': 'assets/images/power_ups/s3.png',
            'load_balancer': 'assets/images/power_ups/load_balancer.png',
            'auto_scaling': 'assets/images/power_ups/auto_scaling.png'
        }
        
        try:
            self.image = pygame.image.load(power_up_images[power_type])
            self.image = pygame.transform.scale(self.image, (48, 48))  # Smaller than enemies
        except:
            # Fallback power-up
            self.image = pygame.Surface((48, 48))
            colors = {'s3': (0, 255, 0), 'load_balancer': (0, 0, 255), 'auto_scaling': (255, 255, 0)}
            self.image.fill(colors.get(power_type, (255, 255, 255)))
            
            # Add text label
            try:
                font = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 8)
            except:
                font = pygame.font.SysFont(None, 16)
            text = font.render(power_type.upper()[:2], False, BLACK)
            text_rect = text.get_rect(center=(24, 24))
            self.image.blit(text, text_rect)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed_y = 2  # Slow fall speed
        
    def update(self):
        self.rect.y += self.speed_y
        
        # Remove if off screen
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

class SideShip(pygame.sprite.Sprite):
    """Auto Scaling duplicate ships"""
    def __init__(self, x, y, side='left'):
        super().__init__()
        self.side = side
        
        # Load ship sprite (same as player)
        try:
            self.image = pygame.image.load("assets/images/ship/starship_cirrus.png")
            self.image = pygame.transform.scale(self.image, PLAYER_SPRITE_SIZE)
        except:
            # Fallback
            self.image = pygame.Surface(PLAYER_SPRITE_SIZE)
            self.image.fill(AWS_ORANGE)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = PLAYER_SPEED
        
        # Shooting cooldown (synchronized with player)
        self.cooldown = 0
        self.cooldown_time = PLAYER_COOLDOWN  # Same as player
        
    def update(self, player_rect=None):
        # Update cooldown
        if self.cooldown > 0:
            self.cooldown -= 1
            
        # Follow player's vertical position but maintain horizontal offset
        if player_rect:
            self.rect.y = player_rect.y
            
            # Maintain position relative to player
            if self.side == 'left':
                self.rect.x = player_rect.x - 80  # 80 pixels to the left
            else:  # right
                self.rect.x = player_rect.x + 80  # 80 pixels to the right
                
            # Keep within screen bounds
            if self.rect.left < 0:
                self.rect.left = 0
            elif self.rect.right > SCREEN_WIDTH:
                self.rect.right = SCREEN_WIDTH
    
    def shoot(self):
        """Side ships can also shoot (with cooldown matching player)"""
        if self.cooldown == 0:
            self.cooldown = self.cooldown_time
            return Laser(self.rect.centerx, self.rect.top, -10)
        return None

class Laser(pygame.sprite.Sprite):
    def __init__(self, x, y, speed):
        super().__init__()
        self.image = pygame.Surface([4, 15])
        
        # Player lasers are blue, enemy lasers are red
        if speed < 0:  # Player laser (moving up)
            self.image.fill(BLUE)
        else:  # Enemy laser (moving down)
            self.image.fill(RED)
            
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.y = y
        self.speed = speed
        self.speed_x = 0  # For Load Balancer spread effect
        
    def update(self):
        self.rect.y += self.speed
        self.rect.x += self.speed_x  # Add horizontal movement
        # Remove if it goes off screen
        if self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

class LaserBeam(pygame.sprite.Sprite):
    """Lambda's charged laser beam that lasts for 1 second and follows Lambda movement"""
    def __init__(self, lambda_enemy):
        super().__init__()
        # Create a thin vertical laser beam
        self.image = pygame.Surface((4, SCREEN_HEIGHT))
        self.image.fill(YELLOW)  # Bright yellow laser beam
        
        self.rect = self.image.get_rect()
        self.lambda_enemy = lambda_enemy  # Reference to the Lambda that created this beam
        self.rect.centerx = lambda_enemy.rect.centerx
        self.rect.top = lambda_enemy.rect.bottom
        
        # Laser beam duration (1 second at 60fps)
        self.duration = 60
        self.timer = 0
        
    def update(self):
        self.timer += 1
        
        # Follow the Lambda's horizontal movement
        if self.lambda_enemy and hasattr(self.lambda_enemy, 'rect'):
            self.rect.centerx = self.lambda_enemy.rect.centerx
        
        # Flash effect - alternate between yellow and white
        if self.timer % 6 < 3:  # Flash every 6 frames
            self.image.fill(YELLOW)
        else:
            self.image.fill(WHITE)
        
        # Remove after duration
        if self.timer >= self.duration:
            self.kill()

class BossLaser(pygame.sprite.Sprite):
    """Boss's massive laser beam that follows the boss"""
    def __init__(self, boss):
        super().__init__()
        # Create a thick vertical laser beam
        self.image = pygame.Surface((12, SCREEN_HEIGHT))
        self.image.fill(RED)  # Red boss laser
        
        self.rect = self.image.get_rect()
        self.boss = boss  # Reference to the boss
        self.rect.centerx = boss.rect.centerx
        self.rect.top = boss.rect.bottom
        
        # Laser beam duration (5 seconds at 60fps)
        self.duration = BOSS_LASER_DURATION
        self.timer = 0
        
    def update(self):
        self.timer += 1
        
        # Follow the boss's horizontal movement
        if self.boss and hasattr(self.boss, 'rect'):
            self.rect.centerx = self.boss.rect.centerx
        
        # Flash effect - alternate between red and orange
        if self.timer % 8 < 4:  # Flash every 8 frames
            self.image.fill(RED)
        else:
            self.image.fill((255, 100, 0))  # Orange
        
        # Remove after duration
        if self.timer >= self.duration:
            self.kill()

class CloudFormationBoss(pygame.sprite.Sprite):
    """CloudFormation boss enemy with multiple abilities and explosion sequence"""
    def __init__(self, x, y):
        super().__init__()
        
        # Load boss sprites for different abilities
        self.sprites = {}
        # Map expected names to actual file names in the codebase
        sprite_mapping = {
            'cloudformation': 'cloudformation.png',
            'cloudformation_laser': 'cloudformation_laser_powered.png',  # Actual file name
            'cloudformation_ec2_spawn': 'cloudformation_ec2_spawn.png',
            'cloudformation_dynamodb_spawn': 'cloudformation_dynamodb_spawn.png',
            'cloudformation_lambda_spawn': 'cloudformation_lambda_spawn.png'
        }
        
        for sprite_key, sprite_filename in sprite_mapping.items():
            try:
                sprite = pygame.image.load(f"assets/images/enemies/boss/{sprite_filename}")
                self.sprites[sprite_key] = pygame.transform.scale(sprite, BOSS_SIZE)
            except:
                # Fallback sprites
                fallback = pygame.Surface(BOSS_SIZE)
                fallback.fill((100, 100, 100))  # Gray cloud
                
                try:
                    font = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 12)
                except:
                    font = pygame.font.SysFont(None, 16)
                
                # Different text for different abilities
                if 'laser' in sprite_key:
                    text = font.render("CF-L", False, RED)
                elif 'ec2' in sprite_key:
                    text = font.render("CF-E", False, BLUE)
                elif 'dynamodb' in sprite_key:
                    text = font.render("CF-D", False, PURPLE)
                elif 'lambda' in sprite_key:
                    text = font.render("CF-λ", False, YELLOW)
                else:
                    text = font.render("CF", False, WHITE)
                
                text_rect = text.get_rect(center=(BOSS_SIZE[0]//2, BOSS_SIZE[1]//2))
                fallback.blit(text, text_rect)
                self.sprites[sprite_key] = fallback
        
        # Load explosion sprites from the explosion directory
        self.explosion_sprites = []
        for i in range(1, 10):  # 1.png to 9.png
            try:
                explosion = pygame.image.load(f"assets/images/explosion/{i}.png")
                explosion = pygame.transform.scale(explosion, BOSS_SIZE)
                self.explosion_sprites.append(explosion)
            except:
                # Fallback explosion frame
                explosion = pygame.Surface(BOSS_SIZE)
                colors = [(255, 255, 0), (255, 200, 0), (255, 100, 0), (255, 50, 0), (255, 0, 0)]
                color = colors[min(i-1, len(colors)-1)]
                explosion.fill(color)
                self.explosion_sprites.append(explosion)
        
        # Set initial sprite
        self.current_sprite = 'cloudformation'
        self.image = self.sprites[self.current_sprite].copy()
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.max_health = BOSS_MAX_HEALTH
        self.health = self.max_health
        
        # Movement pattern (very slow horizontal)
        self.speed_x = LEVEL_CONFIGS[4]['enemy_speed']  # Very slow
        self.boss_direction = 1  # 1 for right, -1 for left (boss-specific direction)
        
        # Boss abilities
        self.ability_timer = 0
        self.ability_interval = LEVEL_CONFIGS[4]['enemy_shoot_interval']
        self.ability_chance = LEVEL_CONFIGS[4]['enemy_shoot_chance']
        self.ability_active = False
        self.ability_duration = 60  # 1 second to show ability sprite
        self.ability_timer_active = 0
        
        # Ability warning system (1 second before execution)
        self.ability_warning = False
        self.ability_warning_timer = 0
        self.next_ability = None
        
        # Laser ability system (3 second duration)
        self.laser_active = False
        self.laser_timer = 0
        
        # Fade in effect
        self.alpha = 0
        self.fading_in = True
        self.fade_timer = 0
        
        # Boss state
        self.intro_complete = False
        self.exploding = False
        self.explosion_frame = 0
        self.explosion_timer = 0
        self.explosion_positions = []  # Store multiple explosion positions and timers
        
    def update(self):
        # Handle fade in effect
        if self.fading_in:
            self.fade_timer += 1
            self.alpha = min(255, (self.fade_timer / BOSS_FADE_IN_DURATION) * 255)
            
            # Apply alpha to current sprite
            temp_image = self.sprites[self.current_sprite].copy()
            temp_image.set_alpha(int(self.alpha))
            self.image = temp_image
            
            if self.fade_timer >= BOSS_FADE_IN_DURATION:
                self.fading_in = False
                self.intro_complete = True
                self.alpha = 255
                self.image = self.sprites[self.current_sprite].copy()
            return None  # Don't do any other updates during fade-in
        
        # Handle explosion sequence
        if self.exploding:
            self.explosion_timer += 1
            
            # Create new random explosions periodically
            if self.explosion_timer % 15 == 0:  # Every 15 frames (0.25 seconds)
                # Create random explosion position around boss
                boss_center_x = self.rect.centerx
                boss_center_y = self.rect.centery
                
                # Random position within 150 pixels of boss center
                offset_x = random.randint(-150, 150)
                offset_y = random.randint(-150, 150)
                
                explosion_x = boss_center_x + offset_x
                explosion_y = boss_center_y + offset_y
                
                # Add new explosion with position and start timer
                self.explosion_positions.append({
                    'x': explosion_x,
                    'y': explosion_y,
                    'timer': 0
                })
            
            # Update all explosion timers and remove finished ones
            self.explosion_positions = [exp for exp in self.explosion_positions if exp['timer'] < len(self.explosion_sprites) * 7]
            
            # Update timers for all explosions
            for explosion in self.explosion_positions:
                explosion['timer'] += 1
            
            return None  # Don't do anything else while exploding
        
        # Only start normal boss behavior after intro is complete
        if not self.intro_complete:
            return None  # Don't move or use abilities until intro is done
        
        # Protect boss direction from external interference
        if hasattr(self, 'direction'):
            # If something set the generic 'direction' attribute, ignore it
            # Boss uses boss_direction exclusively
            pass
        
        # Handle ability sprite display (after ability execution)
        if self.ability_active:
            self.ability_timer_active += 1
            if self.ability_timer_active >= self.ability_duration:
                self.ability_active = False
                self.ability_timer_active = 0
                self.current_sprite = 'cloudformation'
                self.image = self.sprites[self.current_sprite].copy()
        
        # Handle laser ability duration (3 seconds)
        if self.laser_active:
            self.laser_timer += 1
            if self.laser_timer >= BOSS_LASER_DURATION:  # 3 seconds
                self.laser_active = False
                self.laser_timer = 0
                self.current_sprite = 'cloudformation'
                self.image = self.sprites[self.current_sprite].copy()
                print("Boss laser ability ended")
        
        # Move horizontally very slowly (HORIZONTAL ONLY - NO VERTICAL MOVEMENT)
        # Apply movement (only affects X coordinate, Y stays constant)
        movement = self.speed_x * self.boss_direction
        self.rect.x += movement
        
        # ABSOLUTE Y POSITION LOCK - prevent any vertical drift
        if not hasattr(self, 'spawn_y'):
            self.spawn_y = 100  # Store original spawn Y position
        self.rect.y = self.spawn_y  # Force Y position to stay at spawn height
        
        # Debug: Print movement info occasionally
        if hasattr(self, 'debug_counter'):
            self.debug_counter += 1
        else:
            self.debug_counter = 0
            
        if self.debug_counter % 120 == 0:  # Every 2 seconds
            print(f"Boss moving: speed={self.speed_x}, direction={self.boss_direction}, position=({self.rect.x}, {self.rect.y})")
        
        # Check screen edges and reverse direction (stay at same Y position)
        # Use more generous margins and ensure proper boundary detection
        if self.boss_direction == 1:  # Moving right
            if self.rect.right >= SCREEN_WIDTH - 5:  # 5 pixel margin from right edge
                self.boss_direction = -1  # Change to move left
                self.rect.right = SCREEN_WIDTH - 5  # Keep within bounds
                print(f"Boss hit right edge, reversing to left. Position: {self.rect.x}, Direction: {self.boss_direction}")
        else:  # Moving left (boss_direction == -1)
            if self.rect.left <= 5:  # 5 pixel margin from left edge
                self.boss_direction = 1   # Change to move right
                self.rect.left = 5  # Keep within bounds
                print(f"Boss hit left edge, reversing to right. Position: {self.rect.x}, Direction: {self.boss_direction}")
        
        # Boss abilities (only after intro is complete and not during laser)
        if not self.ability_active and not self.ability_warning and not self.laser_active:
            self.ability_timer += 1
            if self.ability_timer >= self.ability_interval:
                # Always execute ability (100% chance)
                # Start warning phase (1 second before ability)
                self.next_ability = self.choose_ability()
                self.ability_warning = True
                self.ability_warning_timer = 0
                
                # Show warning sprite based on next ability
                if self.next_ability == 'laser':
                    self.current_sprite = 'cloudformation_laser'
                elif self.next_ability == 'spawn_ec2':
                    self.current_sprite = 'cloudformation_ec2_spawn'
                elif self.next_ability == 'spawn_dynamodb':
                    self.current_sprite = 'cloudformation_dynamodb_spawn'
                elif self.next_ability == 'spawn_lambda':
                    self.current_sprite = 'cloudformation_lambda_spawn'
                
                self.image = self.sprites[self.current_sprite].copy()
                print(f"Boss warning: {self.next_ability} ability in 1 second!")
                self.ability_timer = 0
        
        # Handle ability warning phase
        if self.ability_warning:
            self.ability_warning_timer += 1
            if self.ability_warning_timer >= 60:  # 1 second warning at 60fps
                # Execute the ability (guaranteed)
                self.ability_warning = False
                self.ability_warning_timer = 0
                ability = self.next_ability
                self.next_ability = None
                
                # Special handling for laser ability
                if ability == 'laser':
                    self.laser_active = True
                    self.laser_timer = 0
                    print("Boss executing laser ability (3 seconds)")
                else:
                    print(f"Boss executing ability: {ability}")
                
                return ability
        
        return None
    
    def choose_ability(self):
        """Randomly choose one of 4 abilities and change sprite"""
        abilities = [
            ('laser', 'cloudformation_laser'),
            ('spawn_ec2', 'cloudformation_ec2_spawn'),
            ('spawn_dynamodb', 'cloudformation_dynamodb_spawn'),
            ('spawn_lambda', 'cloudformation_lambda_spawn')
        ]
        
        chosen_ability, sprite_name = random.choice(abilities)
        
        # Change sprite to show ability
        self.current_sprite = sprite_name
        self.image = self.sprites[sprite_name].copy()
        self.ability_active = True
        self.ability_timer_active = 0
        
        if chosen_ability == 'laser':
            return self.shoot_massive_laser()
        elif chosen_ability == 'spawn_ec2':
            return self.spawn_ec2()
        elif chosen_ability == 'spawn_dynamodb':
            return self.spawn_dynamodb()
        elif chosen_ability == 'spawn_lambda':
            return self.spawn_lambda()
        
        return None
    
    def shoot_massive_laser(self):
        """Create a massive laser beam"""
        return BossLaser(self)
    
    def spawn_ec2(self):
        """Spawn an EC2 instance below the boss in a limited area"""
        # Spawn in area below boss (limited horizontal range)
        boss_center_x = self.rect.centerx
        spawn_area_width = 300  # 300 pixels wide spawn area
        min_x = max(50, boss_center_x - spawn_area_width // 2)
        max_x = min(SCREEN_WIDTH - 100, boss_center_x + spawn_area_width // 2)
        
        x = random.randint(min_x, max_x)
        y = self.rect.bottom + 80  # 80 pixels below boss
        
        ec2_enemy = Enemy(x, y, level=1, stationary=False)
        # Set horizontal movement only
        ec2_enemy.direction = random.choice([-1, 1])  # Random initial direction
        return ec2_enemy
    
    def spawn_dynamodb(self):
        """Spawn a DynamoDB table below the boss in a limited area"""
        # Spawn in area below boss (limited horizontal range)
        boss_center_x = self.rect.centerx
        spawn_area_width = 300  # 300 pixels wide spawn area
        min_x = max(50, boss_center_x - spawn_area_width // 2)
        max_x = min(SCREEN_WIDTH - 100, boss_center_x + spawn_area_width // 2)
        
        x = random.randint(min_x, max_x)
        y = self.rect.bottom + 80  # 80 pixels below boss
        
        dynamodb_enemy = DynamoDBEnemy(x, y)
        # Set horizontal movement only
        dynamodb_enemy.direction = random.choice([-1, 1])  # Random initial direction
        return dynamodb_enemy
    
    def spawn_lambda(self):
        """Spawn a Lambda that moves horizontally below the boss in a limited area"""
        # Spawn in area below boss (limited horizontal range)
        boss_center_x = self.rect.centerx
        spawn_area_width = 300  # 300 pixels wide spawn area
        min_x = max(100, boss_center_x - spawn_area_width // 2)
        max_x = min(SCREEN_WIDTH - 200, boss_center_x + spawn_area_width // 2)
        
        x = random.randint(min_x, max_x)
        y = self.rect.bottom + 80  # 80 pixels below boss
        
        lambda_enemy = LambdaEnemy(x, y)
        # Lambda enemies use group movement, so they'll move together horizontally
        return lambda_enemy
    
    def draw_explosions(self, screen):
        """Draw all explosion effects around the boss"""
        if self.exploding:
            for explosion in self.explosion_positions:
                # Calculate current frame for this explosion
                frame_duration = 7
                current_frame = min(explosion['timer'] // frame_duration, len(self.explosion_sprites) - 1)
                
                if current_frame < len(self.explosion_sprites):
                    explosion_sprite = self.explosion_sprites[current_frame]
                    explosion_rect = explosion_sprite.get_rect()
                    explosion_rect.centerx = explosion['x']
                    explosion_rect.centery = explosion['y']
                    screen.blit(explosion_sprite, explosion_rect)
    
    def start_explosion(self):
        """Start the boss explosion sequence"""
        self.exploding = True
        self.explosion_timer = 0
        self.explosion_frame = 0
        self.explosion_positions = []  # Reset explosion positions
    
    def take_damage(self):
        """Handle taking damage - no visual damage states"""
        self.health -= 1
        return self.health <= 0  # Return True if boss is destroyed

class LambdaEnemy(pygame.sprite.Sprite):
    """Lambda enemy that shoots charged laser beams"""
    # Class variables for coordinated movement
    group_direction = 1  # Shared direction for all Lambda instances
    edge_hit = False     # Flag to coordinate direction changes
    
    def __init__(self, x, y):
        super().__init__()
        
        # Load Lambda sprites
        try:
            self.original_image = pygame.image.load("assets/images/enemies/lambda.png")
            self.original_image = pygame.transform.scale(self.original_image, ENEMY_SPRITE_SIZE)
            self.powered_image = pygame.image.load("assets/images/enemies/lambda_powered.png")
            self.powered_image = pygame.transform.scale(self.powered_image, ENEMY_SPRITE_SIZE)
            self.image = self.original_image.copy()
        except:
            # Fallback Lambda enemy
            self.original_image = pygame.Surface(ENEMY_SPRITE_SIZE)
            self.original_image.fill(ORANGE)
            
            # Add Lambda symbol (λ)
            try:
                font = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 16)
            except:
                font = pygame.font.SysFont(None, 24)
            text = font.render("λ", False, BLACK)
            text_rect = text.get_rect(center=(ENEMY_SPRITE_SIZE[0]//2, ENEMY_SPRITE_SIZE[1]//2))
            self.original_image.blit(text, text_rect)
            
            # Powered version (brighter)
            self.powered_image = pygame.Surface(ENEMY_SPRITE_SIZE)
            self.powered_image.fill(YELLOW)
            self.powered_image.blit(text, text_rect)
            
            self.image = self.original_image.copy()
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.max_health = 3  # Lambda takes 3 hits to destroy
        self.health = self.max_health
        self.boss_level_mode = False  # Flag for boss level behavior
        
        # Movement pattern (horizontal only)
        self.speed_x = LEVEL_CONFIGS[3]['enemy_speed']  # Horizontal speed
        
        # Shooting mechanics
        self.shoot_timer = 0
        self.shoot_interval = LEVEL_CONFIGS[3]['enemy_shoot_interval']
        self.shoot_chance = LEVEL_CONFIGS[3]['enemy_shoot_chance']
        
        # Charging mechanics
        self.charging = False
        self.charge_timer = 0
        self.charge_duration = 78  # 1.3 seconds charge time (78 frames at 60fps)
    
    def set_boss_level_mode(self, boss_mode=True):
        """Set whether this enemy should use boss level movement (horizontal only)"""
        self.boss_level_mode = boss_mode
        
    def update(self):
        # Move horizontally using the shared group direction
        movement = self.speed_x * LambdaEnemy.group_direction
        self.rect.x += movement
        
        # Movement behavior depends on boss level mode
        if self.boss_level_mode:
            # BOSS LEVEL: Lock Y position for horizontal-only movement
            if not hasattr(self, 'spawn_y'):
                self.spawn_y = self.rect.y
            self.rect.y = self.spawn_y  # Force Y position to stay at spawn height
        # For normal levels, Lambda enemies don't move down individually
        # Their downward movement is handled by the group system
        
        # Check if this Lambda hits screen edges
        hit_edge = False
        if LambdaEnemy.group_direction == 1:  # Moving right
            if self.rect.right >= SCREEN_WIDTH - 5:  # 5 pixel margin
                hit_edge = True
                self.rect.right = SCREEN_WIDTH - 5  # Keep within bounds
        else:  # Moving left (direction == -1)
            if self.rect.left <= 5:  # 5 pixel margin
                hit_edge = True
                self.rect.left = 5  # Keep within bounds
        
        # If this Lambda hit an edge, signal for group direction change
        if hit_edge:
            LambdaEnemy.edge_hit = True
        
        # Handle charging and shooting
        if self.charging:
            # Use powered sprite when charging
            self.image = self.powered_image.copy()
            
            self.charge_timer += 1
            
            if self.charge_timer >= self.charge_duration:
                self.charging = False
                self.charge_timer = 0
                # Revert to original sprite after shooting
                self.update_sprite_based_on_health()
                return self.shoot_laser_beam()
        else:
            # Use original sprite when not charging
            self.update_sprite_based_on_health()
            
            # Normal shooting timer
            self.shoot_timer += 1
            if self.shoot_timer >= self.shoot_interval:
                if random.random() < self.shoot_chance:
                    self.charging = True
                    self.charge_timer = 0
                self.shoot_timer = 0
        
        return None
    
    @classmethod
    def update_group_movement(cls):
        """Call this method once per frame to handle group direction changes"""
        if cls.edge_hit:
            cls.group_direction *= -1  # Reverse direction for all Lambda instances
            cls.edge_hit = False       # Reset the flag
    
    def update_sprite_based_on_health(self):
        """Update sprite appearance based on health (similar to DynamoDB)"""
        if self.health <= 0:
            return
            
        # Start with original image
        self.image = self.original_image.copy()
        
        # Calculate damage percentage
        damage_percent = 1.0 - (self.health / self.max_health)
        
        if damage_percent > 0:
            # Create damage overlay (gets redder as health decreases)
            damage_overlay = pygame.Surface(ENEMY_SPRITE_SIZE)
            
            if damage_percent <= 0.2:  # 80-100% health - slight yellow tint
                damage_overlay.fill((255, 255, 0))
                alpha = int(30 * (damage_percent / 0.2))
            elif damage_percent <= 0.4:  # 60-80% health - orange tint
                damage_overlay.fill((255, 165, 0))
                alpha = int(50 * ((damage_percent - 0.2) / 0.2))
            elif damage_percent <= 0.6:  # 40-60% health - light red
                damage_overlay.fill((255, 100, 100))
                alpha = int(70 * ((damage_percent - 0.4) / 0.2))
            elif damage_percent <= 0.8:  # 20-40% health - red
                damage_overlay.fill((255, 50, 50))
                alpha = int(90 * ((damage_percent - 0.6) / 0.2))
            else:  # 0-20% health - dark red
                damage_overlay.fill((200, 0, 0))
                alpha = int(110 * ((damage_percent - 0.8) / 0.2))
            
            damage_overlay.set_alpha(alpha)
            self.image.blit(damage_overlay, (0, 0))
    
    def shoot_laser_beam(self):
        """Create a charged laser beam that follows this Lambda"""
        return LaserBeam(self)
    
    def take_damage(self):
        """Handle taking damage"""
        self.health -= 1
        self.update_sprite_based_on_health()  # Update appearance immediately
        return self.health <= 0  # Return True if enemy is destroyed
