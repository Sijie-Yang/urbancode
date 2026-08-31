Street experience
=================

Urban question
--------------

How do street-level photos sit on the same units as NDVI?

Result first
------------

.. figure:: /_static/workflows/street_experience.png
   :alt: Sample photo, point coverage, grid counts, colorfulness, NDVI, and reachability
   :width: 100%

   Eight licensed Commons photos, not a Punggol census. The figure is
   produced by ``examples/workflows/street_experience.py``.

1. Catalog files, then color
----------------------------

The taught chain is ``uc.svi.filename`` → ``uc.svi.color`` →
``uc.svi.as_layer`` → ``uc.fusion.aggregate``. Geotags come from
``examples/data/real/streetview/catalog.json``. Image IDs are unique
**inside** Punggol, not across the whole file.

.. literalinclude:: ../../../examples/workflows/street_experience.py
   :language: python
   :start-after: # tutorial:start
   :end-before: # tutorial:end

``filename`` lists JPEGs. ``color`` adds pixel statistics.
``as_layer`` makes a point Layer. Empty cells stay null after
``aggregate``; null is not zero.

2. Inspect the catalog first
----------------------------

::

   import pandas as pd

   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   print(catalog["city_id"].value_counts().to_string())

::

   punggol              8
   kallio               8
   greenwich_village    8

Eight photos land in 3 of 81 cells (one cell has six). Call
``result.plot(indicator="photo_count")`` after the combine step.

VATA is a different quantity. See
:doc:`/workflows/research_cases/thermal_comfort_in_sight`.

Limitations
-----------

* Not a survey of Punggol streets.
* Faces and plates may appear; this is not a privacy-cleared set.
* Colorfulness is a pixel statistic, not thermal affordance.
