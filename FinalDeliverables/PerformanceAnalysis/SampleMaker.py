# SampleMaker.py
import math
import random

def generate_grid_with_obstacles(size, obstacle_count, is_random_placement):
    """
    Generates a single grid with a fixed start/goal and a variable number of obstacles.

    Args:
        size (int): The grid size (NxN).
        obstacle_count (int): The number of obstacles to place.
        is_random_placement (bool): The strategy for placing obstacles. True means
                                    random placement; False uses a predefined, safe
                                    strategy to guarantee a solution path.

    Returns:
        dict: A dictionary object for the generated sample.
    """
    grid = [['.' for _ in range(size)] for _ in range(size)]
    start_pos = (0, 0)
    # Goal is fixed at the top-right
    gold_pos = (0, size - 1)
    grid[gold_pos[0]][gold_pos[1]] = 'G'
    
    # Determine the pool of possible coordinates for obstacles
    if is_random_placement:
        # Random placement can be anywhere except start and goal
        obstacle_pool = [(r, c) for r in range(size) for c in range(size) 
                         if (r, c) != start_pos and (r, c) != gold_pos]
        random.shuffle(obstacle_pool)
    else:
        # Predefined placement avoids the first row to guarantee a path
        obstacle_pool = [(r, c) for r in range(1, size) for c in range(size)]

    # Place the specified number of obstacles from the determined pool
    for i in range(min(obstacle_count, len(obstacle_pool))):
        r, c = obstacle_pool[i]
        grid[r][c] = 'O'

    sample = {'start_pos': start_pos, 'grid': grid}
    return sample
def generate_grid_with_gold_count(size, gold_count, place_gold_close):
    """
    Generates a single grid with a specific number of gold pieces.

    Args:
        size (int): The grid size (NxN).
        gold_count (int): The number of gold pieces to place.
        place_gold_close (bool): The strategy for placing gold. True means
                                 placing gold near the start (0,0), False
                                 means placing it far away.

    Returns:
        dict: A dictionary object for the generated sample.
    """
    grid = [['.' for _ in range(size)] for _ in range(size)]
    start_pos = (0, 0)

    possible_coords = [(r, c) for r in range(size) for c in range(size) if (r, c) != start_pos]

    possible_coords.sort(key=lambda p: p[0] + p[1], reverse=not place_gold_close)

    for i in range(min(gold_count, len(possible_coords))):
        r, c = possible_coords[i]
        grid[r][c] = 'G'

    sample = {'start_pos': start_pos, 'grid': grid}
    return sample


def generate_single_grid_instance(size, goalClose):
    """
    Generates a single benchmark instance of a specific size.
    """
    grid = [['.' for _ in range(size)] for _ in range(size)]
    start_pos = (0, 0)
    if goalClose:
        gold_pos = (0, 1) if size > 1 else (0, 0)
    else:
        gold_pos = (size - 1, size - 1)
    if start_pos == gold_pos:
        grid[start_pos[0]][start_pos[1]] = 'G'
    else:
        grid[gold_pos[0]][gold_pos[1]] = 'G'
    sample = {'start_pos': start_pos, 'max_steps': 1, 'grid': grid}
    return sample


def generate_benchmark_instances(goalClose=False, max_size=40, max_steps=42):
    """
    Generates a list of benchmark instances directly in memory.
    """
    benchmark_samples = []
    for size in range(1, max_size + 1):
        grid = [['.' for _ in range(size)] for _ in range(size)]
        start_pos = (0, 0)
        if goalClose:
            gold_pos = (0, 1) if size > 1 else (0, 0)
        else:
            gold_pos = (size - 1, size - 1)
        if start_pos == gold_pos:
            grid[start_pos[0]][start_pos[1]] = 'G'
        else:
            grid[gold_pos[0]][gold_pos[1]] = 'G'
        sample = {'start_pos': start_pos, 'max_steps': max_steps, 'grid': grid}
        benchmark_samples.append(sample)
    return benchmark_samples