UrbanKernel draft
=================

``UrbanKernel`` is **not implemented**. This page lists fields for a
later ``execute`` call. See :doc:`adr-005-operation-runtime-boundary`.

StreetRAG resolves ``selection_ref`` **before** the call. The spec
below has entity IDs or geometry only. UrbanCode never sees session
state.

OperationSpec (fields only)
---------------------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Field
     - Meaning
   * - ``operation``
     - Name from the list below (e.g. ``ndvi``).
   * - ``city_id``
     - Package identity.
   * - ``entity_ids``
     - Explicit Place / Street / Region IDs, or empty.
   * - ``geometry``
     - Optional GeoJSON / WKT when IDs are not enough.
   * - ``layer_refs``
     - Names or paths of input layers (City v1 names ok).
   * - ``parameters``
     - Operation-specific JSON object.
   * - ``scenario_id``
     - ``baseline`` or a scenario id.
   * - ``request_id``
     - Caller correlation id (not a session handle).

There is no ``selection_ref`` field. There is no chat or memory
blob.

OperationResult (fields only)
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 28 72

   * - Field
     - Meaning
   * - ``request_id``
     - Echo of the spec.
   * - ``status``
     - ``ok`` / ``partial`` / ``error``.
   * - ``observations``
     - List of Observation objects (see :doc:`urban-package-v3`).
   * - ``artifact_refs``
     - New or updated layer / figure paths.
   * - ``coverage``
     - What was computed vs requested.
   * - ``errors``
     - Structured codes, not LLM text.
   * - ``provenance_ids``
     - Receipts written for this call.

First operations (later phases)
-------------------------------

Listed only. Not implemented in this round.

* ``count`` — entity or feature counts
* ``zonal_stats`` — raster stats on polygons
* ``reachability`` — network accessibility
* ``ndvi`` — spectral index (and siblings later)
* ``park_accessibility`` — green access on the street graph
* ``rank`` / ``filter`` — order or subset by an existing metric

These wrap named UrbanCode functions. They are not a second
implementation.

Out of this draft
-----------------

No Python class, no ``urbancode.contracts``, no Recipes-as-tools,
no Punggol GAC loop.
