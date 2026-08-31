ADR-002: UrbanPackage v3
========================

Status
   Draft. Not the on-disk format of this release.

Context
-------

UrbanCode City **v1** is ``manifest.json`` plus ``layers/``. StreetRAG
City Package **v2** (``schema_version=2``) already exists in that
product. Neither side should break the other this week. A shared
next contract is still needed so indicators, entities, and
provenance can travel without copying Pydantic models.

Decision
--------

The next **shared** on-disk contract is **UrbanPackage v3**.

* UrbanCode City v1 remains the **supported** save format
  (``SCHEMA_VERSION`` stays 1).
* StreetRAG Package v2 remains StreetRAG’s format until they migrate.
  That migration is not UrbanCode’s job.
* v3 is additive and **draft only** in this repository. See
  :doc:`urban-package-v3`.

Consequences
------------

Readers of v1 and v2 keep working. Future ``city.export_package`` /
``uc.open_package`` (Unified Phase 2) will emit and read v3. This
round provides a field map, not a migrator.

Out of scope this week
----------------------

No ``export_package``, no schema migration, no fixture rebuild, no
``urbancode.contracts`` package.
