uc.svi.filename
===============

Urban question
--------------

Which image files are in this folder?

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
   print(table.head())

``table`` is a pandas DataFrame with one row per discovered image file. It contains filenames and paths only--no coordinates or perception scores are inferred.

The figure below is the output for the committed fixture. Live-source
recipes can return different timestamps or inventories.

.. figure:: ../../../_static/recipes/streetview/filename_punggol.png
   :alt: uc.svi.filename result for the registered dataset
   :width: 100%

   Output of ``uc.svi.filename`` on dataset ``streetview``.
   Unit: filename. Backend: pandas.

Inputs
------

image directory

Spatial support
---------------

Native support: image and geotagged point. Grid means are used only when coverage is sufficient.

Parameters
----------

``folder`` of image files. No model, no scores.

Method
------

Lists image files in a folder. No perception scores.

Backend: ``pandas``. Output unit: ``filename``.

Output
------

DataFrame with Filename and path. Not a spatial sample.

How to read
-----------

The contact sheet is the catalog, not a spatial sample.

Parameters and sensitivity
--------------------------

Hidden files are ignored; extension filter is image types.

Failure modes
-------------

Missing folder raises.

Limitations
-----------

- catalog only; no perception scores
- photo locations are recorded separately

Related pages
-------------

- Domain: :doc:`/domains/streetview`
- API: :doc:`/reference/api/streetview`
- Workflow: :doc:`/workflows/street_experience`
- Dataset: :doc:`/reference/datasets`
- Catalog: :doc:`/reference/capabilities`
