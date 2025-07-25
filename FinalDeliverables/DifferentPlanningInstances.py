
import random
from visualizer import visualize_solution
from GoldsInMineField import goldsInMineFieldSolver


def run_arbitrary_tests():
    """
    Runs a predefined suite of test cases to verify the solver's logic.
    """
    print("\n--- Running Arbitrary Test Cases ---")
    
    # Integrated your new test cases
    test_cases = [
        {
            "name": "Test 1: Impossible Path (Gold Blocked)",
            "grid": [
                ['.', 'O', '.'],
                ['O', 'G', 'O'],
                ['.', 'O', '.']
            ],
            "start_pos": (0, 0),
            "max_steps": 10,
            "expects_solution": False
        },
        {
            "name": "Test 2: Simple path with Collect",
            "grid": [
                ['.', '.', '.'],
                ['O', 'G', 'O'],
                ['.', 'O', '.']
            ],
            "start_pos": (0, 0),
            "max_steps": 10,
            "expects_solution": True
        },
        {
            "name": "Test 3: Skinny row with Gold",
            "grid": [
                ['.', '.', '.', '.', 'G']
            ],
            "start_pos": (0, 0),
            "max_steps": 10,
            "expects_solution": True
        },
        {
            "name": "Test 4: Skinny col with Gold",
            "grid": [
                ['.'], ['.'], ['.'], ['.'], ['.'], ['G']
            ],
            "start_pos": (0, 0),
            "max_steps": 10,
            "expects_solution": True
        },
        {
            "name": "Test 5: Max Steps Too Low",
            "grid": [
                ['.', '.', 'G']
            ],
            "start_pos": (0, 0),
            "max_steps": 2, # Needs 3 (move, move, collect)
            "expects_solution": False
        },
        {
            "name": "Test 6: No Gold on Map",
            "grid": [
                ['.', 'O', '.'],
                ['.', '.', '.']
            ],
            "start_pos": (0, 0),
            "max_steps": 5,
            "expects_solution": True 
        },
        {
            "name": "Test 7: Invalid Start Position (Obstacle)",
            "grid": [
                ['.', 'O'],
                ['G', '.']
            ],
            "start_pos": (0, 1),
            "max_steps": 5,
            "expects_solution": False 
        },
        {
            "name": "Test 8: map with full of Gold",
            "grid": [
                ['G', 'G', 'G'],
                ['G', 'G', 'G'],
                ['G', 'G', 'G'],
            ],
            "start_pos": (0, 0),
            "max_steps": 20,
            "expects_solution": True
        },
    ]

    passed_count = 0
    for i, test in enumerate(test_cases):
        print(f"\nRunning: {test['name']}...")
        solution = goldsInMineFieldSolver(test["grid"], test["start_pos"], test["max_steps"])
        
        has_solution = solution is not None
        
        if has_solution == test["expects_solution"]:
            print(f"Result: PASS")
            passed_count += 1
        else:
            print(f"Result: FAIL")
            print(f"  - Expected solution: {test['expects_solution']}, but got: {has_solution}")

    print(f"\n--- Test Summary ---")
    print(f"{passed_count}/{len(test_cases)} tests passed.")
    input("Press Enter to return to the main menu.")



def generate_random_instance(rows, cols, num_obstacles, num_gold):
    """
    Generates a random grid with obstacles, gold, and a start position.
    
    Returns:
        A tuple (grid, start_pos) or (None, None) if generation is impossible.
    """
    if num_obstacles + num_gold + 1 > rows * cols:
        print("Error: Too many items for the grid size.")
        return None, None

    # Create an empty grid
    grid = [['.' for _ in range(cols)] for _ in range(rows)]
    
    # Get all possible coordinates
    all_coords = [(r, c) for r in range(rows) for c in range(cols)]
    random.shuffle(all_coords)
    
    # Place obstacles
    for _ in range(num_obstacles):
        r, c = all_coords.pop()
        grid[r][c] = 'O'
        
    # Place gold
    for _ in range(num_gold):
        r, c = all_coords.pop()
        grid[r][c] = 'G'
        
    # Place start position
    start_pos = all_coords.pop()
    
    return grid, start_pos

def run_random_instance_mode():
    """
    Handles the user interaction for running a randomly generated instance.
    """
    # --- Default Values ---
    params = {
        "rows": 10,
        "cols": 10,
        "num_obstacles": 30,
        "num_gold": 10,
        "max_steps": 100
    }

    print("\n--- Generate Random Instance ---")
    print("Default parameters:")
    print(f"  - Grid Size: {params['rows']}x{params['cols']}")
    print(f"  - Obstacles: {params['num_obstacles']}")
    print(f"  - Gold: {params['num_gold']}")
    print(f"  - Max Steps: {params['max_steps']}")

    modify = input("Do you want to modify these values? (y/n): ").lower()

    if modify == 'y':
        try:
            print("Enter new values (press Enter to keep default):")
            rows_in = input(f"  Enter number of rows ({params['rows']}): ")
            if rows_in: params['rows'] = int(rows_in)
            
            cols_in = input(f"  Enter number of columns ({params['cols']}): ")
            if cols_in: params['cols'] = int(cols_in)

            obstacles_in = input(f"  Enter number of obstacles ({params['num_obstacles']}): ")
            if obstacles_in: params['num_obstacles'] = int(obstacles_in)

            gold_in = input(f"  Enter number of gold pieces ({params['num_gold']}): ")
            if gold_in: params['num_gold'] = int(gold_in)

            steps_in = input(f"  Enter maximum steps allowed ({params['max_steps']}): ")
            if steps_in: params['max_steps'] = int(steps_in)

        except ValueError:
            print("Invalid input. Using default values.")
    
    # --- Generate and Solve ---
    try:
        grid, start_pos = generate_random_instance(
            params['rows'], 
            params['cols'], 
            params['num_obstacles'], 
            params['num_gold']
        )

        if grid is None:
            return

        print("\nGenerated Minefield:")
        for row in grid:
            print(" ".join(row))
        print(f"Start Position: {start_pos}")
        print(f"Max Steps: {params['max_steps']}")

        solution = goldsInMineFieldSolver(grid, start_pos, params['max_steps'])

        if solution:
            req = input("\nSolution found! Press 1 to visualize the solution. Press any other key to continue: ")
            if req == '1':
                visualize_solution(solution, len(grid), len(grid[0]))
        else:
            input("\nNo solution found. Press Enter to continue.")

    except Exception as e:
        print(f"An error occurred during generation or solving: {e}")




