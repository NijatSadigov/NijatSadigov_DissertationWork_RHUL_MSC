import sys
import os
import subprocess
import glob
import csv
import math
from pddl_generator import generate_pddl_problem
import matplotlib.pyplot as plt

# --- CSV Helper ---
def _append_csv_result(csv_path, row, header):
    write_header = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header)
        if write_header:
            w.writeheader()
        w.writerow(row)

# --- System Path Setup ---
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
except NameError:
    sys.path.append(os.getcwd())

# --- Project Imports ---
from GoldsInMineField import solve_minefield_plan
from DifferentPlanningInstances import (generate_reachable_instance, generate_random_instance)


# ==============================================================================
# ===  HELPER FUNCTIONS ==============================================
# ==============================================================================

def _get_pddl_instance_generation_params():
    """Prompts user for seed for PDDL benchmark reproducibility."""
    seed_in = input("Enter a seed for reproducibility (blank for random): ").strip()
    seed = None if seed_in == "" else int(seed_in)
    return seed, True

def _get_z3_analysis_params():
    """Prompts user for common Z3 analysis parameters: time limit, seed, and reachability."""
    try:
        time_limit_in = input("Enter a time limit per run in seconds (default: 120): ").strip()
        time_limit = 120 if time_limit_in == "" else int(time_limit_in)
        if time_limit <= 0:
            print("Time limit must be positive. Using default of 120s.")
            time_limit = 120
    except ValueError:
        print("Invalid number. Using default of 120s.")
        time_limit = 120

    seed_in = input("Enter a seed for reproducibility (blank for random): ").strip()
    seed = None if seed_in == "" else int(seed_in)
    
    req_in = input("Require reachability (all gold reachable from start)? (Y/n): ").strip().lower()
    require_reachability = (req_in != 'n')
    
    return time_limit, seed, require_reachability


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

def _plot_performance_results(title, x_label, success_data, failure_data, x_ticks_range, cancellation_reason=None):
    """
    Generates and displays a performance plot using matplotlib.

    Args:
        title (str): The main title for the plot.
        x_label (str): The label for the x-axis.
        success_data (tuple): A tuple of (x_values, y_values) for successful runs.
        failure_data (tuple): A tuple of (x_values, y_values) for failed runs.
        x_ticks_range (range): The range of ticks to display on the x-axis.
        cancellation_reason (str, optional): A message to display if the analysis was cut short.
    """


    plt.figure(figsize=(12, 8))
    
    success_x, success_y = success_data
    failure_x, failure_y = failure_data

    all_x = sorted(list(set(success_x + failure_x)))
    if all_x:
        point_map = {x: y for x, y in zip(success_x, success_y)}
        point_map.update({x: y for x, y in zip(failure_x, failure_y)})
        all_y = [point_map[x] for x in all_x]
        plt.plot(all_x, all_y, color='gray', linestyle='--', alpha=0.6, label='_nolegend_')

    plt.scatter(success_x, success_y, color='blue', zorder=5, label='Solution Found')
    plt.scatter(failure_x, failure_y, color='red', zorder=5, label='No Solution / Timeout')
    
    plt.title(f"Solver Performance\n{title}")
    plt.xlabel(x_label)
    plt.ylabel("Solve Time (seconds)")
    plt.grid(True)
    if x_ticks_range:
        plt.xticks(x_ticks_range)
    plt.legend()

    if cancellation_reason:
        plt.figtext(0.5, 0.01, cancellation_reason, wrap=True, ha="center", fontsize=9, color='red', style='italic')
        plt.tight_layout(rect=[0, 0.05, 1, 1]) 
    else:
        plt.tight_layout()
        
    plt.show()





# ==============================================================================
# === MAIN ANALYSIS FUNCTIONS ==================================================
# ==============================================================================

