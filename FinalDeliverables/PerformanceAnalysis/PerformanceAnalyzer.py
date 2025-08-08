# PerformanceAnalyzer.py

import sys
import os

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
except NameError:
    sys.path.append(os.getcwd())

from GoldsInMineField import solve_minefield_plan
from SampleMaker import (generate_benchmark_instances,
                         generate_single_grid_instance,
                         generate_grid_with_gold_count,
                         generate_grid_with_obstacles)

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib is not installed. Plotting will be disabled.")


def get_cost_params():
    """Helper function to get cost parameters from the user."""
    max_cost_input = None
    costs_input = None
    if input("Include cost constraints? (y/n): ").lower() == 'y':
        try:
            max_cost_input = int(input("  Enter max total cost (e.g., 30): "))
            costs_input = {
                'move': int(input("  Enter cost for 'move' (default: 1): ") or 1),
                'collect': int(input("  Enter cost for 'collect' (default: 1): ") or 1),
                'stay': int(input("  Enter cost for 'stay' (default: 0): ") or 0)
            }
        except ValueError:
            print("Invalid cost input. Continuing without cost constraints.")
            return None, None
    return max_cost_input, costs_input


def analyze_performance_by_grid_size():
    """Analyzes solver performance across multiple grid sizes, with optional cost constraints."""
    if not MATPLOTLIB_AVAILABLE:
        print("Cannot run analysis without matplotlib.")
        return

    try:
        k = int(input("Enter the maximum grid size to test (up to 40): "))
        if not (1 <= k <= 40):
            print("Error: Please enter a number between 1 and 40.")
            return
        goal_pos_choice = input("Place goal 'close' to start or 'far'? (c/f): ").lower()
        if goal_pos_choice not in ['c', 'f']:
            print("Invalid choice. Please enter 'c' for close or 'f' for far.")
            return
        goal_is_close = (goal_pos_choice == 'c')
        max_steps_input = int(input("Enter max steps (Warning: a low value may make the problem unsolvable): "))
        if max_steps_input < 1:
            print("Error: Max steps must be at least 1.")
            return

        max_cost, costs = get_cost_params()

    except ValueError:
        print("Error: Invalid input. Please enter an integer.")
        return

    BENCHMARK_SAMPLES = generate_benchmark_instances(
        goalClose=goal_is_close, max_size=k, max_steps=max_steps_input
    )
    
    success_sizes, success_times = [], []
    failure_sizes, failure_times = [], []
    
    # --- Build Plot Title ---
    title_parts = [
        f"vs. Grid Size",
        f"(Goal: {'Close' if goal_is_close else 'Far'}, Steps: {max_steps_input})"
    ]
    if max_cost is not None:
        title_parts.append(f"(Max Cost: {max_cost})")
    title = " ".join(title_parts)

    print(f"\n--- Analyzing Performance {title} ---")

    for i, sample in enumerate(BENCHMARK_SAMPLES):
        size = len(sample['grid'])
        grid = sample['grid']
        start_pos = sample['start_pos']
        max_steps = sample['max_steps']

        print(f"\nTesting grid {i+1}/{k} (Size: {size}x{size})...")
        
        print("Initial Grid:")
        for row in grid:
            print(f"  {' '.join(row)}")
        
        solution, final_cost, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps, max_cost=max_cost, costs=costs
        )
        
        status = ""
        if solution:
            status = "Success"
            if final_cost is not None:
                status += f" (Cost: {final_cost})"
            success_sizes.append(size)
            success_times.append(solve_time)
        else:
            status = "Failure (No Solution)"
            failure_sizes.append(size)
            failure_times.append(solve_time)

        print(f"  -> Result: {status}, Time: {solve_time:.4f} seconds")

    # --- Plotting Logic ---
    print("\nAnalysis complete. Generating plot...")
    plt.figure(figsize=(12, 7))
    all_sizes = sorted(success_sizes + failure_sizes)
    all_times = [t for s, t in sorted(zip(success_sizes + failure_sizes, success_times + failure_times))]
    if all_sizes:
        plt.plot(all_sizes, all_times, color='gray', linestyle='--', alpha=0.6, label='_nolegend_')
    plt.scatter(success_sizes, success_times, color='blue', zorder=5, label='Solution Found')
    plt.scatter(failure_sizes, failure_times, color='red', zorder=5, label='No Solution Found')
    plt.title(f"Solver Performance {title.replace(') (', ', ')}")
    plt.xlabel("Grid Size (N x N)")
    plt.ylabel("Solve Time (seconds)")
    plt.grid(True)
    plt.xticks(range(1, k + 1))
    plt.legend()
    plt.tight_layout()
    plt.show()


