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

Install ``urbancode[standard]``, clone this repository, and run
the blocks from the **repository root**. The pocket
``examples/data/real/punggol`` is a docs fixture; it is not inside
the PyPI wheel. A live alternative is ``uc.fetch("Punggol, Singapore")``.

1. Import and load
------------------

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)

``city`` is a ``City``. ``lazy=True`` does not open rasters until a
later command needs them. The committed ``manifest.json`` already
stores the StudyArea, so you do not rebuild a bbox.

::

   print(city.place)
   print(city.keys())

::

   Punggol, Singapore
   ['streets', 'buildings', 'parks', 'pois', 'sentinel2', 'dem', 'water']

2. Look at the study area
-------------------------

::

   print(city.study_area.city_id)
   print(city.study_area.metric_crs)
   print(city.study_area.bbox)

::

   punggol
   EPSG:32648
   (103.90101643295905, 1.3959501786810404,
    103.91898363615519, 1.4140498401820776)

``city_id`` is ``punggol``. The metric CRS is UTM 48N
(``EPSG:32648``). The bbox is about 103.90–103.92 E, 1.396–1.414 N:
a 2 km pocket, not the municipal outline.

3. Build 250 m units
--------------------

::

   units = uc.units.grid(city, cell_size=250)
   print(len(units.frame), units.kind, units.metric_crs)
   print(list(units.frame["unit_id"].head(3)))

::

   81 grid EPSG:32648
   ['grid:EPSG:32648:250:1510:617', 'grid:EPSG:32648:250:1510:618',
    'grid:EPSG:32648:250:1510:619']

Eighty-one clipped cells. The ID encodes CRS, cell size, column, and
row. This grid is a comparison frame, not the city
(:doc:`/concepts/spatial_support_and_maps`).

4. Measure NDVI
---------------

::

   ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
   print(ndvi.kind, ndvi.data.shape)
   ndvi.plot()

::

   raster (200, 200)

That is a 10 m raster Layer, formula (B08 − B04) / (B08 + B04).
Finite values on this date run from about −0.29 to 0.65, mean 0.21.

.. figure:: /_static/recipes/imagery/indices_punggol.png
   :alt: NDVI, NDWI, and NDBI for the Punggol 2 km pocket
   :width: 100%

   Native Sentinel-2 indices. Call ``ndvi.plot()`` to draw the NDVI
   panel only.

5. Measure walk reachability
----------------------------

::

   reach = uc.network.accessibility(
       city["streets"], radius=150, metric="reachability"
   )
   print(reach.kind, reach.data.number_of_nodes())
   reach.plot()

::

   graph 1425

``city["streets"]`` is the graph payload. Reachability is a node
count inside 150 m of graph length, not population access. On this
pocket the node values run from 0 to 98 (mean about 23).

.. figure:: /_static/recipes/network/accessibility_punggol.png
   :alt: Network reachability on the Punggol walk graph
   :width: 100%

   Graph Layer before aggregation. Call ``reach.plot()``.

6. Put both maps on the same units
----------------------------------

::

   ndvi_grid = uc.fusion.aggregate(
       ndvi, units, stat="mean", indicator="ndvi"
   )
   print(ndvi_grid.to_pandas()[["unit_id", "value", "coverage"]].head(3))

::

                        unit_id    value  coverage
   grid:EPSG:32648:250:1510:617  0.146     1.0
   grid:EPSG:32648:250:1510:618  0.154     1.0
   grid:EPSG:32648:250:1510:619  0.137     1.0

81 rows, coverage 1.0 on this fixture, mean NDVI 0.208.

::

   reach_grid = uc.fusion.aggregate(
       reach, units, stat="mean", indicator="reachability"
   )
   print(reach_grid.to_pandas()["value"].isna().sum())

::

   32

32 of 81 cells have no street node, so ``value`` is null and
``coverage`` is 0. Missing stays null, not zero.

7. Combine and plot
-------------------

::

   result = uc.fusion.combine(units, ndvi_grid, reach_grid)
   print(result.to_pandas().groupby("indicator")["value"].mean())
   result.plot(indicator="ndvi")

::

   ndvi            0.208
   reachability   16.030

162 records (81 × 2 indicators). Switch
``indicator="reachability"`` for the network map. Edge cells can
have lower coverage; always read ``value`` with ``coverage``.

The two maps answer different questions. High NDVI follows parks on
28 July 2024. High reachability follows the dense walk graph, not
the water edge.

Limitations
-----------

* One Sentinel-2 date is not a seasonal mean.
* 150 m reachability is graph length, not a door-to-door walk.
* The pocket is 2 km, so betweenness later will be boundary-sensitive.

Next: :doc:`first_project` (save / reload). Concepts:
:doc:`/concepts/study_area_city_layer`,
:doc:`/concepts/analysis_units`,
:doc:`/concepts/indicators`.
