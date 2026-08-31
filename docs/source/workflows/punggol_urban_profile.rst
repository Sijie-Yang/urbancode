Punggol urban profile
=====================

Urban question
--------------

What does the 2 km Punggol pocket look like as a **core** profile
of vector context, walk-network reachability, NDVI/NDBI, and terrain
on one 250 m grid?

Result first
------------

.. figure:: /_static/workflows/punggol_urban_profile.png
   :alt: Punggol core profile with vector context, reachability, NDVI, NDBI, and slope
   :width: 100%

   Punggol, Singapore — 2 km × 2 km · 250 m units · EPSG:32648.
   Context map first, then native rasters and fused reachability.

1. Context map
--------------

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   city.plot(layers=["water", "parks", "buildings", "streets"])

``city`` is the lazy container; the plot reads four existing layers
without downloading data. This is OSM geometry, not a satellite
product. Parks are OSM tags.

2. Four native measures
-----------------------

::

   ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
   ndbi = uc.imagery.ndbi(city.layers["sentinel2"])
   slope = uc.imagery.slope(city.layers["dem"])
   reach = uc.network.accessibility(
       city["streets"], radius=150, metric="reachability"
   )
   print(ndvi.kind, ndbi.kind, slope.kind, reach.kind)

::

   raster raster raster graph

NDVI/NDBI are 10 m Sentinel-2 (28 July 2024). Slope is DEM
degrees. Reachability is 1,425 graph nodes.

.. figure:: /_static/recipes/imagery/indices_punggol.png
   :alt: Punggol NDVI, NDWI, and NDBI
   :width: 100%

.. figure:: /_static/recipes/network/accessibility_punggol.png
   :alt: Punggol walk-graph reachability
   :width: 100%

3. Fuse onto one grid
---------------------

::

   units = uc.units.grid(city, cell_size=250)
   result = uc.fusion.combine(
       units,
       uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi"),
       uc.fusion.aggregate(ndbi, units, stat="mean", indicator="ndbi"),
       uc.fusion.aggregate(slope, units, stat="mean", indicator="slope"),
       uc.fusion.aggregate(reach, units, stat="mean", indicator="reachability"),
   )
   print(result.to_pandas().groupby("indicator")["value"].mean().round(3))

::

   indicator
   ndbi            -0.027
   ndvi             0.208
   reachability    16.030
   slope            4.977
   Name: value, dtype: float64

``result`` contains four aligned indicator series on the same unit
IDs. On this fixture 49 of 81 cells have a street node.
Call ``result.plot(indicator="ndvi")`` and
``result.save("punggol_indicators")``.

Climate and street-view stay on their own pages.

Limitations
-----------

* 2 km extract, not Punggol planning units.
* One satellite date is not a year of vegetation.

Next: :doc:`green_accessibility`. Recipes for each command live
under :doc:`/reference/recipes/index`.
