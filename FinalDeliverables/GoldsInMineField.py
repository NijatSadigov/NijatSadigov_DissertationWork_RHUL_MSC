from z3 import *
import time

# Helper to check if a cell contains the robot in any state.
def is_robot_cell(cell_state):
    """A simple helper function to determine if a cell contains the robot."""
    return Or(cell_state == 'R', cell_state == 'RG', cell_state == 'RC')

# Encodes cost accumulation based on the robot's actions at each step.
def add_cost_constraints(solver, state, total_cost, costs, num_rows, num_cols, max_steps):
    """Adds constraints for tracking the cumulative cost of the plan."""
    print("Adding cost constraints...")
    solver.add(total_cost[0] == 0) # Plan starts with zero cost.

    # For each step, increment cost based on the action taken.
    for t in range(max_steps):
        # A 'move' occurs if the robot's position changes between t and t+1.
        robot_cell_matches = [And(is_robot_cell(state[t][r][c]), is_robot_cell(state[t+1][r][c])) for r in range(num_rows) for c in range(num_cols)]
        is_stay_or_collect = Or(robot_cell_matches)
        is_move = Not(is_stay_or_collect)
        solver.add(Implies(is_move, total_cost[t+1] == total_cost[t] + costs['move']))
        
        # A 'collect' action occurs if the robot stays and the cell state changes from 'RG' to 'RC'.
        did_collect = Or([And(state[t][r][c] == 'RG', state[t+1][r][c] == 'RC') for r in range(num_rows) for c in range(num_cols)])
        solver.add(Implies(did_collect, total_cost[t+1] == total_cost[t] + costs['collect']))
        
        # A 'stay' action occurs if the robot did not move and did not collect.
        is_stay_no_collect = And(is_stay_or_collect, Not(did_collect))
        solver.add(Implies(is_stay_no_collect, total_cost[t+1] == total_cost[t] + costs['stay']))

# Defines the goal: all gold collected, optionally within a cost budget.
def add_goal_constraints(solver, state, grid, num_rows, num_cols, max_steps, total_cost=None, max_cost=None):
    """Adds goal constraints, requiring all gold to be collected, potentially under a max_cost."""
    print("Adding goal constraints...")
    gold_locations = [(r, c) for r in range(num_rows) for c in range(num_cols) if grid[r][c] == 'G']
    
    if not gold_locations:
        print("No gold on the map to set a goal for.")
        return []

    # At each step t, define a boolean indicating if all gold is collected.
    goal_met_at_step_t = [
        And([Or(state[t][r][c] == 'C', state[t][r][c] == 'RC') for r, c in gold_locations])
        for t in range(max_steps + 1)
    ]

    if max_cost is not None and total_cost is not None:
        # Goal: find a step 't' where all gold is collected AND the cost is within budget.
        print(f"Applying cost constraint: max_cost <= {max_cost}")
        possible_solutions = [
            And(goal_met_at_step_t[t], total_cost[t] <= max_cost)
            for t in range(1, max_steps + 1)
        ]
        solver.add(Or(possible_solutions))
    else:
        # Standard Goal: all gold must be collected by the final step.
        solver.add(goal_met_at_step_t[max_steps])
    
    print(f"Goal set: All {len(gold_locations)} gold pieces must be collected.")
    return gold_locations

# Main solver function using a bounded model checking approach.
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
    
    # Each cell must have a valid state representation.
    possible_cell_states = ['.', 'G', 'R', 'O', 'RC', 'RG', 'C']
    for t in range(max_steps + 1):
        for i in range(num_rows):
            for j in range(num_cols):
                solver.add(Or([state[t][i][j] == cell for cell in possible_cell_states]))
    
    # Initial state (t=0) constraints based on the input grid.
    for i in range(num_rows):
        for j in range(num_cols):
            if (i, j) == start_pos: continue
            solver.add(state[0][i][j] == grid[i][j])

    start_cell_content = grid[start_pos[0]][start_pos[1]]
    solver.add(state[0][start_pos[0]][start_pos[1]] == ('RG' if start_cell_content == 'G' else 'R'))

    # Add all model constraints.
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
        
        # Extract the full path up to max_steps to find the goal step
        full_path = [
            [[model.evaluate(state[t][i][j]).as_string().strip('"') for j in range(num_cols)] for i in range(num_rows)]
            for t in range(max_steps + 1)
        ]

        # Find the first step where the goal is met
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
            solution = full_path[:goal_step + 1] # Truncate solution to the goal step
            if total_cost is not None:
                final_cost = model.evaluate(total_cost[goal_step]).as_long()
        
        print("Solution found!")
        return solution, final_cost, solve_time
    else:
        print("No solution found within the given bounds (and cost constraints if any).")
        return None, None, solve_time