def analyze_performance_by_grid_size():
    """
    Analyzes solver performance by iterating through grid sizes.
    Each grid is randomly generated with 1 gold and 1 obstacle.
    """

    try:
        k = int(input("Enter the maximum grid size to test (e.g., 10): "))
        if not (2 <= k <= 40):
            print("Error: Please enter a number between 2 and 40.")
            return
        
        max_steps_input = int(input("Enter max steps (Warning: a low value may make it unsolvable): "))
        if max_steps_input < 1:
            print("Error: Max steps must be at least 1.")
            return

        time_limit, seed, require_reachability = _get_z3_analysis_params()
        max_cost, costs = get_cost_params()

    except ValueError:
        print("Error: Invalid input. Please enter an integer.")
        return

    success_sizes, success_times = [], []
    failure_sizes, failure_times = [], []
    cancellation_reason = None
    
    title_parts = [
        f"vs. Grid Size (Random Instances)",
        f"(1 Gold, 1 Obstacle, Steps: {max_steps_input})"
    ]
    if max_cost is not None:
        title_parts.append(f"(Max Cost: {max_cost})")
    title = "\n".join(title_parts)

    print(f"\n--- Analyzing Performance {title.replace('\n', ' ')} ---")
    print(f"Time limit per run set to {time_limit} seconds.")
    
    current_seed = seed
    for size in range(2, k + 1):
        print(f"\nTesting grid size {size}x{size}...")

        grid, start_pos = None, None
        if require_reachability:
            grid, start_pos, tries = generate_reachable_instance(
                size, size, num_obstacles=1, num_gold=1, seed=current_seed
            )
            if grid:
                print(f"  Generated a reachable instance in {tries} attempt(s).")
            else:
                print("  Failed to generate a reachable instance. Skipping this size.")
                if seed is not None: current_seed += 1
                continue
        else:
            grid, start_pos = generate_random_instance(
                size, size, num_obstacles=1, num_gold=1, seed=current_seed
            )
            print("  Generated a random instance.")

        if seed is not None:
            current_seed += 1

        print("Initial Grid:")
        for row in grid:
            print(f"  {' '.join(row)}")
        
        solution, final_cost, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps_input, max_cost=max_cost, costs=costs
        )
        
        if solve_time > time_limit:
            cancellation_reason = (
                f"Analysis stopped at grid size {size}x{size}. "
                f"Solve time ({solve_time:.2f}s) exceeded the limit of {time_limit}s."
            )
            print(f"  -> Result: TIMEOUT, Time: {solve_time:.4f} seconds")
            print(f"\n{cancellation_reason}")
            failure_sizes.append(size)
            failure_times.append(solve_time)
            break

        if solution:
            print(f"  -> Result: Success, Time: {solve_time:.4f} seconds")
            success_sizes.append(size)
            success_times.append(solve_time)
        else:
            print(f"  -> Result: Failure, Time: {solve_time:.4f} seconds")
            failure_sizes.append(size)
            failure_times.append(solve_time)

    print("\nAnalysis complete. Generating plot...")
    _plot_performance_results(
        title=title,
        x_label="Grid Size (N x N)",
        success_data=(success_sizes, success_times),
        failure_data=(failure_sizes, failure_times),
        x_ticks_range=range(2, k + 1),
        cancellation_reason=cancellation_reason
    )

def analyze_performance_by_max_steps():
    """
    Analyzes performance by iterating max_steps (k) on a single,
    randomly generated grid.
    """
    
    try:
        size = int(input("Enter the desired grid size (e.g., 5): "))
        num_gold = int(input("Enter the number of gold pieces: "))
        num_obstacles = int(input("Enter the number of obstacles: "))
        
        if num_gold + num_obstacles + 1 > size * size:
            print("Error: Too many items for the grid size. Aborting.")
            return

        k_max = int(input("Enter the max 'k' (max_steps) to test up to: "))
        if k_max < 1:
            print("Error: Max 'k' must be at least 1.")
            return
        
        time_limit, seed, require_reachability = _get_z3_analysis_params()
        max_cost, costs = get_cost_params()

    except ValueError:
        print("Error: Invalid input.")
        return

    print("\nGenerating a random instance for the analysis...")
    grid, start_pos = None, None
    if require_reachability:
        grid, start_pos, tries = generate_reachable_instance(
            size, size, num_obstacles, num_gold, seed=seed
        )
        if not grid:
            print("Failed to generate a reachable instance. Aborting analysis.")
            return
        print(f"  Generated a reachable instance in {tries} attempt(s).")
    else:
        grid, start_pos = generate_random_instance(
            size, size, num_obstacles, num_gold, seed=seed
        )
        print("  Generated a random instance.")

    title_parts = [
        f"vs. Max Steps (k) on {size}x{size} Grid",
        f"({num_gold} Gold, {num_obstacles} Obstacles)"
    ]
    if max_cost is not None:
        title_parts.append(f"(Max Cost: {max_cost})")
    title = "\n".join(title_parts)

    print(f"\n--- Analyzing Performance {title.replace('\n', ' ')} ---")
    print(f"Time limit per run set to {time_limit} seconds.")
    print("Using this Grid for all tests:")
    for row in grid:
        print(f"  {' '.join(row)}")
    
    success_k, success_times = [], []
    failure_k, failure_times = [], []
    cancellation_reason = None

    for k in range(1, k_max + 1):
        print(f"\nTesting with max_steps = {k}...")
        solution, _, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps=k, max_cost=max_cost, costs=costs
        )

        if solve_time > time_limit:
            cancellation_reason = (
                f"Analysis stopped at max_steps={k}. "
                f"Solve time ({solve_time:.2f}s) exceeded the limit of {time_limit}s."
            )
            print(f"  -> Result: TIMEOUT, Time: {solve_time:.4f} seconds")
            print(f"\n{cancellation_reason}")
            failure_k.append(k)
            failure_times.append(solve_time)
            break

        if solution:
            print(f"  -> Result: Success, Time: {solve_time:.4f} seconds")
            success_k.append(k)
            success_times.append(solve_time)
        else:
            print(f"  -> Result: Failure, Time: {solve_time:.4f} seconds")
            failure_k.append(k)
            failure_times.append(solve_time)

    print("\nAnalysis complete. Generating plot...")
    _plot_performance_results(
        title=title,
        x_label="Max Steps (k)",
        success_data=(success_k, success_times),
        failure_data=(failure_k, failure_times),
        x_ticks_range=range(1, k_max + 1),
        cancellation_reason=cancellation_reason
    )

