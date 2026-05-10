(define (problem clean-all-rooms)
  (:domain vacuum-robot)
  (:objects
    robot - robot
    pokoj1 pokoj2 pokoj3 - room
  )
  (:init
    (at robot pokoj1)
    (dirty pokoj1)
    (dirty pokoj2)
    (dirty pokoj3)
  )
  (:goal
    (and (clean pokoj1) (clean pokoj2) (clean pokoj3))
  )
)
