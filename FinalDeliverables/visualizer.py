import pygame

CELL_SIZE = 60
UI_PANEL_HEIGHT = 100
PANEL_SIDE_PADDING = 15

COLORS = {
    '.': (255, 255, 255),
    'G': (255, 215, 0),
    'O': (139, 69, 19),
    'R': (0, 0, 255),
    'RG': (0, 128, 0),
    'RC': (30, 144, 255),
    'C': (192, 192, 192)
}
GRID_LINE_COLOR = (200, 200, 200)
UI_PANEL_COLOR = (40, 40, 40)
TEXT_COLOR = (255, 255, 255)


def find_robot(grid_step, rows, cols):
    for r in range(rows):
        for c in range(cols):
            if 'R' in grid_step[r][c]:
                return (r, c)
    return None


def calculate_step_costs(solution, rows, cols, costs):
    step_costs = [0] * len(solution)
    if not costs:
        return step_costs
    for t in range(1, len(solution)):
        prev_step = solution[t - 1]
        curr_step = solution[t]
        prev_robot_pos = find_robot(prev_step, rows, cols)
        curr_robot_pos = find_robot(curr_step, rows, cols)
        action_cost = 0
        if prev_robot_pos and curr_robot_pos:
            if prev_robot_pos != curr_robot_pos:
                action_cost = costs.get('move', 0)
            else:
                r, c = prev_robot_pos
                if prev_step[r][c] == 'RG' and curr_step[r][c] == 'RC':
                    action_cost = costs.get('collect', 0)
                else:
                    action_cost = costs.get('stay', 0)
        step_costs[t] = step_costs[t - 1] + action_cost
    return step_costs


def draw_grid(screen, grid_data, rows, cols, x_offset):
    for r in range(rows):
        for c in range(cols):
            rect = pygame.Rect(
                x_offset + c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE, CELL_SIZE
            )
            cell_type = grid_data[r][c]
            base_color = COLORS.get(cell_type, COLORS.get(cell_type[:1], (0, 0, 0)))
            pygame.draw.rect(screen, base_color, rect)
            if 'R' in cell_type:
                robot_rect = pygame.Rect(
                    x_offset + c * CELL_SIZE + 10,
                    r * CELL_SIZE + 10,
                    CELL_SIZE - 20,
                    CELL_SIZE - 20,
                )
                robot_color = COLORS.get(cell_type, (255, 0, 0))
                pygame.draw.rect(screen, robot_color, robot_rect)
            pygame.draw.rect(screen, GRID_LINE_COLOR, rect, 1)


def visualize_solution(solution, rows, cols, final_cost=None, costs=None):
    pygame.init()
    screen_width = max(cols * CELL_SIZE, 800)
    screen_height = rows * CELL_SIZE + UI_PANEL_HEIGHT
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("Golds in MineField - Solution Path")

    font = pygame.font.Font(None, 28)
    small_font = pygame.font.Font(None, 22)

    running = True
    current_step = 0
    step_costs = calculate_step_costs(solution, rows, cols, costs)

    if final_cost is None:
        final_cost = step_costs[-1] if step_costs else 0

    instructions = "Use Left/Right arrow keys to navigate. ESC to quit."

    grid_width = cols * CELL_SIZE
    x_offset = (screen_width - grid_width) // 2

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

        screen.fill((30, 30, 30))

        ui_panel_rect = pygame.Rect(0, rows * CELL_SIZE, screen_width, UI_PANEL_HEIGHT)
        pygame.draw.rect(screen, UI_PANEL_COLOR, ui_panel_rect)

        draw_grid(screen, solution[current_step], rows, cols, x_offset)

        step_text = font.render(f"Step: {current_step}/{len(solution)-1}", True, TEXT_COLOR)
        cost_text = font.render(f"Cost: {step_costs[current_step]} / {final_cost}", True, TEXT_COLOR)
        instr_text = small_font.render(instructions, True, TEXT_COLOR)

        screen.blit(step_text, (PANEL_SIDE_PADDING, rows * CELL_SIZE + 15))
        screen.blit(cost_text, (PANEL_SIDE_PADDING, rows * CELL_SIZE + 50))
        screen.blit(instr_text, (PANEL_SIDE_PADDING, rows * CELL_SIZE + 75))

        pygame.display.flip()

    pygame.quit()
