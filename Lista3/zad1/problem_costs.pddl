(define (problem deliver-packages-costs)
  (:domain transport-logistics-costs)

  (:objects
    wroclaw poznan gdansk krakow warszawa - city
    paczka1 paczka2 paczka3 paczka4 - package
    truck1 truck2 - truck
    plane1 - plane
    ship1 - ship
  )

  (:init
    (= (total-cost) 0)

    ;; --- Pozycje pojazdów ---
    (at-truck truck1 wroclaw)
    (at-truck truck2 warszawa)
    (at-plane plane1 wroclaw)
    (at-ship ship1 gdansk)

    ;; --- Pozycje paczek ---
    (at-package paczka1 wroclaw)   ; cel: gdansk
    (at-package paczka2 krakow)    ; cel: poznan
    (at-package paczka3 warszawa)  ; cel: wroclaw
    (at-package paczka4 gdansk)    ; cel: krakow

    ;; --- Drogi (dwukierunkowe) ---
    (road wroclaw poznan) (road poznan wroclaw)
    (road poznan gdansk)  (road gdansk poznan)
    (road wroclaw krakow) (road krakow wroclaw)
    (road krakow warszawa) (road warszawa krakow)
    (road poznan warszawa) (road warszawa poznan)

    ;; --- Trasy lotnicze (dwukierunkowe) ---
    (air-route wroclaw warszawa) (air-route warszawa wroclaw)
    (air-route wroclaw gdansk)   (air-route gdansk wroclaw)

    ;; --- Trasy morskie (dwukierunkowe) ---
    (sea-route gdansk warszawa) (sea-route warszawa gdansk)

    ;; --- Infrastruktura ---
    (has-airport wroclaw)
    (has-airport warszawa)
    (has-airport gdansk)
    (has-port gdansk)
    (has-port warszawa)
  )

  (:goal
    (and
      (at-package paczka1 gdansk)
      (at-package paczka2 poznan)
      (at-package paczka3 wroclaw)
      (at-package paczka4 krakow)
    )
  )

  (:metric minimize (total-cost))
)
