Indicator results
=================

Named compute functions still return a :class:`~urbancode.city.Layer`.
:func:`urbancode.fusion.aggregate` wraps those Layers onto
:class:`~urbancode.units.AnalysisUnits`.

.. autoclass:: urbancode.indicators.IndicatorRecord

.. autoclass:: urbancode.indicators.IndicatorResult
   :members: to_pandas, to_geopandas, to_xarray, to_layer, plot, save, load

See also
--------

* Concept: :doc:`/concepts/indicators`
* Domain: :doc:`/domains/fusion`
* Recipe: :doc:`/reference/recipes/fusion/combine_punggol`
