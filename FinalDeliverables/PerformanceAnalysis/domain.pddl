;; PDDL Domain for the Robot in a Minefield Problem
;;
;; This domain defines the actions a robot can take to navigate a grid,
;; avoid obstacles, and collect all pieces of gold.

(define (domain minefield)
  
  (:requirements :strips :typing  :negative-preconditions)

  (:types
    robot gold location - object
  )

  (:predicates
    ;; --- Robot State ---
    (at ?r - robot ?l - location)      ; The robot ?r is at a specific ?location

    ;; --- Grid Properties ---
    (gold-at ?g - gold ?l - location) ; A piece of gold ?g is at a ?location
    (obstacle-at ?l - location)     ; There is an obstacle at a ?location
    (adjacent ?l1 - location ?l2 - location) ; Location ?l1 is adjacent to ?l2

    ;; --- Goal Tracking ---
    (collected ?g - gold)             ; The piece of gold ?g has been collected
  )

  ;; --- ACTION: Move ---
  ;; The robot moves from a starting location to an adjacent one.
  (:action move
    :parameters (?r - robot ?from - location ?to - location)
    :precondition (and
                    (at ?r ?from)             ; Robot must be at the starting location
                    (adjacent ?from ?to)      ; The destination must be adjacent
                    (not (obstacle-at ?to))   ; The destination cannot be an obstacle
                  )
    :effect (and
              (not (at ?r ?from))           ; Robot is no longer at the starting location
              (at ?r ?to)                   ; Robot is now at the new location
            )
  )

  ;; --- ACTION: Collect ---
  ;; The robot collects a piece of gold at its current location.
  (:action collect
    :parameters (?r - robot ?g - gold ?l - location)
    :precondition (and
                    (at ?r ?l)                ; Robot must be at the location of the gold
                    (gold-at ?g ?l)           ; Gold must be at that same location
                    (not (collected ?g))      ; The gold must not have been collected already
                  )
    :effect (and
              (collected ?g)                ; The gold is now marked as collected
            )
  )
)