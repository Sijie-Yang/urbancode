Heat exposure
=============

Urban question
--------------

Where do thermal stress, low vegetation, and built-up surfaces overlap?

Result first
------------

.. figure:: /_static/workflows/real_heat_stress.png
   :alt: Punggol UTCI, NDVI, NDBI, building fraction, and high-UTCI/low-NDVI overlap
   :width: 100%

   Punggol, Singapore — 2 km × 2 km · 250 m units · EPSG:32648.
   Observed Open-Meteo weather at 2024-07-15T14:00 UTC plus a modelled
   spatial MRT proxy. Native NDVI/NDBI rasters sit beside the 250 m
   UTCI surface. Overlap is high UTCI ∩ low NDVI, not a causal proof.

What you will learn
-------------------

* How to keep observed weather and modelled MRT distinct.
* How a vegetation / built-up proxy creates spatial UTCI contrast.
* How to join UTCI, NDVI, NDBI, and building fraction on units.

Dataset
-------

* Weather: Open-Meteo archive at the pocket centre (T, RH, wind observed).
* MRT: modelled NDVI/NDBI proxy, flag ``modelled_mrt_proxy``.
* Imagery: Sentinel-2 L2A 2024-07-28 (different date from the weather).
* Buildings: OSM footprints.

Installation
------------

::

   pip install "urbancode[standard]"

Step-by-step
------------

.. literalinclude:: ../../../examples/workflows/real_heat_stress.py
   :language: python
   :caption: examples/workflows/real_heat_stress.py

APIs: :func:`urbancode.climate.utci`, :func:`urbancode.imagery.ndvi`,
:func:`urbancode.imagery.ndbi`, :func:`urbancode.fusion.aggregate`,
:func:`urbancode.fusion.combine`.

Reading the result
------------------

* Spatial contrast comes from the MRT proxy, not from the point weather.
* Low-NDVI / high-NDBI cells can show higher UTCI. That is overlap.
* Air temperature itself is a constant field and is labelled as such.

Limitations
-----------

* The MRT formula is a documented proxy, not a measured campaign.
* Weather and Sentinel-2 dates differ.
* Not shade-resolved and not medical advice.
* Wind is 10 m Open-Meteo; confirm the UTCI height convention.

Related pages
-------------

* Domain: :doc:`/domains/climate`
* Recipe: :doc:`/reference/recipes/climate/utci_real`
* Concept: :doc:`/concepts/provenance_quality`
