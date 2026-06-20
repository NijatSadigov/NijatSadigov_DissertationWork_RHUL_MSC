from z3 import *
import time

def is_robot_cell(cell_state):
    """A simple helper function to tell if a cell contains the robot."""
    return Or(cell_state == 'R', cell_state == 'RG', cell_state == 'RC')

def add_cost_constraints(solver, state, total_cost, costs, num_rows, num_cols, max_steps):
    """Adds constraints for tracking the cumulative cost of the plan."""
    print("Adding cost constraints...")
    solver.add(total_cost[0] == 0) 

    for t in range(max_steps):
        robot_cell_matches = [And(is_robot_cell(state[t][r][c]), is_robot_cell(state[t+1][r][c])) for r in range(num_rows) for c in range(num_cols)]
        is_stay_or_collect = Or(robot_cell_matches)
        is_move = Not(is_stay_or_collect)
        solver.add(Implies(is_move, total_cost[t+1] == total_cost[t] + costs['move']))
        
        did_collect = Or([And(state[t][r][c] == 'RG', state[t+1][r][c] == 'RC') for r in range(num_rows) for c in range(num_cols)])
        solver.add(Implies(did_collect, total_cost[t+1] == total_cost[t] + costs['collect']))
        
        is_stay_no_collect = And(is_stay_or_collect, Not(did_collect))
        solver.add(Implies(is_stay_no_collect, total_cost[t+1] == total_cost[t] + costs['stay']))

def add_goal_constraints(solver, state, grid, num_rows, num_cols, max_steps, total_cost=None, max_cost=None):
    """Adds goal constraints, requiring all gold to be collected, potentially under a max_cost."""
    print("Adding goal constraints...")
    gold_locations = [(r, c) for r in range(num_rows) for c in range(num_cols) if grid[r][c] == 'G']
    
    if not gold_locations:
        print("No gold on the map to set a goal for.")
        return []

    goal_met_at_step_t = [
        And([Or(state[t][r][c] == 'C', state[t][r][c] == 'RC') for r, c in gold_locations])
        for t in range(max_steps + 1)
    ]

    if max_cost is not None and total_cost is not None:
        print(f"Applying cost constraint: max_cost <= {max_cost}")
        possible_solutions = [
            And(goal_met_at_step_t[t], total_cost[t] <= max_cost)
            for t in range(1, max_steps + 1)
        ]
        solver.add(Or(possible_solutions))
    else:
        solver.add(goal_met_at_step_t[max_steps])
    
    print(f"Goal set: All {len(gold_locations)} gold pieces must be collected.")
    return gold_locations

def solve_minefield_plan(grid, start_pos, max_steps, max_cost=None, costs=None):
    """Encodes the planning problem as SMT and uses Z3 to find a valid plan."""
    num_rows = len(grid) if grid else 0
    num_cols = len(grid[0]) if num_rows > 0 else 0
    if (num_rows == 0 or num_cols == 0):
        print("Invalid grid dimensions.")
        return None, None, 0.0
    if not (0 <= start_pos[0] < num_rows and 0 <= start_pos[1] < num_cols) or (grid[start_pos[0]][start_pos[1]] == 'O'):
        print("Invalid starting position.")
        return None, None, 0.0
    
    if costs is None:
        costs = {'move': 1, 'collect': 1, 'stay': 0}
        
    state = [[[String(f'state_{t}_{i}_{j}') for j in range(num_cols)] for i in range(num_rows)] for t in range(max_steps + 1)]
    solver = Solver()
    
    possible_cell_states = ['.', 'G', 'R', 'O', 'RC', 'RG', 'C']
    for t in range(max_steps + 1):
        for i in range(num_rows):
            for j in range(num_cols):
                solver.add(Or([state[t][i][j] == cell for cell in possible_cell_states]))
    
    for i in range(num_rows):
        for j in range(num_cols):
            if (i, j) == start_pos: continue
            solver.add(state[0][i][j] == grid[i][j])

    start_cell_content = grid[start_pos[0]][start_pos[1]]
    solver.add(state[0][start_pos[0]][start_pos[1]] == ('RG' if start_cell_content == 'G' else 'R'))

    add_transition_constraints(solver, state, grid, num_rows, num_cols, max_steps)
    add_collect_action_constraints(solver, state, num_rows, num_cols, max_steps)
    
    total_cost = None
    if max_cost is not None:
        total_cost = [Int(f'cost_{t}') for t in range(max_steps + 1)]
        add_cost_constraints(solver, state, total_cost, costs, num_rows, num_cols, max_steps)
    
    gold_locations = add_goal_constraints(solver, state, grid, num_rows, num_cols, max_steps, total_cost, max_cost)

    print("\nSolving...")
    start_time = time.time()
    result = solver.check()
    solve_time = time.time() - start_time
    print(f"Solver finished in {solve_time:.4f} seconds.")

    if result == sat:
        model = solver.model()
        
        full_path = [
            [[model.evaluate(state[t][i][j]).as_string().strip('"') for j in range(num_cols)] for i in range(num_rows)]
            for t in range(max_steps + 1)
        ]

        goal_step = -1
        for t in range(max_steps + 1):
            is_goal_met = True
            if not gold_locations:
                goal_step = 0
                break
            for r_gold, c_gold in gold_locations:
                cell = full_path[t][r_gold][c_gold]
                if not (cell == 'C' or cell == 'RC'):
                    is_goal_met = False
                    break
            if is_goal_met:
                goal_step = t
                break

        final_cost = None
        solution = None
        if goal_step != -1:
            solution = full_path[:goal_step + 1] 
            if total_cost is not None:
                final_cost = model.evaluate(total_cost[goal_step]).as_long()
        
        print("Solution found!")
        return solution, final_cost, solve_time
    else:
        print("No solution found within the given bounds (and cost constraints if any).")
        return None, None, solve_time

