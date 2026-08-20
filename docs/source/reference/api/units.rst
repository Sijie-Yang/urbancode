Analysis units
==============

Need ``urbancode[vector]`` to build a grid. Public constructors are
``grid``, ``hexgrid`` (Shapely pointy-top hexes), and ``from_layer``.

.. autoclass:: urbancode.area.StudyArea
   :members: from_bbox, from_geometry, from_place

.. autoclass:: urbancode.units.AnalysisUnits

.. autofunction:: urbancode.units.grid
.. autofunction:: urbancode.units.hexgrid
.. autofunction:: urbancode.units.from_layer

See also
--------

* Domain: :doc:`/domains/units`
* Concept: :doc:`/concepts/analysis_units`
* Recipes: :doc:`/reference/recipes/units/index`
* Workflow: :doc:`/workflows/multi_city_comparison`
