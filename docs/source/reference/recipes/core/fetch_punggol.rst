uc.fetch
========

Urban question
--------------

Which OSM and imagery layers cover this place?

Real case
---------

- Dataset: ``punggol``
- Domain: vector
- Extra: ``urbancode[network]``
- Offline: True

Copy this
---------

.. code-block:: python

   import urbancode as uc

   # Live download. The docs figure uses the committed pocket instead.
   city = uc.fetch("Punggol, Singapore")

``city`` is the downloaded :class:`~urbancode.city.City`. Because this is a live call, its layer inventory and OSM/STAC timestamps can differ from the committed figure below.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/cli/fetch.png
   :alt: uc.fetch result for the registered dataset
   :width: 100%

   Output of ``uc.fetch`` on dataset ``punggol``.
   Unit: mixed. Backend: osmnx.

Inputs
------

place or bbox

Spatial support
---------------

Native support: OSM footprints, parks, and points. Do not aggregate before the vector map is shown.

Parameters
----------

``place`` or bbox plus modality presets. ``on_error`` can keep partial success.

Method
------

Live fetch writes a City directory from OSM and STAC. This page uses the committed pocket.

Backend: ``osmnx``. Output unit: ``mixed``.

Output
------

City directory. This recipe uses the committed pocket, not a live Overpass call.

How to read
-----------

Treat the figure as the output contract of uc.fetch, not a live Overpass result.

Parameters and sensitivity
--------------------------

Live OSM and STAC change daily; the figure is the fixture.

Failure modes
-------------

Network errors raise unless ``on_error`` swallows them.

Limitations
-----------

- the offline recipe plots the committed pocket, not a live download
- live refresh is a Tier 2 network job

Related pages
-------------

- Domain: :doc:`/domains/vector`
- API: :doc:`/reference/api/city`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
