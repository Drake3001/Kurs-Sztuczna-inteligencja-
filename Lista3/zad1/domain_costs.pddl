(define (domain transport-logistics-costs)
  (:requirements :strips :typing :action-costs)
  (:types city package truck plane ship)

  (:functions
    (total-cost) - number
  )

  (:predicates
    (at-truck ?t - truck ?c - city)
    (at-plane ?p - plane ?c - city)
    (at-ship ?s - ship ?c - city)
    (at-package ?p - package ?c - city)
    (in-truck ?p - package ?t - truck)
    (in-plane ?p - package ?pl - plane)
    (in-ship ?p - package ?s - ship)
    (road ?c1 - city ?c2 - city)
    (air-route ?c1 - city ?c2 - city)
    (sea-route ?c1 - city ?c2 - city)
    (has-airport ?c - city)
    (has-port ?c - city)
  )

  ;; === TRANSPORT DROGOWY (koszt: 10) ===
  (:action drive
    :parameters (?t - truck ?from - city ?to - city)
    :precondition (and (at-truck ?t ?from) (road ?from ?to))
    :effect (and
      (at-truck ?t ?to)
      (not (at-truck ?t ?from))
      (increase (total-cost) 10)
    )
  )

  ;; === TRANSPORT LOTNICZY (koszt: 50) ===
  (:action fly
    :parameters (?pl - plane ?from - city ?to - city)
    :precondition (and
      (at-plane ?pl ?from)
      (has-airport ?from)
      (has-airport ?to)
      (air-route ?from ?to)
    )
    :effect (and
      (at-plane ?pl ?to)
      (not (at-plane ?pl ?from))
      (increase (total-cost) 50)
    )
  )

  ;; === TRANSPORT WODNY (koszt: 5) ===
  (:action sail
    :parameters (?s - ship ?from - city ?to - city)
    :precondition (and
      (at-ship ?s ?from)
      (has-port ?from)
      (has-port ?to)
      (sea-route ?from ?to)
    )
    :effect (and
      (at-ship ?s ?to)
      (not (at-ship ?s ?from))
      (increase (total-cost) 5)
    )
  )

  ;; === ZAŁADUNEK / ROZŁADUNEK - CIĘŻARÓWKA (koszt: 1) ===
  (:action load-truck
    :parameters (?p - package ?t - truck ?c - city)
    :precondition (and (at-package ?p ?c) (at-truck ?t ?c))
    :effect (and
      (in-truck ?p ?t)
      (not (at-package ?p ?c))
      (increase (total-cost) 1)
    )
  )

  (:action unload-truck
    :parameters (?p - package ?t - truck ?c - city)
    :precondition (and (in-truck ?p ?t) (at-truck ?t ?c))
    :effect (and
      (at-package ?p ?c)
      (not (in-truck ?p ?t))
      (increase (total-cost) 1)
    )
  )

  ;; === ZAŁADUNEK / ROZŁADUNEK - SAMOLOT (koszt: 2) ===
  (:action load-plane
    :parameters (?p - package ?pl - plane ?c - city)
    :precondition (and (at-package ?p ?c) (at-plane ?pl ?c))
    :effect (and
      (in-plane ?p ?pl)
      (not (at-package ?p ?c))
      (increase (total-cost) 2)
    )
  )

  (:action unload-plane
    :parameters (?p - package ?pl - plane ?c - city)
    :precondition (and (in-plane ?p ?pl) (at-plane ?pl ?c))
    :effect (and
      (at-package ?p ?c)
      (not (in-plane ?p ?pl))
      (increase (total-cost) 2)
    )
  )

  ;; === ZAŁADUNEK / ROZŁADUNEK - STATEK (koszt: 1) ===
  (:action load-ship
    :parameters (?p - package ?s - ship ?c - city)
    :precondition (and (at-package ?p ?c) (at-ship ?s ?c))
    :effect (and
      (in-ship ?p ?s)
      (not (at-package ?p ?c))
      (increase (total-cost) 1)
    )
  )

  (:action unload-ship
    :parameters (?p - package ?s - ship ?c - city)
    :precondition (and (in-ship ?p ?s) (at-ship ?s ?c))
    :effect (and
      (at-package ?p ?c)
      (not (in-ship ?p ?s))
      (increase (total-cost) 1)
    )
  )
)
