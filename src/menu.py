import pygame
import os
import random
import math
from src.constants import *

class Star:
    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.brightness = random.randint(50, 255)
        self.fade_speed = random.uniform(1, 3)
        self.size = random.randint(1, 3)
        self.twinkle_phase = random.uniform(0, 2 * math.pi)
        self.twinkle_speed = random.uniform(0.05, 0.15)
        # More varied lifetimes: 2-15 seconds at 60fps
        self.lifetime = random.randint(120, 900)  
        self.age = 0
        self.current_brightness = self.brightness  # Initialize current_brightness
        
    def update(self):
        self.age += 1
        self.twinkle_phase += self.twinkle_speed
        
        # Calculate brightness with twinkling effect
        twinkle_factor = (math.sin(self.twinkle_phase) + 1) / 2  # 0 to 1
        base_brightness = self.brightness
        
        # Fade out near end of lifetime
        if self.age > self.lifetime * 0.8:
            fade_factor = 1 - ((self.age - self.lifetime * 0.8) / (self.lifetime * 0.2))
            base_brightness *= fade_factor
            
        self.current_brightness = int(base_brightness * (0.3 + 0.7 * twinkle_factor))
        
        return self.age < self.lifetime
        
    def draw(self, screen):
        if self.current_brightness > 0:
            color = (self.current_brightness, self.current_brightness, self.current_brightness)
            if self.size == 1:
                screen.set_at((int(self.x), int(self.y)), color)
            else:
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.size)

