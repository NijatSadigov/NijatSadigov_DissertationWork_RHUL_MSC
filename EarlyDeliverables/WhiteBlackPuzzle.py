from z3 import * 

# Following piece of code shows how to solve the WhiteBlackPuzzle using
# Satisfiability Modulo Theories (SMT) and Bounded Model Checking (BMC) with the Z3 solver.
# THis problem taken from CS5980 Autonomous intelligent systems, Final project task 3 which we did during class period in pddl.
# ----------------------------
# Problem Description:
# Puzzle consists of 4 empty positions. The initial setup is like this:
#   [Black, White, White, Empty]
#
# Valid Moves:
# 1. A tile may move into an adjacent empty cell (cost = 1).
# 2. A tile may jump over one tile into an empty cell two positions away (cost = 2).
# 3. At each step, at least one tile must move or jump.
# Goal:
# The goal is to arrange the tiles in a way that the black tile is the right-most tile,
# located at the rihght of both white tiles. The position of the empty cell does not matter.
#
# ----------------------------
def whiteBlackPuzzleSolver(inputState, maxSteps):
    """
    Solves the WhiteBlackPuzzle using Z3 SMT solver and bounded model checking.

    Args:
        inputState (list of str): The initial configuration of the puzzle.
            Example: ['B', 'W', 'W', 'E'] 
            where 'B' = black tile, 'W' = white tile, 'E' = empty space.
        maxSteps (int): Maximum number of steps (bound) allowed to reach the goal.

    Returns:
        None. Prints the solution steps if the goal is reachable within the given bound.
    """
    state = [
    [String(f'state_{t}_{i}') for i in range(4)]
    for t in range(maxSteps + 1)
    ]
    tile_names = ['B', 'W', 'E']
    # Add cost variables for each step
    cost = [Int(f'cost_{t}') for t in range(maxSteps + 1)]
    solver = Solver()
    # First rule: every tile must be in one of the three states
    for t in range(maxSteps + 1):
        for i in range(4):
            solver.add(Or([state[t][i] == tile for tile in tile_names]))
    # Initial state:
    for i in range(4):
        solver.add(state[0][i] == inputState[i])
    # Initial cost is zero
    solver.add(cost[0] == 0)
    # Transition rules
    add_transition_constraints(solver, state, cost, maxSteps)
    add_goal_constraints(solver, state, maxSteps)
    if solver.check() == sat:
        model = solver.model()
        # Extract the solution steps
        solution = []
        for t in range(maxSteps + 1):
            step = [model.evaluate(state[t][i]).as_string() for i in range(4)]
            step_cost = model.evaluate(cost[t]).as_long()
            solution.append((step, step_cost))
        total_cost = model.evaluate(cost[maxSteps]).as_long()
        # Print the solution steps
        print("Solution found:")
        for t, (step, step_cost) in enumerate(solution):
            print(f"Step {t}: {step} | Cost: {step_cost}")
        print(f"Total cost: {total_cost}")
    else:
        print("No solution found within the given bound.")

def add_transition_constraints(solver, state, cost, maxSteps):
    """
    Adds transition constraints for valid moves and jumps for each time step, and updates cost.
    """
    for t in range(maxSteps):
        transitions = []
        for i in range(4):
            # Move left
            if i > 0:
                transitions.append(
                    And(
                        state[t][i] != 'E', state[t][i - 1] == 'E',
                        state[t + 1][i - 1] == state[t][i],
                        state[t + 1][i] == 'E',
                        *[state[t + 1][j] == state[t][j] for j in range(4) if j != i and j != i - 1],
                        cost[t + 1] == cost[t] + 1
                    )
                )
            # Move right
            if i < 3:
                transitions.append(
                    And(
                        state[t][i] != 'E', state[t][i + 1] == 'E',
                        state[t + 1][i + 1] == state[t][i],
                        state[t + 1][i] == 'E',
                        *[state[t + 1][j] == state[t][j] for j in range(4) if j != i and j != i + 1],
                        cost[t + 1] == cost[t] + 1
                    )
                )
            # Jump left
            if i > 1:
                transitions.append(
                    And(
                        state[t][i] != 'E', state[t][i - 2] == 'E',
                        state[t + 1][i - 2] == state[t][i],
                        state[t + 1][i] == 'E',
                        *[state[t + 1][j] == state[t][j] for j in range(4) if j != i and j != i - 2],
                        cost[t + 1] == cost[t] + 2
                    )
                )
            # Jump right
            if i < 2:
                transitions.append(
                    And(
                        state[t][i] != 'E', state[t][i + 2] == 'E',
                        state[t + 1][i + 2] == state[t][i],
                        state[t + 1][i] == 'E',
                        *[state[t + 1][j] == state[t][j] for j in range(4) if j != i and j != i + 2],
                        cost[t + 1] == cost[t] + 2
                    )
                )
        solver.add(Or(*transitions))

def add_goal_constraints(solver, state, maxSteps):
    """
    Adds goal constraints: black tile is the right-most tile, to the right of both white tiles, empty can be anywhere.
    """
    # Enforce tile counts
    solver.add(Sum([If(state[maxSteps][i] == 'B', 1, 0) for i in range(4)]) == 1)
    solver.add(Sum([If(state[maxSteps][i] == 'W', 1, 0) for i in range(4)]) == 2)
    solver.add(Sum([If(state[maxSteps][i] == 'E', 1, 0) for i in range(4)]) == 1)
    # For all i, if state[maxSteps][i] == 'B', then for all j, if state[maxSteps][j] == 'W', i > j
    constraints = []
    for i in range(4):
        for j in range(4):
            if i != j:
                constraints.append(
                    Implies(
                        And(state[maxSteps][i] == 'B', state[maxSteps][j] == 'W'),
                        i > j
                    )
                )
    solver.add(And(constraints))
#---------------------#
def main():
    # Example input state
    inputState = ['B', 'W', 'W', 'E']  # Initial configuration
    maxSteps = 5  # Maximum number of steps to reach the goal
    whiteBlackPuzzleSolver(inputState, maxSteps)
if __name__ == "__main__":
    main()