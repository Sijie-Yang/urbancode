15-minute quickstart
====================

Urban question
--------------

How green is each 250 m cell in the Punggol pocket, and how many
street nodes can you reach from that cell?

Result first
------------

.. figure:: /_static/recipes/fusion/combine_punggol.png
   :alt: Combined NDVI on the Punggol 250 m grid
   :width: 100%

   Mean Sentinel-2 NDVI on a 250 m grid for the Punggol 2 km pocket
   (item ``S2B_MSIL2A_20240728T031519``, 28 July 2024). High values
   are greener canopies on that date only.

What you will learn
-------------------

* The object chain: StudyArea → City → Units → analysis → IndicatorResult.
* How to load the real Punggol fixture offline.
* How NDVI and network reachability share one unit frame.
* Where CRS, units, indicators, and provenance are documented.
* That the 250 m grid is a comparison support, not the city
  (:doc:`/concepts/spatial_support_and_maps`).

Dataset
-------

.. list-table::
   :header-rows: 1
   :widths: 24 76

   * - Field
     - Value
   * - City
     - Punggol, Singapore
   * - Boundary
     - 2 km × 2 km pocket, not the municipal outline
   * - Source
     - OSM (ODbL) + Sentinel-2 L2A via Planetary Computer
   * - Acquisition
     - Sentinel-2 2024-07-28; OSM extract date in the manifest
   * - Resolution
     - Sentinel-2 resampled to 10 m; grid 250 m
   * - CRS
     - Geographic EPSG:4326; metric EPSG:32648
   * - License
     - ODbL + Copernicus Sentinel license
   * - Fixture
     - ``examples/data/real/punggol``
   * - Kind
     - Observed OSM geometries and one satellite scene; derived NDVI

Installation
------------

::

   pip install "urbancode[standard]"

Object flow
-----------

::

   StudyArea
   → City / Layer
   → AnalysisUnits
   → domain metric (Layer)
   → fusion.aggregate (IndicatorResult)
   → plot / save / provenance

* StudyArea → :doc:`/concepts/study_area_city_layer`
* CRS → :doc:`/concepts/crs_alignment`
* Units → :doc:`/concepts/analysis_units`
* IndicatorResult → :doc:`/concepts/indicators`
* Provenance → :doc:`/concepts/provenance_quality`

Step-by-step
------------

1. Load the City
~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :start-at: city = load_punggol
   :end-at: city = load_punggol()

``load_punggol`` calls ``uc.load`` and attaches the study area plus
locator. See :func:`urbancode.city.load`.

2. Define the StudyArea
~~~~~~~~~~~~~~~~~~~~~~~

The pocket helper sets ``city.study_area`` from the committed bbox
(lon/lat). See ``StudyArea.from_bbox`` in :doc:`/reference/api/units`.

3. Build AnalysisUnits
~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :start-at: units = uc.units.grid
   :end-at: units = uc.units.grid

IDs look like ``grid:EPSG:32648:250:col:row``. See :func:`urbancode.units.grid`.

4. Compute NDVI
~~~~~~~~~~~~~~~

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :start-at: ndvi = uc.imagery.ndvi
   :end-at: ndvi = uc.imagery.ndvi

.. figure:: /_static/recipes/imagery/indices_punggol.png
   :alt: NDVI, NDWI, and NDBI for the Punggol 2 km pocket
   :width: 100%

   Spectral indices from the committed Sentinel-2 window. NDVI uses
   B08 and B04. See :func:`urbancode.imagery.ndvi`.

5. Compute reachability
~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :start-at: reach = uc.network.accessibility
   :end-at: reach = uc.network.accessibility

This is a node count on the walk graph inside 150 m, not population
access. See :func:`urbancode.network.accessibility`.

6. Aggregate and combine
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :start-at: ndvi_result = uc.fusion.aggregate
   :end-at: table = combined.to_pandas()

See :func:`urbancode.fusion.aggregate` and :func:`urbancode.fusion.combine`.

7. Plot, save, reload
~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :start-at: fig, axes = plt.subplots
   :end-at: dest = saved

Use ``IndicatorResult.load``, not a module-level ``load``. Receipts
land in ``provenance/receipts.jsonl``. See
:doc:`/reference/api/indicators`.

Reading the result
------------------

* Waterfront and park cells show higher NDVI than dense building blocks
  on 28 July 2024.
* Reachability is higher where the walk graph is dense, not where NDVI
  is high. The two maps answer different questions.
* Edge cells can have lower coverage. Read ``value`` with ``coverage``.

Limitations
-----------

* One Sentinel-2 date is not a seasonal mean.
* 150 m reachability is graph length, not a door-to-door walk.
* The pocket is 2 km, so betweenness and closeness are boundary-sensitive.

Related pages
-------------

* Domain: :doc:`/domains/fusion`
* Recipe: :doc:`/reference/recipes/fusion/combine_punggol`
* Workflow: :doc:`/workflows/punggol_urban_profile`
* Next: :doc:`first_project`

Use UrbanCode when you want this chain to be the same in every city.
Use GeoPandas or OSMnx directly when you need a custom overlay or
graph algorithm that UrbanCode does not wrap.

Full script
-----------

.. literalinclude:: ../../../examples/workflows/punggol_end_to_end.py
   :language: python
   :caption: examples/workflows/punggol_end_to_end.py
