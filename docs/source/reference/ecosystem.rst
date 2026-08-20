Ecosystem
=========

UrbanCode does not own the GIS Python stack. This page records how
each package relates to UrbanCode today.

Four tiers
----------

* **Tier 1 — Integrated.** Called inside UrbanCode, tested, and
  written into provenance.
* **Tier 2 — Official adapter.** ``uc.adapters`` re-exports the
  package. UrbanCode does not wrap every function.
* **Tier 3 — Interoperable.** Hand the object via ``layer.data`` or
  a standard file. UrbanCode does not call it.
* **Tier 4 — Roadmap.** Evaluation only. Not a current feature.

Foundation / vector
-------------------

.. list-table::
   :header-rows: 1
   :widths: 18 16 14 14 20 18

   * - Package
     - Role
     - Status
     - Domain
     - UrbanCode hook
     - Extra
   * - numpy / pandas
     - arrays and tables
     - integrated
     - core
     - IndicatorResult
     - core
   * - GeoPandas
     - vector frames
     - integrated
     - vector
     - load, aggregate
     - vector
   * - Shapely
     - geometry
     - integrated
     - units
     - grid / hexgrid
     - vector
   * - pyproj
     - CRS
     - integrated
     - core
     - StudyArea
     - vector
   * - pyogrio / GDAL
     - vector I/O
     - integrated
     - vector
     - City I/O
     - vector
   * - Fiona
     - older I/O
     - interoperable
     - vector
     - ``layer.data``
     - —
   * - DuckDB Spatial
     - large SQL
     - roadmap
     - vector
     - —
     - —
   * - GeoArrow / PyArrow
     - columnar interchange
     - interoperable
     - vector
     - parquet export
     - vector
   * - Dask-GeoPandas
     - distributed vector
     - roadmap
     - vector
     - —
     - —
   * - PostGIS / GeoAlchemy2
     - database
     - roadmap
     - vector
     - —
     - —
   * - h3-py
     - global grid
     - roadmap
     - units
     - —
     - —

Network
-------

.. list-table::
   :header-rows: 1
   :widths: 18 16 14 14 20 18

   * - Package
     - Role
     - Status
     - Domain
     - UrbanCode hook
     - Extra
   * - OSMnx
     - OSM graphs
     - integrated
     - network
     - ``network.fetch``
     - network
   * - NetworkX
     - graph algorithms
     - integrated
     - network
     - centrality, access
     - network
   * - momepy
     - morphology; ``gdf_to_nx``
     - integrated (interchange)
     - network
     - ``graph_from_gdf``
     - network
   * - cityseer
     - multi-scale network
     - roadmap
     - network
     - —
     - —
   * - Pandana / r5py
     - access / transit
     - roadmap
     - network
     - —
     - —
   * - igraph / rustworkx
     - large graphs
     - roadmap
     - network
     - —
     - —
   * - peartree / partridge / GTFS Kit
     - GTFS
     - roadmap
     - mobility
     - —
     - —

Raster / earth observation
--------------------------

.. list-table::
   :header-rows: 1
   :widths: 22 18 14 14 16 16

   * - Package
     - Role
     - Status
     - Domain
     - Hook
     - Extra
   * - Rasterio
     - raster I/O
     - integrated
     - imagery
     - read, indices
     - imagery
   * - rioxarray / Xarray
     - labelled rasters
     - integrated
     - imagery
     - read
     - imagery
   * - pystac-client
     - STAC search
     - integrated
     - imagery
     - fetch
     - imagery
   * - planetary-computer
     - signing
     - integrated
     - imagery
     - fetch
     - imagery
   * - stackstac / odc-stac / Dask
     - time stacks
     - roadmap
     - imagery
     - —
     - —
   * - exactextract / rasterstats
     - zonal backends
     - roadmap
     - imagery
     - —
     - —
   * - rio-cogeo / geocube
     - COG / cube
     - roadmap
     - imagery
     - —
     - —
   * - xarray-spatial / Whitebox / richdem
     - extra terrain
     - roadmap
     - imagery
     - —
     - —

Spatial statistics
------------------

PySAL, libpysal, esda, spreg, segregation, pointpats, spaghetti,
mgwr, and splot are **roadmap**. There is no ``uc.pysal`` API.

Climate
-------

* pythermalcomfort — integrated (``uc.climate.utci``), extra
  ``climate``.
* xclim, pvlib — roadmap.
* Meteostat, cdsapi, earthaccess — interoperable data portals.

Street view
-----------

* ZenSVI — integrated for live ``streetview.fetch``.
* streetlevel — experimental Google adapter.
* Pillow / OpenCV — integrated for I/O and color.
* PyTorch / torchvision / transformers — integrated for models.
* Provider SDKs — live only; photos are not redistributed.

Mobility
--------

MovingPandas, trackintel, and scikit-mobility are roadmap.
Pandana and r5py are listed under network.

Visualization
-------------

* Matplotlib — integrated (``viz`` extra).
* mapclassify, contextily — interoperable / imagery extra has
  contextily.
* Folium, Plotly, GeoViews, Datashader, lonboard, pydeck,
  kepler.gl, leafmap, geemap — interoperable or roadmap. UrbanCode
  does not wrap them.

3D / LiDAR
----------

PDAL, laspy, Open3D, PyVista, trimesh, py3dtiles — roadmap.

Official links
--------------

* `GeoPandas <https://geopandas.org/>`__
* `OSMnx <https://osmnx.readthedocs.io/>`__
* `momepy <https://docs.momepy.org/>`__
* `Rasterio <https://rasterio.readthedocs.io/>`__
* `Xarray <https://docs.xarray.dev/>`__
* `rioxarray <https://corteva.github.io/rioxarray/stable/>`__
* `PySAL <https://pysal.org/>`__
* `pythermalcomfort <https://pythermalcomfort.readthedocs.io/>`__

Use UrbanCode when you need the City / units / IndicatorResult
contract.
Use the upstream package directly when the function you need is
not in :doc:`capabilities`.