def analyze_performance_by_gold_count():
    """
    Analyzes performance by iterating the gold count. For each count,
    a new random instance is generated with a fixed number of obstacles.
    """
    
    try:
        size = int(input("Enter the desired grid size (e.g., 8): "))
        num_obstacles = int(input("Enter the fixed number of obstacles: "))
        max_steps = int(input("Enter the fixed max steps (k): "))
        
        max_possible_gold = size * size - 1 - num_obstacles
        if max_possible_gold < 1:
            print("Error: Not enough space for even one gold with the given obstacles.")
            return

        gold_prompt = (f"Enter max gold count to test up to (max possible is {max_possible_gold}): ")
        max_gold_input = int(input(gold_prompt))
        max_gold_input = min(max_gold_input, max_possible_gold)
        if max_gold_input < 1:
            print("Error: Max gold must be at least 1.")
            return

        time_limit, seed, require_reachability = _get_z3_analysis_params()
        max_cost, costs = get_cost_params()

    except ValueError:
        print("Error: Invalid input.")
        return

    title_parts = [
        f"vs. Gold Count on {size}x{size} Grid",
        f"(Steps: {max_steps}, Obstacles: {num_obstacles})"
    ]
    if max_cost is not None:
        title_parts.append(f"(Max Cost: {max_cost})")
    title = "\n".join(title_parts)
        
    print(f"\n--- Analyzing Performance {title.replace('\n', ' ')} ---")
    print(f"Time limit per run set to {time_limit} seconds.")
    
    success_golds, success_times = [], []
    failure_golds, failure_times = [], []
    cancellation_reason = None
    
    current_seed = seed
    for g_count in range(1, max_gold_input + 1):
        print(f"\nTesting with {g_count} gold piece(s)...")
        
        grid, start_pos = None, None
        if require_reachability:
            grid, start_pos, tries = generate_reachable_instance(
                size, size, num_obstacles, g_count, seed=current_seed
            )
            if not grid:
                print("  Failed to generate a reachable instance. Skipping this count.")
                if seed is not None: current_seed += 1
                continue
            print(f"  Generated a reachable instance in {tries} attempt(s).")
        else:
            grid, start_pos = generate_random_instance(
                size, size, num_obstacles, g_count, seed=current_seed
            )
            print("  Generated a random instance.")

        if seed is not None:
            current_seed += 1

        print("Generated Grid:")
        for row in grid:
            print(f"  {' '.join(row)}")
        
        solution, _, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps, max_cost=max_cost, costs=costs
        )
        
        if solve_time > time_limit:
            cancellation_reason = (
                f"Analysis stopped at {g_count} gold pieces. "
                f"Solve time ({solve_time:.2f}s) exceeded the limit of {time_limit}s."
            )
            print(f"  -> Result: TIMEOUT, Time: {solve_time:.4f} seconds")
            print(f"\n{cancellation_reason}")
            failure_golds.append(g_count)
            failure_times.append(solve_time)
            break

        if solution:
            print(f"  -> Result: Success, Time: {solve_time:.4f} seconds")
            success_golds.append(g_count)
            success_times.append(solve_time)
        else:
            print(f"  -> Result: Failure, Time: {solve_time:.4f} seconds")
            failure_golds.append(g_count)
            failure_times.append(solve_time)
            
    print("\nAnalysis complete. Generating plot...")
    _plot_performance_results(
        title=title,
        x_label="Number of Gold Pieces",
        success_data=(success_golds, success_times),
        failure_data=(failure_golds, failure_times),
        x_ticks_range=range(1, max_gold_input + 1),
        cancellation_reason=cancellation_reason
    )