class Menu:
    def __init__(self, screen):
        self.screen = screen
        
        # Load Press Start 2P font
        try:
            self.font_title = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 36)
            self.font_button = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 24)
            self.font_small = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 16)
            self.font_tiny = pygame.font.Font('assets/fonts/PressStart2P-Regular.ttf', 12)
        except:
            # Fallback to system fonts if Press Start 2P fails to load
            self.font_title = pygame.font.Font(None, 72)
            self.font_button = pygame.font.Font(None, 48)
            self.font_small = pygame.font.Font(None, 32)
            self.font_tiny = pygame.font.Font(None, 24)
        
        # Load background image
        try:
            self.background = pygame.image.load('assets/images/bg/main_menu_background.png')
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.background = None
            
        # Load and play menu music
        try:
            if ENABLE_AUDIO:
                pygame.mixer.music.load('assets/audio/main_menu.wav')
                pygame.mixer.music.set_volume(MENU_MUSIC_VOLUME)
                pygame.mixer.music.play(-1)  # Loop indefinitely
        except:
            pass
            
        # Button properties
        self.button_width = 200
        self.button_height = 60
        self.play_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - self.button_width // 2,
            SCREEN_HEIGHT // 2 + 50,
            self.button_width,
            self.button_height
        )
        self.exit_button_rect = pygame.Rect(
            SCREEN_WIDTH // 2 - self.button_width // 2,
            SCREEN_HEIGHT // 2 + 130,
            self.button_width,
            self.button_height
        )
        
        self.selected_button = 0  # 0 = play, 1 = exit
        
        # Initialize stars
        self.stars = []
        self.max_stars = 50
        # Create initial stars
        for _ in range(self.max_stars):
            star = Star()
            # Give initial stars random ages so they don't all disappear at once
            star.age = random.randint(0, star.lifetime // 2)
            self.stars.append(star)
        
    def update_stars(self):
        """Update star animations and replace disappeared stars"""
        # Count stars that died this frame
        stars_before = len(self.stars)
        
        # Update existing stars and remove dead ones
        self.stars = [star for star in self.stars if star.update()]
        
        # Count how many stars died
        stars_died = stars_before - len(self.stars)
        
        # Replace each dead star with a new one (with some randomness)
        for _ in range(stars_died):
            if random.random() < 0.8:  # 80% chance to replace immediately
                self.stars.append(Star())
            # 20% chance to leave empty space for a while
        
        # Occasionally add a star if we're below max (to handle the 20% gaps)
        if len(self.stars) < self.max_stars and random.random() < 0.1:  # 10% chance per frame
            self.stars.append(Star())
            
    def draw_stars(self):
        """Draw all stars"""
        for star in self.stars:
            star.draw(self.screen)
        
    def draw_text_with_outline(self, text, font, color, outline_color, x, y, align="center"):
        """Draw text with pixel-style outline for retro effect"""
        # Draw outline by rendering text in multiple positions
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx != 0 or dy != 0:
                    outline_surface = font.render(text, False, outline_color)
                    outline_rect = outline_surface.get_rect()
                    if align == "center":
                        outline_rect.center = (x + dx, y + dy)
                    self.screen.blit(outline_surface, outline_rect)
        
        # Draw main text
        text_surface = font.render(text, False, color)
        text_rect = text_surface.get_rect()
        if align == "center":
            text_rect.center = (x, y)
        self.screen.blit(text_surface, text_rect)
        return text_rect
        
    def draw_transparent_button(self, rect, text, font, text_color, border_color, is_selected=False):
        """Draw a transparent button with border"""
        # Create a transparent surface
        button_surface = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        
        # Fill with semi-transparent background if selected
        if is_selected:
            button_surface.fill((255, 255, 255, 30))  # Very light transparent white
        else:
            button_surface.fill((0, 0, 0, 50))  # Semi-transparent black
            
        # Draw border
        border_width = 3 if is_selected else 2
        pygame.draw.rect(button_surface, border_color, button_surface.get_rect(), border_width)
        
        # Blit the button surface to screen
        self.screen.blit(button_surface, rect)
        
        # Draw text centered on button
        text_surface = font.render(text, False, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        self.screen.blit(text_surface, text_rect)
        
    def draw_main_menu(self):
        # Draw background
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill(BLACK)
        
        # Update and draw stars
        self.update_stars()
        self.draw_stars()
        
        # Draw title with pixel-style outline
        self.draw_text_with_outline(
            "CLOUD INVADERS", 
            self.font_title, 
            AWS_ORANGE, 
            BLACK, 
            SCREEN_WIDTH // 2, 
            120
        )
        
        # Draw subtitle
        self.draw_text_with_outline(
            "AWS Edition", 
            self.font_small, 
            AWS_BLUE, 
            BLACK, 
            SCREEN_WIDTH // 2, 
            160
        )
        
        # Draw buttons
        self.draw_transparent_button(
            self.play_button_rect,
            "PLAY",
            self.font_button,
            WHITE if self.selected_button != 0 else AWS_ORANGE,
            AWS_ORANGE if self.selected_button == 0 else WHITE,
            self.selected_button == 0
        )
        
        self.draw_transparent_button(
            self.exit_button_rect,
            "EXIT",
            self.font_button,
            WHITE if self.selected_button != 1 else RED,
            RED if self.selected_button == 1 else WHITE,
            self.selected_button == 1
        )
        
        # Draw controls hint at bottom
        self.draw_text_with_outline(
            "ARROWS to navigate • ENTER to select • SPACE to shoot • ESC to quit",
            self.font_tiny,
            WHITE,
            BLACK,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - 30
        )
        
        pygame.display.flip()
        
    def run(self):
        """Run the menu and return True if player wants to play, False to quit"""
        # Restart menu music when returning to menu
        try:
            if ENABLE_AUDIO:
                pygame.mixer.music.stop()  # Stop any current music
                pygame.mixer.music.load('assets/audio/main_menu.wav')
                pygame.mixer.music.set_volume(MENU_MUSIC_VOLUME)
                pygame.mixer.music.play(-1)  # Loop indefinitely
        except:
            pass
            
        clock = pygame.time.Clock()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.mixer.music.stop()
                    return False
                    
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self.selected_button = max(0, self.selected_button - 1)
                    elif event.key == pygame.K_DOWN:
                        self.selected_button = min(1, self.selected_button + 1)
                    elif event.key == pygame.K_RETURN:
                        pygame.mixer.music.stop()
                        if self.selected_button == 0:  # Play
                            return True
                        else:  # Exit
                            return False
                    elif event.key == pygame.K_ESCAPE:
                        pygame.mixer.music.stop()
                        return False
                        
                elif event.type == pygame.MOUSEMOTION:
                    # Check if mouse is over buttons
                    mouse_pos = pygame.mouse.get_pos()
                    if self.play_button_rect.collidepoint(mouse_pos):
                        self.selected_button = 0
                    elif self.exit_button_rect.collidepoint(mouse_pos):
                        self.selected_button = 1
                        
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        mouse_pos = pygame.mouse.get_pos()
                        if self.play_button_rect.collidepoint(mouse_pos):
                            pygame.mixer.music.stop()
                            return True
                        elif self.exit_button_rect.collidepoint(mouse_pos):
                            pygame.mixer.music.stop()
                            return False
            
            self.draw_main_menu()
            clock.tick(60)  # 60 FPS
