Spatial support and maps
========================

Urban question
--------------

When should a map show streets and buildings, and when should it
show a 250 m grid?

Result first
------------

.. figure:: /_static/concepts/native_to_fusion.png
   :alt: Native geometries become domain indicators, then common units, then fusion
   :width: 100%

   Streets, buildings, raster pixels, and observation points keep
   their native geometry through domain analysis. Common
   ``AnalysisUnits`` appear only when modalities must be compared.

What you will learn
-------------------

* Native geometry is the spatial support of the data.
* Analysis units are a comparison frame, not the city.
* Missing, zero, and no-coverage are different.
* Offline context is not an online basemap.

Native geometry
---------------

* Buildings are footprints.
* Streets are edges and nodes.
* Imagery is raster pixels (10 m Sentinel-2, 30 m DEM).
* Street-view is a photo plus a geotagged point.

Domain pages show this geometry first.

Analysis units
--------------

Grid, hexgrid, administrative polygons, and custom neighbourhoods
are comparison supports. They let NDVI, reachability, and photo
counts share a row key.

**Analysis units provide a common comparison support. They do not
replace the native geometry of streets, buildings, imagery, or
observations.**

When to show which
------------------

* Vector, network, imagery, climate fields, and street-view points:
  native geometry first.
* Fusion and multi-city comparison: common units, always with city
  context underneath.
* A 250 m cell is not a building and not a neighbourhood boundary.

Missing, zero, no coverage
--------------------------

* Missing / no coverage: no observation in that unit. Draw
  transparent or hatch. Do not paint a solid grey block over the
  city.
* Zero: a real zero (no park, no reachable node, NDVI near 0).
* No coverage is not the same as zero.

Context vs basemap
------------------

UrbanCode docs draw committed OSM / Sentinel-derived context
offline. That is not a tiled web basemap. ``contextily`` is
optional and live-only.

Locator vs study boundary
-------------------------

The black outline is the 2 km study pocket. The inset is the
parent city (Singapore, Helsinki, New York) so the pocket can be
placed. The inset is a locator, not a cadastral claim.

Related pages
-------------

* :doc:`analysis_units`
* :doc:`/getting_started/quickstart`
* :doc:`/domains/vector`
* :doc:`/domains/network`
* :doc:`/domains/imagery`
* :doc:`/domains/streetview`
* :doc:`/domains/fusion`
* :doc:`/workflows/index`
