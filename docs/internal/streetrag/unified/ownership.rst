Ownership matrix
================

Who owns which concern. StreetRAG is not in this repository; the
right-hand column is a contract for a downstream consumer.

System split
------------

.. list-table::
   :header-rows: 1
   :widths: 28 36 36

   * - Concern
     - UrbanCode
     - StreetRAG
   * - Discover catalogs
     - UrbanDS (later / sibling)
     - May request a place
   * - Fetch OSM / STAC / SVI
     - Yes
     - No
   * - Compute indices/metrics
     - Yes (named functions)
     - No second formula
   * - Fuse / validate layers
     - Yes
     - No
   * - On-disk City / package
     - City v1 now; UrbanPackage v3 later
     - Package v2 now; consume v3 later
   * - Mint PSR / observation IDs
     - Yes (later)
     - Reuse only
   * - GAC loop
     - No
     - Yes
   * - LLM / NL answers
     - No
     - Yes
   * - SpatialMemory
     - No
     - Yes
   * - Resolve ``selection_ref``
     - No
     - Yes, **before** calling UrbanCode
   * - Session overwrite of baseline
     - No
     - Must not

Native StreetRAG tools
----------------------

These stay in StreetRAG. UrbanCode will not grow them.

* **ground** — bind a question to a study area and current selection
* **selection** — resolve ``selection_ref`` to IDs or geometry
* **memory** — SpatialMemory read/write (“why we called”)
* **retrieve** — fetch Observations and artifacts already in the package

Must come from UrbanKernel later
--------------------------------

StreetRAG must not reimplement these. They are UrbanCode compute
(today as named functions; later as kernel operations).

* NDVI / other spectral indices
* UTCI (weather calculator, not a satellite index)
* morphology (when added)
* zonal statistics
* park accessibility / reachability

Reading a package
-----------------

A StreetRAG process that only **reads** ``urban_package.json``,
entity tables, and observation JSON **must not** need ``torch``,
``osmnx``, or ``rasterio``. Those extras stay on the UrbanCode
compute path. See :doc:`/architecture/ecosystem`.
