uc.perception.thermal_affordance
================================

Urban question
--------------

What visual thermal affordance does TCIS assign to these photos?

Real case
---------

- Dataset: ``streetview``
- Domain: perception
- Extra: ``urbancode[perception]``
- Offline: True

Command
-------

.. code-block:: python

   uc.perception.thermal_affordance(...)

Inputs
------

A geolocated image Layer from ``uc.images.from_table``.

Spatial support
---------------

Native support: photo point. Fusion support: unit mean only where
photos exist. Unobserved units stay empty.

Parameters
----------

``device`` is ``cpu`` or ``cuda``. ``include_features`` keeps TCIS
initial-feature columns (default True).

Method
------

The TCIS backend extracts image features, runs the two-stage
network, and returns a Layer. The canonical score is
``thermal_affordance`` (VATA). ``thermal_comfort`` is only a
compatibility alias on the deprecated DataFrame entry.

Backend: ``torch``. Output unit: ``score_0_5``.

Output
------

Point Layer with ``image_id``, VATA, VPI heads, and model
provenance (weights SHA-256, stats SHA-256, device, UrbanCode
version).

Figure
------

.. figure:: ../../../_static/recipes/perception/thermal_affordance_punggol.png
   :alt: VATA on eight Punggol photo points and 250 m units
   :width: 100%

   Output of TCIS VATA on eight Commons photos. Unit: score 0–5.
   Unobserved units are hatched. This is not a city-scale map.

How to read
-----------

A high score is the model's visual thermal affordance. It is not
measured personal comfort and not UTCI.

Parameters and sensitivity
--------------------------

Changing device should not change the score. Changing the photo
crop or JPEG quality will.

Failure modes
-------------

Missing weights raise after a failed download. Missing image files
raise. Importing ``urbancode.perception`` does not import torch.

Limitations
-----------

- VATA is visual thermal affordance, not measured comfort and not UTCI
- eight Commons photos are a sample, not a Punggol census

Complete script
---------------

.. literalinclude:: ../../../../../examples/recipes/perception/thermal_affordance_punggol.py
   :language: python
   :caption: examples/recipes/perception/thermal_affordance_punggol.py

Related pages
-------------

- API: :doc:`/reference/api/perception`
- Workflow: :doc:`/workflows/research_cases/thermal_comfort_in_sight`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
