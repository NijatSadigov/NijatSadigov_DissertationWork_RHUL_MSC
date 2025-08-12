# pddl_generator.py

def generate_pddl_problem(grid, start_pos, problem_name="autogen-problem", domain_name="minefield", filename="generated-problem.pddl"):
    """
    Generates PDDL problem file from  grid input then saves it.

    Args:
        grid (list of lists):  2D list representing the minefield.
        start_pos (tuple): (row, col) starting position of the robot.
        problem_name (str): name for the PDDL problem.
        domain_name (str):  name of the PDDL domain to reference.
        filename (str):  path to save the generated .pddl file.
    """
    rows = len(grid)
    cols = len(grid[0])
    
    # --- 1. dedect objects ---
    locations = [f"loc-{r}-{c}" for r in range(rows) for c in range(cols)]
    gold_locations = [(r, c) for r in range(rows) for c in range(cols) if grid[r][c] == 'G']
    gold_objects = [f"gold{i+1}" for i in range(len(gold_locations))]
    gold_map = {loc: obj for loc, obj in zip(gold_locations, gold_objects)}

    # --- 2. Build PDDL Components as Strings ---

    # set (:objects)
    objects_pddl = "(:objects\n"
    objects_pddl += "    robot1 - robot\n"
    if locations:
        objects_pddl += f"    {' '.join(locations)} - location\n"
    if gold_objects:
        objects_pddl += f"    {' '.join(gold_objects)} - gold\n"
    objects_pddl += ")\n"

    # set (:init)
    init_pddl = "(:init\n"
    # set robot position
    init_pddl += f"    (at robot1 loc-{start_pos[0]}-{start_pos[1]})\n\n"
    # set gold and obstacles
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 'G':
                init_pddl += f"    (gold-at {gold_map[(r,c)]} loc-{r}-{c})\n"
            elif grid[r][c] == 'O':
                init_pddl += f"    (obstacle-at loc-{r}-{c})\n"
    init_pddl += "\n"
    # set adjacency
    for r in range(rows):
        for c in range(cols):
            # Check right neighbor
            if c + 1 < cols:
                init_pddl += f"    (adjacent loc-{r}-{c} loc-{r}-{c+1})\n"
                init_pddl += f"    (adjacent loc-{r}-{c+1} loc-{r}-{c})\n"
            # check bottom neighbor
            if r + 1 < rows:
                init_pddl += f"    (adjacent loc-{r}-{c} loc-{r+1}-{c})\n"
                init_pddl += f"    (adjacent loc-{r+1}-{c} loc-{r}-{c})\n"
    init_pddl += ")\n"
    
    # set (:goal)
    goal_pddl = "(:goal (and\n"
    if not gold_objects:
        goal_pddl = "(:goal (and))\n" # empty goal if no gold
    else:
        for gold_obj in gold_objects:
            goal_pddl += f"    (collected {gold_obj})\n"
        goal_pddl += "))\n"

    # --- 3. write final code ---
    pddl_content = (
        f"(define (problem {problem_name})\n"
        f"  (:domain {domain_name})\n\n"
        f"{objects_pddl}\n"
        f"{init_pddl}\n"
        f"{goal_pddl}"
        f")\n"
    )

    with open(filename, "w") as f:
        f.write(pddl_content)