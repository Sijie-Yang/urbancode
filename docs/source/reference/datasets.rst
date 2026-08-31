Datasets
========

Committed fixtures used by Recipes and Workflows. Live downloads
are not part of the offline docs build.

Rules
-----

1. Real data only for urban conclusions.
2. Synthetic fixtures live under ``examples/data/contracts/`` or
   ``tests/fixtures/synthetic/`` and set ``synthetic: true``.
3. Every real directory has ``manifest.json``, ``LICENSE.md``,
   checksums, and a build script.
4. CI does not hit Overpass or STAC.
5. Illustrative street-view points stay labelled illustrative.

Real pockets
------------

.. list-table::
   :header-rows: 1
   :widths: 18 20 14 16 16 16

   * - dataset_id
     - City
     - Extent
     - Metric CRS
     - Path
     - Kind
   * - punggol
     - Punggol, Singapore
     - 2 km × 2 km
     - EPSG:32648
     - ``examples/data/real/punggol``
     - observed OSM + S2 + DEM
   * - kallio
     - Kallio, Helsinki
     - 2 km × 2 km
     - EPSG:32635
     - ``examples/data/real/kallio``
     - observed OSM + S2 + DEM
   * - greenwich_village
     - Greenwich Village, New York
     - 2 km × 2 km
     - UTM (NY)
     - ``examples/data/real/greenwich_village``
     - observed OSM + S2 + DEM

Shared layers: ``streets``, ``buildings``, ``parks``, ``pois``,
``sentinel2``, ``dem``. Sentinel-2 items are June–August 2024
calendar windows. Punggol is equatorial; do not treat NDVI
differences as city essence.

Punggol (detail)
----------------

* Boundary: bbox in the manifest, not the municipal outline.
* Sentinel-2 item: ``S2B_MSIL2A_20240728T031519_R118_T48NUG_20240728T071428``
* Date: 2024-07-28; bands B02, B03, B04, B08, B11 at 10 m.
* DEM: Copernicus GLO-30.
* License: ODbL + Copernicus Sentinel + Copernicus DEM.
* Recipes: network, imagery, units, fusion, punggol urban profile.
* ``examples/data/punggol_pocket`` is an archived smaller extract
  (different bbox and bands). Do not mix it with this fixture.

Climate
-------

``examples/data/real/climate`` — Open-Meteo archive fields at each
pocket centre. Air temperature, humidity, and wind are observed.
Mean radiant temperature is modelled. Intended recipe:
:doc:`/reference/recipes/climate/utci_real`.

Street view
-----------

``examples/data/real/streetview`` — geotagged, redistributable
Wikimedia Commons photos. This is not a Mapillary dump and not a
street-level census. ``uc.svi.fetch`` stays live-only.

Research cases
--------------

``examples/data/research_cases/thermal_comfort_in_sight`` — license,
citation, and checksums for the Thermal Comfort in Sight case.
Photos stay in the streetview fixture. Eight Punggol Commons
photos are a sample, not a city-scale map. TCIS weights are not
committed.

``examples/data/research_cases/heat_resilience_in_sight`` — city-month
SHR summaries for an eight-city **application**, not a validation.
Singapore n = 21,772 is not the TCIS 92,233 survey set. Per-image
VATA and the hourly climate cache stay out of Git.

Synthetic / contracts
---------------------

``examples/data/contracts/`` holds schema-only pockets (including
relocated Helsinki / NYC synthetic leftovers). Use them to test
unit IDs and combine checks. Do not plot them as city results.

Build and validate
------------------

::

   python scripts/data/build_real_pockets.py
   python scripts/data/build_climate_cases.py
   python scripts/data/build_streetview_cases.py
   python scripts/data/dataset_manifest.py

Manifest schema: ``examples/data/real/_schema.md``.

Related pages
-------------

* Workflow: :doc:`/workflows/multi_city_comparison`
* Concept: :doc:`/concepts/provenance_quality`
* City format: :doc:`/reference/city_format`
