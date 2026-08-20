UrbanCode
=========

UrbanCode is a unified, provenance-aware workflow layer for reproducible
urban analysis across vector, network, earth observation, climate, and
street-view data.

It is not a replacement for GeoPandas, OSMnx, Rasterio, or momepy.
Those packages do the geometry, graph, and raster work. UrbanCode
binds them to one contract: ``StudyArea``, ``City``, ``Layer``,
``AnalysisUnits``, ``IndicatorResult``, and provenance receipts.
The same analysis can then be reused across cities and data modalities.

Import the package as ``uc``.

30-second example
-----------------

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   city.study_area = uc.StudyArea.from_bbox(*city.metadata["bbox"], city_id="punggol")
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.imagery.ndvi(city.layers["sentinel2"].path)
   result = uc.fusion.aggregate(ndvi, units, stat="mean", indicator="ndvi")
   result.plot(indicator="ndvi")
   result.save("punggol_ndvi")

The committed Punggol pocket is a real 2 km extract. This snippet is
offline. Full walkthrough: :doc:`getting_started/quickstart`.

Five user paths
---------------

.. list-table::
   :widths: 28 72
   :header-rows: 1

   * - Path
     - Start here
   * - New user
     - :doc:`getting_started/quickstart`
   * - Urban researcher
     - :doc:`workflows/index`
   * - GIS developer
     - :doc:`domains/index`
   * - API user
     - :doc:`reference/api/index`
   * - Reproducibility reviewer
     - :doc:`concepts/provenance_quality` and :doc:`reference/datasets`

Real cases
----------

.. list-table::
   :header-rows: 0
   :widths: 33 33 34

   * - .. figure:: /_static/workflows/green_accessibility.png
          :alt: Punggol NDVI, park distance, and walk reachability on one 250 m grid
          :width: 100%

          Punggol green accessibility. NDVI, nearest park, and network
          reachability on the same units.

     - .. figure:: /_static/recipes/climate/utci_real.png
          :alt: UTCI on the Punggol DEM grid from observed weather and modelled MRT
          :width: 100%

          Heat exposure. Observed Open-Meteo weather plus modelled mean
          radiant temperature.

     - .. figure:: /_static/workflows/real_multi_city.png
          :alt: NDVI small multiples for Punggol, Kallio, and Greenwich Village
          :width: 100%

          Multi-city comparison. Same 2 km extent and 250 m scheme on
          three real pockets.

Urban questions
---------------

.. list-table::
   :header-rows: 1
   :widths: 34 22 22 22

   * - Urban question
     - Domain
     - Workflow
     - Catalog
   * - Urban form and land use
     - :doc:`domains/vector`
     - :doc:`workflows/punggol_urban_profile`
     - :doc:`reference/capabilities`
   * - Walking connectivity and accessibility
     - :doc:`domains/network`
     - :doc:`workflows/green_accessibility`
     - :doc:`reference/capabilities`
   * - Vegetation, water, and built-up surfaces
     - :doc:`domains/imagery`
     - :doc:`workflows/punggol_urban_profile`
     - :doc:`reference/capabilities`
   * - Terrain and solar orientation
     - :doc:`domains/imagery`
     - :doc:`workflows/multi_city_comparison`
     - :doc:`reference/capabilities`
   * - Outdoor thermal stress
     - :doc:`domains/climate`
     - :doc:`workflows/heat_exposure`
     - :doc:`reference/capabilities`
   * - Street-level perception
     - :doc:`domains/streetview`
     - :doc:`workflows/street_experience`
     - :doc:`reference/capabilities`
   * - Cross-modal neighbourhood indicators
     - :doc:`domains/fusion`
     - :doc:`workflows/green_accessibility`
     - :doc:`reference/capabilities`
   * - Cross-city comparison
     - :doc:`domains/units`
     - :doc:`workflows/multi_city_comparison`
     - :doc:`reference/capabilities`

Scope
-----

UrbanCode owns workflow orchestration and the shared objects.
Backend packages own the algorithms. Advanced users can drop to
``layer.data`` (GeoDataFrame, Xarray, or NetworkX graph) and call
upstream libraries directly. UrbanCode does not re-export every
GeoPandas, OSMnx, or Rasterio function.

Use UrbanCode when you need the same units, indicator table, and
receipts across modalities or cities.
Use the upstream package directly when you need a geometry predicate,
a custom graph algorithm, or a raster window that UrbanCode does not
wrap.

See :doc:`reference/ecosystem` for integrated, adapter, interoperable,
and roadmap packages.

.. toctree::
   :maxdepth: 2
   :caption: Get started

   getting_started/index

.. toctree::
   :maxdepth: 2
   :caption: Concepts

   concepts/index

.. toctree::
   :maxdepth: 2
   :caption: Workflows

   workflows/index

.. toctree::
   :maxdepth: 2
   :caption: Domains

   domains/index

.. toctree::
   :maxdepth: 2
   :caption: Reference

   reference/index
   migration/svi-to-streetview

.. toctree::
   :maxdepth: 1
   :caption: Development

   development/architecture
   development/roadmap
   changelog

* :ref:`genindex`
* :ref:`search`
