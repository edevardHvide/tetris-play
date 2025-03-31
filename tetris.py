import pygame
import random
import time
import json
import os
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()  # Initialize the mixer for sound effects
pygame.key.set_repeat(200, 50)  # Enable key repeat (initial delay, repeat interval in ms)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
CYAN = (0, 255, 255)   # I piece
YELLOW = (255, 255, 0)  # O piece
PURPLE = (128, 0, 128)  # T piece
GREEN = (0, 255, 0)    # S piece
RED = (255, 0, 0)      # Z piece
BLUE = (0, 0, 255)     # J piece
ORANGE = (255, 165, 0)  # L piece
FLASH_WHITE = (220, 220, 220)  # Color for line clear flash effect

# Sound loading with multiple fallback methods
def load_sound(filename, default_volume=0.5):
    # List of possible file paths to try
    paths_to_try = [
        filename,                        # Current directory
        os.path.join('sounds', filename),  # sounds/ subdirectory
        os.path.join('assets', 'sounds', filename),  # assets/sounds/ subdirectory
        os.path.join(os.path.dirname(__file__), filename),  # Script directory
        os.path.join(os.path.dirname(__file__), 'sounds', filename)  # Script's sounds/ subdirectory
    ]
    
    # Also try different extensions if not specified
    if '.' not in filename:
        extensions = ['.wav', '.ogg', '.mp3']
        base_paths = paths_to_try.copy()
        paths_to_try = []
        for path in base_paths:
            for ext in extensions:
                paths_to_try.append(f"{path}{ext}")
    
    # Try each path
    for path in paths_to_try:
        try:
            if os.path.exists(path):
                sound = pygame.mixer.Sound(path)
                sound.set_volume(default_volume)
                print(f"Successfully loaded sound: {path}")
                return sound
        except Exception as e:
            print(f"Failed to load {path}: {e}")
    
    # If all paths fail, try creating from bytearray (for WAV format)
    try:
        # Generate a simple beep sound (sine wave)
        print("Generating fallback beep sound...")
        import array
        import math
        
        sample_rate = 44100
        duration = 0.2  # seconds
        volume = 0.5
        n_samples = int(round(duration * sample_rate))
        
        # Generate sine wave
       
        
        sound = pygame.mixer.Sound(buffer=buf)
        sound.set_volume(default_volume)
        return sound
    except Exception as e:
        print(f"Failed to generate fallback sound: {e}")
    
    # Last resort - silent sound
    print("Warning: Using silent sound as last resort")
    return pygame.mixer.Sound(buffer=bytearray(100))

# Try to load sounds
try:
    print("Attempting to load sound effects...")
    LINE_CLEAR_SOUND = load_sound("line_clear", 0.7)
    MULTIPLIER_UP_SOUND = load_sound("multiplier_up", 0.6)
except Exception as e:
    print(f"Critical sound loading error: {e}")
    # Create silent sounds if all else fails
    LINE_CLEAR_SOUND = pygame.mixer.Sound(buffer=bytearray(100))
    MULTIPLIER_UP_SOUND = pygame.mixer.Sound(buffer=bytearray(100))

# Highscore file
HIGHSCORE_FILE = "tetris_highscores.json"

