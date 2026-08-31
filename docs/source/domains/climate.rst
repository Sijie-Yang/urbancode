Climate
=======

Urban question
--------------

Where does outdoor thermal stress look high when air temperature,
humidity, and wind are observed and mean radiant temperature is
modelled?

Result first
------------

.. figure:: /_static/recipes/climate/utci_real.png
   :alt: UTCI on the Punggol DEM grid from observed weather and modelled MRT
   :width: 100%

   UTCI in °C after a spatial MRT proxy
   (``Tair + 6·NDBI − 4·NDVI``) and observed Open-Meteo T/RH/wind
   at 2024-07-15T14:00 UTC. MRT is modelled, not measured.

What you will learn
-------------------

* The canonical function is :func:`urbancode.climate.utci`.
* The four UTCI inputs and their honesty labels.
* Why this is not a medical diagnosis or a measured campaign.

Installation
------------

::

   pip install "urbancode[climate,imagery]"

``climate`` installs the UTCI backend. ``imagery`` is included here
because the mapped case passes raster inputs; scalar UTCI alone only
needs ``urbancode[climate]``.

UrbanCode API
-------------

* :func:`urbancode.climate.utci`

``uc.imagery.utci`` is a compatibility alias. Do not follow a second
tutorial on the imagery page.

::

   import urbancode as uc

   utci = uc.climate.utci(tdb=31.2, rh=74, v=1.8)
   print(float(utci))

::

   34.0

Backend stack
-------------

.. list-table::
   :header-rows: 1
   :widths: 22 24 20 16 18

   * - Package
     - Responsibility
     - Called by UrbanCode
     - Direct use?
     - Status
   * - pythermalcomfort
     - UTCI equation
     - ``climate.utci``
     - Rarely
     - integrated
   * - Xarray / rioxarray
     - raster alignment
     - input rasters
     - Yes
     - integrated
   * - Rasterio
     - grid I/O
     - output Layer
     - Yes
     - integrated
   * - xclim, pvlib
     - broader climate / solar
     - no
     - Yes
     - planned
   * - Meteostat, CDS, earthaccess
     - data portals
     - no
     - Yes
     - interoperable

Inputs
------

.. list-table::
   :header-rows: 1
   :widths: 28 18 54

   * - Variable
     - Label
     - This case
   * - Air temperature
     - observed
     - Open-Meteo 2 m, 2024-07-15T14:00 UTC
   * - Relative humidity
     - observed
     - Open-Meteo
   * - Wind speed
     - observed
     - Open-Meteo 10 m; UTCI expects a reference height —
       see pythermalcomfort
   * - Mean radiant temperature
     - modelled
     - ``Tair + 6·clip(NDBI,0,1) − 4·clip(NDVI,0,1)`` (``modelled_mrt_proxy``)

Do not treat MRT as a measurement.

Reading the result
------------------

* Spatial contrast follows the NDVI/NDBI MRT proxy, not the point
  weather field. Air temperature itself is spatially constant.
* After ``fusion.aggregate``, high-UTCI cells are exposure on that
  timestamp, not a climate normal.
* Low NDVI and high UTCI can overlap; that is a joint map, not a
  causal claim. See :doc:`/workflows/heat_exposure`.

Limitations
-----------

* UTCI is an outdoor thermal index, not a personal medical diagnosis.
* Shade and sun are not resolved when MRT is copied from air
  temperature.
* The weather timestamp is not the Sentinel-2 date.
* Wind-height conversion is the backend's responsibility; check
  the version in the receipt.
* A synthetic method demo still exists as a contract script
  (``examples/workflows/climate_heat_stress.py``). It is not a
  real-city conclusion.

Related pages
-------------

* Recipe: :doc:`/reference/recipes/climate/utci_real`
* Workflow: :doc:`/workflows/heat_exposure`
* API: :doc:`/reference/api/climate`
* Upstream: `pythermalcomfort <https://pythermalcomfort.readthedocs.io/>`__

Use UrbanCode when UTCI must join NDVI on the same units.
Use pythermalcomfort directly when you already have four aligned
arrays and no City workflow.
