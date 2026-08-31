City directory format
=====================

A City directory contains ``manifest.json``, ``layers/``, and optional
``area/study_area.gpkg`` plus ``provenance/receipts.jsonl``.

``SCHEMA_VERSION`` is **1**. New fields are additive. ``uc.load`` /
``City.to_dir`` round-trip vectors, rasters, tables, graphs, and images.

Lazy layers copy their source files on save instead of materializing
them in memory.
