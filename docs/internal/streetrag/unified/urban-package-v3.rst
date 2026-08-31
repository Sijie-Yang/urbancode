UrbanPackage v3 draft
=====================

This page is a **draft on-disk contract**. It is not implemented.
``SCHEMA_VERSION`` in ``urbancode.city`` stays **1**. City v1
(``manifest.json`` + ``layers/``) remains the supported save format.

JSON Schema stubs live beside this page. They are documentation
artifacts. They are not imported by UrbanCode and do not define a
``urbancode.contracts`` extra.

* ``schemas/urban-package-v3.schema.json``
* ``schemas/entity.schema.json``
* ``schemas/observation.schema.json``
* ``schemas/relation.schema.json``
* ``schemas/operation.schema.json``
* ``schemas/result.schema.json``

Proposed tree
-------------

::

   urban_package.json
   area/study_area.json
   layers/{vector,raster,graph,tables,images}/
   entities/{places,streets,regions}/
   observations/{baseline,scenarios/<id>}/
   relations/
   trajectories/
   indicators/
   artifacts/
   provenance/receipts.jsonl

``urban_package.json`` is the v3 root (schema version 3, city id,
CRS, layer index, entity index). It is not a rename of City v1
``manifest.json``.

Compatibility
-------------

* **UrbanCode City v1** stays readable and writable. Do not migrate
  the Punggol fixture in this round.
* **StreetRAG City Package v2** stays StreetRAG’s format until they
  migrate. That work is not in this repository.
* **v3 is additive.** Future ``city.export_package`` /
  ``uc.open_package`` (Unified Phase 2) will emit and read v3.
  This page is a **field map**, not a migrator.

City v1 Layer → v3
------------------

The map is honest and incomplete. StreetRAG v2 field names are
taken from a completed remote audit; this workspace does not re-read
that tree.

.. list-table::
   :header-rows: 1
   :widths: 32 68

   * - City v1
     - UrbanPackage v3 (draft)
   * - ``kind=raster``
     - ``layers/raster`` only. Not PSR entities.
       See :doc:`adr-006-raster-and-psr-policy`.
   * - ``kind=vector`` (buildings, parks, pois)
     - ``layers/vector`` plus later Place or Region entities under
       ``entities/``.
   * - ``kind=graph`` (streets)
     - ``layers/graph`` plus later Street entities (``edge_id``).
   * - ``kind=images`` (streetview)
     - ``layers/images`` (street-view files).
   * - ``kind=table`` (comfort)
     - Later Street Observation. Not a layer clone.
   * - ``place`` / ``boundary``
     - ``area/study_area.json``
   * - ``metadata`` / checksums
     - ``provenance/receipts.jsonl`` plus layer metadata

Proposed Observation fields
---------------------------

UrbanCode will **compute** these. StreetRAG will **store and
retrieve** them. Mapping only; no Pydantic in this repo. See
:doc:`adr-004-indicator-observation-mapping`.

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Field
     - Meaning
   * - ``observation_id``
     - Minted by UrbanCode. Deterministic, versioned.
   * - ``city_id``
     - Package / study identity.
   * - ``entity_level``
     - ``place`` / ``street`` / ``region``.
   * - ``entity_id``
     - ``place_id`` / ``edge_id`` / ``region_id``.
   * - ``metric_key``
     - e.g. ``ndvi_mean``, ``visual_comfort``.
   * - ``value``
     - Numeric or null. **Missing is not 0.**
   * - ``unit``
     - SI or documented unit string.
   * - ``measurement_scale``
     - ratio / interval / ordinal / nominal.
   * - ``direction``
     - higher-is-better / lower-is-better / none.
   * - ``spatial_support``
     - Geometry or coverage used for the value.
   * - ``temporal.valid_from``
     - Inclusive start (ISO-8601 or null).
   * - ``temporal.valid_to``
     - Exclusive end (ISO-8601 or null).
   * - ``scenario_id``
     - ``baseline`` or a scenario id. Never overwrite baseline.
       See :doc:`adr-007-scenario-and-memory-policy`.
   * - ``method``
     - Named UrbanCode function or recipe id.
   * - ``parameters``
     - JSON object of compute parameters.
   * - ``coverage``
     - Fraction or mask summary; not a substitute value.
   * - ``uncertainty``
     - Optional numeric or structured interval.
   * - ``quality_flags``
     - List of codes (nodata, unofficial, experimental).
   * - ``provenance_id``
     - Pointer into ``provenance/receipts.jsonl``.
   * - ``artifact_ref``
     - Path or URI to a layer / figure / table.

A **percentile does not replace the raw value**. Store both if both
are needed. StreetRAG must not invent a second formula for the same
``metric_key``.

What this draft does not claim
------------------------------

* Exact StreetRAG v2 JSON key parity (audit was remote; do not copy
  their models here).
* A working exporter or validator.
* Trajectories, relations, or indicator catalogs as runtime APIs.
