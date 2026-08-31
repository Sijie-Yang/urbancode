ADR-003: Entity ID ownership
============================

Status
   Accepted as policy. IDs are not minted in this release.

Context
-------

StreetRAG’s Place–Street–Region (PSR) model needs stable IDs.
UrbanCode today has layer names and file paths, not
``place_id`` / ``edge_id`` / ``region_id``. If each product mints
its own IDs, observations cannot join.

Decision
--------

**UrbanCode mints** ``place_id``, ``edge_id``, ``region_id``,
``observation_id``, and ``relation_id``. StreetRAG **must reuse**
them. It does not allocate a second ID for the same entity.

IDs are:

* **deterministic** — same source geometry and version produce the
  same ID
* **source-aware** — the mint includes the data source (OSM, fixture,
  user layer)
* **versioned** — a schema or geometry revision changes the ID
  namespace, not silently overwrite the old ID

Consequences
------------

StreetRAG selections resolve to UrbanCode IDs before any kernel
call (:doc:`adr-005-operation-runtime-boundary`). Raster cells are
not PSR entities (:doc:`adr-006-raster-and-psr-policy`).

Out of scope this week
----------------------

No AnalysisUnits, no ID minting code, no PSR tables on disk.
