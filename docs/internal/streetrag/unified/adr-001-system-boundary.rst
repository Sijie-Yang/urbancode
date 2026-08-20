ADR-001: System boundary
========================

Status
   Accepted for Unified Phase 0 (documentation). Not implemented.

Context
-------

UrbanCode already fetches, computes, and stores urban layers. StreetRAG
(a separate product) reasons over a city with Ground–Act–Consolidate
and SpatialMemory. The two codebases must not merge. Mixing LLM
control flow into UrbanCode, or reimplementing GIS inside StreetRAG,
would duplicate formulas and pull heavy extras into the wrong process.

Decision
--------

UrbanCode is the **deterministic engine and data plane**: fetch,
compute, fuse, validate, and write packages. StreetRAG is the
**reasoner**: Ground–Act–Consolidate plus SpatialMemory.

* UrbanCode does not run GAC, does not call an LLM, and does not
  store session memory.
* StreetRAG does not reimplement OSM download, raster indices,
  zonal stats, or network metrics. Those sink to UrbanCode later.
* Dependency is one-way. StreetRAG may later depend on a **light**
  UrbanCode contracts extra. UrbanCode never imports StreetRAG.

Consequences
------------

Named UrbanCode functions stay the public compute API. A future
``UrbanKernel`` is a typed façade over those functions, not a second
formula set. StreetRAG may read an UrbanPackage without installing
``torch``, ``osmnx``, or ``rasterio``.

Out of scope this week
----------------------

No kernel, no contracts extra, no StreetRAG code changes, no move of
``uc.climate`` or other modules.
