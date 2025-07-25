from z3 import *
#-----------------------------
# FINAL DELIVERABLES, TASK 1- Develop code for encoding a planning problem on a 2-d grid with obstacle as a BMC problem.

#-----------------------------
# Problem Description:
"""
Main player is a robot that is trying to collect gold from a field.
The minefield is represented as a 2D grid where each cell can either be empty, has gold, or be an obstacle.
# The robot can move in four directions (up, down, left, right) and can collect gold.
# The robot starts at a given position and the goal is to collect all the gold while avoiding mines and obstacles.
# The robot can only move to adjacent cells that are not occupied by mines or obstacles.
# The robot can collect gold from a cell if it is present there.
# The goal is to find a sequence of moves that allows the robot to collect all the gold.
"""

def goldsInMineFieldSolver(grid, startPos, maxSteps):
    """
    Solves the Golds in MineField problem using Z3 SMT solver and bounded model checking.
    """
    rowsCount = len(grid) if grid else 0
    colsCount = len(grid[0]) if rowsCount > 0 else 0
    if (rowsCount == 0 or colsCount == 0):
        print("Invalid grid dimensions.")
        return None
    if not (0 <= startPos[0] < rowsCount and 0 <= startPos[1] < colsCount) or ( grid[startPos[0]][startPos[1]] == 'O'):
        print("Invalid starting position.")
        return None
        
    state = [[[String(f'state_{t}_{i}_{j}') for j in range(colsCount)] for i in range(rowsCount)] for t in range(maxSteps + 1)]
    solver = Solver()
    
    possible_cell_states = ['.', 'G', 'R', 'O', 'RC', 'RG', 'C']
    for t in range(maxSteps + 1):
        for i in range(rowsCount):
            for j in range(colsCount):
                solver.add(Or([state[t][i][j] == cell for cell in possible_cell_states]))
    
    for i in range(rowsCount):
        for j in range(colsCount):
            if (i, j) == startPos: continue
            solver.add(state[0][i][j] == grid[i][j])

    start_cell_content = grid[startPos[0]][startPos[1]]
    if start_cell_content == 'G':
        solver.add(state[0][startPos[0]][startPos[1]] == 'RG')
    else:
        solver.add(state[0][startPos[0]][startPos[1]] == 'R')

    add_transition_constraints(solver, state, grid, rowsCount, colsCount, maxSteps)
    add_collectAction_constraints(solver, state, rowsCount, colsCount, maxSteps)
    add_goal_constraints(solver, state, grid, rowsCount, colsCount, maxSteps)

    print("\nSolving...")
    if solver.check() == sat:
        model = solver.model()
        solution = []
        for t in range(maxSteps + 1):
            step = [[model.evaluate(state[t][i][j]).as_string().strip('"') for j in range(colsCount)] for i in range(rowsCount)]
            solution.append(step)
        print("Solution found!")
        return solution
    else:
        print("No solution found within the given bound.")
        return None

def is_robot(cell_state):
    return Or(cell_state == 'R', cell_state == 'RG', cell_state == 'RC')

def add_transition_constraints(solver, state, grid, rowsCount, colsCount, maxSteps):
    print("Adding transition constraints...")
    for t in range(maxSteps + 1):
        robot_indicators = [is_robot(state[t][r][c]) for r in range(rowsCount) for c in range(colsCount)]
        robot_count = Sum([If(indicator, 1, 0) for indicator in robot_indicators])
        solver.add(robot_count == 1)
    for t in range(maxSteps):
        for r_prev in range(rowsCount):
            for c_prev in range(colsCount):
                robot_at_prev_loc = is_robot(state[t][r_prev][c_prev])
                possible_move_outcomes = []
                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                    r_next, c_next = r_prev + dr, c_prev + dc
                    if 0 <= r_next < rowsCount and 0 <= c_next < colsCount and grid[r_next][c_next] != 'O':
                        possible_move_outcomes.append(is_robot(state[t+1][r_next][c_next]))
                
                collect_action_outcome = state[t+1][r_prev][c_prev] == 'RC'
                solver.add(Implies(state[t][r_prev][c_prev] == 'RG', Or(Or(possible_move_outcomes), collect_action_outcome)))
                solver.add(Implies(And(robot_at_prev_loc, state[t][r_prev][c_prev] != 'RG'), Or(possible_move_outcomes)))

    for t in range(maxSteps):
        for r in range(rowsCount):
            for c in range(colsCount):
                solver.add(Implies(state[t][r][c] == 'O', state[t+1][r][c] == 'O'))
                not_disturbed = And(Not(is_robot(state[t][r][c])), Not(is_robot(state[t+1][r][c])))
                solver.add(Implies(not_disturbed, state[t+1][r][c] == state[t][r][c]))
                
                robot_leaves = And(is_robot(state[t][r][c]), Not(is_robot(state[t+1][r][c])))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'R'), state[t+1][r][c] == '.'))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'RG'), state[t+1][r][c] == 'G'))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'RC'), state[t+1][r][c] == 'C'))

                robot_enters = And(Not(is_robot(state[t][r][c])), is_robot(state[t+1][r][c]))
                solver.add(Implies(And(robot_enters, state[t][r][c] == '.'), state[t+1][r][c] == 'R'))
                solver.add(Implies(And(robot_enters, state[t][r][c] == 'G'), state[t+1][r][c] == 'RG'))
                solver.add(Implies(And(robot_enters, state[t][r][c] == 'C'), state[t+1][r][c] == 'RC'))
                
                robot_stays = And(is_robot(state[t][r][c]), is_robot(state[t+1][r][c]))
                solver.add(Implies(And(robot_stays, state[t][r][c] == 'R'), state[t+1][r][c] == 'R'))
                solver.add(Implies(And(robot_stays, state[t][r][c] == 'RC'), state[t+1][r][c] == 'RC'))

def add_collectAction_constraints(solver, state, rowsCount, colsCount, maxSteps):
    print("Adding collect action constraints...")
    for t in range(maxSteps):
        for r in range(rowsCount):
            for c in range(colsCount):
                collect_action_occurred = And(is_robot(state[t][r][c]), state[t+1][r][c] == 'RC')
                precondition_for_collect = state[t][r][c] == 'RG'
                solver.add(Implies(collect_action_occurred, precondition_for_collect))

def add_goal_constraints(solver, state, grid, rowsCount, colsCount, maxSteps):
    print("Adding goal constraints...")
    gold_locations = []
    for r in range(rowsCount):
        for c in range(colsCount):
            if grid[r][c] == 'G':
                gold_locations.append((r, c))
    if not gold_locations:
        print("No gold on the map to set a goal for.")
        return
    all_gold_collected_conditions = []
    for r, c in gold_locations:
        is_collected = Or(state[maxSteps][r][c] == 'C', state[maxSteps][r][c] == 'RC')
        all_gold_collected_conditions.append(is_collected)
    solver.add(And(all_gold_collected_conditions))
    print(f"Goal set: All {len(gold_locations)} gold pieces must be collected.")

