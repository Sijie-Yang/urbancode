Heat exposure
=============

Urban question
--------------

Where do thermal stress, low vegetation, and built-up surfaces overlap?

Result first
------------

.. figure:: /_static/workflows/real_heat_stress.png
   :alt: Punggol UTCI, NDVI, NDBI, building fraction, and high-UTCI/low-NDVI overlap
   :width: 100%

   Observed Open-Meteo weather at 2024-07-15T14:00 UTC plus a modelled
   spatial MRT proxy. Punggol 2 km pocket, 250 m units. Overlap is not
   a causal proof.

1. The public index is a number
-------------------------------

::

   import urbancode as uc

   utci = uc.climate.utci(tdb=31.2, rh=74, v=1.8)
   print(float(utci))

::

   34.0

``tdb`` is air temperature (°C), ``rh`` percent, ``v`` wind (m/s).
Mean radiant temperature defaults to air temperature unless you pass
``tr=``. This is not medical advice.

2. Vegetation and built-up on the grid
--------------------------------------

A spatial UTCI map needs a temperature **raster**. UrbanCode does
not ship a public MRT-proxy helper. You can still join NDVI, NDBI,
and building fraction on units:

::

   city = uc.load("examples/data/real/punggol", lazy=True)
   units = uc.units.grid(city, cell_size=250)
   ndvi = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units, stat="mean", indicator="ndvi",
   )
   ndbi = uc.fusion.aggregate(
       uc.imagery.ndbi(city.layers["sentinel2"]),
       units, stat="mean", indicator="ndbi",
   )
   buildings = uc.fusion.aggregate(
       city.layer("buildings"),
       units, stat="area_fraction", indicator="building_fraction",
   )
   print(ndvi.to_pandas()["value"].mean().round(3))
   print(ndbi.to_pandas()["value"].mean().round(3))
   print(buildings.to_pandas()["value"].mean().round(3))

::

   0.208
   -0.027
   0.175

Building fraction is OSM footprint area / clipped cell area, mean
0.175. The clipped denominator prevents edge cells from including
land outside the study envelope.

::

   result = uc.fusion.combine(units, ndvi, ndbi, buildings)
   result.plot(indicator="ndvi")

``result`` contains 243 records (81 units × 3 indicators). The plot
selects the existing ``ndvi`` records; ``combine`` does not calculate
UTCI or apply the documentation-only MRT proxy.

3. Reproduce the hero figure
----------------------------

The panel above is ``examples/workflows/real_heat_stress.py``. Weather
is Open-Meteo at **2024-07-15T14:00 UTC**. Sentinel-2 is
**2024-07-28** (13-day gap). The spatial MRT proxy is

``Tair + 6 * clip(NDBI, 0, 1) - 4 * clip(NDVI, 0, 1)``.

Those coefficients are a documentation proxy, not a measured
campaign. Every record carries ``modelled_mrt_proxy`` and
``weather_imagery_date_gap``.

.. literalinclude:: ../../../examples/workflows/real_heat_stress.py
   :language: python
   :start-after: # tutorial:start
   :end-before: # tutorial:end

``tr=`` on ``uc.climate.utci`` can be a GeoTIFF if you have one.
UrbanCode does not ship a public MRT-proxy helper; this script is
the documented example.

Limitations
-----------

* The MRT formula is a proxy, not a measured campaign.
* Weather and imagery dates differ by 13 days.
* Not shade-resolved.
