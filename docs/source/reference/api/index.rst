API reference
=============

Public entry points grouped by urban task, in the same spirit as a
measure-first library. Training helpers inside
``urbancode.svi.perception`` are not scanned.

Prefer these names in new code. Legacy ``uc.reachability_radius`` and
friends stay importable for old notebooks; they are not the documented
surface.

Study area, city, and layers
----------------------------

.. currentmodule:: urbancode.area

.. autosummary::

   StudyArea

.. currentmodule:: urbancode.city

.. autosummary::

   City
   Layer
   load

.. currentmodule:: urbancode.fetch

.. autosummary::

   fetch

.. currentmodule:: urbancode.images

.. autosummary::

   from_table

Analysis units
--------------

Shared spatial frames for multimodal work.

.. currentmodule:: urbancode.units

.. autosummary::

   grid
   hexgrid
   from_layer
   AnalysisUnits

Measuring vegetation, water, built-up surface, and terrain
----------------------------------------------------------

.. currentmodule:: urbancode.imagery

.. autosummary::

   read
   fetch
   ndvi
   ndwi
   ndbi
   slope
   aspect
   hillshade
   zonal_stats

Measuring street-network connectivity
-------------------------------------

.. currentmodule:: urbancode.network

.. autosummary::

   fetch
   centrality
   accessibility
   clustering
   local_efficiency

Measuring outdoor heat
----------------------

.. currentmodule:: urbancode.climate

.. autosummary::

   utci

Measuring streetscape perception
--------------------------------

VATA is visual thermal affordance. It is not measured personal comfort
and it is not UTCI.

.. currentmodule:: urbancode.perception

.. autosummary::

   thermal_affordance

.. currentmodule:: urbancode.svi

.. autosummary::

   fetch
   color
   filename
   as_layer

Fusing scores onto shared units
-------------------------------

.. currentmodule:: urbancode.fusion

.. autosummary::

   aggregate
   aggregate_many
   combine

.. currentmodule:: urbancode.indicators

.. autosummary::

   IndicatorResult

By module
---------

Signatures, types, and raises live on these pages.

.. toctree::
   :maxdepth: 1

   city
   network
   imagery
   climate
   streetview
   images
   perception
   units
   indicators
   fusion
   backends
   adapters

See also: :doc:`/reference/recipes/index`, :doc:`/reference/capabilities`,
:doc:`/domains/index`.