def analyze_performance_by_obstacle_density():
    """
    Analyzes performance by iterating obstacle count. For each count,
    a new random instance is generated with a fixed number of gold pieces.
    """
    
    try:
        size = int(input("Enter grid size (e.g., 8): "))
        num_gold = int(input("Enter the fixed number of gold pieces: "))
        max_steps = int(input("Enter fixed max steps (k): "))
        
        max_possible_obs = size * size - 1 - num_gold
        if max_possible_obs < 0:
            print("Error: Not enough space for obstacles with the given gold count.")
            return

        prompt = f"Enter max obstacle count to test up to (max possible is {max_possible_obs}): "
        max_obs_input = int(input(prompt))
        max_obs_input = min(max_obs_input, max_possible_obs)
        if max_obs_input < 0:
            print("Error: Max obstacles must be non-negative.")
            return

        time_limit, seed, require_reachability = _get_z3_analysis_params()
        max_cost, costs = get_cost_params()

    except ValueError:
        print("Error: Invalid input.")
        return
        
    title_parts = [
        f"vs. Obstacle Count on {size}x{size} Grid",
        f"(Steps: {max_steps}, Gold: {num_gold})"
    ]
    if max_cost is not None:
        title_parts.append(f"(Max Cost: {max_cost})")
    title = "\n".join(title_parts)

    print(f"\n--- Analyzing Performance {title.replace('\n', ' ')} ---")
    print(f"Time limit per run set to {time_limit} seconds.")
    
    success_obs, success_times = [], []
    failure_obs, failure_times = [], []
    cancellation_reason = None
    
    current_seed = seed
    for o_count in range(max_obs_input + 1):
        print(f"\nTesting with {o_count} obstacle(s)...")
        
        grid, start_pos = None, None
        if require_reachability:
            grid, start_pos, tries = generate_reachable_instance(
                size, size, o_count, num_gold, seed=current_seed
            )
            if not grid:
                print("  Failed to generate a reachable instance. Skipping this count.")
                if seed is not None: current_seed += 1
                continue
            print(f"  Generated a reachable instance in {tries} attempt(s).")
        else:
            grid, start_pos = generate_random_instance(
                size, size, o_count, num_gold, seed=current_seed
            )
            print("  Generated a random instance.")

        if seed is not None:
            current_seed += 1

        print("Generated Grid:")
        for row in grid:
            print(f"  {' '.join(row)}")
        
        solution, _, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps, max_cost=max_cost, costs=costs
        )
        
        if solve_time > time_limit:
            cancellation_reason = (
                f"Analysis stopped at {o_count} obstacles. "
                f"Solve time ({solve_time:.2f}s) exceeded the limit of {time_limit}s."
            )
            print(f"  -> Result: TIMEOUT, Time: {solve_time:.4f} seconds")
            print(f"\n{cancellation_reason}")
            failure_obs.append(o_count)
            failure_times.append(solve_time)
            break
        
        if solution:
            print(f"  -> Result: Success, Time: {solve_time:.4f} seconds")
            success_obs.append(o_count)
            success_times.append(solve_time)
        else:
            print(f"  -> Result: Failure, Time: {solve_time:.4f} seconds")
            failure_obs.append(o_count)
            failure_times.append(solve_time)
            
    print("\nAnalysis complete. Generating plot...")
    _plot_performance_results(
        title=title,
        x_label="Number of Obstacles",
        success_data=(success_obs, success_times),
        failure_data=(failure_obs, failure_times),
        x_ticks_range=range(max_obs_input + 1),
        cancellation_reason=cancellation_reason
    )
