Coverage, quality, and provenance
=================================

Urban question
--------------

Where did this number come from, and how complete is the unit?

Result first
------------

The Punggol save directory looks like::

   punggol_indicators/
     records.csv
     records.parquet
     result.json
     units.gpkg
     provenance/receipts.jsonl

``receipts.jsonl`` holds the source Layer stamp plus ``aggregate``
and ``combine`` steps. That is a list of compute steps, not a
StreetRAG derivation graph.

What you will learn
-------------------

* Source, processing, and model provenance.
* Spatial and temporal coverage.
* Observed / modelled / assumed / synthetic labels.
* Quality flags you will actually see.

Four kinds of provenance
------------------------

* **Source** — OSM extract, Sentinel-2 item ID, Open-Meteo timestamp,
  Wikimedia file. See the dataset :doc:`/reference/datasets`.
* **Processing** — function name, parameters (radius, cell size,
  statistic), backend package.
* **Model** — TCIS weights, Places365, modelled mean radiant
  temperature. A model score is not a field measurement.
* **Coverage** — fraction of the unit that intersected the source.
  Missing stays null.

Honesty labels
--------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Label
     - Meaning in this project
   * - observed
     - OSM geometries, Sentinel-2 reflectance, Open-Meteo T/RH/wind,
       geotagged Commons photos
   * - modelled
     - MRT set equal to air temperature; TCIS / Places365 scores
   * - derived
     - NDVI, slope, reachability, zonal means
   * - assumed
     - hillshade azimuth/altitude; walk network type
   * - synthetic
     - contract fixtures under ``examples/data/contracts/`` only

Synthetic fixtures must not be described as city observations.

Quality flags
-------------

Flags you will see on the Punggol and street-view runs:

* ``nodata`` — no value
* ``partial_coverage`` / ``low_coverage`` — raster fraction
* ``no_network`` / ``no_observation`` — empty join
* ``synthetic_location`` — street-view point placed for illustration
* ``modelled_mrt`` — radiant temperature was not measured

Read ``value`` together with ``coverage`` and flags.

Related pages
-------------

* Dataset manifests: :doc:`/reference/datasets`
* City on-disk format: :doc:`/reference/city_format`
* Workflow: :doc:`/workflows/punggol_urban_profile`

Use UrbanCode when you need receipts next to the table.
Use the upstream package directly when you are not persisting a
study.
