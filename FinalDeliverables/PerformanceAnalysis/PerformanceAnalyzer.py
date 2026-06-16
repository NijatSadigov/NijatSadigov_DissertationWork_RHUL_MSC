import sys
import os
import subprocess
import glob
import time
import csv
import math
from pddl_generator import generate_pddl_problem

def _append_csv_result(csv_path, row, header):
    write_header = not os.path.exists(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=header)
        if write_header:
            w.writeheader()
        w.writerow(row)
try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    sys.path.append(parent_dir)
except NameError:
    sys.path.append(os.getcwd())

from GoldsInMineField import solve_minefield_plan
from SampleMaker import (generate_single_grid_instance,
                         generate_grid_with_gold_count,
                         generate_grid_with_obstacles,
                         generate_benchmark_instances)
from DifferentPlanningInstances import generate_reachable_instance


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


def _run_single_z3_benchmark(benchmark_instances):
    """
    A helper function that runs the benchmark for the Z3 SMT solver.
    
    Returns:
        A tuple containing three lists: (sizes, times, plan_lengths)
    """
    sizes, times, plan_lengths = [], [], []
    print("\n--- Running Benchmark for: Z3 Solver ---")

    for sample in benchmark_instances:
        grid = sample['grid']
        start_pos = sample['start_pos']
        max_steps = sample['max_steps']
        size = sample['grid_size']
        print(f"  Testing grid (Size: {size}x{size}, MaxSteps: {max_steps})...", end='', flush=True)

        solution, _, solve_time = solve_minefield_plan(
            grid, start_pos, max_steps, max_cost=None, costs=None
        )
        
        plan_length = 0
        if solution:
            plan_length = len(solution) - 1
            print(f" ->  Success! Length: {plan_length}, Time: {solve_time:.4f}s")
            sizes.append(size)
            times.append(solve_time)
            plan_lengths.append(plan_length)
        else:
            print(' -> Failure')
        
        csv_row = {
            'planner': 'Z3 Solver',
            'grid_size': size,
            'solve_time_search_s': solve_time,
            'translator_time_s': 0, 
            'plan_length': plan_length,
            'optimal': False 
        }
        _append_csv_result(os.path.join(os.getcwd(), 'benchmark_results.csv'), csv_row,
                           header=['planner','grid_size','solve_time_search_s','translator_time_s','plan_length','optimal'])

    return sizes, times, plan_lengths


def _run_single_planner_benchmark(planner_config, benchmark_instances, planner_path):
    """
    A helper function that runs the benchmark for a single planner configuration.
    
    Returns:
        A tuple containing three lists: (sizes, times, plan_lengths)
    """
    sizes, times, plan_lengths = [], [], []
    config_name = planner_config['name']
    
    print(f"\n--- Running Benchmark for: {config_name} ---")

    for sample in benchmark_instances:
        grid = sample['grid']
        start_pos = sample['start_pos']
        size = sample['grid_size']
        print(f"  Testing grid (Size: {size}x{size})...", end='', flush=True)

        # Sanitize the config name for use as a filename. 'A*' must become
        # 'AStar' because '*' is illegal in Windows filenames (matches the
        # checked-in temp-problem-AStar-*.pddl artifacts).
        problem_filename = f"temp-problem-{config_name.replace(' ', '-').replace('*', 'Star')}.pddl"
        generate_pddl_problem(grid, start_pos, f"problem-size-{size}", filename=problem_filename)

        domain_filename = "domain.pddl"
        
        planner_type = planner_config['type']
        planner_value = planner_config['value']

        if planner_type == 'search':
            full_command = [
                f"./{planner_path}",
                domain_filename,
                problem_filename,
                "--search",
                planner_value
            ]
        else:
            full_command = [
                f"./{planner_path}",
                "--alias",
                planner_value,
                domain_filename,
                problem_filename
            ]

        result = subprocess.run(full_command, capture_output=True, text=True, check=False)

        plan_candidates = sorted(glob.glob('sas_plan*'), key=os.path.getmtime)
        success = ('Solution found.' in result.stdout)
        length = None
        if success and plan_candidates:
            plan_file = plan_candidates[-1]
            with open(plan_file, 'r', encoding='utf-8') as f:
                length = len([line for line in f if line.strip() and not line.strip().startswith(';')])
            try:
                os.remove(plan_file)
            except OSError:
                pass

        lines_out = result.stdout.split('\n')
        st_line = next((ln for ln in lines_out if 'Search time:' in ln), None)
        tr_line = next((ln for ln in lines_out if 'Translator time:' in ln), None)
        def _parse_time(ln):
            try:
                return float(ln.split(':',1)[1].strip().replace('s',''))
            except Exception:
                return 0.0
        search_time_val = _parse_time(st_line) if st_line else 0.0
        translator_time_val = _parse_time(tr_line) if tr_line else 0.0

        if success:
            length_display = length if length is not None else 0
            print(f" ->  Success! Length: {length_display}, Search: {search_time_val:.4f}s, Translator: {translator_time_val:.4f}s")
            sizes.append(size)
            times.append(search_time_val)
            plan_lengths.append(length_display)
        else:
            print(' -> Failure')

        csv_row = {
            'planner': config_name,
            'grid_size': size,
            'solve_time_search_s': search_time_val,
            'translator_time_s': translator_time_val,
            'plan_length': (length if length is not None else 0),
            'optimal': (config_name.startswith('A*'))
        }
        _append_csv_result(os.path.join(os.getcwd(), 'benchmark_results.csv'), csv_row,
                           header=['planner','grid_size','solve_time_search_s','translator_time_s','plan_length','optimal'])

    return sizes, times, plan_lengths

