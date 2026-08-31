Choose your path
================

After :doc:`first_project`, pick one track. Each page lists what it
needs and whether it stays offline.

.. list-table::
   :header-rows: 1
   :widths: 18 28 18 18 18

   * - Path
     - Start here
     - Extra
     - Mode
     - Prerequisite
   * - GIS / units / fusion
     - :doc:`/workflows/punggol_urban_profile`
     - ``standard``
     - offline
     - :doc:`quickstart`
   * - Street-view imagery
     - :doc:`/workflows/street_experience`
     - ``svi`` (fetch needs ``download``)
     - offline catalog
     - :doc:`/domains/streetview`
   * - Climate and perception
     - :doc:`/workflows/heat_exposure` then
       :doc:`/workflows/research_cases/thermal_comfort_in_sight`
     - ``climate`` / ``perception``
     - offline summaries; full TCIS is heavy
     - :doc:`/domains/climate`
   * - Research reproduction
     - :doc:`/workflows/research_cases/index`
     - ``perception`` or committed CSVs
     - Git-reproducible / HF cache / external store
     - the paper page for that case

Labels
------

* **offline** — committed fixtures under ``examples/data/real/``.
* **live** — Overpass, STAC, or ``uc.svi.fetch``. Not in default CI.
* **heavy** — TCIS weights or the 92,233-image store. Not in Git.

The five canonical workflows are Punggol urban profile, green
accessibility, heat exposure, street experience, and multi-city
comparison.

Next: :doc:`/workflows/index`.
