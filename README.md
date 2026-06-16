# Satisfiability Modulo Theories and Bounded Model Checking for AI Planning

**MSc Individual Project — Royal Holloway, University of London**
MSc in Artificial Intelligence · Department of Computer Science · September 2025
Author: **Nijat Sadigov**

This repository contains the software developed for my MSc dissertation, which
investigates how **Satisfiability Modulo Theories (SMT)** and **Bounded Model
Checking (BMC)** can be used to solve AI planning problems. The planning task is
re-framed as a formal-verification problem: a 2-D grid-world ("MineField") is
encoded as a single logical formula and solved with the **Z3 SMT solver**. A
satisfying model corresponds to a verified plan. The planner is extended to
support **cost constraints**, ships with a **Pygame** visualiser, and includes a
**performance-analysis harness** that benchmarks the SMT planner against the
classical **Fast Downward** planner.

The full write-up is in [`Dissertation.pdf`](Dissertation.pdf).

---

## The MineField problem

A robot starts on a cell of an `N × N` grid and must collect every gold piece
while avoiding obstacles. Each cell is encoded by a short symbol:

| Symbol | Meaning                         |
|:------:|---------------------------------|
| `.`    | Empty cell                      |
| `G`    | Gold                            |
| `O`    | Obstacle (impassable)           |
| `R`    | Robot on an empty cell          |
| `RG`   | Robot on a gold cell            |
| `RC`   | Robot on a collected-gold cell  |
| `C`    | Collected-gold cell (empty)     |

The robot may move to an adjacent non-obstacle cell, *stay*, or *collect* gold it
is standing on. The solver searches over a bounded horizon of `k` steps
(`max_steps`): the grid state at every step `0..k` is a set of Z3 variables, and
transition / frame / goal constraints are added so that any satisfying assignment
is a valid plan. With cost constraints enabled, each `move` / `collect` / `stay`
action carries a configurable cost and the plan must stay within a budget.

---

## Repository structure

```
.
├── Dissertation.pdf                     # Full dissertation
├── README.md
├── EarlyDeliverables/                   # Standalone learning prototypes
│   ├── Sudoku_z3Solver.py               #   Sudoku solved with Z3 (SMT demo)
│   └── WhiteBlackPuzzle.py              #   White/Black puzzle (BMC demo)
└── FinalDeliverables/
    ├── main.py                          # ENTRY POINT — interactive SMT planner
    ├── GoldsInMineField.py              # Core BMC/SMT encoding + Z3 solver
    ├── DifferentPlanningInstances.py    # Random instance generation + test suite
    ├── visualizer.py                    # Pygame step-by-step path visualiser
    └── PerformanceAnalysis/
        ├── PerformanceAnalyzer.py       # Interactive benchmark / analysis menu
        ├── SampleMaker.py               # Grid generators for benchmarks
        ├── pddl_generator.py            # Writes PDDL problem files
        ├── domain.pddl                  # MineField PDDL domain
        ├── fast-downward.sif            # Singularity image of Fast Downward (Linux)
        ├── benchmark_results.csv        # Accumulated benchmark output
        └── temp-problem-*.pddl          # Auto-generated PDDL problem artifacts
```

---

## Requirements

| Component        | Needed for                          | Install                  |
|------------------|-------------------------------------|--------------------------|
| Python ≥ 3.8     | Everything                          | python.org               |
| `z3-solver`      | Core planner (all of `FinalDeliverables`, both early demos) | `pip install z3-solver`  |
| `pygame`         | Solution visualiser (imported by `main.py`) | `pip install pygame`     |
| `matplotlib`     | Performance-analysis plots (optional) | `pip install matplotlib` |
| Fast Downward    | Comparative benchmarking only (option 5) | `fast-downward.sif` (Singularity/Apptainer) — **Linux only** |

Quick start — install everything in one command:

```bash
pip install -r requirements.txt
```

> **Note on `pygame`:** On very recent Python versions where `pygame` has no
> wheel yet, the community fork works as a drop-in replacement:
> `pip install pygame-ce`.

---

## Running the project

### 1. The SMT planner (main entry point)

```bash
cd FinalDeliverables
python main.py
```

This launches an interactive menu:

1. **Solve the default minefield (with costs)** — runs the planner on a
   predefined grid with a cost budget, then optionally visualises the path.
2. **Solve a randomly generated instance** — prompts for grid size, gold count,
   obstacle count, horizon `k`, and optional cost constraints.
3. **Run arbitrary test cases** — a predefined suite that checks planner
   correctness (PASS / FAIL printed to the console).
4. **Exit.**

**Visualiser controls:** `←` / `→` step through the plan, `Esc` to quit.

### 2. The performance analyzer

```bash
cd FinalDeliverables/PerformanceAnalysis
python PerformanceAnalyzer.py
```

Menu options:

- **1–4 — Z3 SMT solver analysis:** isolate one variable (grid size, max steps
  `k`, gold count, or obstacle density) and plot solve time / plan length.
- **5 — Comparative analysis:** benchmark the SMT planner against Fast Downward
  configurations (**A\* with LMCut**, **A\* with hMax**, **LAMA**) and optionally
  Z3. This generates PDDL problems on the fly and runs the `fast-downward.sif`
  image, so it **requires Linux with Singularity/Apptainer** and the
  `fast-downward.sif` file present in this folder.

Plots require `matplotlib`; without it the analysis still runs but plotting is
skipped (a warning is printed). Results are appended to `benchmark_results.csv`.

### 3. Early prototypes

```bash
cd EarlyDeliverables
python Sudoku_z3Solver.py     # SMT demonstration: Sudoku with Z3
python WhiteBlackPuzzle.py    # BMC demonstration: White/Black puzzle
```

---

## Platform notes

- **Core planner (`main.py`) and both early demos are cross-platform** —
  verified on Windows 11 (Python 3.14) and originally developed on Ubuntu. They
  depend only on `z3-solver` (and `pygame` for the visualiser).
- **Comparative benchmarking (option 5) is Linux-only**, because it invokes the
  `fast-downward.sif` Singularity/Apptainer container. The other analysis modes
  (options 1–4) are pure Z3 and run anywhere.
- **Windows filename compatibility:** the project was first developed on Ubuntu,
  where the auto-generated temporary PDDL files for the A\* planners contained a
  `*` character (e.g. `temp-problem-A*-with-LMCut.pddl`). `*` is illegal in
  Windows filenames, so those files use `Star` / `AStar` instead
  (`temp-problem-AStar-with-LMCut.pddl`). The filename-generation code in
  `PerformanceAnalyzer.py` sanitises `*` → `Star` accordingly, while keeping the
  human-readable `A*` labels in plots and in `benchmark_results.csv`.

---

## How it works (brief)

The planner in `GoldsInMineField.py` builds a Z3 model with one string variable
per cell per time-step over a horizon of `k` steps, then asserts:

- **Initial state** — fixes the grid and the robot's starting cell at `t = 0`.
- **Transition model** — legal moves to adjacent non-obstacle cells, the
  *collect* action, and *frame axioms* keeping unaffected cells unchanged.
- **Goal** — every gold cell is in a collected state (`C` / `RC`); with costs
  enabled, the goal must additionally be reached within the cost budget.

If Z3 reports `sat`, the satisfying model is decoded into a step-by-step plan
(truncated at the first step where the goal is met). The performance harness
encodes the same instances as PDDL (`pddl_generator.py` + `domain.pddl`) so that
Fast Downward can solve them for comparison.
