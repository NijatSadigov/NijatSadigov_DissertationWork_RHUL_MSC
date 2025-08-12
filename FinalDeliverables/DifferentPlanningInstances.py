# DifferentPlanningInstances.py
import random
from collections import deque

from visualizer import visualize_solution
from GoldsInMineField import solve_minefield_plan



def _neighbors(r, c, rows, cols):
    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            yield nr, nc

def _bfs_reachable(grid, start):
    """Return the set of coordinates reachable from start (avoiding 'O')."""
    rows, cols = len(grid), len(grid[0])
    if grid[start[0]][start[1]] == 'O':
        return set()  
    q = deque([start])
    seen = {start}
    while q:
        r, c = q.popleft()
        for nr, nc in _neighbors(r, c, rows, cols):
            if (nr, nc) not in seen and grid[nr][nc] != 'O':
                seen.add((nr, nc))
                q.append((nr, nc))
    return seen


def generate_random_instance(rows, cols, num_obstacles, num_gold, seed=None):
    """
    Pure random placement with optional seed (reproducible).
    Cells: '.' empty, 'O' obstacle, 'G' gold.
    Returns (grid, start_pos).
    """
    if rows <= 0 or cols <= 0:
        raise ValueError("rows and cols must be positive.")
    if num_obstacles < 0 or num_gold < 0:
        raise ValueError("num_obstacles and num_gold must be non-negative.")
    if num_obstacles + num_gold + 1 > rows * cols:
        raise ValueError("Too many items for the grid size (needs ≥ 1 empty cell for start).")

    rng = random.Random(seed)
    grid = [['.' for _ in range(cols)] for _ in range(rows)]

    cells = [(r, c) for r in range(rows) for c in range(cols)]
    rng.shuffle(cells)

    # Place obstacles
    for _ in range(num_obstacles):
        r, c = cells.pop()
        grid[r][c] = 'O'

    # Place gold
    for _ in range(num_gold):
        r, c = cells.pop()
        grid[r][c] = 'G'

    # Prefer start on empty if possible; otherwise any remaining cell
    start_candidates = [p for p in cells if grid[p[0]][p[1]] == '.'] or cells
    start_pos = rng.choice(start_candidates)

    return grid, start_pos

def generate_reachable_instance(
    rows, cols, num_obstacles, num_gold,
    seed=None, max_tries=1000
):
    """
    Generate purely random instances until one where ALL gold cells are reachable
    from the start (ignoring max steps, costs, etc.). Uses 'seed' to make the
    sequence of attempts deterministic; each attempt has its own sub-seed.

    Returns (grid, start_pos, tries) or (None, None, tries_if_exhausted).
    """
    rng = random.Random(seed)
    for attempt in range(1, max_tries + 1):
        attempt_seed = rng.getrandbits(64)  # deterministic sequence under given 'seed'
        grid, start = generate_random_instance(rows, cols, num_obstacles, num_gold, seed=attempt_seed)

        golds = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 'G']
        reachable = _bfs_reachable(grid, start)

        if all(g in reachable for g in golds):
            return grid, start, attempt

    return None, None, max_tries



def run_random_instance_mode():
    """
    Interactive flow to create an instance with optional seed and optional
    reachability requirement. After generation, it calls the solver so the user
    can test performance/visualization — the generator itself never calls the solver.
    """
    params = {
        "rows": 5, "cols": 5,
        "num_obstacles": 5,
        "num_gold": 3,
        "max_steps": 25
    }
    seed = None
    require_reachability = True

    costs = None
    max_cost = None

    print("\n--- Generate Random Instance ---")
    print("Enter parameters for the random instance (press Enter to use defaults).")
    try:
        params['rows'] = int(input(f"Enter number of rows ({params['rows']}): ") or params['rows'])
        params['cols'] = int(input(f"Enter number of columns ({params['cols']}): ") or params['cols'])
        params['num_obstacles'] = int(input(f"Enter number of obstacles ({params['num_obstacles']}): ") or params['num_obstacles'])
        params['num_gold'] = int(input(f"Enter number of gold pieces ({params['num_gold']}): ") or params['num_gold'])
        params['max_steps'] = int(input(f"Enter maximum steps ({params['max_steps']}): ") or params['max_steps'])

        seed_in = input("Enter a seed for reproducibility (blank for random): ").strip()
        seed = None if seed_in == "" else int(seed_in)

        req_in = input("Require reachability (all gold reachable from start)? (Y/n): ").strip().lower()
        require_reachability = (req_in != 'n')

        if input("Use cost constraints? (y/n): ").strip().lower() == 'y':
            print("Enter cost parameters:")
            max_cost = int(input("  Max total cost (e.g., 30): "))
            costs = {
                'move': int(input("  Cost for 'move' (e.g., 1): ")),
                'collect': int(input("  Cost for 'collect' (e.g., 1): ")),
                'stay': int(input("  Cost for 'stay' (e.g., 0): "))
            }

    except ValueError:
        print("Invalid input. Please enter integers only. Aborting.")
        return

    try:
        if require_reachability:
            grid, start_pos, tries = generate_reachable_instance(
                params['rows'], params['cols'],
                params['num_obstacles'], params['num_gold'],
                seed=seed, max_tries=1000
            )
            if grid is None:
                print("\nFailed to find a reachable instance within the attempt limit.")
                input("Press Enter to continue.")
                return
            print(f"\nFound a reachable instance after {tries} attempt(s).")
        else:
            grid, start_pos = generate_random_instance(
                params['rows'], params['cols'],
                params['num_obstacles'], params['num_gold'],
                seed=seed
            )

        print("\nGenerated Minefield:")
        for row in grid:
            print(" ".join(row))
        print(f"Start Position: {start_pos}, Max Steps: {params['max_steps']}")
        if max_cost is not None:
            print(f"Max Cost: {max_cost}")

        # Now let the actual solver try it (for testing/visualization only)
        solution, final_cost, _ = solve_minefield_plan(
            grid, start_pos, params['max_steps'],
            max_cost=max_cost, costs=costs
        )

        if solution:
            if final_cost is not None:
                print(f"\nSolver found a plan; total cost: {final_cost}")
            else:
                print("\nSolver found a plan.")
            if input("Press 1 to visualize the solution. Any other key to skip: ").strip() == '1':
                visualize_solution(solution, len(grid), len(grid[0]), final_cost=final_cost, costs=costs)
        else:
            print("\nSolver did not find a plan (even though all gold is reachable).")
            input("Press Enter to continue.")

    except Exception as e:
        print(f"Error during generation or solving: {e}")

