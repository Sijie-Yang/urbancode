Multi-city comparison
=====================

Urban question
--------------

Can the same 2 km extent, unit rule, and indicator schema run on
Punggol, Kallio, and Greenwich Village without pretending the
dates are identical?

Result first
------------

.. figure:: /_static/workflows/multi_city_context.png
   :alt: Streets, buildings, parks, and water for three 2 km pockets
   :width: 100%

   Each panel is a 2 km × 2 km pocket. Metric CRS differs.

.. figure:: /_static/workflows/real_multi_city.png
   :alt: NDVI, reachability, park fraction, and building fraction with city context
   :width: 100%

   Same 250 m constructor. Dates differ; this is not a city ranking.

1. Each City already knows its CRS
----------------------------------

::

   import urbancode as uc

   for name in ("punggol", "kallio", "greenwich_village"):
       city = uc.load(f"examples/data/real/{name}", lazy=True)
       print(name, city.place, city.study_area.metric_crs)

::

   punggol Punggol, Singapore EPSG:32648
   kallio Kallio, Helsinki EPSG:32635
   greenwich_village Greenwich Village, New York EPSG:32618

Do not reuse Punggol unit IDs in Helsinki.

2. Repeat the same constructor
------------------------------

::

   city = uc.load("examples/data/real/kallio", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units, stat="mean", indicator="ndvi",
   )
   print(len(units.frame), round(float(ndvi.to_pandas()["value"].mean()), 3))
   ndvi.plot(indicator="ndvi")

::

   81 0.166

Kallio: 81 cells, mean NDVI about 0.166 (boreal summer window).
Punggol mean NDVI is 0.208 (28 July). Greenwich Village is about
0.112 (northern summer). The highest mean is not “the greenest
city”.

Loop the same two calls for the other pockets if you want a table
of means. Built-up fraction follows OSM completeness as much as form.

Limitations
-----------

* Different OSM vintages and Sentinel-2 items.
* 2 km pockets are not municipal extents.
