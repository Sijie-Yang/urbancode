UrbanCode
=========

UrbanCode is a library for reproducible urban analysis across street
networks, earth observation, climate, and street-view imagery. It is
built on GeoPandas, OSMnx, Rasterio, and related tools.

Import the package as ``uc``.

Some of the functionality that UrbanCode offers:

* Load a study area and keep vector, raster, and graph layers in one
  ``City``.
* Build shared analysis units (grid, hex, or from a layer).
* Measure vegetation, water, built-up surface, and terrain.
* Measure street-network centrality, clustering, and walk reachability.
* Compute UTCI from observed weather plus a documented MRT proxy.
* Score street photos for visual thermal affordance (VATA).
* Fuse those quantities onto the same units with provenance receipts.

UrbanCode owns the shared objects and the workflow. Backend packages
own the algorithms. Advanced users can drop to ``layer.data`` and call
GeoPandas, OSMnx, or Rasterio directly.

Comments, suggestions, and bug reports are welcome via
`GitHub <https://github.com/Sijie-Yang/UrbanCode>`__.

Getting started
---------------

Install extras, then follow the three-page walkthrough:

* :doc:`getting_started/installation`
* :doc:`getting_started/quickstart`
* :doc:`getting_started/first_project`

Examples
--------

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   print(city.place, city.keys()[:3])

::

   Punggol, Singapore ['streets', 'buildings', 'parks']

::

   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.imagery.ndvi(city.layers["sentinel2"])
   result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
   print(round(float(result.to_pandas()["value"].mean()), 3))
   result.plot(indicator="ndvi")

::

   0.208

``units`` is the 250 m comparison grid, ``ndvi`` is the native
Sentinel-2 raster, and ``result`` is an ``IndicatorResult`` with one
mean and one coverage value per cell. The plot produced by the last
line is the map below.

.. figure:: /_static/recipes/fusion/combine_punggol.png
   :alt: Mean Punggol NDVI on the 250 m grid
   :width: 100%

   Mean NDVI for the committed Sentinel-2 window. This is one date,
   not a seasonal vegetation score.

Reachability is a separate graph measure::

   reach = uc.network.accessibility(
       city["streets"], radius=150, metric="reachability"
   )
   print(reach.data.number_of_nodes())

::

   1425

``reach`` is a graph ``Layer``. The 1,425 nodes carry a
``reachability`` attribute counting other nodes within 150 m of graph
length; the value is not population or travel time.

The committed Punggol pocket is a real 2 km extract. This snippet is
offline. Walkthrough: :doc:`getting_started/quickstart`.

Install
-------

::

   pip install urbancode
   pip install "urbancode[standard]"     # vector + network + imagery + climate + viz
   pip install "urbancode[svi]"          # TCIS + color

Python 3.10+. The core wheel is small. Torch is not in ``[standard]``.
See :doc:`getting_started/installation` for extras and backends.

How to cite
-----------

Yang, Sijie. *UrbanCode: a unified Python library for multimodal urban
analysis*. https://github.com/Sijie-Yang/UrbanCode

Research cases built on UrbanCode should also cite the original papers
(Thermal Comfort in Sight, Heat Resilience in Sight).

Contributing
------------

Bug reports and ideas belong on the GitHub tracker. Documentation and
tests are as useful as new code. Development notes:
:doc:`development/architecture` and :doc:`development/roadmap`.

.. toctree::
   :hidden:
   :maxdepth: 1

   Home <self>

.. toctree::
   :hidden:
   :caption: User guide
   :maxdepth: 2

   getting_started/index
   concepts/index
   domains/index

.. toctree::
   :hidden:
   :caption: Examples
   :maxdepth: 2

   workflows/index

.. toctree::
   :hidden:
   :caption: API
   :maxdepth: 2

   reference/index
   migration/streetview-to-svi

.. toctree::
   :hidden:
   :caption: For contributors
   :maxdepth: 1

   development/architecture
   development/roadmap
   changelog
   GitHub <https://github.com/Sijie-Yang/UrbanCode>
