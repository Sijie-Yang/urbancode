uc.StudyArea.from_bbox
======================

Urban question
--------------

What is the study boundary and canonical metric CRS?

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
   print(city.study_area.bbox)
   area = uc.StudyArea.from_bbox(
       *city.metadata["bbox"], city_id="punggol"
   )

``city.study_area.bbox`` is the stored west/south/east/north envelope. ``area`` is a new :class:`~urbancode.area.StudyArea` built from the same coordinates; no layers are copied into it.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/core/study_area_punggol.png
   :alt: uc.StudyArea.from_bbox result for the registered dataset
   :width: 100%

   Output of ``uc.StudyArea.from_bbox`` on dataset ``punggol``.
   Unit: CRS. Backend: pyproj.

Inputs
------

west south east north

Spatial support
---------------

Native support: OSM footprints, parks, and points. Do not aggregate before the vector map is shown.

Parameters
----------

``xmin, ymin, xmax, ymax`` in lon/lat. Optional ``place`` and ``city_id``.

Method
------

StudyArea.from_bbox stores lon/lat and derives a metric CRS from the centre.

Backend: ``pyproj``. Output unit: ``CRS``.

Output
------

StudyArea with geographic CRS, metric CRS, and bbox.

How to read
-----------

The envelope is the 2 km pocket, not the municipal boundary.

Parameters and sensitivity
--------------------------

Metric CRS is derived from the centre, not from a national grid name.

Failure modes
-------------

Inverted bbox raises.

Limitations
-----------

- four numbers outside the geographic range are not treated as lon/lat
- the committed pocket is a 2 km extract, not the municipal boundary

Related pages
-------------

- Domain: :doc:`/domains/vector`
- API: :doc:`/reference/api/city`
- Workflow: :doc:`/workflows/punggol_urban_profile`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
