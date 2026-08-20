Roadmap
=======

Shipped
-------

* ``StudyArea``, ``City`` / ``Layer``, ``AnalysisUnits``
* ``IndicatorResult`` with coverage, quality flags, and receipts
* ``fusion.aggregate`` for raster, graph, polygon, point, and table
* ``uc.streetview`` as the official street-view implementation
* Five research workflows on real 2 km pockets (Punggol, Kallio,
  Greenwich Village)
* ``uc.images.from_table``, ``uc.perception.thermal_affordance``,
  and the Thermal Comfort in Sight research case

``SCHEMA_VERSION`` stays 1. ``import urbancode`` stays light.

Later
-----

* City Landscape in Sight (window-view perception, H3, TrueSkill,
  spatial CV, local Moran / hotspots). Design only; no public API
  in this release.
* Morphology / Momepy named functions
* PySAL spatial stats
* Mobility
* ``uc.*.analyze`` recipes
* Live observatory tutorials (network required)

Those items are planned. They are not public exports.

StreetRAG is a future downstream consumer.