def cost_effect_performance_analyser():
    """
    Analyzes and compares solver performance under different cost scenarios
    by iterating through progressively larger grid sizes.
    """
    

    density_map = {'r': 0.10, 'c': 0.30, 'cr': 0.45}
    density_names = {'r': 'Rare', 'c': 'Common', 'cr': 'Crowded'}

    try:
        print("\n--- Configure Cost Effect Benchmark ---")
        max_size = int(input("Enter the maximum grid size to test (e.g., 10): ") or 10)
        
        gold_density_key = input("Gold density [r]are/[c]ommon/[cr]owded (default: c): ").strip().lower() or 'c'
        obs_density_key = input("Obstacle density [r]are/[c]ommon/[cr]owded (default: c): ").strip().lower() or 'c'

        if gold_density_key not in density_map or obs_density_key not in density_map:
            print("Invalid density key. Please use 'r', 'c', or 'cr'.")
            return
        
        max_steps = int(input("Enter fixed max steps (k) for all runs (e.g., 30): ") or 30)
        time_limit, seed, _ = _get_z3_analysis_params() 

        print("\n--- Defining Cost Scenarios ---")
        print("Three scenarios will be tested: No Cost, a High-Cost (generous) budget, and a Low-Cost (restrictive) budget.")
        generous_max_cost = int(input("Enter the max cost for the 'High-Cost Budget' scenario (e.g., 30): ") or 30)
        low_max_cost = int(input("Enter the max cost for the 'Low-Cost Budget' scenario (e.g., 5): ") or 5)
        
        print("\nEnter the costs for actions:")
        move_cost = int(input("  Cost for 'move' (e.g., 1): ") or 1)
        collect_cost = int(input("  Cost for 'collect' (e.g., 2): ") or 2)
        stay_cost = int(input("  Cost for 'stay' (e.g., 0): ") or 0)
        
        costs_input = {'move': move_cost, 'collect': collect_cost, 'stay': stay_cost}

    except ValueError:
        print("Error: Invalid input. Please enter integers only.")
        return

    print(f"\nGenerating {max_size-1} benchmark instances...")
    benchmark_instances = []
    current_seed = seed
    for size in range(2, max_size + 1):
        total_cells = size * size
        num_gold = max(1, math.floor(total_cells * density_map[gold_density_key]))
        num_obstacles = math.floor(total_cells * density_map[obs_density_key])

        if num_gold + num_obstacles >= total_cells:
            print(f"Warning: At size {size}x{size}, item count exceeds cell count. Skipping.")
            continue
            
        print(f"  Generating size {size}x{size} (Gold: {num_gold}, Obs: {num_obstacles})...", end='', flush=True)
        grid, start_pos, tries = generate_reachable_instance(
            size, size, num_obstacles, num_gold, seed=current_seed
        )
        if grid:
            print(f" Found after {tries} tries.")
            if current_seed is not None: current_seed += 1
            benchmark_instances.append({
                'grid': grid, 'start_pos': start_pos, 'grid_size': size
            })
        else:
            print(f" Failed after many tries. Aborting benchmark generation.")
            break
            
    if not benchmark_instances:
        print("\nNo benchmark instances were generated. Exiting.")
        return

    cost_scenarios = [
        {"name": "No Cost", "max_cost": None, "costs": None},
        {"name": "High-Cost Budget", "max_cost": generous_max_cost, "costs": costs_input},
        {"name": "Low-Cost Budget", "max_cost": low_max_cost, "costs": costs_input}
    ]
    
    results = {scenario["name"]: {"success": [], "failure": []} for scenario in cost_scenarios}

    for scenario in cost_scenarios:
        name = scenario["name"]
        print(f"\n--- Running Benchmark for: {name} ---")
        for instance in benchmark_instances:
            size = instance['grid_size']
            print(f"  Testing grid size {size}x{size}...", end='', flush=True)

            solution, _, solve_time = solve_minefield_plan(
                instance['grid'], instance['start_pos'], max_steps, 
                max_cost=scenario['max_cost'], costs=scenario['costs']
            )

            if solve_time > time_limit:
                print(f" -> TIMEOUT ({solve_time:.2f}s)")
                results[name]["failure"].append((size, solve_time))
                break 
            elif solution:
                print(f" -> Success ({solve_time:.2f}s)")
                results[name]["success"].append((size, solve_time))
            else:
                print(f" -> No Solution ({solve_time:.2f}s)")
                results[name]["failure"].append((size, solve_time))

    print("\nAnalysis complete. Generating comparison plot...")
    plt.figure(figsize=(12, 8))
    
    colors = {"No Cost": "blue", "High-Cost Budget": "green", "Low-Cost Budget": "red"}

    for name, data in results.items():
        if data["success"]:
            sizes, times = zip(*data["success"])
            plt.plot(sizes, times, 'o-', label=f"{name} (Success)", color=colors[name])
        
        if data["failure"]:
            sizes, times = zip(*data["failure"])
            plt.plot(sizes, times, 'x--', label=f"{name} (Failure/Timeout)", color=colors[name], markersize=8)

    title_line1 = f"Cost Constraint Performance Comparison"
    title_line2 = f"(Gold: {density_names[gold_density_key]}, Obstacles: {density_names[obs_density_key]}, k={max_steps})"
    plt.title(f"{title_line1}\n{title_line2}")
    plt.xlabel("Grid Size (N x N)")
    plt.ylabel("Solve Time (seconds)")
    plt.grid(True)
    plt.xticks(range(2, max_size + 1))
    plt.legend()
    plt.tight_layout()
    plt.show()



# ==============================================================================
# === COMPARATIVE ANALYSIS (PDDL) ==============================================
# ==============================================================================

def _execute_planner_run(planner_config, problem_filename, domain_filename, planner_path):
    """
    Executes a single run of a PDDL planner and parses the output.
    Returns: Tuple (success, search_time, translator_time, plan_length)
    """
    planner_type, planner_value = planner_config['type'], planner_config['value']

    if planner_type == 'search':
        full_command = [f"./{planner_path}", domain_filename, problem_filename, "--search", planner_value]
    else: 
        full_command = [f"./{planner_path}", "--alias", planner_value, domain_filename, problem_filename]

    result = subprocess.run(full_command, capture_output=True, text=True, check=False)

    plan_candidates = sorted(glob.glob('sas_plan*'), key=os.path.getmtime)
    success = 'Solution found.' in result.stdout
    plan_length = None
    if success and plan_candidates:
        plan_file = plan_candidates[-1]
        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                plan_length = len([line for line in f if line.strip() and not line.strip().startswith(';')])
            os.remove(plan_file)
        except OSError: pass

    lines_out = result.stdout.split('\n')
    st_line = next((ln for ln in lines_out if 'Search time:' in ln), None)
    tr_line = next((ln for ln in lines_out if 'Translator time:' in ln), None)
    
    def _parse_time(line):
        try:
            return float(line.split(':', 1)[1].strip().replace('s', ''))
        except (ValueError, IndexError):
            return 0.0
    
    search_time = _parse_time(st_line) if st_line else 0.0
    translator_time = _parse_time(tr_line) if tr_line else 0.0
    
    return success, search_time, translator_time, (plan_length or 0)


