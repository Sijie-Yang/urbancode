Image observations
==================

Urban question
--------------

How is a geotagged city photo different from a Sentinel-2 pixel?

Result first
------------

A photo is a discrete observation. A satellite image is a continuous
raster. UrbanCode keeps them in different modules so window-view
photos never become ``streetview``, and Sentinel-2 never becomes
``images``.

Domain boundaries
-----------------

.. list-table::
   :header-rows: 1
   :widths: 22 78

   * - Module
     - What it holds
   * - ``uc.imagery``
     - Continuous geographic rasters: Sentinel-2, DEM, NDVI, NDBI.
   * - ``uc.images``
     - Discrete city photos with metadata: path, coordinates, license.
   * - ``uc.streetview``
     - Street-view acquisition and street-specific features.
   * - ``uc.perception``
     - Human-perception scores from city photos (street or window view).
   * - ``uc.climate``
     - Physical thermal indices such as UTCI.
   * - ``uc.fusion``
     - The same scores on shared ``AnalysisUnits``.

Window-view imagery is ``view_type="windowview"`` on an images Layer.
It is not street view. Satellite imagery is not an images Layer.

Contract
--------

::

   images = uc.images.from_table(
       frame,
       id_column="image_id",
       path_column="image_path",
       lon="longitude",
       lat="latitude",
       view_type="streetview",
       source="wikimedia-commons",
       license="CC BY-SA 4.0",
   )

Each row needs a unique ``image_id``. One location can have several
photos, so geometry-only IDs are not allowed. Automatic IDs require
an explicit ``id_strategy="uri_hash"`` or ``"checksum"``.

The Layer also carries ``view_type``, ``city_id``, ``source``,
``license``, ``captured_at``, and ``location_quality``.

``uc.streetview.as_layer()`` stays. It calls this helper and sets
``view_type="streetview"``.

See also
--------

* API: :doc:`/reference/api/images`
* Recipe: :doc:`/reference/recipes/images/from_table_punggol`
* Research case: :doc:`/workflows/research_cases/thermal_comfort_in_sight`