# Encodes the transition model from step t to t+1.
def add_transition_constraints(solver, state, grid, num_rows, num_cols, max_steps):
    """This includes constraints for valid robot movement, frame axioms for static elements
    (obstacles, collected gold), and state changes when the robot interacts with a cell."""
    print("Adding transition constraints...")
    # Constraint: Exactly one robot on the grid at all times.
    for t in range(max_steps + 1):
        robot_indicators = [is_robot_cell(state[t][r][c]) for r in range(num_rows) for c in range(num_cols)]
        solver.add(Sum([If(indicator, 1, 0) for indicator in robot_indicators]) == 1)

    # Robot movement rules.
    for t in range(max_steps):
        for r_prev in range(num_rows):
            for c_prev in range(num_cols):
                robot_at_prev = is_robot_cell(state[t][r_prev][c_prev])
                possible_moves = []
                # The robot can move to an adjacent, non-obstacle cell, or stay.
                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    r_next, c_next = r_prev + dr, c_prev + dc
                    if 0 <= r_next < num_rows and 0 <= c_next < num_cols and grid[r_next][c_next] != 'O':
                        possible_moves.append(is_robot_cell(state[t+1][r_next][c_next]))
                
                # If on gold, the robot can move OR perform a 'collect' action.
                collect_outcome = state[t+1][r_prev][c_prev] == 'RC'
                solver.add(Implies(state[t][r_prev][c_prev] == 'RG', Or(Or(possible_moves), collect_outcome)))
                # If not on gold, the robot can only move.
                solver.add(Implies(And(robot_at_prev, state[t][r_prev][c_prev] != 'RG'), Or(possible_moves)))

    # Frame Axioms: what remains unchanged between steps.
    for t in range(max_steps):
        for r in range(num_rows):
            for c in range(num_cols):
                # Obstacles are static.
                solver.add(Implies(state[t][r][c] == 'O', state[t+1][r][c] == 'O'))
                
                # If a cell is not affected by the robot, its state persists.
                not_disturbed = And(Not(is_robot_cell(state[t][r][c])), Not(is_robot_cell(state[t+1][r][c])))
                solver.add(Implies(not_disturbed, state[t+1][r][c] == state[t][r][c]))
                
                # When the robot leaves a cell, it reverts to its underlying type.
                robot_leaves = And(is_robot_cell(state[t][r][c]), Not(is_robot_cell(state[t+1][r][c])))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'R'), state[t+1][r][c] == '.'))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'RG'), state[t+1][r][c] == 'G'))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'RC'), state[t+1][r][c] == 'C'))
                
                # When the robot enters a cell, its state updates to include the robot.
                robot_enters = And(Not(is_robot_cell(state[t][r][c])), is_robot_cell(state[t+1][r][c]))
                solver.add(Implies(And(robot_enters, state[t][r][c] == '.'), state[t+1][r][c] == 'R'))
                solver.add(Implies(And(robot_enters, state[t][r][c] == 'G'), state[t+1][r][c] == 'RG'))
                solver.add(Implies(And(robot_enters, state[t][r][c] == 'C'), state[t+1][r][c] == 'RC'))
                
                # If the robot stays without collecting, its state persists.
                robot_stays = And(is_robot_cell(state[t][r][c]), is_robot_cell(state[t+1][r][c]))
                solver.add(Implies(And(robot_stays, state[t][r][c] == 'R'), state[t+1][r][c] == 'R'))
                solver.add(Implies(And(robot_stays, state[t][r][c] == 'RC'), state[t+1][r][c] == 'RC'))

# Encodes the preconditions for the 'collect gold' action.
def add_collect_action_constraints(solver, state, num_rows, num_cols, max_steps):
    """Ensures a 'collect' action is only possible if the robot is on a gold cell ('RG')."""
    print("Adding collect action constraints...")
    for t in range(max_steps):
        for r in range(num_rows):
            for c in range(num_cols):
                # If a collect action occurred (state becomes 'RC'), the precondition is that the state was 'RG'.
                collect_occurred = And(is_robot_cell(state[t][r][c]), state[t+1][r][c] == 'RC')
                precondition = state[t][r][c] == 'RG'
                solver.add(Implies(collect_occurred, precondition))