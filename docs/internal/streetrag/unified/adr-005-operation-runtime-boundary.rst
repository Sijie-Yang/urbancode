ADR-005: Operation runtime boundary
===================================

Status
   Accepted as policy. ``UrbanKernel`` is not implemented.

Context
-------

StreetRAG selections are session-scoped (``selection_ref``,
SpatialContext). UrbanCode functions take explicit graphs, rasters,
and tables. If UrbanCode accepted a session handle, it would import
StreetRAG state and stop being deterministic.

Decision
--------

Later: ``UrbanKernel.execute(OperationSpec) -> OperationResult``.

StreetRAG **resolves** ``selection_ref`` **before** the call and
passes explicit entity IDs or geometry. UrbanCode **never** sees
session state, chat history, or SpatialMemory.

Field drafts: :doc:`urban-kernel`.

Consequences
------------

The kernel is a typed door over named functions already in
UrbanCode. Recipes-as-tools and GAC loops stay in StreetRAG.

Out of scope this week
----------------------

No ``UrbanKernel`` class, no OperationSpec runtime, no count /
zonal / reachability kernel operations.
