from z3 import * 

#EARLY DELIVERABLES TASK 3 (Develop code for SMT solving of a simple example problem (e.g., Sudoku, or job shop scheduling)).
# here I am going to solve a sudoku problem using z3 

#---------------------#
# Problem description:
#Sudoku is a logic-based combinatorial number-placement puzzle.
# The objective is to fill a 9×9 grid with digits so that each column, each row,
#  and each of the 9  3×3 subgrids that creates the grid (also called "blocks" or "regions") contain all of the digits from 1 to 9.
# Rules:
# 1. Each row must contain the numbers 1-9 without repetition.
# 2. Each column must contain the numbers 1-9 without repetition.
# 3. Each of the nine 3x3 subgrids must contain the numbers 1-9 without repetition.
#----------------------#

def printVisuallyBetterGrid(matrix):
    """
    Prints a 9x9 Sudoku grid in a visually formatted style.

    Args:
        matrix (list of list of int): A 9x9 grid representing the Sudoku puzzle or solution.
        Zeros (0) will be shown as dots for better readability.

    Returns:
        None
    """
    print("-" * 25)
    for i in range(9):
        row = ""
        for j in range(9):
            if j % 3 == 0:
                row += "| "
            val = matrix[i][j]
            row += (str(val) if val != 0 else ".") + " "
        row += "|"
        print(row)
        if (i + 1) % 3 == 0:
            print("-" * 25)


import time

def sudokuSolver(puzzle):
    """
    Solves a 9x9 Sudoku puzzle using the Z3 SMT solver.

    Args:
        puzzle (list of list of int): A 9x9 grid where 0 represents an empty cell 
        and 1–9 are given clues.

    Prints:
        The unsolved puzzle, the solved puzzle, and the time taken to solve.

    Returns:
        None
    """
    print("Unsolved Puzzle:")
    printVisuallyBetterGrid(puzzle)

    start_time = time.time()

    grid = [[Int(f'pos_{i}_{j}') for j in range(9)] for i in range(9)]
    solver = Solver()

    for i in range(9):
        for j in range(9):
            solver.add(And(grid[i][j] >= 1, grid[i][j] <= 9))
    for i in range(9):
        solver.add(Distinct(grid[i]))
    for j in range(9):
        solver.add(Distinct([grid[i][j] for i in range(9)]))
    for block1 in range(3):
        for block2 in range(3):
            solver.add(Distinct([grid[i][j] for i in range(block1*3, block1*3+3)
                                               for j in range(block2*3, block2*3+3)]))
    for i in range(9):
        for j in range(9):
            if puzzle[i][j] != 0:
                solver.add(grid[i][j] == puzzle[i][j])

    if solver.check() == sat:
        model = solver.model()
        solved = [[model.evaluate(grid[i][j]).as_long() for j in range(9)] for i in range(9)]

        end_time = time.time()
        elapsed = end_time - start_time

        print("Solved Sudoku:")
        printVisuallyBetterGrid(solved)
        print(f"Solved in {elapsed:.4f} seconds")
    else:
        print("No solution found.")


def main():
        

    easyLevel_puzzle = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    mediumLevel_puzzle = [
        [0, 0, 0, 0, 0, 0, 2, 0, 0],
        [0, 8, 0, 0, 0, 7, 0, 9, 0],
        [6, 0, 2, 0, 0, 0, 5, 0, 0],
        [0, 7, 0, 0, 6, 0, 0, 0, 0],
        [0, 0, 0, 9, 0, 1, 0, 0, 0],
        [0, 0, 0, 0, 2, 0, 0, 4, 0],
        [0, 0, 5, 0, 0, 0, 6, 0, 3],
        [0, 9, 0, 4, 0, 0, 0, 7, 0],
        [0, 0, 6, 0, 0, 0, 0, 0, 0]
    ]
    hardLevel_puzzle = [
        [0, 0, 0, 0, 0, 0, 0, 1, 2],
        [0, 0, 0, 0, 0, 0, 7, 0, 0],
        [0, 0, 0, 4, 0, 0, 0, 0, 0],
        [0, 0, 0, 0, 5, 0, 4, 0, 7],
        [0, 0, 8, 0, 0, 0, 3, 0, 0],
        [3, 0, 6, 0, 4, 0, 0, 0, 0],
        [0, 0, 0, 0, 0, 9, 0, 0, 0],
        [0, 0, 1, 0, 0, 0, 0, 0, 0],
        [2, 4, 0, 0, 0, 0, 0, 0, 0]
    ]

    print("Easy Level Sudoku:")
    sudokuSolver(easyLevel_puzzle)
    print("\nMedium Level Sudoku:")
    sudokuSolver(mediumLevel_puzzle)
    print("\nHard Level Sudoku:")
    sudokuSolver(hardLevel_puzzle)





main()