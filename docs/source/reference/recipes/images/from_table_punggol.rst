uc.images.from_table
====================

Urban question
--------------

How do geotagged city photos become an observation Layer?

Real case
---------

- Dataset: ``streetview``
- Domain: images
- Extra: ``urbancode[vector]``
- Offline: True

Copy this
---------

.. code-block:: python

   import pandas as pd
   import urbancode as uc

   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   photos = uc.images.from_table(
       catalog[catalog["city_id"] == "punggol"],
       view_type="streetview",
       image_root="examples/data/real/streetview",
   )
   print(photos.kind, photos.metadata["n_images"])
   photos.plot()

``catalog`` is the three-city source table. ``photos`` is the eight-row Punggol point :class:`~urbancode.city.Layer`; ``n_images`` counts catalog rows and ``photos.plot()`` maps their coordinates.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/images/from_table_punggol.png
   :alt: uc.images.from_table result for the registered dataset
   :width: 100%

   Output of ``uc.images.from_table`` on dataset ``streetview``.
   Unit: image. Backend: geopandas.

Inputs
------

table with image_id, path, and lon/lat

Spatial support
---------------

See :doc:`/concepts/spatial_support_and_maps` for native vs aggregated geometry.

Parameters
----------

See the signature of ``uc.images.from_table`` in the API reference. The recipe uses the committed fixture and does not hard-code result values.

Method
------

Builds a geolocated photo Layer. image_id must be unique.

Backend: ``geopandas``. Output unit: ``image``.

Output
------

point Layer. Unit: image.

How to read
-----------

Each point is one photo, not a street census.

Parameters and sensitivity
--------------------------

Change one parameter at a time (radius, cell size, date) and compare coverage.

Failure modes
-------------

Missing extras raise ``MissingExtraError``. Invalid parameters raise ``ValueError``.

Limitations
-----------

- image_id must be unique; one location can have several photos
- window-view photos use view_type=windowview, not streetview

Related pages
-------------

- Domain: :doc:`/concepts/image_observations`
- API: :doc:`/reference/api/images`
- Workflow: :doc:`/workflows/research_cases/thermal_comfort_in_sight`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
