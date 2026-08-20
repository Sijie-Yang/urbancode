uc.streetview.as_layer
======================

Urban question
--------------

Where do these photo observations sit on the map?

Real case
---------

- Dataset: ``streetview``
- Domain: streetview
- Extra: ``urbancode[vector]``
- Offline: True

Command
-------

.. code-block:: python

   uc.streetview.as_layer(...)

Inputs
------

table with lon/lat

Spatial support
---------------

Native support: image and geotagged point. Grid means are used only when coverage is sufficient.

Parameters
----------

Table with lon/lat columns. Rows without coordinates are dropped.

Method
------

Builds a point Layer from lon/lat columns.

Backend: ``geopandas``. Output unit: ``point``.

Output
------

Point Layer. CRS EPSG:4326 unless given.

Figure
------

.. figure:: ../../../_static/recipes/streetview/as_layer_punggol.png
   :alt: uc.streetview.as_layer result for the registered dataset
   :width: 100%

   Output of ``uc.streetview.as_layer`` on dataset ``streetview``.
   Unit: point. Backend: geopandas.

How to read
-----------

Only geotagged rows are observations. Illustrative points stay labelled.

Parameters and sensitivity
--------------------------

Illustrative (non-geotagged) points must stay labelled as such.

Failure modes
-------------

All-missing coordinates raise or return an empty layer.

Limitations
-----------

- only geotagged photos are real observations
- illustrative coordinates must stay labelled illustrative

Complete script
---------------

.. literalinclude:: ../../../../../examples/recipes/streetview/as_layer_punggol.py
   :language: python
   :caption: examples/recipes/streetview/as_layer_punggol.py

Related pages
-------------

- Domain: :doc:`/domains/streetview`
- API: :doc:`/reference/api/streetview`
- Workflow: :doc:`/workflows/street_experience`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
