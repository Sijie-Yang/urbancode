Street experience
=================

Urban question
--------------

How do street-level visual conditions relate to network position
and neighbourhood context?

Result first
------------

.. figure:: /_static/workflows/street_experience.png
   :alt: Sample photo, point coverage, grid counts, colorfulness, NDVI, and reachability
   :width: 100%

   Punggol, Singapore — 2 km × 2 km · EPSG:32648. Sample photo,
   geotagged points on streets/buildings, then grid counts.
   Colorfulness is drawn only where photos exist. Illustrative
   Commons sample, not a census. ML recipes stay live/heavy.

What you will learn
-------------------

* How ``filename``, ``color``, and ``as_layer`` become units.
* How to keep illustrative coordinates labelled.
* How to join photo features with network or NDVI without
  over-claiming coverage.

Dataset
-------

Wikimedia Commons photos under redistributable licenses, stored
in ``examples/data/real/streetview``. Capture coordinates are used
only when the catalog records them. Otherwise the workflow stays
honest about missing geolocation.

Installation
------------

::

   pip install "urbancode[standard,streetview]"

Step-by-step
------------

.. literalinclude:: ../../../examples/workflows/street_experience.py
   :language: python
   :caption: examples/workflows/street_experience.py

The older ``streetview_to_grid`` script remains as a shorter
catalog → grid helper. Prefer this page for the research question.

Model steps (segmentation, detection, scene, comfort) have their
own recipes. They use committed precomputed artifacts offline.

Reading the result
------------------

* A colourful photo is not a comfortable street.
* Sparse points leave most cells null. Null is not zero.
* Network centrality of the nearest node is context, not a cause
  of the photo.

Limitations
-----------

* Not a complete survey of Punggol streets.
* Provider archives cannot be committed here.
* Model domain shift across cities is expected.
* Faces and plates may appear; this is not a privacy-cleared set.

Related pages
-------------

* Domain: :doc:`/domains/streetview`
* Recipes: :doc:`/reference/recipes/streetview/color_punggol`,
  :doc:`/reference/recipes/streetview/as_layer_punggol`
* Responsible use: :doc:`/domains/streetview`

Use UrbanCode when photo rows must join a City grid.
Use OpenCV or ZenSVI directly when you are inspecting one image
or a live download.
