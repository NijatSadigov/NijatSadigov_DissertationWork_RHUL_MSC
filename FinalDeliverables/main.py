from DifferentPlanningInstances import run_arbitrary_tests, run_random_instance_mode
from GoldsInMineField import solve_minefield_plan
from visualizer import visualize_solution

def solve_default_minefield():
    """Runs the solver on a default field with predefined constraints."""
    default_minefield = [
        ['.', 'G', 'O', '.', 'O'],
        ['.', 'G', 'O', '.', 'O'],
        ['O', '.', '.', 'G', 'O'],
        ['O', '.', '.', 'G', 'O'],
        ['O', '.', '.', 'G', 'O'],
    ]
    start_position = (0, 0)
    max_steps = 25
    
    costs = {'move': 1, 'collect': 2, 'stay': 0}
    max_total_cost = 30
    
    print("\n--- Solving Default Minefield with Cost Constraints ---")
    print("Grid:")
    for row in default_minefield:
        print(" ".join(row))
    print("Starting position:", start_position)
    print("Max steps allowed:", max_steps)
    print(f"Costs: Move={costs['move']}, Collect={costs['collect']}, Stay={costs['stay']}")
    print(f"Maximum allowed cost: {max_total_cost}")

    solution, final_cost, _ = solve_minefield_plan(
        default_minefield, start_position, max_steps, max_cost=max_total_cost, costs=costs
    )
    
    if solution:
        print(f"\nSolution found with a total cost of: {final_cost}!")
        if input("Press 1 to visualize the solution. Press any other key to exit: ") == '1':
            visualize_solution(solution, len(default_minefield), len(default_minefield[0]), final_cost=final_cost, costs=costs)
        else:
            print("\nExiting without visualization.")
    else:
        print("\nNo solution found with the given constraints.")

def main():
    """Main function to run the solver with different options."""
    print("Starting Golds in MineField Solver...\n")
    while True:
        print("\nPlease choose an option:")
        print("1. Solve the default minefield (with costs).")
        print("2. Solve a randomly generated instance.")
        print("3. Run arbitrary test cases.")
        print("0. Exit.")
        choice = input("Enter your choice: ")

        if choice == '1':
            solve_default_minefield()
        elif choice == '2':
            run_random_instance_mode()
        elif choice == '3':
            run_arbitrary_tests()
        elif choice == '0':
            print("Exiting.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main()