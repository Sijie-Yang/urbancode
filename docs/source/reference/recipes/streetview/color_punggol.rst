uc.svi.color
============

Urban question
--------------

How colourful are these street photos?

Real case
---------

- Dataset: ``streetview``
- Domain: streetview
- Extra: ``urbancode[svi]``
- Offline: True

Copy this
---------

.. code-block:: python

   import urbancode as uc

   table = uc.svi.filename("examples/data/real/streetview/punggol")
   color = uc.svi.color(
       table, folder_path="examples/data/real/streetview/punggol"
   )
   print(color.head())

``table`` is the input file catalog. ``color`` is a copy augmented with pixel-statistic columns such as ``Colorfulness``; these are image-level features, not comfort measurements.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/streetview/color_punggol.png
   :alt: uc.svi.color result for the registered dataset
   :width: 100%

   Output of ``uc.svi.color`` on dataset ``streetview``.
   Unit: colorfulness. Backend: opencv.

Inputs
------

image catalog

Spatial support
---------------

Native support: image and geotagged observation point. Fusion support: grid mean only when coverage is sufficient.

Parameters
----------

Catalog plus ``folder_path``. OpenCV Colorfulness and related pixel stats.

Method
------

OpenCV Colorfulness and related pixel statistics.

Backend: ``opencv``. Output unit: ``colorfulness``.

Output
------

DataFrame columns include Colorfulness. Unit is a pixel statistic.

How to read
-----------

High Colorfulness is a more saturated photo, not a comfort score.

Parameters and sensitivity
--------------------------

JPEG compression and crop change Colorfulness more than the formula.

Failure modes
-------------

Unreadable images are skipped or raise depending on OpenCV.

Limitations
-----------

- Colorfulness is a pixel statistic, not a comfort score
- camera processing affects the value

Related pages
-------------

- Domain: :doc:`/domains/streetview`
- API: :doc:`/reference/api/streetview`
- Workflow: :doc:`/workflows/street_experience`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