def add_transition_constraints(solver, state, grid, num_rows, num_cols, max_steps):
    """This includes constraints for valid robot movement, frame axioms for static elements
    (obstacles, collected gold), and state changes when the robot interacts with a cell."""
    print("Adding transition constraints...")
    for t in range(max_steps + 1):
        robot_indicators = [is_robot_cell(state[t][r][c]) for r in range(num_rows) for c in range(num_cols)]
        solver.add(Sum([If(indicator, 1, 0) for indicator in robot_indicators]) == 1)

    for t in range(max_steps):
        for r_prev in range(num_rows):
            for c_prev in range(num_cols):
                robot_at_prev = is_robot_cell(state[t][r_prev][c_prev])
                possible_moves = []
                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    r_next, c_next = r_prev + dr, c_prev + dc
                    if 0 <= r_next < num_rows and 0 <= c_next < num_cols and grid[r_next][c_next] != 'O':
                        possible_moves.append(is_robot_cell(state[t+1][r_next][c_next]))
                
                collect_outcome = state[t+1][r_prev][c_prev] == 'RC'
                solver.add(Implies(state[t][r_prev][c_prev] == 'RG', Or(Or(possible_moves), collect_outcome)))
                solver.add(Implies(And(robot_at_prev, state[t][r_prev][c_prev] != 'RG'), Or(possible_moves)))

    for t in range(max_steps):
        for r in range(num_rows):
            for c in range(num_cols):
                solver.add(Implies(state[t][r][c] == 'O', state[t+1][r][c] == 'O'))
                
                not_disturbed = And(Not(is_robot_cell(state[t][r][c])), Not(is_robot_cell(state[t+1][r][c])))
                solver.add(Implies(not_disturbed, state[t+1][r][c] == state[t][r][c]))
                
                robot_leaves = And(is_robot_cell(state[t][r][c]), Not(is_robot_cell(state[t+1][r][c])))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'R'), state[t+1][r][c] == '.'))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'RG'), state[t+1][r][c] == 'G'))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'RC'), state[t+1][r][c] == 'C'))
                
           
                robot_enters = And(Not(is_robot_cell(state[t][r][c])), is_robot_cell(state[t+1][r][c]))
                solver.add(Implies(And(robot_enters, state[t][r][c] == '.'), state[t+1][r][c] == 'R'))
                solver.add(Implies(And(robot_enters, state[t][r][c] == 'G'), state[t+1][r][c] == 'RG'))
                solver.add(Implies(And(robot_enters, state[t][r][c] == 'C'), state[t+1][r][c] == 'RC'))
                
                
                robot_stays = And(is_robot_cell(state[t][r][c]), is_robot_cell(state[t+1][r][c]))
                solver.add(Implies(And(robot_stays, state[t][r][c] == 'R'), state[t+1][r][c] == 'R'))
                solver.add(Implies(And(robot_stays, state[t][r][c] == 'RC'), state[t+1][r][c] == 'RC'))

def add_collect_action_constraints(solver, state, num_rows, num_cols, max_steps):
    """Ensures a 'collect' action is only possible if the robot is on a gold cell ('RG')."""
    print("Adding collect action constraints...")
    for t in range(max_steps):
        for r in range(num_rows):
            for c in range(num_cols):
                collect_occurred = And(is_robot_cell(state[t][r][c]), state[t+1][r][c] == 'RC')
                precondition = state[t][r][c] == 'RG'
                solver.add(Implies(collect_occurred, precondition))