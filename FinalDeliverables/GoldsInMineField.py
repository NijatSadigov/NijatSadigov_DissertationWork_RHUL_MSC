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
    Args:
        grid (list of list of str): The minefield represented as a 2D grid.
            Example: [['.', 'G', 'O'], 
                      ['.', '.', 'G'], 
                      ['O', '.', '.']]
            where '.' = empty cell,'G' = gold, and 'O' = obstacle.
        startPos (tuple): The starting position of the robot in the grid (row, column).
        maxSteps (int): Maximum number of steps allowed to collect all gold.
    
    """
    rowsCount = len(grid) if grid else 0
    colsCount = len(grid[0]) if rowsCount > 0 else 0
    if (rowsCount == 0 or colsCount == 0):
        print("Invalid grid dimensions.")
        return
    if (startPos[0] < 0 or startPos[0] >= rowsCount or startPos[1] < 0 or startPos[1] >= colsCount) or ( grid[startPos[0]][startPos[1]] == 'O'):
        # Check if the starting position is valid (inside of grid or not a obstacle)
        print("Invalid starting position.")
        return
    # State variable for each cell at each time step: '.', 'G', 'R', 'O', 'RC', 'RG'
    # where '.' = empty cell, 'G' = gold, 'R' = robot, 'O' = obstacle, 'RC' = robot on collected gold cell, 'RG' = robot on gold 'C' = collected gold cell.
    state = [[[String(f'state_{t}_{i}_{j}') for j in range(colsCount)] for i in range(rowsCount)] for t in range(maxSteps + 1)]
    solver = Solver()
    
    possible_cell_states = ['.', 'G', 'R', 'O', 'RC', 'RG', 'C']
    for t in range(maxSteps + 1):
        for i in range(rowsCount):
            for j in range(colsCount):
                solver.add(Or([state[t][i][j] == cell for cell in possible_cell_states]))
    
    # Initial state
    
    # First designing the grid
    for i in range(rowsCount):
        for j in range(colsCount):
            if (i, j) == startPos:
                continue
            solver.add(state[0][i][j] == grid[i][j])

    # Then putting the robot, checking if it starts on gold.
    start_cell_content = grid[startPos[0]][startPos[1]]
    if start_cell_content == 'G':
        solver.add(state[0][startPos[0]][startPos[1]] == 'RG')
    else:
        solver.add(state[0][startPos[0]][startPos[1]] == 'R')

    # Transition rules (for easy readibility I will write it as different function)
    add_transition_constraints(solver, state, grid, rowsCount, colsCount, maxSteps)
    add_collectAction_constraints(solver, state, rowsCount, colsCount, maxSteps)
    add_goal_constraints(solver, state, grid, rowsCount, colsCount, maxSteps)

    # Check if the solver can find a solution
    print("\nSolving...")
    if solver.check() == sat:
        model = solver.model()
        # Extract the solution steps
        solution = []
        for t in range(maxSteps + 1):
            step = [[model.evaluate(state[t][i][j]).as_string().strip('"') for j in range(colsCount)] for i in range(rowsCount)]
            solution.append(step)
        # Print the solution steps
        print("Solution found:")
        for t, step in enumerate(solution):
            print(f"--- Step {t} ---")
            for row in step:
                print(" ".join(row))
    else:
        print("No solution found within the given bound.")

#---------------------#
#---------------------#

# Helper function-- checks if a cell state has the robot.
def is_robot(cell_state):
    # A cell has a robot if its state is 'R' (Robot), 'RG' (Robot on Gold), or 'RC' (Robot on Collected Gold).
    return Or(cell_state == 'R', cell_state == 'RG', cell_state == 'RC')

def add_transition_constraints(solver, state, grid, rowsCount, colsCount, maxSteps):
    """
    Adds transition constraints to the solver for robot movement.
    - The robot can move up, down, left, right, or wait.
    - The robot cannot move into obstacles ('O').
    - Guarantes that only one robot can be on grid at each step.
    - Handles cell states change during movement of robot (enter-leaves-waits).
    """
    print("Adding transition constraints...")

    # --- Main Eules ---

    # 1. Exactly One Robot.
    for t in range(maxSteps + 1):
        robot_indicators = [is_robot(state[t][r][c]) for r in range(rowsCount) for c in range(colsCount)]
        solver.add(PbEq([(indicator, 1) for indicator in robot_indicators], 1))

    # 2. Movement Constraint: The robot can only move to a valid adjacent ( or stay in same ) cell, or collect.
    for t in range(maxSteps):
        for r_prev in range(rowsCount):
            for c_prev in range(colsCount):
                # condition: IF the robot is at (r_prev, c_prev) at time t...
                robot_at_prev_loc = is_robot(state[t][r_prev][c_prev])

                # => at time t+1, it must be in one of the possible next positions.
                # FFollowing lines iterate through all possible moves (including waiting).
                possible_move_outcomes = []
                for dr, dc in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:  # Wait, Up, Down, Left, Right
                    r_next, c_next = r_prev + dr, c_prev + dc
                    if 0 <= r_next < rowsCount and 0 <= c_next < colsCount and grid[r_next][c_next] != 'O':
                        possible_move_outcomes.append(is_robot(state[t+1][r_next][c_next]))
                
                # The "collect" action is an alternative to moving.
                # It means staying in the same cell and changing state from RG to RC.
                collect_action_outcome = state[t+1][r_prev][c_prev] == 'RC'
                
                # If the robot is on gold, it can either move OR collect.
                solver.add(Implies(state[t][r_prev][c_prev] == 'RG', Or(Or(possible_move_outcomes), collect_action_outcome)))
                
                # If the robot is NOT on gold, it can only move.
                solver.add(Implies(And(robot_at_prev_loc, state[t][r_prev][c_prev] != 'RG'), Or(possible_move_outcomes)))

    # 3. FOloowing lines modify cells based on state and action of robot.
    for t in range(maxSteps):
        for r in range(rowsCount):
            for c in range(colsCount):
                # Obstacles are static so their state will always remain same.
                solver.add(Implies(state[t][r][c] == 'O', state[t+1][r][c] == 'O'))
                
                # states which has not been interacted by robot, stays same.
                not_disturbed = And(Not(is_robot(state[t][r][c])), Not(is_robot(state[t+1][r][c])))
                solver.add(Implies(not_disturbed, state[t+1][r][c] == state[t][r][c]))

                # --- Changing cells ---
                # A. LOGIC FOR WHEN A ROBOT LEAVES A CELL
                robot_leaves = And(is_robot(state[t][r][c]), Not(is_robot(state[t+1][r][c])))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'R'), state[t+1][r][c] == '.'))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'RG'), state[t+1][r][c] == 'G'))
                solver.add(Implies(And(robot_leaves, state[t][r][c] == 'RC'), state[t+1][r][c] == 'C'))

                # B. LOGIC FOR WHEN A ROBOT ENTERS A CELL
                robot_enters = And(Not(is_robot(state[t][r][c])), is_robot(state[t+1][r][c]))
                solver.add(Implies(And(robot_enters, state[t][r][c] == '.'), state[t+1][r][c] == 'R'))
                solver.add(Implies(And(robot_enters, state[t][r][c] == 'G'), state[t+1][r][c] == 'RG'))
                solver.add(Implies(And(robot_enters, state[t][r][c] == 'C'), state[t+1][r][c] == 'RC'))
                # C. LOGIC FOR WHEN A ROBOT STAYS IN THE SAME CELL
                robot_stays = And(is_robot(state[t][r][c]), is_robot(state[t+1][r][c]))
                solver.add(Implies(And(robot_stays, state[t][r][c] == 'R'), state[t+1][r][c] == 'R'))
                solver.add(Implies(And(robot_stays, state[t][r][c] == 'RC'), state[t+1][r][c] == 'RC'))
#---------------------#


def add_collectAction_constraints(solver, state, rowsCount, colsCount, maxSteps):
    # This function would define the logic for collecting gold.
    # For example, if a robot is on a gold cell 'RG', the gold is considered collected.
    print("Adding collect action constraints...")
    for t in range(maxSteps):
        for r in range(rowsCount):
            for c in range(colsCount):
                # If a cell becomes 'RC', it must be because the robot was on 'RG' in the same cell
                # in the previous step. This defines the "collect" action.
                collect_action_occurred = And(
                    is_robot(state[t][r][c]), 
                    state[t+1][r][c] == 'RC'
                )
                precondition_for_collect = state[t][r][c] == 'RG'
                solver.add(Implies(collect_action_occurred, precondition_for_collect))
#---------------------#

def add_goal_constraints(solver, state, grid, rowsCount, colsCount, maxSteps):
    """
    Adds goal constraints to ensure all gold is collected by the final step.
    """
    print("Adding goal constraints...")
    
    # First find all golds
    gold_locations = []
    for r in range(rowsCount):
        for c in range(colsCount):
            if grid[r][c] == 'G':
                gold_locations.append((r, c))

    # no gold = no goal.
    if not gold_locations:
        print("No gold on the map to set a goal for.")
        return

    # Create a list of conditions, one for each piece of gold.
    all_gold_collected_conditions = []
    for r, c in gold_locations:
        # For a gold to be considered as collected, all of them should be either 'C' or 'RC' at the last step.
        # 'C' means it was collected, 'RC' means the robot was on it and collected it.
        is_collected = Or(state[maxSteps][r][c] == 'C', state[maxSteps][r][c] == 'RC')
        all_gold_collected_conditions.append(is_collected)
    
    solver.add(And(all_gold_collected_conditions))
    print(f"Goal set: All {len(gold_locations)} gold pieces must be collected.")


#---------------------#
# Main function to run the solver with different options.
def main():
    
    print("Starting Golds in MineField Solver...\n")
    while True:
        print("Please choose correct number for different options:")
        print("1. Solve Golds in MineField with default minefield.")
        print("2. Solve Golds in MineField with randomly generated planning instances.")
        print("3. Solve arbitrary generated planning instances. (Testing)")
        print("0. Exit.")
        choice = input("Enter your choice: ")

        if choice == '1':
            defaultMineFieldSolver()
        elif choice == '0':
            exit(0)
        elif choice == '2' or choice == '3':
            
            if choice == '2':
                # Placeholder for random generation logic
                print("Randomly generated planning instances are not implemented yet.")
            elif choice == '3':
                # Placeholder for testing logic
                print("Testing arbitrary generated planning instances is not implemented yet.")
            
        else:
            print("Invalid choice, please try again.")
#---------------------#

def defaultMineFieldSolver():
    # Define the minefield grid
    defaultMinefield = [
        ['.', 'G', 'O','.','O'],
        ['.', 'G', 'O','.','O'],
        ['O', '.', '.','G','O'],
        ['O', '.', '.','G','O'],
        ['O', '.', '.','G','O'],
    ]
    start_position = (0, 0)  # Starting position of the robot
    # Increased max_steps to allow enough time to find a solution for collecting all gold.
    max_steps = 20
    print("Default minefield:")
    print ("Grid:")
    for row in defaultMinefield:
        print(" ".join(row))
    print ("Starting position:", start_position)
    print ("Max steps allowed:", max_steps)
    goldsInMineFieldSolver(defaultMinefield, start_position, max_steps)


#---------------------#
def GridVisualization(grid):
    """
    Visualizes the grid in a readable format.
    Args:
        grid (list of list of str): The minefield represented as a 2D grid.
    """
    for row in grid:
        print(" ".join(row))
    print("\n")


if __name__ == "__main__":
    main()