# Pop-up animation class
class PopUp:
    def __init__(self, text, position, color, size=36, duration=1.5):
        self.text = text
        self.position = list(position)  # Make a copy to modify
        self.color = color
        self.size = size
        self.start_time = time.time()
        self.duration = duration
        self.font = pygame.font.SysFont('Arial', size, bold=True)
        
    def update(self):
        # Move upward slightly
        self.position[1] -= 0.5
        # Check if expired
        return time.time() - self.start_time < self.duration
        
    def draw(self, screen):
        # Calculate alpha (fade out)
        elapsed = time.time() - self.start_time
        if elapsed > self.duration * 0.7:  # Start fading out after 70% of duration
            alpha = 255 * (1 - (elapsed - self.duration * 0.7) / (self.duration * 0.3))
        else:
            alpha = 255
            
        # Render with pulsing size
        pulse = 1.0 + 0.1 * abs(math.sin(elapsed * 10))
        current_size = int(self.size * pulse)
        font = pygame.font.SysFont('Arial', current_size, bold=True)
        
        text_surface = font.render(self.text, True, self.color)
        text_surface.set_alpha(int(alpha))
        screen.blit(text_surface, 
                   (self.position[0] - text_surface.get_width() // 2, 
                    self.position[1] - text_surface.get_height() // 2))

# Tetromino shapes represented as [rotation][y][x]
SHAPES = {
    'I': [
        [[0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0],
         [0, 0, 1, 0]],
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [1, 1, 1, 1],
         [0, 0, 0, 0]],
        [[0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0]]
    ],
    'O': [
        [[0, 0, 0, 0],
         [0, 1, 1, 0],
         [0, 1, 1, 0],
         [0, 0, 0, 0]]
    ],
    'T': [
        [[0, 0, 0, 0],
         [0, 1, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 1, 0, 0]],
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 1, 0, 0]],
        [[0, 0, 0, 0],
         [0, 1, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 0, 0]]
    ],
    'S': [
        [[0, 0, 0, 0],
         [0, 1, 1, 0],
         [1, 1, 0, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 0, 1, 0]],
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [0, 1, 1, 0],
         [1, 1, 0, 0]],
        [[0, 0, 0, 0],
         [1, 0, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 0, 0]]
    ],
    'Z': [
        [[0, 0, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [0, 0, 1, 0],
         [0, 1, 1, 0],
         [0, 1, 0, 0]],
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 1, 0]],
        [[0, 0, 0, 0],
         [0, 1, 0, 0],
         [1, 1, 0, 0],
         [1, 0, 0, 0]]
    ],
    'J': [
        [[0, 0, 0, 0],
         [1, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [0, 1, 1, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0]],
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [1, 1, 1, 0],
         [0, 0, 1, 0]],
        [[0, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [1, 1, 0, 0]]
    ],
    'L': [
        [[0, 0, 0, 0],
         [0, 0, 1, 0],
         [1, 1, 1, 0],
         [0, 0, 0, 0]],
        [[0, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 1, 0]],
        [[0, 0, 0, 0],
         [0, 0, 0, 0],
         [1, 1, 1, 0],
         [1, 0, 0, 0]],
        [[0, 0, 0, 0],
         [1, 1, 0, 0],
         [0, 1, 0, 0],
         [0, 1, 0, 0]]
    ]
}

# Map shape names to colors
SHAPE_COLORS = {
    'I': CYAN,
    'O': YELLOW,
    'T': PURPLE,
    'S': GREEN,
    'Z': RED,
    'J': BLUE,
    'L': ORANGE
}

# Game constants
CELL_SIZE = 30
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
SCREEN_WIDTH = BOARD_WIDTH * CELL_SIZE + 200  # Extra space for UI elements
SCREEN_HEIGHT = BOARD_HEIGHT * CELL_SIZE

class Tetromino:
    def __init__(self, shape):
        self.shape = shape
        self.rotation = 0
        self.shape_data = SHAPES[shape]
        self.color = SHAPE_COLORS[shape]
    
    def get_shape_matrix(self):
        return self.shape_data[self.rotation]
    
    def rotate(self, direction=1):
        # Rotate clockwise (1) or counterclockwise (-1)
        num_rotations = len(self.shape_data)
        self.rotation = (self.rotation + direction) % num_rotations


class GameBoard:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        self.colors = [[0 for _ in range(width)] for _ in range(height)]
    
    def is_collision(self, tetromino, position):
        shape_matrix = tetromino.get_shape_matrix()
        for y in range(4):
            for x in range(4):
                if shape_matrix[y][x]:
                    board_x = position[0] + x
                    board_y = position[1] + y
                    
                    # Check for boundaries or collision with placed pieces
                    if (board_x < 0 or board_x >= self.width or 
                        board_y >= self.height or 
                        (board_y >= 0 and self.grid[board_y][board_x])):
                        return True
        return False
    
    def place_tetromino(self, tetromino, position):
        shape_matrix = tetromino.get_shape_matrix()
        for y in range(4):
            for x in range(4):
                if shape_matrix[y][x]:
                    board_x = position[0] + x
                    board_y = position[1] + y
                    if 0 <= board_y < self.height and 0 <= board_x < self.width:
                        self.grid[board_y][board_x] = 1
                        self.colors[board_y][board_x] = tetromino.color
    
    def clear_lines(self):
        lines_cleared = 0
        lines_to_clear = []
        
        # Find complete lines
        for y in range(self.height - 1, -1, -1):
            if all(self.grid[y]):
                lines_to_clear.append(y)
                lines_cleared += 1
        
        # Return early if no lines to clear
        if not lines_cleared:
            return 0, []
            
        return lines_cleared, lines_to_clear
    
    def remove_lines(self, lines_to_clear):
        # Remove the lines in order from top to bottom
        for line in sorted(lines_to_clear):
            # Move all lines above down
            for move_y in range(line, 0, -1):
                for x in range(self.width):
                    self.grid[move_y][x] = self.grid[move_y-1][x]
                    self.colors[move_y][x] = self.colors[move_y-1][x]
            
            # Clear the top line
            for x in range(self.width):
                self.grid[0][x] = 0
                self.colors[0][x] = 0


class TetrisGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption('Tetris MVP')
        
        self.board = GameBoard(BOARD_WIDTH, BOARD_HEIGHT)
        self.clock = pygame.time.Clock()
        
        self.current_tetromino = None
        self.next_tetromino = None
        self.saved_tetromino = None  # Add a saved/held piece
        self.can_save_piece = True   # Flag to prevent multiple saves in a row
        self.position = [0, 0]
        
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.game_over_ready_to_restart = False  # New state to track after name entry
        self.paused = False  # Add pause state
        self.multiplier = 1  # Starting multiplier
        self.last_clear_time = 0  # Time of last line clear
        self.flash_lines = []  # Lines currently being flashed
        self.flash_start_time = 0  # When the flash effect started
        self.combo_decay_time = 5.0  # Seconds before combo resets
        self.popups = []  # List of active popups
        self.prev_multiplier = 1  # Track previous multiplier for animations
        
        self.drop_speed = 1.0  # seconds between drops
        self.speed_increase_factor = 0.9995  # Make this closer to 1 for slower increase
        self.min_drop_speed = 0.1  # Increase min speed to make it not get too fast
        self.last_drop_time = time.time()
        
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont('Arial', 32, bold=True)
        
        # Highscore system
        self.highscores = self.load_highscores()
        self.player_name = ""
        self.name_input_active = False
        
        # Initialize with random pieces
        self.spawn_tetromino()
    
    def load_highscores(self):
        if os.path.exists(HIGHSCORE_FILE):
            try:
                with open(HIGHSCORE_FILE, 'r') as f:
                    return json.load(f)
            except:
                print("Error loading highscores, creating new file")
        # Return empty list instead of pre-populated defaults
        return []
        
    def save_highscores(self):
        with open(HIGHSCORE_FILE, 'w') as f:
            json.dump(self.highscores, f)
            
    def check_highscore(self):
        # Only activate name input when game is over
        if self.game_over and not self.game_over_ready_to_restart:
            self.name_input_active = True
            return True
        return False
    
    def add_highscore(self, name):
        # Always add new score
        self.highscores.append({"name": name, "score": self.score})
        self.highscores.sort(key=lambda x: x["score"], reverse=True)
        # Keep only top 5
        self.highscores = self.highscores[:5]
        self.save_highscores()
        
        # Update game state
        self.name_input_active = False
        self.game_over_ready_to_restart = True
        
        # Debug print
        print(f"Highscore added. Ready to restart: {self.game_over_ready_to_restart}")
    
    def spawn_tetromino(self):
        if self.next_tetromino:
            self.current_tetromino = self.next_tetromino
        else:
            shape = random.choice(list(SHAPES.keys()))
            self.current_tetromino = Tetromino(shape)
        
        shape = random.choice(list(SHAPES.keys()))
        self.next_tetromino = Tetromino(shape)
        
        # Initial position (centered at the top)
        self.position = [self.board.width // 2 - 2, -1]
        
        # Apply a very small speed increase with each new piece
        self.drop_speed = max(self.min_drop_speed, self.drop_speed * self.speed_increase_factor)
        
        # Allow saving again with the new piece
        self.can_save_piece = True
        
        # Check if the new piece immediately collides (game over)
        if self.board.is_collision(self.current_tetromino, self.position):
            self.game_over = True
            # When game over happens, immediately check for highscore
            self.check_highscore()
    
    def move_left(self):
        new_position = [self.position[0] - 1, self.position[1]]
        if not self.board.is_collision(self.current_tetromino, new_position):
            self.position = new_position
    
    def move_right(self):
        new_position = [self.position[0] + 1, self.position[1]]
        if not self.board.is_collision(self.current_tetromino, new_position):
            self.position = new_position
    
    def move_down(self):
        new_position = [self.position[0], self.position[1] + 1]
        if not self.board.is_collision(self.current_tetromino, new_position):
            self.position = new_position
            return True
        else:
            # Place the piece if it can't move down anymore
            self.board.place_tetromino(self.current_tetromino, self.position)
            
            # Check for lines
            lines, lines_to_clear = self.board.clear_lines()
            
            if lines > 0:
                # Start the flash effect
                self.flash_lines = lines_to_clear
                self.flash_start_time = time.time()
                
                # Play sound effect
                LINE_CLEAR_SOUND.play()
                
                # Update multiplier and score
                current_time = time.time()
                self.prev_multiplier = self.multiplier  # Save for animation
                
                if current_time - self.last_clear_time <= self.combo_decay_time:
                    self.multiplier += 1
                    # Play multiplier sound if it increased
                    if self.multiplier > self.prev_multiplier:
                        MULTIPLIER_UP_SOUND.play()
                        # Add multiplier popup
                        center_x = SCREEN_WIDTH // 2
                        self.popups.append(PopUp(f"MULTIPLIER x{self.multiplier}!", 
                                             [center_x, SCREEN_HEIGHT // 2 + 50], 
                                             ORANGE, 32, 2.0))
                else:
                    self.multiplier = 1
                
                self.last_clear_time = current_time
                
                # Add score with multiplier
                base_score = [0, 100, 300, 500, 800][lines] * self.level
                points_earned = base_score * self.multiplier
                self.score += points_earned
                
                # Create a popup for points
                center_x = SCREEN_WIDTH // 2
                center_y = SCREEN_HEIGHT // 2
                self.popups.append(PopUp(f"+{points_earned}", [center_x, center_y], GREEN, 48, 1.5))
                
                self.lines_cleared += lines
                
                # Level up every 10 lines
                old_level = self.level
                self.level = (self.lines_cleared // 10) + 1
                
                # If leveled up, make a more significant speed increase
                if self.level > old_level:
                    # Make level speed increase more gradual (0.05 per level instead of 0.1)
                    self.drop_speed = max(self.min_drop_speed, 1.0 - (self.level - 1) * 0.05)
                    # Add level up popup
                    center_x = SCREEN_WIDTH // 2
                    self.popups.append(PopUp(f"LEVEL UP! {self.level}", 
                                        [center_x, SCREEN_HEIGHT // 2 - 50], 
                                        YELLOW, 40, 2.0))
            else:
                # Check if multiplier should reset (no lines cleared)
                current_time = time.time()
                if current_time - self.last_clear_time > self.combo_decay_time:
                    self.multiplier = 1
                    
                # Spawn a new piece immediately if no lines to clear
                self.spawn_tetromino()
            
            return False
    
    def hard_drop(self):
        while self.move_down():
            pass
    
    def rotate(self):
        self.current_tetromino.rotate()
        if self.board.is_collision(self.current_tetromino, self.position):
            # If rotation causes collision, rotate back
            self.current_tetromino.rotate(-1)
    
    def update(self):
        current_time = time.time()
        
        # Handle line clear animation
        if self.flash_lines:
            # Flash effect duration (0.5 seconds)
            if current_time - self.flash_start_time > 0.5:
                # Remove the lines after flash effect
                self.board.remove_lines(self.flash_lines)
                self.flash_lines = []
                # Spawn a new piece after lines are cleared
                self.spawn_tetromino()
        else:
            # Only perform normal drop if not in the middle of line clear animation
            if current_time - self.last_drop_time > self.drop_speed:
                self.move_down()
                self.last_drop_time = current_time
            
            # Check if multiplier should reset (time elapsed)
            if self.multiplier > 1 and current_time - self.last_clear_time > self.combo_decay_time:
                self.multiplier = 1
        
        # Update popups
        self.popups = [popup for popup in self.popups if popup.update()]
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw the board grid
        for y in range(self.board.height):
            for x in range(self.board.width):
                # Draw cell border
                pygame.draw.rect(self.screen, GRAY, 
                                [x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE], 1)
                
                # If cell is occupied, fill it
                if self.board.grid[y][x]:
                    # Flash effect if this row is being cleared
                    if y in self.flash_lines:
                        pygame.draw.rect(self.screen, FLASH_WHITE,
                                        [x * CELL_SIZE + 1, y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2])
                    else:
                        pygame.draw.rect(self.screen, self.board.colors[y][x],
                                        [x * CELL_SIZE + 1, y * CELL_SIZE + 1, CELL_SIZE - 2, CELL_SIZE - 2])
        
        # Draw current tetromino (only if not during line clear animation)
        if self.current_tetromino and not self.flash_lines:
            shape_matrix = self.current_tetromino.get_shape_matrix()
            for y in range(4):
                for x in range(4):
                    if shape_matrix[y][x]:
                        pygame.draw.rect(self.screen, self.current_tetromino.color,
                                        [(self.position[0] + x) * CELL_SIZE + 1,
                                         (self.position[1] + y) * CELL_SIZE + 1,
                                         CELL_SIZE - 2, CELL_SIZE - 2])
        
        # Draw UI (score, level, next piece)
        ui_x = BOARD_WIDTH * CELL_SIZE + 20
        
        # Score
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (ui_x, 30))
        
        # Level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (ui_x, 60))
        
        # Lines
        lines_text = self.font.render(f"Lines: {self.lines_cleared}", True, WHITE)
        self.screen.blit(lines_text, (ui_x, 90))
        
        # Next piece
        next_text = self.font.render("Next:", True, WHITE)
        self.screen.blit(next_text, (ui_x, 140))
        
        if self.next_tetromino:
            shape_matrix = self.next_tetromino.get_shape_matrix()
            for y in range(4):
                for x in range(4):
                    if shape_matrix[y][x]:
                        pygame.draw.rect(self.screen, self.next_tetromino.color,
                                        [ui_x + x * (CELL_SIZE - 5),
                                         170 + y * (CELL_SIZE - 5),
                                         CELL_SIZE - 7, CELL_SIZE - 7])
        
        # Draw saved/held piece section with better layout
        saved_text = self.font.render("Hold (Ctrl+C):", True, WHITE)
        self.screen.blit(saved_text, (ui_x, 240))
        
        # Draw a box to indicate the hold area
        hold_box_rect = pygame.Rect(ui_x, 270, 120, 100)
        pygame.draw.rect(self.screen, GRAY, hold_box_rect, 1)
        
        if self.saved_tetromino:
            shape_matrix = self.saved_tetromino.get_shape_matrix()
            # Center the piece in the box
            center_x = ui_x + 60
            center_y = 270 + 50
            
            # Calculate the dimensions of the tetromino to center it
            min_x, max_x, min_y, max_y = 4, 0, 4, 0
            for y in range(4):
                for x in range(4):
                    if shape_matrix[y][x]:
                        min_x = min(min_x, x)
                        max_x = max(max_x, x)
                        min_y = min(min_y, y)
                        max_y = max(max_y, y)
            
            width = max_x - min_x + 1
            height = max_y - min_y + 1
            
            # Draw the piece centered
            for y in range(4):
                for x in range(4):
                    if shape_matrix[y][x]:
                        pygame.draw.rect(self.screen, self.saved_tetromino.color,
                                        [center_x - (width * (CELL_SIZE - 5)) // 2 + (x - min_x) * (CELL_SIZE - 5),
                                         center_y - (height * (CELL_SIZE - 5)) // 2 + (y - min_y) * (CELL_SIZE - 5),
                                         CELL_SIZE - 7, CELL_SIZE - 7])
        else:
            # Show "Empty" text when no piece is saved
            empty_text = self.font.render("Empty", True, GRAY)
            self.screen.blit(empty_text, (ui_x + 60 - empty_text.get_width() // 2, 270 + 50 - empty_text.get_height() // 2))
        
        # Multiplier (highlight if higher than 1)
        pygame.draw.rect(self.screen, GRAY, [ui_x, 390, 160, 50], 0 if self.multiplier > 1 else 1)
        
        # Calculate font size based on multiplier value for pulsing effect
        mult_size = 24
        if self.multiplier > 1:
            # Make it pulse a bit
            elapsed = time.time() - self.last_clear_time
            if elapsed < 1.0:  # Pulse for 1 second after increasing
                mult_size = int(24 + 8 * abs(math.sin(elapsed * 10)))
        
        mult_font = pygame.font.SysFont('Arial', mult_size, bold=(self.multiplier > 1))
        multiplier_color = ORANGE if self.multiplier > 1 else WHITE
        multiplier_text = mult_font.render(f"Multiplier: x{self.multiplier}", True, multiplier_color)
        self.screen.blit(multiplier_text, (ui_x + 80 - multiplier_text.get_width()//2, 415 - multiplier_text.get_height()//2))
        
        # Draw popups
        for popup in self.popups:
            popup.draw(self.screen)
        
        # Pause overlay
        if self.paused:
            pause_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            pause_surface.set_alpha(150)
            pause_surface.fill(BLACK)
            self.screen.blit(pause_surface, (0, 0))
            
            pause_text = self.big_font.render("PAUSED", True, WHITE)
            resume_text = self.font.render("Press P to resume", True, WHITE)
            
            self.screen.blit(pause_text, 
                            (SCREEN_WIDTH // 2 - pause_text.get_width() // 2, 
                             SCREEN_HEIGHT // 2 - 30))
            self.screen.blit(resume_text, 
                            (SCREEN_WIDTH // 2 - resume_text.get_width() // 2, 
                             SCREEN_HEIGHT // 2 + 20))
        
        # Game over or name input
        if self.game_over:
            game_over_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            game_over_surface.set_alpha(150)
            game_over_surface.fill(BLACK)
            self.screen.blit(game_over_surface, (0, 0))
            
            if self.name_input_active:
                # Draw name input dialog
                pygame.draw.rect(self.screen, GRAY, 
                                [SCREEN_WIDTH // 4, SCREEN_HEIGHT // 3, 
                                 SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3])
                
                # Change text based on whether it's a new highscore or just game over
                if not self.highscores or self.score > min([hs["score"] for hs in self.highscores]) or len(self.highscores) < 5:
                    input_text = self.big_font.render("NEW HIGHSCORE!", True, YELLOW)
                else:
                    input_text = self.big_font.render("GAME OVER", True, WHITE)
                
                name_prompt = self.font.render("Enter your name:", True, WHITE)
                name_text = self.big_font.render(self.player_name + "_", True, WHITE)
                instruction = self.font.render("Press ENTER when done", True, WHITE)
                
                self.screen.blit(input_text, 
                                (SCREEN_WIDTH // 2 - input_text.get_width() // 2, 
                                 SCREEN_HEIGHT // 3 + 20))
                self.screen.blit(name_prompt, 
                                (SCREEN_WIDTH // 2 - name_prompt.get_width() // 2, 
                                 SCREEN_HEIGHT // 3 + 70))
                self.screen.blit(name_text, 
                                (SCREEN_WIDTH // 2 - name_text.get_width() // 2, 
                                 SCREEN_HEIGHT // 3 + 120))
                self.screen.blit(instruction, 
                                (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 
                                 SCREEN_HEIGHT // 3 + 170))
            elif self.game_over_ready_to_restart:
                # Ready to restart with any key
                game_over_text = self.big_font.render("GAME OVER", True, WHITE)
                score_text = self.font.render(f"Final Score: {self.score}", True, WHITE)
                restart_text = self.font.render("Press ANY KEY to play again", True, WHITE)
                
                self.screen.blit(game_over_text, 
                                (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                                 SCREEN_HEIGHT // 2 - 80))
                self.screen.blit(score_text, 
                                (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 
                                 SCREEN_HEIGHT // 2 - 40))
                
                # Draw highscores below
                highscore_text = self.font.render("Highscores:", True, WHITE)
                self.screen.blit(highscore_text, 
                                (SCREEN_WIDTH // 2 - highscore_text.get_width() // 2, 
                                 SCREEN_HEIGHT // 2))
                
                if self.highscores:
                    for i, hs in enumerate(self.highscores):
                        hs_text = self.font.render(f"{i+1}. {hs['name']}: {hs['score']}", True, 
                                                 YELLOW if i == 0 else WHITE)
                        self.screen.blit(hs_text, 
                                        (SCREEN_WIDTH // 2 - hs_text.get_width() // 2, 
                                         SCREEN_HEIGHT // 2 + 30 + i * 25))
                
                self.screen.blit(restart_text, 
                                (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                                 SCREEN_HEIGHT // 2 + 160))
            else:
                # Standard game over screen
                game_over_text = self.big_font.render("GAME OVER", True, WHITE)
                restart_text = self.font.render("Press R to restart", True, WHITE)
                
                self.screen.blit(game_over_text, 
                                (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, 
                                 SCREEN_HEIGHT // 2 - 30))
                self.screen.blit(restart_text, 
                                (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                                 SCREEN_HEIGHT // 2 + 20))
        
        pygame.display.flip()
    
    def handle_name_input(self, event):
        if event.key == pygame.K_RETURN:
            if self.player_name:  # Ensure name isn't empty
                self.add_highscore(self.player_name)
            else:
                self.add_highscore("Anonymous")
            # Add print statement for debugging
            print(f"Added highscore for {self.player_name if self.player_name else 'Anonymous'}")
            print(f"game_over_ready_to_restart: {self.game_over_ready_to_restart}")
        elif event.key == pygame.K_BACKSPACE:
            self.player_name = self.player_name[:-1]
        elif event.unicode.isalnum() and len(self.player_name) < 10:  # Limit to 10 chars
            self.player_name += event.unicode
    
    def save_piece(self):
        if not self.can_save_piece:
            return  # Prevent saving multiple times without placing a piece
        
        if self.saved_tetromino is None:
            # First time saving - just store current piece and get a new one
            self.saved_tetromino = self.current_tetromino
            self.spawn_new_current_piece()
        else:
            # Swap current piece with saved piece
            self.current_tetromino, self.saved_tetromino = self.saved_tetromino, self.current_tetromino
            
            # Reset position to top of board
            self.position = [self.board.width // 2 - 2, -1]
            
            # Check for collision after swap (game over if can't place)
            if self.board.is_collision(self.current_tetromino, self.position):
                self.game_over = True
                self.check_highscore()
        
        # Prevent saving again until a piece is placed
        self.can_save_piece = False

    def spawn_new_current_piece(self):
        # Helper method to get a new current piece from next queue
        if self.next_tetromino:
            self.current_tetromino = self.next_tetromino
            
            # Get a new next piece
            shape = random.choice(list(SHAPES.keys()))
            self.next_tetromino = Tetromino(shape)
            
            # Reset position
            self.position = [self.board.width // 2 - 2, -1]
            
            # Check for collision (game over if can't place)
            if self.board.is_collision(self.current_tetromino, self.position):
                self.game_over = True
                self.check_highscore()
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Handle keyboard inputs
                if event.type == pygame.KEYDOWN:
                    if self.game_over:
                        if self.name_input_active:
                            # Handle name input
                            self.handle_name_input(event)
                        elif self.game_over_ready_to_restart:
                            # Restart game with any key
                            self.__init__()
                        elif event.key == pygame.K_r:
                            # Original restart with R key
                            self.__init__()
                    else:
                        # Game is active
                        if event.key == pygame.K_LEFT:
                            self.move_left()
                        elif event.key == pygame.K_RIGHT:
                            self.move_right()
                        elif event.key == pygame.K_DOWN:
                            self.move_down()
                        elif event.key == pygame.K_UP:
                            self.rotate()
                        elif event.key == pygame.K_SPACE:
                            self.hard_drop()
                        elif event.key == pygame.K_p:  # P key toggles pause
                            self.paused = not self.paused
                        elif event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                            # Ctrl+C to save/swap piece
                            if not self.paused:
                                self.save_piece()
            
            # Game logic update
            if not self.game_over and not self.paused:
                self.update()
            # Ensure name input is activated as soon as game over happens
            elif self.game_over and not self.name_input_active and not self.game_over_ready_to_restart:
                self.check_highscore()
            
            # Drawing
            self.draw()
            
            # Cap at 60 FPS
            self.clock.tick(60)
        
        pygame.quit()


if __name__ == "__main__":
    game = TetrisGame()
    game.run()