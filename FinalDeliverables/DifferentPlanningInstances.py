import random
from visualizer import visualize_solution
from GoldsInMineField import solve_minefield_plan

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
    total_solve_time = 0
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

def generate_random_instance(rows, cols, num_obstacles, num_gold):
    """Generates a random grid with obstacles, gold, and a start position."""
    if num_obstacles + num_gold + 1 > rows * cols:
        print("Error: Too many items for the grid size.")
        return None, None

    grid = [['.' for _ in range(cols)] for _ in range(rows)]
    all_coords = [(r, c) for r in range(rows) for c in range(cols)]
    random.shuffle(all_coords)
    
    for _ in range(num_obstacles):
        grid[all_coords.pop()[0]][all_coords.pop()[1]] = 'O'
    for _ in range(num_gold):
        grid[all_coords.pop()[0]][all_coords.pop()[1]] = 'G'
    start_pos = all_coords.pop()
    
    return grid, start_pos

def run_random_instance_mode():
    """Handles user interaction for solving a randomly generated instance."""
    params = {
        "rows": 5, "cols": 5, "num_obstacles": 5,
        "num_gold": 3, "max_steps": 25
    }
    costs = None
    max_cost = None

    print("\n--- Generate Random Instance ---")
    print("Enter parameters for the random instance (press Enter to use defaults).")
    
    try:
        # User input for instance parameters
        params['rows'] = int(input(f"Enter number of rows ({params['rows']}): ") or params['rows'])
        params['cols'] = int(input(f"Enter number of columns ({params['cols']}): ") or params['cols'])
        params['num_obstacles'] = int(input(f"Enter number of obstacles ({params['num_obstacles']}): ") or params['num_obstacles'])
        params['num_gold'] = int(input(f"Enter number of gold pieces ({params['num_gold']}): ") or params['num_gold'])
        params['max_steps'] = int(input(f"Enter maximum steps ({params['max_steps']}): ") or params['max_steps'])

        if input("Do you want to use cost constraints? (y/n): ").lower() == 'y':
            print("Enter cost parameters:")
            max_cost = int(input("  Enter max total cost (e.g., 30): "))
            costs = {
                'move': int(input("  Enter cost for a 'move' action (e.g., 1): ")),
                'collect': int(input("  Enter cost for a 'collect' action (e.g., 1): ")),
                'stay': int(input("  Enter cost for a 'stay' action (e.g., 0): "))
            }

    except ValueError:
        print("Invalid input. Please enter integers only. Aborting.")
        return

    try:
        grid, start_pos = generate_random_instance(
            params['rows'], params['cols'], 
            params['num_obstacles'], params['num_gold']
        )
        if grid is None: return

        print("\nGenerated Minefield:")
        for row in grid: print(" ".join(row))
        print(f"Start Position: {start_pos}, Max Steps: {params['max_steps']}")
        if max_cost is not None:
            print(f"Max Cost: {max_cost}")

        solution, final_cost, _ = solve_minefield_plan(
            grid, start_pos, params['max_steps'], 
            max_cost=max_cost, costs=costs
        )

        if solution:
            if final_cost is not None:
                print(f"\nSolution found with a total cost of: {final_cost}!")
            else:
                print("\nSolution found!")
            
            if input("Press 1 to visualize the solution. Press any other key to continue: ") == '1':
                visualize_solution(solution, len(grid), len(grid[0]), final_cost=final_cost, costs=costs)
        else:
            input("\nNo solution found. Press Enter to continue.")
    except Exception as e:
        print(f"An error occurred during generation or solving: {e}")