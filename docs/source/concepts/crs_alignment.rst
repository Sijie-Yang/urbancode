CRS and alignment
=================

Urban question
--------------

Why does a 400 m walk radius fail if the graph is still in
EPSG:4326, and what does UrbanCode reproject for you?

Result first
------------

.. figure:: /_static/recipes/units/units_punggol.png
   :alt: Punggol units drawn in the metric CRS
   :width: 100%

   Analysis units are built in the metric CRS (EPSG:32648 for
   Punggol). Cell size is metres, not degrees.

What you will learn
-------------------

* Geographic CRS vs projected CRS.
* Why metric radii cannot be applied to lon/lat as if they were metres.
* What ``fusion.aggregate`` reprojects automatically.
* Where precision can be lost.

Geographic vs projected
-----------------------

EPSG:4326 stores degrees. Distances and areas are not metres.
Punggol's metric CRS is EPSG:32648 (UTM 48N). Kallio uses a Finnish
UTM zone; Greenwich Village uses a New York UTM zone. Each pocket
stores ``geographic_crs`` and ``metric_crs`` in its manifest.

Wrong vs right
--------------

Wrong — treat lon/lat as metres::

   # Do not do this. 400 is 400 degrees, not 400 metres.
   area = uc.StudyArea.from_bbox(377740, 154330, 379740, 156330)

Right — lon/lat bbox, metric work in the derived CRS::

   area = uc.StudyArea.from_bbox(103.9010, 1.3959, 103.9190, 1.4140)
   units = uc.units.grid(city, cell_size=250)  # metres in metric_crs

``StudyArea.from_bbox`` with a projected ``crs=`` reprojects to WGS84
before UTM is stored. Metres passed as lon/lat raise.

What automatic reprojection does
--------------------------------

* Vector → units: GeoPandas reprojects the frame to the unit CRS
  before overlay or spatial join.
* Raster → units: Rasterio / rioxarray keep the raster grid; zonal
  stats sample in the raster CRS and attach coverage.
* Graph → units: nodes are read from ``layer.crs`` or
  ``graph.graph["crs"]`` and reprojected before the point-in-cell
  join.

UrbanCode does not silently resample a raster onto the unit grid
unless a function's contract says so.

Precision losses
----------------

* Degree ↔ metre conversion near the poles is poorly conditioned;
  these pockets are mid-latitude or equatorial.
* Repeated raster reprojection changes values. Prefer one warp.
* Nodata, transform, and extent travel with the GeoTIFF. A preview
  RGB is not a reflectance product.

Backend roles
-------------

.. list-table::
   :header-rows: 1
   :widths: 22 28 22 14 14

   * - Package
     - Responsibility
     - Called by UrbanCode
     - Direct use?
     - Status
   * - pyproj
     - Coordinate operations
     - StudyArea, units
     - Rarely
     - integrated
   * - GeoPandas
     - Vector CRS
     - load, aggregate
     - Yes, via ``layer.data``
     - integrated
   * - Rasterio / rioxarray
     - Raster CRS, transform, nodata
     - imagery, zonal stats
     - Yes
     - integrated

Related pages
-------------

* Concept: :doc:`study_area_city_layer`, :doc:`analysis_units`
* Domain: :doc:`/domains/fusion`
* Dataset: :doc:`/reference/datasets`

Use UrbanCode when several layers must meet on metric units.
Use pyproj or GeoPandas directly when you are diagnosing a single
CRS mismatch.
