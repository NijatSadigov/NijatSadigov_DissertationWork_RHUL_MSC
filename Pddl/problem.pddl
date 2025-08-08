;; PDDL Problem File for the Default Minefield Instance (Complete)

(define (problem default-minefield-instance)
  (:domain minefield)

  (:objects
    ;; Define all cell locations, e.g., loc-row-col
    loc-0-0 loc-0-1 loc-0-2 loc-0-3 loc-0-4
    loc-1-0 loc-1-1 loc-1-2 loc-1-3 loc-1-4
    loc-2-0 loc-2-1 loc-2-2 loc-2-3 loc-2-4
    loc-3-0 loc-3-1 loc-3-2 loc-3-3 loc-3-4
    loc-4-0 loc-4-1 loc-4-2 loc-4-3 loc-4-4 - location

    ;; Define the single robot
    robot1 - robot

    ;; Define the gold pieces
    gold1 gold2 gold3 gold4 gold5 - gold
  )

  (:init
    ;; --- Robot's Initial Position ---
    (at robot1 loc-0-0)

    ;; --- Gold Locations ---
    (gold-at gold1 loc-0-1)
    (gold-at gold2 loc-1-1)
    (gold-at gold3 loc-2-3)
    (gold-at gold4 loc-3-3)
    (gold-at gold5 loc-4-3)

    ;; --- Obstacle Locations ---
    (obstacle-at loc-0-2)
    (obstacle-at loc-0-4)
    (obstacle-at loc-1-2)
    (obstacle-at loc-1-4)
    (obstacle-at loc-2-0)
    (obstacle-at loc-2-4)
    (obstacle-at loc-3-0)
    (obstacle-at loc-3-4)
    (obstacle-at loc-4-0)
    (obstacle-at loc-4-4)

    ;; --- Adjacency Predicates (Complete for 5x5 Grid) ---
    (adjacent loc-0-0 loc-0-1) (adjacent loc-0-1 loc-0-0)
    (adjacent loc-0-0 loc-1-0) (adjacent loc-1-0 loc-0-0)
    (adjacent loc-0-1 loc-0-2) (adjacent loc-0-2 loc-0-1)
    (adjacent loc-0-1 loc-1-1) (adjacent loc-1-1 loc-0-1)
    (adjacent loc-0-2 loc-0-3) (adjacent loc-0-3 loc-0-2)
    (adjacent loc-0-2 loc-1-2) (adjacent loc-1-2 loc-0-2)
    (adjacent loc-0-3 loc-0-4) (adjacent loc-0-4 loc-0-3)
    (adjacent loc-0-3 loc-1-3) (adjacent loc-1-3 loc-0-3)
    (adjacent loc-0-4 loc-1-4) (adjacent loc-1-4 loc-0-4)
    (adjacent loc-1-0 loc-1-1) (adjacent loc-1-1 loc-1-0)
    (adjacent loc-1-0 loc-2-0) (adjacent loc-2-0 loc-1-0)
    (adjacent loc-1-1 loc-1-2) (adjacent loc-1-2 loc-1-1)
    (adjacent loc-1-1 loc-2-1) (adjacent loc-2-1 loc-1-1)
    (adjacent loc-1-2 loc-1-3) (adjacent loc-1-3 loc-1-2)
    (adjacent loc-1-2 loc-2-2) (adjacent loc-2-2 loc-1-2)
    (adjacent loc-1-3 loc-1-4) (adjacent loc-1-4 loc-1-3)
    (adjacent loc-1-3 loc-2-3) (adjacent loc-2-3 loc-1-3)
    (adjacent loc-1-4 loc-2-4) (adjacent loc-2-4 loc-1-4)
    (adjacent loc-2-0 loc-2-1) (adjacent loc-2-1 loc-2-0)
    (adjacent loc-2-0 loc-3-0) (adjacent loc-3-0 loc-2-0)
    (adjacent loc-2-1 loc-2-2) (adjacent loc-2-2 loc-2-1)
    (adjacent loc-2-1 loc-3-1) (adjacent loc-3-1 loc-2-1)
    (adjacent loc-2-2 loc-2-3) (adjacent loc-2-3 loc-2-2)
    (adjacent loc-2-2 loc-3-2) (adjacent loc-3-2 loc-2-2)
    (adjacent loc-2-3 loc-2-4) (adjacent loc-2-4 loc-2-3)
    (adjacent loc-2-3 loc-3-3) (adjacent loc-3-3 loc-2-3)
    (adjacent loc-2-4 loc-3-4) (adjacent loc-3-4 loc-2-4)
    (adjacent loc-3-0 loc-3-1) (adjacent loc-3-1 loc-3-0)
    (adjacent loc-3-0 loc-4-0) (adjacent loc-4-0 loc-3-0)
    (adjacent loc-3-1 loc-3-2) (adjacent loc-3-2 loc-3-1)
    (adjacent loc-3-1 loc-4-1) (adjacent loc-4-1 loc-3-1)
    (adjacent loc-3-2 loc-3-3) (adjacent loc-3-3 loc-3-2)
    (adjacent loc-3-2 loc-4-2) (adjacent loc-4-2 loc-3-2)
    (adjacent loc-3-3 loc-3-4) (adjacent loc-3-4 loc-3-3)
    (adjacent loc-3-3 loc-4-3) (adjacent loc-4-3 loc-3-3)
    (adjacent loc-3-4 loc-4-4) (adjacent loc-4-4 loc-3-4)
    (adjacent loc-4-0 loc-4-1) (adjacent loc-4-1 loc-4-0)
    (adjacent loc-4-1 loc-4-2) (adjacent loc-4-2 loc-4-1)
    (adjacent loc-4-2 loc-4-3) (adjacent loc-4-3 loc-4-2)
    (adjacent loc-4-3 loc-4-4) (adjacent loc-4-4 loc-4-3)
  )

  (:goal
    (and
      (collected gold1)
      (collected gold2)
      (collected gold3)
      (collected gold4)
      (collected gold5)
    )
  )
)