def _get_optimal_plan_length(instance, planner_path):
    """Runs A* (lmcut) on a single instance to find the optimal plan length."""
    grid, start_pos, size = instance['grid'], instance['start_pos'], len(instance['grid'])
    
    problem_filename = "temp_minefield_problem.pddl"
    domain_filename = "domain.pddl"
    generate_pddl_problem(grid, start_pos, f"problem-size-{size}", filename=problem_filename)

    full_command = [f"./{planner_path}", domain_filename, problem_filename, "--search", "astar(lmcut())"]

    print(f"\nFinding optimal plan length on {size}x{size} grid...", end='', flush=True)
    result = subprocess.run(full_command, capture_output=True, text=True, check=False)
    
    try: os.remove(problem_filename)
    except OSError: pass

    plan_candidates = sorted(glob.glob('sas_plan*'), key=os.path.getmtime)
    success = ('Solution found.' in result.stdout)
    
    if success and plan_candidates:
        plan_file = plan_candidates[-1]
        try:
            with open(plan_file, 'r', encoding='utf-8') as f:
                length = len([line for line in f if line.strip() and not line.strip().startswith(';')])
            os.remove(plan_file)
            print(f" -> Success! Plan length: {length}")
            return length
        except (OSError, FileNotFoundError):
            print(" -> Error reading plan file.")
            return None
    else:
        print(" -> Failure. Could not determine optimal plan length.")
        return None

