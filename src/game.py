import pygame
import sys
import os
import random
from src.constants import *
from src.sprites import Player, Enemy, DynamoDBEnemy, Laser, Asteroid, PowerUp, SideShip, LambdaEnemy, LaserBeam, CloudFormationBoss, BossLaser
from src.menu import Menu

class Game:
    def __init__(self):
        # Initialize pygame
        pygame.init()
        
        # Initialize audio mixer
        if ENABLE_AUDIO:
            # Conservative audio initialization to prevent overflow
            pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
            # Limit mixer channels to prevent overflow
            pygame.mixer.set_num_channels(8)  # Reduced from 16 to 8
            pygame.mixer.set_reserved(1)      # Reserve 1 channel for music
            self.load_audio()
        
        # Set up the display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cloud Invaders")
        
        # Create menu
        self.menu = Menu(self.screen)
        
        # Game state
        self.clock = pygame.time.Clock()
        self.game_over = False
        self.win = False
        self.game_over_reason = ""  # Track why the game ended
        
        # Load Press Start 2P font for all text
        try:
            self.font_large = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 24)
            self.font_medium = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 18)
            self.font_small = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 14)
            self.font_tiny = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 12)
        except:
            # Fallback to system fonts
            self.font_large = pygame.font.SysFont(None, 36)
            self.font_medium = pygame.font.SysFont(None, 28)
            self.font_small = pygame.font.SysFont(None, 24)
            self.font_tiny = pygame.font.SysFont(None, 20)
            
        self.credit_timer = 0  # Timer for credit burning
        
        # Level system
        self.current_level = 1  # Start at Level 1 normally for menu
        self.level_complete = False
        self.background = None
        
        # Boss level state
        self.boss_intro_active = False
        self.boss_intro_timer = 0
        self.player_can_shoot = True
        self.boss = None
        self.boss_exploding = False
        self.boss_explosion_timer = 0
        
        # Initialize game objects
        self.initialize_game()
    
    def load_audio(self):
        """Load all audio files"""
        self.sounds = {}
        
        # Load sound effects with 100% volume (except player hit at 40%)
        audio_files = {
            'shoot': ('assets/audio/shoot.wav', 1.0),           # 100%
            'enemy_hit': ('assets/audio/enemy_hit.wav', 1.0),   # 100%
            'player_hit': ('assets/audio/player_hit.wav', 0.4), # 40%
            'game_over': ('assets/audio/game_over.wav', 1.0),   # 100%
            'victory': ('assets/audio/victory.wav', 1.0),       # 100% - Changed to .wav
            'power_up': ('assets/audio/power_up.wav', 0.8),     # 80%
            'next_level': ('assets/audio/next_level.wav', 0.9), # 90%
            'laser': ('assets/audio/laser.mp3', 0.7),           # 70%
            'heartbeat': ('assets/audio/heartbeat.wav', 1.0),   # 100% - Audio directory
            'boss_battle': ('assets/audio/boss_battle.wav', 0.6), # 60% - Changed to .wav
            'boss_explode': ('assets/audio/boss_explode.wav', 1.0) # 100%
        }
        
        for sound_name, (file_path, volume) in audio_files.items():
            if os.path.exists(file_path):
                try:
                    sound = pygame.mixer.Sound(file_path)
                    sound.set_volume(volume)  # Set individual volume
                    self.sounds[sound_name] = sound
                    print(f"Loaded audio: {sound_name} at {int(volume*100)}% volume")
                except pygame.error as e:
                    print(f"Could not load {file_path}: {e}")
                    self.sounds[sound_name] = None
            else:
                print(f"Audio file not found: {file_path}")
                self.sounds[sound_name] = None
    
    def play_sound(self, sound_name):
        """Play sound with rate limiting to prevent overlap and audio bugs"""
        if not ENABLE_AUDIO or sound_name not in self.sounds or not self.sounds[sound_name]:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Initialize sound timing tracker
        if not hasattr(self, 'last_sound_time'):
            self.last_sound_time = {}
        
        # Rate limiting per sound type (prevents audio overlap)
        rate_limits = {
            'shoot': 100,      # Max once per 100ms (10 shots/sec max)
            'player_hit': 200, # Max once per 200ms
            'enemy_hit': 80,   # Max once per 80ms
            'laser': 150,      # Max once per 150ms
            'power_up': 300,   # Max once per 300ms
            'game_over': 500,  # Max once per 500ms
            'victory': 500,    # Max once per 500ms
            'next_level': 400, # Max once per 400ms
            'boss_explode': 1000, # Max once per second
        }
        
        min_interval = rate_limits.get(sound_name, 120)  # Default 120ms
        
        # Check if enough time has passed since last play
        if sound_name in self.last_sound_time:
            time_since_last = current_time - self.last_sound_time[sound_name]
            if time_since_last < min_interval:
                return  # Skip this sound play to prevent overlap
        
        # Play sound and record timestamp
        try:
            self.sounds[sound_name].play()
            self.last_sound_time[sound_name] = current_time
        except pygame.error:
            # Handle audio system errors gracefully
            pass
    
    def cleanup_audio(self):
        """Clean up audio resources to prevent memory leaks and audio bugs"""
        try:
            # Clear sound timing tracker
            if hasattr(self, 'last_sound_time'):
                self.last_sound_time.clear()
            
            # Stop background music
            pygame.mixer.music.stop()
            
            # Force stop all mixer channels
            pygame.mixer.stop()
            
            # Small delay to let audio system reset
            pygame.time.wait(100)
            
        except pygame.error:
            # Handle any audio cleanup errors gracefully
            pass
    
    def periodic_audio_cleanup(self):
        """Perform periodic audio cleanup to prevent overflow"""
        if not hasattr(self, 'last_audio_cleanup'):
            self.last_audio_cleanup = 0
        
        current_time = pygame.time.get_ticks()
        
        # Clean up every 30 seconds
        if current_time - self.last_audio_cleanup > 30000:
            try:
                # Clean up old sound timing entries (older than 5 seconds)
                if hasattr(self, 'last_sound_time'):
                    old_entries = []
                    for sound_name, timestamp in self.last_sound_time.items():
                        if current_time - timestamp > 5000:  # 5 seconds old
                            old_entries.append(sound_name)
                    
                    for sound_name in old_entries:
                        del self.last_sound_time[sound_name]
                
                # Limit total active channels
                active_channels = pygame.mixer.get_busy()
                if active_channels > 6:  # If more than 6 channels active
                    # Stop some channels to prevent overflow
                    for i in range(min(3, active_channels - 3)):
                        pygame.mixer.Channel(i).stop()
                
                self.last_audio_cleanup = current_time
                
            except pygame.error:
                pass
    
    def initialize_game(self):
        """Initialize or reset all game objects"""
        # Reset level to 1 when starting a new game
        if self.game_over or self.win:
            self.current_level = 1
            print(f"Game reset. Starting at level {self.current_level}")  # Debug
        
        # Create sprite groups
        self.player = Player()
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.player_lasers = pygame.sprite.Group()
        self.enemy_lasers = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()  # For DynamoDB asteroids
        self.power_ups = pygame.sprite.Group()  # For power-ups
        self.side_ships = pygame.sprite.Group()  # For Auto Scaling duplicates
        self.laser_beams = pygame.sprite.Group()  # For Lambda laser beams
        self.boss_lasers = pygame.sprite.Group()  # For boss laser beams
        
        self.all_sprites.add(self.player)
        
        # Reset boss-related variables
        self.boss = None
        self.boss_intro_active = False
        self.boss_intro_timer = 0
        self.boss_exploding = False
        self.boss_explosion_timer = 0
        self.player_can_shoot = True
        
        # Load level background
        self.load_level_background()
        
        # Create initial enemies or start boss intro
        if self.current_level == 4:
            self.start_boss_intro()
        else:
            self.create_enemies()
        
        # Reset game state
        self.game_over = False
        self.win = False
        self.level_complete = False
        self.credit_timer = 0
        self.game_over_reason = ""
        
    def load_level_background(self):
        """Load the background image for the current level"""
        if self.current_level in LEVEL_CONFIGS:
            bg_path = LEVEL_CONFIGS[self.current_level]['background']
            try:
                self.background = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except:
                # Fallback to solid color background
                self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                if self.current_level == 1:
                    self.background.fill((20, 20, 40))  # Dark blue for EC2
                elif self.current_level == 2:
                    self.background.fill((40, 20, 40))  # Dark purple for DynamoDB
                elif self.current_level == 3:
                    self.background.fill((40, 40, 20))  # Dark yellow for Lambda
                elif self.current_level == 4:
                    self.background.fill((20, 20, 20))  # Dark gray for boss
                else:
                    self.background.fill(BLACK)
        else:
            self.background = None

    def start_boss_intro(self):
        """Start the boss introduction sequence"""
        print("Starting boss intro...")  # Debug
        self.boss_intro_active = True
        self.boss_intro_timer = 0
        self.player_can_shoot = False
        self.boss_exploding = False  # Ensure boss isn't exploding
        
        # Stop current music and play heartbeat (looped)
        pygame.mixer.music.stop()
        if ENABLE_AUDIO:
            try:
                pygame.mixer.music.load('assets/audio/heartbeat.wav')
                pygame.mixer.music.set_volume(1.0)  # 100% volume
                pygame.mixer.music.play(-1)  # Loop indefinitely
            except:
                pass  # Continue without music if file not found
        
        # Create boss (initially invisible) - positioned lower
        x = SCREEN_WIDTH // 2 - BOSS_SIZE[0] // 2
        y = 100  # Moved down from 50 to 100 for better positioning
        self.boss = CloudFormationBoss(x, y)
        self.enemies.add(self.boss)
        self.all_sprites.add(self.boss)
        print(f"Boss created and added to groups. Enemy count: {len(self.enemies)}, Boss intro active: {self.boss_intro_active}")  # Debug
    
    def update_boss_intro(self):
        """Handle boss introduction sequence"""
        self.boss_intro_timer += 1
        
        # After 7 seconds, start boss battle music and enable shooting
        if self.boss_intro_timer >= BOSS_INTRO_DURATION:
            self.boss_intro_active = False
            self.player_can_shoot = True
            
            # Stop heartbeat and start boss battle music (only once)
            if not hasattr(self, 'boss_music_started'):
                pygame.mixer.music.stop()
                if ENABLE_AUDIO:
                    try:
                        pygame.mixer.music.load('assets/audio/boss_battle.wav')
                        pygame.mixer.music.set_volume(0.6)  # 60% volume
                        pygame.mixer.music.play(-1)  # Loop indefinitely
                        self.boss_music_started = True  # Flag to prevent restarting
                        print("Boss battle music started")
                    except:
                        pass  # Continue without music if file not found

    def load_level_background(self):
        """Load the background image for the current level"""
        if self.current_level in LEVEL_CONFIGS:
            bg_path = LEVEL_CONFIGS[self.current_level]['background']
            try:
                self.background = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
            except:
                # Fallback to solid color background
                self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                if self.current_level == 1:
                    self.background.fill((20, 20, 40))  # Dark blue for EC2
                elif self.current_level == 2:
                    self.background.fill((40, 20, 40))  # Dark purple for DynamoDB
                elif self.current_level == 3:
                    self.background.fill((40, 40, 20))  # Dark yellow for Lambda
                elif self.current_level == 4:
                    self.background.fill((20, 20, 20))  # Dark gray for boss
                else:
                    self.background.fill(BLACK)
        else:
            self.background = None
    
    def create_enemies(self):
        """Create enemies based on current level"""
        if self.current_level == 1:
            # Level 1: 4 rows of 6 EC2 instances each (24 total EC2 enemies)
            for row in range(4):
                for col in range(6):
                    x = 100 + col * 140  # Normal spacing for 96x96 sprites
                    y = 80 + row * 120   # Increased gap between rows from 90 to 120
                    enemy = Enemy(x, y, level=1)
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)
                    
        elif self.current_level == 2:
            # Level 2: 3 rows of 4 DynamoDB instances (12 total DynamoDB enemies)
            for row in range(3):
                for col in range(4):
                    x = 150 + col * 160  # Normal spacing for 96x96 sprites
                    y = 80 + row * 130   # Increased gap between rows from 100 to 130
                    enemy = DynamoDBEnemy(x, y)
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)
                    
        elif self.current_level == 3:
            # Level 3: 3 rows of 5 Lambda functions (15 total Lambda enemies)
            # Reset Lambda class variables for new level
            LambdaEnemy.group_direction = 1
            LambdaEnemy.edge_hit = False
            
            for row in range(3):
                for col in range(5):
                    x = 120 + col * 150  # Spacing for Lambda functions
                    y = 80 + row * 120   # Vertical spacing
                    enemy = LambdaEnemy(x, y)
                    self.enemies.add(enemy)
                    self.all_sprites.add(enemy)
                    
        elif self.current_level == 4:
            # Level 4: Boss level - CloudFormation
            # Boss is created during intro sequence
            pass
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.game_over = True
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.cleanup_audio()  # Clean up audio before exit
                    self.game_over = True
                    return False
        
        # Handle continuous shooting (moved outside event loop)
        # Only process shooting if player is allowed to shoot
        if self.player_can_shoot:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                # Player shooting (continuous when space held)
                lasers = self.player.shoot()
                if lasers:  # Now returns a list
                    for laser in lasers:
                        self.player_lasers.add(laser)
                        self.all_sprites.add(laser)
                    self.play_sound('shoot')  # Play shoot sound
                    
                    # Side ships also shoot (synchronized with player)
                    for side_ship in self.side_ships:
                        side_laser = side_ship.shoot()
                        if side_laser:
                            self.player_lasers.add(side_laser)
                            self.all_sprites.add(side_laser)
        
        return True
    
    def update(self):
        # Handle boss intro sequence
        if self.boss_intro_active:
            self.update_boss_intro()
            # Allow player movement during intro
            self.player.update()
            # Update boss for fade-in effect
            if self.boss:
                self.boss.update()
            return  # Don't update other game elements during intro
        
        # Handle boss explosion sequence
        if self.boss_exploding:
            self.boss_explosion_timer += 1
            
            # Allow player movement during explosion
            self.player.update()
            
            # Update boss explosion effects
            if self.boss:
                self.boss.update()
            
            if self.boss_explosion_timer >= BOSS_EXPLOSION_DURATION:
                # Boss explosion finished, show victory
                self.win = True
                self.game_over = True
                self.game_over_reason = "CloudFormation Boss Defeated!"
                # Stop explosion sound
                pygame.mixer.music.stop()
            return  # Don't update other game elements during explosion
        
        # Update all sprites (except boss - boss updates in enemy loop)
        for sprite in self.all_sprites:
            if not isinstance(sprite, CloudFormationBoss):
                sprite.update()
        
        # Update Lambda group movement (needed for proper Lambda movement)
        from src.sprites import LambdaEnemy
        LambdaEnemy.update_group_movement()
        self.power_ups.update()
        self.laser_beams.update()
        self.boss_lasers.update()
        
        # Periodic audio cleanup to prevent overflow
        self.periodic_audio_cleanup()
        
        # Update side ships to follow player
        for side_ship in self.side_ships:
            side_ship.update(self.player.rect)
        
        # Burn credits based on number of enemies (AWS services running)
        self.credit_timer += 1
        if self.credit_timer >= 60:  # Every second (60 FPS)
            enemy_count = len(self.enemies)
            if self.current_level in LEVEL_CONFIGS:
                credits_to_burn = enemy_count * LEVEL_CONFIGS[self.current_level]['credit_burn_rate']
            else:
                credits_to_burn = enemy_count * CREDIT_BURN_RATE
            self.player.credits -= credits_to_burn
            self.credit_timer = 0
            
            # Check if credits ran out
            if self.player.credits <= 0:
                self.player.credits = 0
                self.game_over = True
                self.win = False
                self.game_over_reason = "You ran out of AWS Credits!"
                return
        
        # Check if enemies need to change direction or move down (not for Lambda)
        if self.current_level != 3:  # Only for EC2 and DynamoDB levels
            move_down = False
            for enemy in self.enemies:
                if enemy.rect.right >= SCREEN_WIDTH or enemy.rect.left <= 0:
                    move_down = True
                    break
        
        # Enemy shooting and special abilities
        for enemy in self.enemies:
            # CloudFormation boss abilities (handle boss update here only)
            if isinstance(enemy, CloudFormationBoss):
                ability_result = enemy.update()  # Boss updates only here
                if ability_result:
                    if isinstance(ability_result, BossLaser):
                        self.boss_lasers.add(ability_result)
                        self.play_sound('laser')
                    elif isinstance(ability_result, (Enemy, DynamoDBEnemy, LambdaEnemy)):
                        # Boss spawned a minion - set boss level mode for horizontal-only movement
                        ability_result.set_boss_level_mode(True)
                        self.enemies.add(ability_result)
                        self.all_sprites.add(ability_result)
            # Lambda enemies have special laser beam shooting
            elif isinstance(enemy, LambdaEnemy):
                laser_beam = enemy.update()
                if laser_beam:
                    self.laser_beams.add(laser_beam)
                    self.play_sound('laser')  # Play laser sound
            else:
                # Regular laser shooting for EC2 and DynamoDB
                laser = enemy.shoot()
                if laser:
                    self.enemy_lasers.add(laser)
                    self.all_sprites.add(laser)
            
            # DynamoDB asteroid shooting
            if isinstance(enemy, DynamoDBEnemy):
                asteroids = enemy.shoot_asteroids()
                for asteroid in asteroids:
                    self.asteroids.add(asteroid)
                    self.all_sprites.add(asteroid)
        
        # Update Lambda group movement coordination (only for Level 3)
        if self.current_level == 3:
            LambdaEnemy.update_group_movement()
        
        # Check for collisions
        # Player lasers hitting enemies
        hits = pygame.sprite.groupcollide(self.enemies, self.player_lasers, False, True)
        for enemy, laser_list in hits.items():
            if enemy.take_damage():  # Enemy destroyed
                # Special handling for boss
                if isinstance(enemy, CloudFormationBoss):
                    # Start boss explosion sequence
                    self.boss_exploding = True
                    self.boss_explosion_timer = 0
                    self.boss.start_explosion()
                    
                    # Loop boss explosion sound for 6 seconds
                    pygame.mixer.music.stop()
                    if ENABLE_AUDIO:
                        try:
                            pygame.mixer.music.load('assets/audio/boss_explode.wav')
                            pygame.mixer.music.set_volume(1.0)  # 100% volume
                            pygame.mixer.music.play(-1)  # Loop indefinitely (will be stopped after 6 seconds)
                        except:
                            pass  # Continue without explosion sound if file not found
                else:
                    # Regular enemy destruction
                    # Power-up drop chance: 5% normal, +20% during boss level (25% total)
                    base_chance = 0.05  # 5% base chance
                    boss_bonus = 0.20 if self.current_level == 4 else 0.0  # +20% during boss level
                    power_up_chance = base_chance + boss_bonus
                    
                    if random.random() < power_up_chance:
                        power_types = ['s3', 'load_balancer', 'auto_scaling']
                        power_type = random.choice(power_types)
                        power_up = PowerUp(enemy.rect.centerx, enemy.rect.centery, power_type)
                        self.power_ups.add(power_up)
                    
                    enemy.kill()
                    self.play_sound('enemy_hit')
        
        # Player collecting power-ups
        power_up_hits = pygame.sprite.spritecollide(self.player, self.power_ups, True)
        for power_up in power_up_hits:
            self.play_sound('power_up')  # Play power-up collection sound
            if power_up.power_type == 'auto_scaling':
                # Create side ships if not already present
                if len(self.side_ships) == 0:
                    left_ship = SideShip(self.player.rect.x - 80, self.player.rect.y, 'left')
                    right_ship = SideShip(self.player.rect.x + 80, self.player.rect.y, 'right')
                    self.side_ships.add(left_ship, right_ship)
                    # Don't add to all_sprites to avoid update() argument issues
            else:
                self.player.activate_power_up(power_up.power_type)
        
        # Side ships taking damage
        for side_ship in self.side_ships:
            # Enemy lasers hitting side ships
            if pygame.sprite.spritecollide(side_ship, self.enemy_lasers, True):
                side_ship.kill()
            # Asteroids hitting side ships
            if pygame.sprite.spritecollide(side_ship, self.asteroids, True):
                side_ship.kill()
        
        # Enemy lasers hitting player - costs credits!
        hits = pygame.sprite.spritecollide(self.player, self.enemy_lasers, True)
        if hits:
            if self.player.take_hit():  # Only process hit if not invincible
                self.player.credits -= HIT_PENALTY
                self.play_sound('player_hit')
                if self.player.credits <= 0:
                    self.player.credits = 0
                    self.game_over = True
                    self.win = False
                    self.game_over_reason = "Enemy attacks drained your AWS Credits!"
                    return
        
        # Asteroids hitting player - costs more credits!
        hits = pygame.sprite.spritecollide(self.player, self.asteroids, True)
        if hits:
            if self.player.take_hit():  # Only process hit if not invincible
                self.player.credits -= HIT_PENALTY * 2  # Asteroids do double damage
                self.play_sound('player_hit')
                if self.player.credits <= 0:
                    self.player.credits = 0
                    self.game_over = True
                    self.win = False
                    self.game_over_reason = "Asteroid impact drained your AWS Credits!"
                    return
        
        # Player lasers hitting asteroids (can destroy them)
        pygame.sprite.groupcollide(self.asteroids, self.player_lasers, True, True)
        
        # Player hit by laser beams (Lambda attacks)
        laser_beam_hits = pygame.sprite.spritecollide(self.player, self.laser_beams, False)
        if laser_beam_hits:
            if self.player.take_hit():  # Only process hit if not invincible
                self.player.credits -= HIT_PENALTY
                self.play_sound('player_hit')
                if self.player.credits <= 0:
                    self.player.credits = 0
                    self.game_over = True
                    self.win = False
                    self.game_over_reason = "Lambda laser beam drained your AWS Credits!"
                    return
        
        # Side ships hit by laser beams (Lambda attacks)
        for side_ship in self.side_ships:
            side_ship_beam_hits = pygame.sprite.spritecollide(side_ship, self.laser_beams, False)
            if side_ship_beam_hits:
                # Side ship destroyed by Lambda laser beam
                side_ship.kill()
                self.play_sound('player_hit')  # Same sound as main player hit
                # No credit penalty for losing side ships (global rule)
        
        # Player hit by boss laser beams
        boss_laser_hits = pygame.sprite.spritecollide(self.player, self.boss_lasers, False)
        if boss_laser_hits:
            if self.player.take_hit():  # Only process hit if not invincible
                self.player.credits -= HIT_PENALTY * 2  # Boss lasers do double damage
                self.play_sound('player_hit')
                if self.player.credits <= 0:
                    self.player.credits = 0
                    self.game_over = True
                    self.win = False
                    self.game_over_reason = "CloudFormation laser obliterated your AWS Credits!"
                    return
        
        # Side ships hit by boss laser beams (Auto Scaling duplicates)
        for side_ship in self.side_ships:
            side_ship_laser_hits = pygame.sprite.spritecollide(side_ship, self.boss_lasers, False)
            if side_ship_laser_hits:
                # Side ship takes damage and is destroyed by boss laser
                side_ship.kill()
                self.play_sound('player_hit')  # Same sound as main player hit
                # No credit penalty for losing side ships (global rule)
        
        # Check win condition - robust boss level handling
        if len(self.enemies) == 0:
            if self.current_level == 4:
                # Level 4 (boss level) - only win if we're not in intro phase
                if not self.boss_intro_active:
                    if hasattr(self, 'boss') and self.boss is not None:
                        # Boss exists but enemies is 0 - this shouldn't happen during normal gameplay
                        print("Boss defeated! Player wins!")  # Debug
                        self.game_over = True
                        self.win = True
                    else:
                        # No boss exists and no enemies - something went wrong, restart boss
                        print("Boss level error - restarting boss intro")  # Debug
                        self.start_boss_intro()
                else:
                    # Boss intro is active, this is normal - don't trigger win
                    print(f"Boss intro active, enemies: {len(self.enemies)}")  # Debug
            elif self.current_level < MAX_LEVELS:
                print(f"Level {self.current_level} complete! Advancing to level {self.current_level + 1}")  # Debug
                self.level_complete = True
            else:
                print("All levels complete! Player wins!")  # Debug
                self.game_over = True
                self.win = True
                
    def next_level(self):
        """Advance to the next level"""
        if self.current_level < MAX_LEVELS:
            self.current_level += 1
            self.level_complete = False
            print(f"Advancing to level {self.current_level}")  # Debug
            
            # Clear all projectiles
            for laser in self.enemy_lasers:
                laser.kill()
            for laser in self.player_lasers:
                laser.kill()
            for asteroid in self.asteroids:
                asteroid.kill()
            for beam in self.laser_beams:
                beam.kill()
            for boss_laser in self.boss_lasers:
                boss_laser.kill()
            
            # Clear all enemies before creating new ones
            for enemy in self.enemies:
                enemy.kill()
            
            # Reset boss state for new level
            self.boss = None
            self.boss_intro_active = False
            self.boss_exploding = False
            
            # Load new level
            self.load_level_background()
            
            # Create enemies or start boss intro based on level
            if self.current_level == 4:
                print("Starting boss level...")  # Debug
                self.start_boss_intro()
            else:
                self.create_enemies()
            
            return True
        return False
    
    def draw_boss_health_bar(self):
        """Draw the boss health bar"""
        if self.boss and self.current_level == 4 and not self.boss_exploding:
            # Health bar position (top center of screen)
            bar_x = (SCREEN_WIDTH - BOSS_HEALTH_BAR_WIDTH) // 2
            bar_y = 10
            
            # Background bar (red)
            background_rect = pygame.Rect(bar_x, bar_y, BOSS_HEALTH_BAR_WIDTH, BOSS_HEALTH_BAR_HEIGHT)
            pygame.draw.rect(self.screen, RED, background_rect)
            
            # Health bar (green to red gradient based on health)
            health_percent = self.boss.health / self.boss.max_health
            health_width = int(BOSS_HEALTH_BAR_WIDTH * health_percent)
            
            if health_width > 0:
                # Color changes from green to yellow to red as health decreases
                if health_percent > 0.6:
                    color = GREEN
                elif health_percent > 0.3:
                    color = YELLOW
                else:
                    color = (255, 100, 0)  # Orange-red
                
                health_rect = pygame.Rect(bar_x, bar_y, health_width, BOSS_HEALTH_BAR_HEIGHT)
                pygame.draw.rect(self.screen, color, health_rect)
            
            # Border
            pygame.draw.rect(self.screen, WHITE, background_rect, 2)
            
            # Boss name only (no health numbers)
            boss_text = self.font_small.render("CloudFormation Boss", False, WHITE)
            text_rect = boss_text.get_rect(center=(SCREEN_WIDTH // 2, bar_y - 15))
            self.screen.blit(boss_text, text_rect)

    def draw(self):
        
        # Draw AWS-themed metrics
        credits_text = self.font_medium.render(f"{LIVES_NAME}: ${self.player.credits:,}", False, AWS_ORANGE)
        level_text = self.font_medium.render(f"Level: {self.current_level}", False, AWS_BLUE)
        
        if self.current_level == 1:
            enemies_text = self.font_small.render(f"EC2 Instances: {len(self.enemies)}", False, WHITE)
        elif self.current_level == 2:
            enemies_text = self.font_small.render(f"DynamoDB Tables: {len(self.enemies)}", False, WHITE)
        else:
            enemies_text = self.font_small.render(f"Services: {len(self.enemies)}", False, WHITE)
            
        if self.current_level in LEVEL_CONFIGS:
            burn_rate = len(self.enemies) * LEVEL_CONFIGS[self.current_level]['credit_burn_rate']
        else:
            burn_rate = len(self.enemies) * CREDIT_BURN_RATE
        burn_text = self.font_small.render(f"Burn Rate: ${burn_rate}/sec", False, RED if burn_rate > 0 else WHITE)
        
        self.screen.blit(credits_text, (20, 20))
        self.screen.blit(level_text, (20, 50))
        self.screen.blit(enemies_text, (20, 80))
        self.screen.blit(burn_text, (20, 110))
        
        # Draw power-up status
        power_up_y = 520
        if self.player.s3_power:
            s3_text = self.font_tiny.render(f"S3 Shield: {self.player.s3_timer//60 + 1}s", False, GREEN)
            self.screen.blit(s3_text, (20, power_up_y))
            power_up_y += 20
            
        if self.player.load_balancer_power:
            lb_text = self.font_tiny.render(f"Load Balancer: {self.player.load_balancer_timer//60 + 1}s", False, BLUE)
            self.screen.blit(lb_text, (20, power_up_y))
            power_up_y += 20
            
        if len(self.side_ships) > 0:
            as_text = self.font_tiny.render(f"Auto Scaling: {len(self.side_ships)} ships", False, YELLOW)
            self.screen.blit(as_text, (20, power_up_y))
        
        pygame.display.flip()
    
    def show_victory_screen(self):
        """Show victory screen with background"""
        # Load victory background
        try:
            victory_bg = pygame.image.load('assets/images/bg/winner_bg.jpg')
            victory_bg = pygame.transform.scale(victory_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.screen.blit(victory_bg, (0, 0))
        except:
            # Try PNG format if JPG fails
            try:
                victory_bg = pygame.image.load('assets/images/bg/winner_bg.png')
                victory_bg = pygame.transform.scale(victory_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.screen.blit(victory_bg, (0, 0))
            except:
                # Fallback to black background
                self.screen.fill(BLACK)
        
        # Create semi-transparent overlay for better text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(120)
        self.screen.blit(overlay, (0, 0))
        
        # Victory title
        if self.current_level >= MAX_LEVELS:
            title_text = self.font_large.render("Congratulations!", False, GREEN)
            subtitle_text = self.font_medium.render("All Levels Complete!", False, WHITE)
        else:
            title_text = self.font_large.render("You Win!", False, GREEN)
            subtitle_text = self.font_medium.render("Victory Achieved!", False, WHITE)
        
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        self.screen.blit(title_text, title_rect)
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Final stats
        final_credits = self.font_small.render(f"Final AWS Credits: ${self.player.credits:,}", False, AWS_ORANGE)
        credits_rect = final_credits.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 10))
        self.screen.blit(final_credits, credits_rect)
        
        level_text = self.font_small.render(f"Reached Level: {self.current_level}", False, AWS_BLUE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(level_text, level_rect)
        
        # Instructions
        instruction_text = self.font_tiny.render("Press ENTER to play again or ESC to quit", False, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100))
        self.screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()

    def show_next_level_screen(self):
        """Show next level screen with background and remaining credits"""
        # Load next level background - try multiple formats
        try:
            next_level_bg = pygame.image.load('assets/images/bg/next_level_bg.png')
            next_level_bg = pygame.transform.scale(next_level_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.screen.blit(next_level_bg, (0, 0))
        except:
            try:
                next_level_bg = pygame.image.load('assets/images/bg/next_level_bg.jpg')
                next_level_bg = pygame.transform.scale(next_level_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.screen.blit(next_level_bg, (0, 0))
            except:
                # Fallback to black background
                self.screen.fill(BLACK)
        
        # Create semi-transparent overlay for better text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(120)  # Lighter overlay than game over screen
        self.screen.blit(overlay, (0, 0))
        
        # Level Complete title
        title_text = self.font_large.render(f"Level {self.current_level} Complete!", False, GREEN)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(title_text, title_rect)
        
        # Remaining credits display
        credits_text = self.font_medium.render(f"Remaining AWS Credits: ${self.player.credits:,}", False, AWS_ORANGE)
        credits_rect = credits_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(credits_text, credits_rect)
        
        # Next level info
        next_level_text = self.font_medium.render(f"Preparing Level {self.current_level + 1}...", False, AWS_BLUE)
        next_level_rect = next_level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(next_level_text, next_level_rect)
        
        # Instructions
        instruction_text = self.font_small.render("Press ENTER to continue", False, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 80))
        self.screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()

    def show_game_over_screen(self):
        """Show game over screen with background and reason"""
        # Load game over background
        try:
            game_over_bg = pygame.image.load('assets/images/bg/game_over_bg.jpg')
            game_over_bg = pygame.transform.scale(game_over_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.screen.blit(game_over_bg, (0, 0))
        except:
            # Fallback to black background
            self.screen.fill(BLACK)
        
        # Create semi-transparent overlay for better text readability
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(150)
        self.screen.blit(overlay, (0, 0))
        
        # Game Over title
        title_text = self.font_large.render("GAME OVER", False, RED)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(title_text, title_rect)
        
        # Game over reason
        reason_text = self.font_medium.render(self.game_over_reason, False, WHITE)
        reason_rect = reason_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40))
        self.screen.blit(reason_text, reason_rect)
        
        # Final stats
        final_credits = self.font_small.render(f"Final Credits: ${self.player.credits:,}", False, AWS_ORANGE)
        credits_rect = final_credits.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        self.screen.blit(final_credits, credits_rect)
        
        level_text = self.font_small.render(f"Reached Level: {self.current_level}", False, AWS_BLUE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        self.screen.blit(level_text, level_rect)
        
        # Instructions
        instruction_text = self.font_tiny.render("Press ENTER to return to menu", False, WHITE)
        instruction_rect = instruction_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 120))
        self.screen.blit(instruction_text, instruction_rect)
        
        pygame.display.flip()

    def show_message(self, title, subtitle):
        self.screen.fill(BLACK)
        title_text = self.font_large.render(title, False, WHITE)
        subtitle_text = self.font_medium.render(subtitle, False, WHITE)
        
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 
                                SCREEN_HEIGHT // 2 - title_text.get_height() // 2))
        self.screen.blit(subtitle_text, (SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2, 
                                   SCREEN_HEIGHT // 2 + 50))
        pygame.display.flip()
    
    def draw(self):
        """Draw all game elements"""
        # Draw background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BLACK)
        
        # Draw all sprites
        self.all_sprites.draw(self.screen)
        self.side_ships.draw(self.screen)  # Draw side ships separately
        self.power_ups.draw(self.screen)  # Draw power-ups on top
        self.laser_beams.draw(self.screen)  # Draw laser beams on top
        self.boss_lasers.draw(self.screen)  # Draw boss lasers on top
        
        # Draw boss explosions if boss is exploding
        if self.boss and self.boss.exploding:
            self.boss.draw_explosions(self.screen)
        
        # Draw boss health bar
        self.draw_boss_health_bar()
        
        # Enhanced UI (no background panel)
        self.draw_enhanced_ui()
        
        # Power-ups UI (left edge)
        self.draw_power_ups_ui()
        
        pygame.display.flip()
    
    def draw_enhanced_ui(self):
        """Draw enhanced UI with detailed information - no background panel"""
        # AWS Credits (top-left)
        credits_text = self.font_medium.render(f"AWS Credits: ${self.player.credits:,}", False, AWS_ORANGE)
        self.screen.blit(credits_text, (20, 15))
        
        # Enemy count with specific names
        enemy_count = len(self.enemies)
        if self.current_level == 1:
            enemies_text = self.font_small.render(f"EC2 Instances: {enemy_count}", False, WHITE)
        elif self.current_level == 2:
            enemies_text = self.font_small.render(f"DynamoDB Tables: {enemy_count}", False, WHITE)
        elif self.current_level == 3:
            enemies_text = self.font_small.render(f"Lambda Functions: {enemy_count}", False, WHITE)
        elif self.current_level == 4:
            if self.boss and not self.boss_exploding:
                enemies_text = self.font_small.render(f"CloudFormation Boss: {enemy_count}", False, WHITE)
            else:
                enemies_text = self.font_small.render(f"Boss Defeated!", False, GREEN)
        else:
            enemies_text = self.font_small.render(f"Services: {enemy_count}", False, WHITE)
        
        self.screen.blit(enemies_text, (20, 45))
        
        # On-demand rate (total burn rate)
        total_burn_rate = enemy_count * CREDIT_BURN_RATE
        if self.current_level == 4 and self.boss:
            total_burn_rate = LEVEL_CONFIGS[4]['credit_burn_rate']  # Boss has special burn rate
        
        burn_rate_text = self.font_small.render(f"On-Demand Rate: ${total_burn_rate}/sec", False, RED)
        self.screen.blit(burn_rate_text, (20, 70))
        
        # Level indicator (top-right)
        level_text = self.font_medium.render(f"Level {self.current_level}", False, AWS_BLUE)
        level_rect = level_text.get_rect()
        self.screen.blit(level_text, (SCREEN_WIDTH - level_rect.width - 20, 15))
        
        # Current level name (top-right)
        level_names = {
            1: "EC2 Invasion",
            2: "DynamoDB Assault", 
            3: "Lambda Swarm",
            4: "CloudFormation Boss"
        }
        level_name = level_names.get(self.current_level, "Unknown")
        level_name_text = self.font_tiny.render(level_name, False, GRAY)
        level_name_rect = level_name_text.get_rect()
        self.screen.blit(level_name_text, (SCREEN_WIDTH - level_name_rect.width - 20, 45))
    
    def draw_power_ups_ui(self):
        """Draw power-ups duration UI on the left edge - no background panel"""
        # Check if any power-ups are active
        has_active_powerups = (self.player.s3_timer > 0 or 
                              self.player.load_balancer_timer > 0 or 
                              len(self.side_ships) > 0)
        
        if not has_active_powerups:
            return  # Don't draw anything if no power-ups are active
        
        # Power-ups title (no background panel)
        title_text = self.font_small.render("Active Power-Ups", False, AWS_BLUE)
        self.screen.blit(title_text, (20, 120))  # Below main UI text
        
        y_offset = 150
        
        # S3 Power-up
        if self.player.s3_timer > 0:
            s3_time_left = self.player.s3_timer // 60  # Convert frames to seconds
            s3_text = self.font_tiny.render(f"S3 Shield: {s3_time_left}s", False, GREEN)
            self.screen.blit(s3_text, (20, y_offset))
            
            # Progress bar for S3
            bar_width = 150
            bar_height = 8
            progress = self.player.s3_timer / S3_DURATION
            filled_width = int(bar_width * progress)
            
            # Background bar
            pygame.draw.rect(self.screen, GRAY, (20, y_offset + 15, bar_width, bar_height))
            # Progress bar
            pygame.draw.rect(self.screen, GREEN, (20, y_offset + 15, filled_width, bar_height))
            
            y_offset += 35
        
        # Load Balancer Power-up
        if self.player.load_balancer_timer > 0:
            lb_time_left = self.player.load_balancer_timer // 60
            lb_text = self.font_tiny.render(f"Load Balancer: {lb_time_left}s", False, BLUE)
            self.screen.blit(lb_text, (20, y_offset))
            
            # Progress bar for Load Balancer
            bar_width = 150
            bar_height = 8
            progress = self.player.load_balancer_timer / LOAD_BALANCER_DURATION
            filled_width = int(bar_width * progress)
            
            pygame.draw.rect(self.screen, GRAY, (20, y_offset + 15, bar_width, bar_height))
            pygame.draw.rect(self.screen, BLUE, (20, y_offset + 15, filled_width, bar_height))
            
            y_offset += 35
        
        # Auto Scaling Power-up
        if len(self.side_ships) > 0:
            auto_scaling_text = self.font_tiny.render("Auto Scaling: Active", False, YELLOW)
            self.screen.blit(auto_scaling_text, (20, y_offset))
            
            # Show side ship count
            ship_count_text = self.font_tiny.render(f"Side Ships: {len(self.side_ships)}", False, YELLOW)
            self.screen.blit(ship_count_text, (20, y_offset + 15))
            
            y_offset += 35
    
    def game_loop(self):
        """Main game loop"""
        # Start background music (skip for boss level)
        if ENABLE_AUDIO and self.current_level != 4:  # Don't play game_bgm for boss level
            try:
                pygame.mixer.music.load('assets/audio/game_bgm.wav')
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play(-1)  # Loop indefinitely
                print("Started game background music")
            except:
                print("Could not load or play game_bgm.wav")
        
        while not self.game_over:
            # Handle events
            if not self.handle_events():
                return False
            
            # Check for level completion
            if self.level_complete:
                # Play next level sound
                self.play_sound('next_level')
                
                # Show next level screen with background and credits
                self.show_next_level_screen()
                
                # Wait for enter key
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            return False
                        elif event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_RETURN:
                                waiting = False
                            elif event.key == pygame.K_ESCAPE:
                                return False
                
                # Advance to next level
                if not self.next_level():
                    # No more levels, player wins
                    self.game_over = True
                    self.win = True
                    break
            
            # Update game state
            self.update()
            
            # Draw everything
            self.draw()
            
            # Control game speed
            self.clock.tick(60)
        
        # Game over screen
        # Stop background music
        if ENABLE_AUDIO:
            pygame.mixer.music.stop()
            
        if self.win:
            self.play_sound('victory')  # Play victory sound
            self.show_victory_screen()  # Use new victory screen with background
        else:
            self.play_sound('game_over')  # Play game over sound
            self.show_game_over_screen()  # Use new game over screen with background and reason
        
        # Wait for ENTER key to restart or ESC to exit
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.cleanup_audio()  # Clean up audio before exit
                    return False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.cleanup_audio()  # Clean up audio before exit
                        return False
                    elif event.key == pygame.K_RETURN:  # Only respond to Enter key
                        self.cleanup_audio()  # Clean up audio before restart
                        waiting = False
                        return True
        
        return True
    
    def run(self):
        """Run the entire game with menu and game loop"""
        running = True
        
        while running:
            # Show menu (this will restart menu music)
            if not self.menu.run():
                break
            
            # Initialize/reset game
            self.initialize_game()
            
            # Run game loop
            if not self.game_loop():
                break
        
        # Clean up
        pygame.quit()
