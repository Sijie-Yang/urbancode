Domains
=======

Each page answers three questions: what UrbanCode unifies, what the
backend package computes, and when to call that package directly.

.. toctree::
   :maxdepth: 1

   vector
   units
   network
   imagery
   climate
   streetview
   perception
   fusion

Keep these modules distinct:

* ``uc.imagery`` — continuous rasters (Sentinel-2, DEM, NDVI).
* ``uc.images`` — discrete geotagged city photos.
* ``uc.svi`` — street-view imagery catalogs, color, and live fetch.
* ``uc.perception`` — human-perception scores from photos.
* ``uc.climate`` — UTCI and physical thermal indices.
* ``uc.fusion`` — the same scores on shared analysis units.

Window-view photos are ``view_type="windowview"`` on an images
Layer. They are not street view. Satellite rasters are not images.

Signatures live in :doc:`/reference/api/index`. Runnable cases live
in :doc:`/reference/recipes/index`.
