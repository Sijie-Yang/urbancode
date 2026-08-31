Unified architecture (UrbanCode × StreetRAG)
============================================

**Frozen.** This tree is a future StreetRAG interface only. Do not
extend UrbanPackage v3, UrbanKernel, or PSR contracts in the current
sprint. Product work is the unified domain API (StudyArea,
AnalysisUnits, IndicatorResult).

**Unified Phase 0** is documentation only. It records how UrbanCode
and StreetRAG should meet later. It does not implement a kernel, a
new on-disk schema, or any StreetRAG types.

This is **not** the same as product Phase 0 on
:doc:`/architecture/analysis-roadmap` (existing-API closure). Keep
that numbering. Call this work Unified Phase 0.

StreetRAG is a **downstream consumer**. It is not a dependency of
this repository. UrbanCode never imports StreetRAG. Do not look for
StreetRAG source in this tree.

::

   UrbanDS discover
        |
        v
   UrbanCode compute
        |
        v
   UrbanPackage v3 (draft)
        |
        v
   StreetRAG reason
        |
        |  explicit IDs or geometry
        v
   UrbanKernel (later)
        |
        |  observations + provenance
        v
   StreetRAG

.. toctree::
   :maxdepth: 1
   :caption: Decisions

   adr-001-system-boundary
   adr-002-urban-package-v3
   adr-003-entity-id-ownership
   adr-004-indicator-observation-mapping
   adr-005-operation-runtime-boundary
   adr-006-raster-and-psr-policy
   adr-007-scenario-and-memory-policy
   ownership

.. toctree::
   :maxdepth: 1
   :caption: Drafts

   urban-package-v3
   urban-kernel

What exists in UrbanCode today
------------------------------

``City`` uses ``SCHEMA_VERSION = 1``. A City is a named bag of
``Layer`` objects (``vector`` / ``raster`` / ``table`` / ``graph`` /
``images``) plus ``manifest.json``. ``StudyArea``, ``AnalysisUnits``,
``IndicatorResult``, and provenance receipts exist in code. Named
functions still return Layers; fusion writes the long indicator table.
See the Punggol fixture at ``examples/data/real/punggol/``.

StreetRAG types, PSR IDs, ``UrbanKernel``, and UrbanPackage v3 export
are **not** implemented. Those remain later interface work.

Next phases (UrbanCode only)
----------------------------

These are file-level intentions for the StreetRAG package contract.
They are not the same as the shipped StudyArea / units / fusion loop.

**Unified Phase 1 (later).** Optional package export hygiene. Still no
StreetRAG types.

**Unified Phase 2.** ``export_package`` / ``uc.open_package`` and a
JSON Schema generated from UrbanCode models. See
:doc:`urban-package-v3`.

**Unified Phase 3.** PSR IDs
(``place_id`` / ``edge_id`` / ``region_id``). See
:doc:`adr-003-entity-id-ownership`.

**Unified Phase 4.** ``UrbanKernel.execute(OperationSpec)``. See
:doc:`urban-kernel`.

**StreetRAG Phase 5** is theirs: consume the package, resolve
selections, run Ground–Act–Consolidate. UrbanCode only documents the
interface.

Out of this round
-----------------

No ``UrbanKernel`` class, no ``urbancode.contracts``, no
``export_package``, no version bump to 0.3.0, no copy of StreetRAG
Pydantic models into this repo.
