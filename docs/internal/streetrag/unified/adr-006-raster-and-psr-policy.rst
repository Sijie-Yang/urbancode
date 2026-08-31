ADR-006: Raster and PSR policy
==============================

Status
   Accepted as policy. Raster layout on disk does not change.

Context
-------

StreetRAG’s native raster path is incomplete. Treating every DEM or
NDVI cell as a Place or Region would explode the PSR graph and
break ID ownership.

Decision
--------

Raw rasters stay ``layers/raster``. StreetRAG consumes:

* raster **metadata** and **coverage**
* **zonal** observations (metric on a Place, Street, or Region)
* **artifact** references (paths or URIs to GeoTIFFs)

Raster **cells are not PSR entities**. UrbanCode does not mint
``place_id`` per pixel.

Consequences
------------

NDVI maps remain layers. A park-mean NDVI is an Observation on a
Region. StreetRAG does not need ``rasterio`` to *read* a package
manifest or observation table.

Out of scope this week
----------------------

No zonal Observation writer, no change to ``uc.imagery.ndvi``
return type, no StreetRAG raster rewrite.
