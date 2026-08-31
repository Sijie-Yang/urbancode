uc.load
=======

Urban question
--------------

Can this City directory be loaded without re-fetching?

Real case
---------

- Dataset: ``punggol``
- Domain: vector
- Extra: ``urbancode[vector]``
- Offline: True

Copy this
---------

.. code-block:: python

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   city.plot(layers=["streets", "buildings", "parks"])

``city`` is the lazily loaded :class:`~urbancode.city.City`. The call to ``city.plot`` renders three existing layers; it does not download or modify data.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/core/city_roundtrip_punggol.png
   :alt: uc.load result for the registered dataset
   :width: 100%

   Output of ``uc.load`` on dataset ``punggol``.
   Unit: mixed. Backend: geopandas.

Inputs
------

City directory

Spatial support
---------------

Native support: OSM footprints, parks, and points. Do not aggregate before the vector map is shown.

Parameters
----------

``path`` to a City directory. ``layers`` optional. ``lazy=True`` avoids opening rasters.

Method
------

Reads a City directory. lazy=True copies source files on save without opening rasters first.

Backend: ``geopandas``. Output unit: ``mixed``.

Output
------

City with Layer inventory, CRS, and stamps.

How to read
-----------

The map is the layer inventory, not a new download.

Parameters and sensitivity
--------------------------

lazy=True copies files on save without decoding rasters first.

Failure modes
-------------

Missing manifest raises. Unknown layer names raise.

Limitations
-----------

- lazy load defers raster and graph reads until a layer is used
- the directory must include manifest.json

Related pages
-------------

- Domain: :doc:`/domains/vector`
- API: :doc:`/reference/api/city`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
