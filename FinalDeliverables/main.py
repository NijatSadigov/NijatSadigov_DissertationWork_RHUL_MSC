from DifferentPlanningInstances import run_arbitrary_tests, run_random_instance_mode
from GoldsInMineField import goldsInMineFieldSolver
from visualizer import visualize_solution


def defaultMineFieldSolver():
    # Define the minefield grid
    defaultMinefield = [
        ['.', 'G', 'O','.','O'],
        ['.', 'G', 'O','.','O'],
        ['O', '.', '.','G','O'],
        ['O', '.', '.','G','O'],
        ['O', '.', '.','G','O'],
    ]
    start_position = (0, 0)  # Start position of the robot
    max_steps = 20
    print("Default minefield:")
    print ("Grid:")
    for row in defaultMinefield:
        print(" ".join(row))
    print ("Starting position:", start_position)
    print ("Max steps allowed:", max_steps)
    solution=goldsInMineFieldSolver(defaultMinefield, start_position, max_steps)
    
    if solution:
        req= input("\nSolution found! Press 1 to visualize the solution. Press any other key to exit: ")
        if req == '1':
            visualize_solution(solution, len(defaultMinefield), len(defaultMinefield[0]))
        else:
            print("\nExiting without visualization.")
    else:
        print("\nNo solution to visualize.")


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
                run_random_instance_mode()
            elif choice == '3':
                # Placeholder for testing logic
                print("Testing arbitrary generated planning instances...")
                run_arbitrary_tests()
            
        else:
            print("Invalid choice, please try again.")
#---------------------#

#---------------------#


if __name__ == "__main__":
    main()