def analyze_performance_with_pddl_planner():
    """Analyzes performance by running planners on a suite of size-progressing, random instances."""
    

    density_map = {'r': 0.10, 'c': 0.30, 'cr': 0.45}
    density_names = {'r': 'Rare', 'c': 'Common', 'cr': 'Crowded'}

    try:
        print("\n--- Configure Benchmark Instances ---")
        max_size = int(input("Enter the maximum grid size to test (e.g., 10): ") or 10)
        
        gold_density_key = input("Gold density [r]are/[c]ommon/[cr]owded: ").strip().lower() or 'c'
        obs_density_key = input("Obstacle density [r]are/[c]ommon/[cr]owded: ").strip().lower() or 'c'

        if gold_density_key not in density_map or obs_density_key not in density_map:
            print("Invalid density key. Please use 'r', 'c', or 'cr'.")
            return
            
        seed, _ = _get_pddl_instance_generation_params()

        prompt = "\nChoose planner: [1] A* (lmcut), [2] A* (hmax), [3] LAMA, [4] Compare Planners: "
        planner_choice = input(prompt)

        planner_path = "fast-downward.sif"
        if not os.path.exists(planner_path):
            print(f" Error: Planner not found at '{planner_path}'!")
            return

    except ValueError:
        print("Error: Invalid input. Please enter integers only.")
        return

    max_steps_value = 50
    include_z3 = False
    
    if planner_choice == '4':
        include_z3 = input("Include Z3 Solver in the comparison? (y/n): ").strip().lower() == 'y'
        if include_z3:
            max_steps_input_val = 0
            while max_steps_input_val <= 0:
                max_steps_input = input("Enter max steps for Z3, or type 'o' to use optimal plan length from A*: ").strip().lower()
                if max_steps_input == 'o':
                    print("\nGenerating a sample instance for the largest grid to find optimal plan length...")
                    total_cells = max_size * max_size
                    num_gold = max(1, math.floor(total_cells * density_map[gold_density_key]))
                    num_obs = math.floor(total_cells * density_map[obs_density_key])
                    if num_gold + num_obs >= total_cells:
                        num_obs = total_cells - num_gold -1

                    temp_grid, _, _ = generate_reachable_instance(max_size, max_size, num_obs, num_gold, seed)
                    
                    if temp_grid:
                        start_for_opt = next(( (r,c) for r in range(max_size) for c in range(max_size) if temp_grid[r][c] != 'O'), (0,0))
                        optimal_length = _get_optimal_plan_length({'grid': temp_grid, 'start_pos': start_for_opt}, planner_path)
                        if optimal_length:
                            max_steps_input_val = optimal_length + 5 
                            print(f"\n--> Using max_steps = {max_steps_input_val} for all Z3 benchmarks. <--\n")
                        else: print("Could not determine optimal length automatically.")
                    else: print("Could not generate a sample instance to determine optimal length.")
                else:
                    try:
                        max_steps_input_val = int(max_steps_input)
                        if max_steps_input_val <= 0: print("Max steps must be a positive integer.")
                    except ValueError: print("Invalid input. Please enter a positive integer or 'o'.")
            if max_steps_input_val > 0:
                max_steps_value = max_steps_input_val

    print(f"\nGenerating {max_size} random instance(s) with size progression...")
    benchmark_instances = []
    current_seed = seed
    for size in range(1, max_size + 1):
        total_cells = size * size
        num_gold = max(1, math.floor(total_cells * density_map[gold_density_key]))
        num_obstacles = math.floor(total_cells * density_map[obs_density_key])

        if num_gold + num_obstacles >= total_cells:
            print(f"Warning: At size {size}x{size}, item count exceeds cell count. Skipping.")
            continue
            
        print(f"  Generating size {size}x{size} (Gold: {num_gold}, Obs: {num_obstacles})...", end='', flush=True)
        grid, start_pos, tries = generate_reachable_instance(
            size, size, num_obstacles, num_gold, seed=current_seed
        )
        if grid:
            print(f" Found after {tries} tries.")
            if current_seed is not None: current_seed += 1
            benchmark_instances.append({
                'grid': grid, 'start_pos': start_pos,
                'max_steps': max_steps_value, 'grid_size': size
            })
        else:
            print(f" Failed after many tries. Aborting benchmark.")
            return
            
    if not benchmark_instances:
        print("\nNo benchmark instances were generated. Exiting.")
        return

    planner_configs = {
        "1": {"type": "search", "value": "astar(lmcut())", "name": "A* with LMCut"},
        "2": {"type": "search", "value": "astar(hmax())", "name": "A* with hMax"},
        "3": {"type": "alias", "value": "lama-first", "name": "LAMA"}
    }
    
    if planner_choice == '4':
        all_planners = [config['name'] for config in planner_configs.values()]
        if include_z3:
            all_planners.append('Z3 Solver')
        comparison_results = {name: {'sizes': [], 'times': [], 'lengths': []} for name in all_planners}

        for instance in benchmark_instances:
            grid, start_pos, size = instance['grid'], instance['start_pos'], instance['grid_size']
            print(f"\n--- Testing Instance: Grid Size {size}x{size} ---")

            problem_filename = "temp_minefield_problem.pddl"
            domain_filename = "domain.pddl"
            generate_pddl_problem(grid, start_pos, f"problem-size-{size}", filename=problem_filename)

            for config in planner_configs.values():
                name = config['name']
                print(f"  -> Running {name}...", end='', flush=True)
                success, search_t, trans_t, length = _execute_planner_run(config, problem_filename, domain_filename, planner_path)

                if success:
                    print(f" Success! Length: {length}, Search: {search_t:.4f}s")
                    comparison_results[name]['sizes'].append(size)
                    comparison_results[name]['times'].append(search_t)
                    comparison_results[name]['lengths'].append(length)
                else:
                    print(" Failure.")
                
                _append_csv_result(
                    os.path.join(os.getcwd(), 'benchmark_results.csv'),
                    {'planner': name, 'grid_size': size, 'solve_time_search_s': search_t, 'translator_time_s': trans_t,
                     'plan_length': length, 'optimal': name.startswith('A*')},
                    ['planner', 'grid_size', 'solve_time_search_s', 'translator_time_s', 'plan_length', 'optimal']
                )
            
            if include_z3:
                print(f"  -> Running Z3 Solver...", end='', flush=True)
                solution, _, solve_time = solve_minefield_plan(
                    grid, start_pos, instance['max_steps'], max_cost=None, costs=None
                )
                plan_length = len(solution) - 1 if solution else 0
                if solution:
                    print(f" Success! Length: {plan_length}, Time: {solve_time:.4f}s")
                    comparison_results['Z3 Solver']['sizes'].append(size)
                    comparison_results['Z3 Solver']['times'].append(solve_time)
                    comparison_results['Z3 Solver']['lengths'].append(plan_length)
                else:
                    print(" Failure.")
                
                _append_csv_result(
                    os.path.join(os.getcwd(), 'benchmark_results.csv'),
                    {'planner': 'Z3 Solver', 'grid_size': size, 'solve_time_search_s': solve_time, 'translator_time_s': 0,
                     'plan_length': plan_length, 'optimal': False},
                    ['planner', 'grid_size', 'solve_time_search_s', 'translator_time_s', 'plan_length', 'optimal']
                )

            try:
                os.remove(problem_filename)
            except OSError:
                pass
        
        print("\nAnalysis complete. Generating comparison plots...")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12), sharex=True)
        
        title_line1 = f"Planner Performance Comparison (Gold: {density_names[gold_density_key]}, Obstacles: {density_names[obs_density_key]})"
        title_line2 = f"(Z3 Max Steps: {max_steps_value})" if include_z3 else ""
        fig.suptitle(f"{title_line1}\n{title_line2}".strip(), fontsize=16)

        colors = {'A* with LMCut': 'red', 'A* with hMax': 'blue', 'LAMA': 'green', 'Z3 Solver': 'gold'}

        for name, data in comparison_results.items():
            if data['sizes']:
                sorted_points = sorted(zip(data['sizes'], data['times'], data['lengths']))
                s_sorted, t_sorted, l_sorted = zip(*sorted_points)
                ax1.plot(s_sorted, t_sorted, 'o-', label=name, color=colors.get(name, 'black'))
                ax2.plot(s_sorted, l_sorted, 'o-', label=name, color=colors.get(name, 'black'))

        ax1.set_title("Solve Time vs. Grid Size"); ax1.set_ylabel("Solve Time (seconds)"); ax1.grid(True); ax1.legend()
        ax2.set_title("Plan Length vs. Grid Size"); ax2.set_xlabel("Grid Size (N x N)"); ax2.set_ylabel("Plan Length"); ax2.grid(True); ax2.legend()
        
        plt.xticks(range(1, max_size + 1)); plt.tight_layout(rect=[0, 0, 1, 0.94]); plt.show()

    elif planner_choice in planner_configs:
        config = planner_configs[planner_choice]
        sizes, times, plan_lengths = [], [], []

        print(f"\n--- Running Benchmark for: {config['name']} ---")
        for instance in benchmark_instances:
            grid, start_pos, size = instance['grid'], instance['start_pos'], instance['grid_size']
            print(f"  Testing grid (Size: {size}x{size})...", end='', flush=True)

            problem_filename = "temp_minefield_problem.pddl"
            domain_filename = "domain.pddl"
            generate_pddl_problem(grid, start_pos, f"problem-size-{size}", filename=problem_filename)

            success, search_t, trans_t, length = _execute_planner_run(config, problem_filename, domain_filename, planner_path)

            if success:
                print(f" Success! Length: {length}, Search: {search_t:.4f}s")
                sizes.append(size)
                times.append(search_t)
                plan_lengths.append(length)
            else:
                print(" Failure.")
            
            try:
                os.remove(problem_filename)
            except OSError:
                pass
            
            _append_csv_result(
                os.path.join(os.getcwd(), 'benchmark_results.csv'),
                {'planner': config['name'], 'grid_size': size, 'solve_time_search_s': search_t, 'translator_time_s': trans_t,
                 'plan_length': length, 'optimal': config['name'].startswith('A*')},
                ['planner', 'grid_size', 'solve_time_search_s', 'translator_time_s', 'plan_length', 'optimal']
            )
        
        if not sizes:
            print("\nNo solutions found to plot.")
            return
            
        print("\nAnalysis complete. Generating plot...")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        fig.suptitle(f"Planner Performance: {config['name']}\n(Gold: {density_names[gold_density_key]}, Obstacles: {density_names[obs_density_key]})", fontsize=16)

        ax1.plot(sizes, times, 'o-', color='blue'); ax1.set_title("Solve Time vs. Grid Size"); ax1.set_ylabel("Solve Time (seconds)"); ax1.grid(True)
        ax2.plot(sizes, plan_lengths, 'o-', color='green'); ax2.set_title("Plan Length vs. Grid Size"); ax2.set_xlabel("Grid Size (N x N)"); ax2.set_ylabel("Plan Length"); ax2.grid(True)
        
        plt.xticks(range(1, max_size + 1)); plt.tight_layout(rect=[0, 0, 1, 0.94]); plt.show()
    else:
        print("Invalid choice.")


# ==============================================================================
# === MAIN EXECUTION ===========================================================
# ==============================================================================

def main():
    """Main menu to run different analysis modes."""
    print("--- GoldsInMineField Performance Analyzer ---")

    while True:
        print("\nPlease choose an analysis type:")
        print("--- Z3 SMT Solver Analysis ---")
        print("1. Analyze performance by Grid Size.")
        print("2. Analyze performance by Max Steps (k).")
        print("3. Analyze performance by Gold Count.")
        print("4. Analyze performance by Obstacle Density.")
        print("5. Analyze performance for Cost Configuration.")

        print("\n--- Comparative Analysis ---")
        print("6. Compare Planners (Fast Downward & Z3).")
        
        print("\n0. Exit.")
        choice = input("Enter your choice: ")

        menu = {
            '1': analyze_performance_by_grid_size,
            '2': analyze_performance_by_max_steps,
            '3': analyze_performance_by_gold_count,
            '4': analyze_performance_by_obstacle_density,
            '5': cost_effect_performance_analyser,
            '6': analyze_performance_with_pddl_planner,
        }
        
        if choice in menu:
            menu[choice]()
        elif choice == '0':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()