Green accessibility
===================

Urban question
--------------

Are greener neighbourhoods also better connected to accessible
parks?

Result first
------------

.. figure:: /_static/workflows/green_accessibility.png
   :alt: Punggol NDVI, nearest park distance, and network reachability
   :width: 100%

   Punggol, Singapore — 2 km × 2 km · 250 m units · EPSG:32648.
   Correlation on this pocket is not causation.

1. Shared units
---------------

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)

``city`` is the committed 2 km pocket and ``units`` is its 81-cell
comparison frame in EPSG:32648. Every result below uses these exact
unit IDs.

2. Three statistics, one function
---------------------------------

Nearest-park distance is not a special API. It is
``stat="nearest_distance"`` on the parks Layer.

::

   ndvi = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units, stat="mean", indicator="ndvi",
   )
   parks = uc.fusion.aggregate(
       city.layer("parks"),
       units, stat="nearest_distance", indicator="park_near_m",
   )
   reach = uc.fusion.aggregate(
       uc.network.accessibility(
           city["streets"], radius=150, metric="reachability"
       ),
       units, stat="mean", indicator="reachability",
   )
   print(round(float(ndvi.to_pandas()["value"].mean()), 3))
   print(round(float(parks.to_pandas()["value"].mean()), 1))

::

   0.208
   80.7

Mean NDVI 0.208. Mean nearest park polygon is about 81 m (minimum 0
where a cell intersects a park). Parks are OSM polygons, not an
official parks layer.

3. Combine and plot
-------------------

::

   result = uc.fusion.combine(units, ndvi, parks, reach)
   result.plot(indicator="ndvi")
   result.plot(indicator="park_near_m")

``result`` is a long table with three records per unit: ``ndvi``,
``park_near_m``, and ``reachability``. The two plot calls select one
indicator at a time; they do not recompute either value.

Some high-NDVI cells are close to a park; some are private or
residual vegetation. High reachability can sit on grey streets.
Do not read this as evidence that greenery causes access.

Limitations
-----------

* Reachability is node count, not population at a park gate.
* Nearest-distance ignores park size and entry points.