def analyze_performance_by_max_steps():
    """Analyzes performance by iterating max_steps (k), with optional cost constraints."""
    if not MATPLOTLIB_AVAILABLE:
        print("Cannot run analysis without matplotlib.")
        return

    try:
        size = int(input("Enter the desired grid size (e.g., 5): "))
        if size < 1:
            print("Error: Grid size must be at least 1.")
            return
        goal_pos_choice = input("Place goal 'close' or 'far'? (c/f): ").lower()
        if goal_pos_choice not in ['c', 'f']:
            return
        goal_is_close = (goal_pos_choice == 'c')
        k_max = int(input("Enter the max 'k' to test up to: "))
        if k_max < 1:
            return
        
        max_cost, costs = get_cost_params()

    except ValueError:
        print("Error: Invalid input.")
        return

    sample = generate_single_grid_instance(size, goal_is_close)
    grid, start_pos = sample['grid'], sample['start_pos']

    title_parts = [
        f"vs. Max Steps (k) on {size}x{size} Grid"
    ]
    if max_cost is not None:
        title_parts.append(f"(Max Cost: {max_cost})")
    title = " ".join(title_parts)

    print(f"\n--- Analyzing Performance {title} ---")
    print("Initial Grid:")
    for row in grid:
        print(f"  {' '.join(row)}")
    
    success_k, success_times = [], []
    failure_k, failure_times = [], []

    for k in range(1, k_max + 1):
        print(f"\nTesting with max_steps = {k}...")
        solution, final_cost, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps=k, max_cost=max_cost, costs=costs
        )
        status = ""
        if solution:
            status = "Success"
            if final_cost is not None:
                status += f" (Cost: {final_cost})"
            success_k.append(k)
            success_times.append(solve_time)
        else:
            status = "Failure (No Solution)"
            failure_k.append(k)
            failure_times.append(solve_time)
        print(f"  -> Result: {status}, Time: {solve_time:.4f} seconds")

    plt.figure(figsize=(12, 7))
    all_k = sorted(success_k + failure_k)
    all_times = [t for s, t in sorted(zip(success_k + failure_k, success_times + failure_times))]
    if all_k:
        plt.plot(all_k, all_times, color='gray', linestyle='--', alpha=0.6, label='_nolegend_')
    plt.scatter(success_k, success_times, color='green', zorder=5, label='Solution Found')
    plt.scatter(failure_k, failure_times, color='red', zorder=5, label='No Solution Found')
    plt.title(f"Solver Performance {title.replace(') (', ', ')}")
    plt.xlabel("Max Steps (k)")
    plt.ylabel("Solve Time (seconds)")
    plt.grid(True)
    plt.xticks(range(1, k_max + 1))
    plt.legend()
    plt.tight_layout()
    plt.show()


def analyze_performance_by_gold_count():
    """Analyzes performance by iterating gold count, with optional cost constraints."""
    if not MATPLOTLIB_AVAILABLE:
        print("Cannot run analysis without matplotlib.")
        return
        
    try:
        size = int(input("Enter the desired grid size (e.g., 5): "))
        if size < 1:
            return
        max_steps = int(input("Enter the fixed max steps (k): "))
        if max_steps < 1:
            return
        max_possible_gold = size * size - 1
        gold_prompt = (f"Enter max gold count to test up to (max possible is {max_possible_gold}): ")
        max_gold_input = int(input(gold_prompt))
        if max_gold_input < 1:
            return
        max_gold_input = min(max_gold_input, max_possible_gold)
        place_gold_close = input("Place gold 'close' or 'far'? (c/f): ").lower() == 'c'

        max_cost, costs = get_cost_params()

    except ValueError:
        print("Error: Invalid input.")
        return

    title_parts = [
        f"vs. Gold Count on {size}x{size} Grid",
        f"(Steps: {max_steps})"
    ]
    if max_cost is not None:
        title_parts.append(f"(Max Cost: {max_cost})")
    title = " ".join(title_parts)
        
    print(f"\n--- Analyzing Performance {title} ---")
    
    success_golds, success_times = [], []
    failure_golds, failure_times = [], []
    
    for g_count in range(1, max_gold_input + 1):
        print(f"\nTesting with {g_count} gold piece(s)...")
        sample = generate_grid_with_gold_count(size, g_count, place_gold_close)
        grid, start_pos = sample['grid'], sample['start_pos']
        print("Generated Grid:")
        for row in grid:
            print(f"  {' '.join(row)}")
        
        solution, final_cost, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps, max_cost=max_cost, costs=costs
        )
        
        status = ""
        if solution:
            status = "Success"
            if final_cost is not None:
                status += f" (Cost: {final_cost})"
            success_golds.append(g_count)
            success_times.append(solve_time)
        else:
            status = "Failure (No Solution)"
            failure_golds.append(g_count)
            failure_times.append(solve_time)
            
        print(f"  -> Result: {status}, Time: {solve_time:.4f} seconds")

    plt.figure(figsize=(12, 7))
    all_g = sorted(success_golds + failure_golds)
    all_times = [t for g, t in sorted(zip(success_golds + failure_golds, success_times + failure_times))]
    if all_g:
        plt.plot(all_g, all_times, color='gray', linestyle='--', alpha=0.6, label='_nolegend_')
    plt.scatter(success_golds, success_times, color='blue', zorder=5, label='Solution Found')
    plt.scatter(failure_golds, failure_times, color='red', zorder=5, label='No Solution Found')
    plt.title(f"Solver Performance {title.replace(') (', ', ')}")
    plt.xlabel("Number of Gold Pieces")
    plt.ylabel("Solve Time (seconds)")
    plt.grid(True)
    plt.xticks(range(1, max_gold_input + 1))
    plt.legend()
    plt.tight_layout()
    plt.show()


