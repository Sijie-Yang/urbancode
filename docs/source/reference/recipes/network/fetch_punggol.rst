uc.network.fetch
================

Urban question
--------------

What street graph covers this study area?

Real case
---------

- Dataset: ``punggol``
- Domain: network
- Extra: ``urbancode[network]``
- Offline: True

Copy this
---------

.. code-block:: python

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   streets = city.layer("streets")
   streets.plot()

``streets`` is the graph :class:`~urbancode.city.Layer` already stored in ``city``. ``streets.plot()`` draws the graph in native support; the code does not aggregate it to a grid.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/network/fetch_punggol.png
   :alt: uc.network.fetch result for the registered dataset
   :width: 100%

   Output of ``uc.network.fetch`` on dataset ``punggol``.
   Unit: graph. Backend: osmnx.

Inputs
------

bbox or place

Spatial support
---------------

Native support: street graph nodes/edges. Recipe figure shows the graph. Fusion to a 250 m grid is optional and only after ``uc.fusion.aggregate``.

Parameters
----------

``place`` or ``bbox``. ``layers`` defaults to streets only; ``layers='all'`` is explicit. ``network_type`` follows OSMnx walk/drive.

Method
------

The committed graph is an OSM walk extract clipped to the pocket.

Backend: ``osmnx``. Output unit: ``graph``.

Output
------

City with graph and vector layers. CRS EPSG:4326 plus a metric CRS stamp.

How to read
-----------

Line density follows the street layout. This is not traffic volume.

Parameters and sensitivity
--------------------------

A 100 m bbox change can drop or add whole streets at the cut.

Failure modes
-------------

Live Overpass failures raise unless ``on_error`` is set on ``uc.fetch``.

Limitations
-----------

- committed pocket is a clipped OSM extract, not a live refresh
- OSM timestamp is the extract date, not a planning-grade inventory

Related pages
-------------

- Domain: :doc:`/domains/network`
- API: :doc:`/reference/api/network`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
