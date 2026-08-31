Perception
==========

Urban question
--------------

How does a street photo score for visual thermal affordance, and how
does that score become a point Layer?

What you will learn
-------------------

* The canonical function is :func:`urbancode.perception.thermal_affordance`.
* VATA is not measured personal comfort and not UTCI.
* Image catalogs become observation Layers through ``uc.images``.

Installation
------------

::

   pip install "urbancode[perception]"

This extra pulls PyTorch. Weights download into
``~/.cache/urbancode/`` on first use; the wheel does not bundle them.
Street-view catalogs and color features live in ``uc.svi`` and need
``urbancode[svi]``.

UrbanCode API
-------------

* :func:`urbancode.perception.thermal_affordance`

::

   import pandas as pd
   import urbancode as uc

   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   photos = uc.images.from_table(
       catalog[catalog["city_id"] == "punggol"],
       view_type="streetview",
       image_root="examples/data/real/streetview",
   )
   scores = uc.perception.thermal_affordance(photos)

``thermal_affordance`` returns a Layer. The deprecated DataFrame
entry is ``uc.svi.comfort``.

Related pages
-------------

* Recipes: :doc:`/reference/recipes/perception/thermal_affordance_punggol`
* Research case: :doc:`/workflows/research_cases/thermal_comfort_in_sight`
* Domain: :doc:`/domains/streetview`
* API: :doc:`/reference/api/perception`