def analyze_performance_by_obstacle_density():
    """Analyzes performance by iterating obstacle count, with optional cost constraints."""
    if not MATPLOTLIB_AVAILABLE:
        print("Cannot run analysis without matplotlib.")
        return

    try:
        size = int(input("Enter grid size (e.g., 5): "))
        if size < 2:
            print("Error: Grid size must be at least 2 for this analysis.")
            return
        max_steps = int(input("Enter fixed max steps (k): "))
        if max_steps < 1:
            return
        is_random = input("Obstacle placement: 'random' or 'predefined'? (r/p): ").lower() == 'r'
        
        max_possible = size * size - 2 if is_random else (size - 1) * size
        prompt = f"Enter max obstacle count (max possible is {max_possible}): "
        max_obs_input = int(input(prompt))
        if max_obs_input < 0:
            return
        max_obs_input = min(max_obs_input, max_possible)

        max_cost, costs = get_cost_params()

    except ValueError:
        print("Error: Invalid input.")
        return
        
    placement_str = "Random" if is_random else "Predefined"
    title_parts = [
        f"vs. Obstacle Density on {size}x{size} Grid",
        f"({placement_str})"
    ]
    if max_cost is not None:
        title_parts.append(f"(Max Cost: {max_cost})")
    title = " ".join(title_parts)

    print(f"\n--- Analyzing Performance {title} ---")
    
    success_obs, success_times = [], []
    failure_obs, failure_times = [], []
    
    for o_count in range(max_obs_input + 1):
        print(f"\nTesting with {o_count} obstacle(s)...")
        sample = generate_grid_with_obstacles(size, o_count, is_random)
        grid, start_pos = sample['grid'], sample['start_pos']
        print("Generated Grid:")
        for row in grid:
            print(f"  {' '.join(row)}")
        
        solution, final_cost, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps, max_cost=max_cost, costs=costs
        )
        
        status = ""
        if solution:
            status = "Success"
            if final_cost is not None:
                status += f" (Cost: {final_cost})"
            success_obs.append(o_count)
            success_times.append(solve_time)
        else:
            status = "Failure (No Solution)"
            failure_obs.append(o_count)
            failure_times.append(solve_time)
            
        print(f"  -> Result: {status}, Time: {solve_time:.4f} seconds")

    plt.figure(figsize=(12, 7))
    all_o = sorted(success_obs + failure_obs)
    all_times = [t for o, t in sorted(zip(success_obs + failure_obs, success_times + failure_times))]
    if all_o or o_count == 0:
        plt.plot(all_o, all_times, color='gray', linestyle='--', alpha=0.6, label='_nolegend_')
    plt.scatter(success_obs, success_times, color='blue', zorder=5, label='Solution Found')
    plt.scatter(failure_obs, failure_times, color='red', zorder=5, label='No Solution Found')
    plt.title(f"Solver Performance {title.replace(') (', ', ')}")
    plt.xlabel("Number of Obstacles")
    plt.ylabel("Solve Time (seconds)")
    plt.grid(True)
    plt.xticks(range(max_obs_input + 1))
    plt.legend()
    plt.tight_layout()
    plt.show()


def main():
    """Main menu to run different analysis modes."""
    print("--- GoldsInMineField Performance Analyzer ---")

    while True:
        print("\nPlease choose an analysis type:")
        print("1. Analyze performance by Grid Size.")
        print("2. Analyze performance by Max Steps (k) for a single grid.")
        print("3. Analyze performance by Gold Count for a single grid size.")
        print("4. Analyze performance by Obstacle Density for a single grid size.")
        print("0. Exit.")
        choice = input("Enter your choice: ")

        if choice == '1':
            analyze_performance_by_grid_size()
        elif choice == '2':
            analyze_performance_by_max_steps()
        elif choice == '3':
            analyze_performance_by_gold_count()
        elif choice == '4':
            analyze_performance_by_obstacle_density()
        elif choice == '0':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()  