def run_arbitrary_tests():
    """Runs a predefined suite of test cases to verify the solver's logic."""
    print("\n--- Running Arbitrary Test Cases ---")
    
    test_cases = [
        {
            "name": "Test 1: Impossible Path (Gold Blocked)",
            "grid": [['.', 'O', '.'], ['O', 'G', 'O'], ['.', 'O', '.']],
            "start_pos": (0, 0), "max_steps": 10, "expects_solution": False
        },
        {
            "name": "Test 2: Simple path with Collect",
            "grid": [['.', '.', '.'], ['O', 'G', 'O'], ['.', 'O', '.']],
            "start_pos": (0, 0), "max_steps": 10, "expects_solution": True
        },
        {
            "name": "Test 3: Skinny row with Gold",
            "grid": [['.', '.', '.', '.', 'G']],
            "start_pos": (0, 0), "max_steps": 10, "expects_solution": True
        },
        {
            "name": "Test 4: Skinny col with Gold",
            "grid": [['.'], ['.'], ['.'], ['.'], ['.'], ['G']],
            "start_pos": (0, 0), "max_steps": 10, "expects_solution": True
        },
        {
            "name": "Test 5: Max Steps Too Low",
            "grid": [['.', '.', 'G']],
            "start_pos": (0, 0), "max_steps": 2, "expects_solution": False
        },
        {
            "name": "Test 6: No Gold on Map",
            "grid": [['.', 'O', '.'], ['.', '.', '.']],
            "start_pos": (0, 0), "max_steps": 5, "expects_solution": True
        },
        {
            "name": "Test 7: Invalid Start Position (Obstacle)",
            "grid": [['.', 'O'], ['G', '.']],
            "start_pos": (0, 1), "max_steps": 5, "expects_solution": False
        },
        {
            "name": "Test 8: map with full of Gold",
            "grid": [['G', 'G', 'G'], ['G', 'G', 'G'], ['G', 'G', 'G']],
            "start_pos": (0, 0), "max_steps": 20, "expects_solution": True
        },
        {
            "name": "Test 9: Cost Constraint (Possible)",
            "grid": [['.', 'G']], "start_pos": (0, 0), "max_steps": 5,
            "costs": {'move': 1, 'collect': 1, 'stay': 0}, "max_cost": 3,
            "expects_solution": True
        },
        {
            "name": "Test 10: Cost Constraint (Impossible)",
            "grid": [['.', 'G']], "start_pos": (0, 0), "max_steps": 5,
            "costs": {'move': 2, 'collect': 2, 'stay': 0}, "max_cost": 3,
            "expects_solution": False
        },
    ]

    passed_count = 0
    total_solve_time = 0.0
    for test in test_cases:
        print(f"\nRunning: {test['name']}...")
        
        costs = test.get("costs")
        max_cost = test.get("max_cost")

        solution, _, solve_time = solve_minefield_plan(
            test["grid"], test["start_pos"], test["max_steps"],
            max_cost=max_cost, costs=costs
        )
        total_solve_time += solve_time
        has_solution = solution is not None
        
        if has_solution == test["expects_solution"]:
            print("Result: PASS")
            passed_count += 1
        else:
            print(f"Result: FAIL - Expected {test['expects_solution']}, but got {has_solution}")

    print("\n--- Test Summary ---")
    print(f"{passed_count}/{len(test_cases)} tests passed.")
    print(f"Total solver time for all tests: {total_solve_time:.4f} seconds.")
    input("Press Enter to return to the main menu.")
