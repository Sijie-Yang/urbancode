Street experience
=================

Urban question
--------------

How do street-level photos sit on the same units as NDVI?

Result first
------------

.. figure:: /_static/workflows/street_experience.png
   :alt: Sample photo, point coverage, grid counts, colorfulness, NDVI, and reachability
   :width: 100%

   Eight licensed Commons photos, not a Punggol census.

1. Inspect the catalog first
----------------------------

The JSON has three cities. Image IDs are unique **inside** Punggol,
not across the whole file.

::

   import pandas as pd

   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   print(catalog["city_id"].value_counts().to_string())

::

   punggol              8
   kallio               8
   greenwich_village    8

2. One city → one Layer
-----------------------

::

   import urbancode as uc

   punggol = catalog[catalog["city_id"] == "punggol"]
   photos = uc.images.from_table(
       punggol,
       view_type="streetview",
       image_root="examples/data/real/streetview",
   )
   print(photos.kind, photos.metadata["n_images"])
   print(photos.data[["image_id", "longitude", "latitude"]].head(2))

::

   vector 8

A point Layer in EPSG:4326. ``image_root`` resolves the relative
``path`` column. Call ``photos.plot()``.

3. Count photos onto the grid
-----------------------------

::

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   counts = uc.fusion.aggregate(
       photos, units, stat="count", indicator="photo_count"
   )
   ndvi = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units, stat="mean", indicator="ndvi",
   )
   print(int((counts.to_pandas()["value"] > 0).sum()))

::

   3

Eight photos land in 3 of 81 cells (one cell has six). Empty cells
stay null. Null is not zero.

::

   result = uc.fusion.combine(units, counts, ndvi)
   result.plot(indicator="photo_count")

``result`` aligns ``photo_count`` and ``ndvi`` by unit ID. The plot
selects the sparse count series; it does not fill unobserved cells or
turn eight photos into area coverage.

VATA is a different quantity. See
:doc:`/workflows/research_cases/thermal_comfort_in_sight`.

Limitations
-----------

* Not a survey of Punggol streets.
* Faces and plates may appear; this is not a privacy-cleared set.
