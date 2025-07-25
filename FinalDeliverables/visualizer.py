import pygame

# ---  Configuration ---
CELL_SIZE = 60
UI_PANEL_HEIGHT = 80 # Extra space at the bottom for UI elements
PANEL_WITDH = 50 # Width of the grid lines
COLORS = {
    '.': (255, 255, 255), # White - Empty
    'G': (255, 215, 0),   # Gold
    'O': (139, 69, 19),    # Brown - Obstacle
    'R': (0, 0, 255),     # Blue - Robot
    'RG': (0, 128, 0),    # Green - Robot on Gold
    'RC': (30, 144, 255), # Dodger Blue - Robot on Collected
    'C': (192, 192, 192)  # Silver - Collected Gold Spot
}
GRID_LINE_COLOR = (200, 200, 200)
UI_PANEL_COLOR = (40, 40, 40)
TEXT_COLOR = (255, 255, 255)

def draw_grid(screen, grid_data, rows, cols):
    """Draws the entire grid on the pygame screen."""
    for r in range(rows):
        for c in range(cols):
            # Draw the cell background color
            rect = pygame.Rect(c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            cell_type = grid_data[r][c]
            # Handle multi-character states like 'RG', 'RC'
            base_cell_type = cell_type[0] 
            pygame.draw.rect(screen, COLORS.get(base_cell_type, (0,0,0)), rect)

            # If robot is present, draw a smaller rectangle inside to represent it
            if 'R' in cell_type:
                 robot_rect = pygame.Rect(c * CELL_SIZE + 10, r * CELL_SIZE + 10, CELL_SIZE - 20, CELL_SIZE - 20)
                 robot_color = COLORS.get(cell_type, (255,0,0)) # Default to red if state unknown
                 pygame.draw.rect(screen, robot_color, robot_rect)

            # Draw grid lines
            pygame.draw.rect(screen, GRID_LINE_COLOR, rect, 1)

def visualize_solution(solution, rows, cols):
    """
    Initializes pygame and displays the solution animation.
    """
    pygame.init()
    screen_width = cols * CELL_SIZE + PANEL_WITDH  # Extra space for UI panel
    # Increase screen height to make space for the UI panel
    screen_height = rows * CELL_SIZE + UI_PANEL_HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Golds in MineField - Solution Path")

    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 20)
    running = True
    current_step = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    current_step = min(current_step + 1, len(solution) - 1)
                if event.key == pygame.K_LEFT:
                    current_step = max(current_step - 1, 0)
                if event.key == pygame.K_ESCAPE:
                    running = False

        screen.fill((30, 30, 30)) # Dark background for the grid area

        # --- Draw UI Panel ---
        ui_panel_rect = pygame.Rect(0, rows * CELL_SIZE, screen_width, UI_PANEL_HEIGHT)
        pygame.draw.rect(screen, UI_PANEL_COLOR, ui_panel_rect)

        # --- Draw Grid ---
        draw_grid(screen, solution[current_step], rows, cols)

        # --- Draw Text on UI Panel ---
        # Display the current step number
        step_text = font.render(f"Step: {current_step}/{len(solution)-1}", True, TEXT_COLOR)
        screen.blit(step_text, (15, rows * CELL_SIZE + 15))

        # Add instructions
        instructions_text = small_font.render("Use Left/Right arrow keys to navigate. ESC to quit.", True, TEXT_COLOR)
        screen.blit(instructions_text, (15, rows * CELL_SIZE + 50))

        pygame.display.flip()
        
    pygame.quit()
