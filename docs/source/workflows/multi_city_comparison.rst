Multi-city comparison
=====================

Urban question
--------------

Can the same 2 km extent, unit rule, and indicator schema run on
Punggol, Kallio, and Greenwich Village without pretending the
dates are identical?

Result first
------------

.. figure:: /_static/workflows/multi_city_context.png
   :alt: Streets, buildings, parks, and water for three 2 km pockets
   :width: 100%

   Punggol, Singapore (EPSG:32648), Kallio, Helsinki (EPSG:32635),
   and Greenwich Village, New York (EPSG:32618). Each panel is a
   2 km × 2 km pocket with a parent-city locator.

.. figure:: /_static/workflows/real_multi_city.png
   :alt: NDVI, reachability, park fraction, and building fraction with city context
   :width: 100%

   Same 250 m constructor. Grid fill is semi-transparent over
   streets and buildings. Dates differ; this is not a city ranking.
   Script: ``examples/workflows/real_multi_city.py``.

What you will learn
-------------------

* Same physical area (2 km × 2 km), same 250 m grid constructor,
  same network radius, same missing-value rule.
* How to keep source dates visible.
* The difference between raw values, within-city percentiles, and
  cross-city scores.

Cities
------

.. list-table::
   :header-rows: 1
   :widths: 22 26 26 26

   * - Pocket
     - Place
     - Metric CRS
     - Notes
   * - punggol
     - Punggol, Singapore
     - EPSG:32648
     - Equatorial; July Sentinel-2
   * - kallio
     - Kallio, Helsinki
     - UTM (Finland)
     - Boreal summer window
   * - greenwich_village
     - Greenwich Village, New York
     - UTM (New York)
     - Northern-summer window

Manifests: :doc:`/reference/datasets`.

Installation
------------

::

   pip install "urbancode[standard]"

Step-by-step
------------

.. literalinclude:: ../../../examples/workflows/real_multi_city.py
   :language: python
   :caption: examples/workflows/real_multi_city.py

Compared fields include vegetation (NDVI), built-up / park area
fractions, and network reachability when the layer exists.
A radar chart is omitted unless you explicitly normalize; raw
NDVI is not a rank.

The synthetic three-city contract script
(``examples/workflows/multi_city_contract.py``) only proves that
unit IDs and schemas align. It is not a real-city ranking.

Reading the result
------------------

* Punggol NDVI is a July equatorial scene. Kallio and Greenwich
  Village are June–August scenes at higher latitudes. Do not call
  the highest mean “the greenest city”.
* Built-up fraction follows OSM completeness as much as form.
* Coverage can differ when a layer is missing; missing is not
  zero.

Limitations
-----------

* Different OSM vintages and Sentinel-2 items.
* 2 km pockets are not municipal extents.
* Terrain and heat are only comparable when the same product and
  timestamp strategy exist for every city.

Related pages
-------------

* Concept: :doc:`/concepts/analysis_units`
* Domain: :doc:`/domains/units`, :doc:`/domains/fusion`
* Dataset: :doc:`/reference/datasets`

Use UrbanCode when the comparison is a repeated contract.
Use a notebook of ad-hoc maps when the unit rules are still
moving.