def _get_optimal_plan_length(instance, planner_path):
    """Runs A* (lmcut) on a single instance to find the optimal plan length."""
    grid = instance['grid']
    start_pos = instance['start_pos']
    size = len(grid)
    config_name = "astar-lmcut-optimal-check"

    problem_filename = f"temp-problem-{config_name}.pddl"
    generate_pddl_problem(grid, start_pos, f"problem-size-{size}", filename=problem_filename)
    domain_filename = "domain.pddl"

    full_command = [
        f"./{planner_path}", domain_filename, problem_filename,
        "--search", "astar(lmcut())"
    ]

    print(f"\nFinding optimal plan length on {size}x{size} grid...", end='', flush=True)
    result = subprocess.run(full_command, capture_output=True, text=True, check=False)

    try:
        os.remove(problem_filename)
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
    if not MATPLOTLIB_AVAILABLE:
        print("Cannot run analysis without matplotlib.")
        return

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
            
        seed_input = input("Enter a seed for reproducibility (blank for random): ").strip()
        seed = None if seed_input == "" else int(seed_input)

        prompt = "\nChoose planner: [1] A* (lmcut), [2] A* (hmax), [3] LAMA, [4] Compare Planners: "
        planner_choice = input(prompt)

        planner_path = "fast-downward.sif"
        if not os.path.exists(planner_path):
            print(f" Error: Planner not found at '{planner_path}'!")
            return

    except ValueError:
        print("Error: Invalid input. Please enter integers only.")
        return

    max_steps_value = 50  # Default value in case of an issue
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
                            max_steps_input_val = optimal_length + 5 # Adding small value to guarantee 
                            print(f"\n--> Using max_steps = {max_steps_input_val} for all Z3 benchmarks. <--\n")
                        else:
                            print("Could not determine optimal length automatically.")
                    else:
                        print("Could not generate a sample instance to determine optimal length.")
                else:
                    try:
                        max_steps_input_val = int(max_steps_input)
                        if max_steps_input_val <= 0:
                            print("Max steps must be a positive integer.")
                    except ValueError:
                        print("Invalid input. Please enter a positive integer or 'o'.")
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
            if current_seed is not None:
                current_seed += 1
            
            sample = {
                'grid': grid, 'start_pos': start_pos,
                'max_steps': max_steps_value,
                'grid_size': size
            }
            benchmark_instances.append(sample)
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
        comparison_results = {}
        for key, config in planner_configs.items():
            sizes, times, lengths = _run_single_planner_benchmark(config, benchmark_instances, planner_path)
            comparison_results[config['name']] = { 'sizes': sizes, 'times': times, 'lengths': lengths }
        
        if include_z3:
            sizes, times, lengths = _run_single_z3_benchmark(benchmark_instances)
            comparison_results['Z3 Solver'] = { 'sizes': sizes, 'times': times, 'lengths': lengths }
        
        print("\nAnalysis complete. Generating comparison plots...")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 12), sharex=True)
        
        title_line1 = f"Planner Performance Comparison (Gold: {density_names[gold_density_key]}, Obstacles: {density_names[obs_density_key]})"
        title_line2 = f"(Z3 Max Steps: {max_steps_value})" if include_z3 else ""
        fig.suptitle(f"{title_line1}\n{title_line2}".strip(), fontsize=16)

        colors = {'A* with LMCut': 'red', 'A* with hMax': 'blue', 'LAMA': 'green'}
        if include_z3:
            colors['Z3 Solver'] = 'gold'

        for name, data in comparison_results.items():
            if data['sizes']:
                sorted_points = sorted(zip(data['sizes'], data['times'], data['lengths']))
                s_sorted, t_sorted, l_sorted = zip(*sorted_points)
                color = colors.get(name, 'black')
                ax1.plot(s_sorted, t_sorted, 'o-', label=name, color=color)
                ax2.plot(s_sorted, l_sorted, 'o-', label=name, color=color)

        ax1.set_title("Solve Time vs. Grid Size")
        ax1.set_ylabel("Solve Time (seconds)")
        ax1.grid(True)
        ax1.legend()

        ax2.set_title("Plan Length vs. Grid Size")
        ax2.set_xlabel("Grid Size (N x N)")
        ax2.set_ylabel("Plan Length (Number of Actions)")
        ax2.grid(True)
        ax2.legend()
        
        plt.xticks(range(1, max_size + 1))
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        plt.show()

    elif planner_choice in planner_configs:
        config = planner_configs[planner_choice]
        sizes, times, plan_lengths = _run_single_planner_benchmark(config, benchmark_instances, planner_path)
        
        if not sizes:
            print("\nNo solutions found to plot.")
            return
            
        print("\nAnalysis complete. Generating plot...")
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        fig.suptitle(f"Planner Performance: {config['name']}\n(Gold: {density_names[gold_density_key]}, Obstacles: {density_names[obs_density_key]})", fontsize=16)

        ax1.plot(sizes, times, 'o-', color='blue')
        ax1.set_title("Solve Time vs. Grid Size")
        ax1.set_ylabel("Solve Time (seconds)")
        ax1.grid(True)

        ax2.plot(sizes, plan_lengths, 'o-', color='green')
        ax2.set_title("Plan Length vs. Grid Size")
        ax2.set_xlabel("Grid Size (N x N)")
        ax2.set_ylabel("Plan Length (Number of Actions)")
        ax2.grid(True)
        
        plt.xticks(range(1, max_size + 1))
        plt.tight_layout(rect=[0, 0, 1, 0.94])
        plt.show()
    else:
        print("Invalid choice.")


def main():
    """Main menu to run different analysis modes."""
    print("--- GoldsInMineField Performance Analyzer ---")

    while True:
        print("\nPlease choose an analysis type:")
        print("--- Z3 SMT Solver Analysis ---")
        print("1. Analyze performance by Grid Size.")
        print("2. Analyze performance by Max Steps (k).")
        print("3. Analyze performance by Gold Count.")
        print("4. Analyze aperformance by Obstacle Density.")
        print("\n--- Comparative Analysis ---")
        print("5. Compare Planners (Fast Downward & Z3).")
        
        print("\n0. Exit.")
        choice = input("Enter your choice: ")

        if choice == '1':
            analyze_performance_by_grid_size()
        elif choice == '2':
            analyze_performance_by_max_steps()
        elif choice == '3':
            analyze_performance_by_gold_count()
        elif choice == '4':
            analyze_performance_by_obstacle_density()
        elif choice == '5':
            analyze_performance_with_pddl_planner()
        elif choice == '0':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()