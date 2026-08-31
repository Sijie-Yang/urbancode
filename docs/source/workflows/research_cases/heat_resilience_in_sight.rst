Heat Resilience in Sight
========================

Urban question
--------------

Where is streetscape thermal-affordance **supply** enough for local
climate **demand**, and where does that margin fail by city and month
— without treating VATA, UTCI, and SHR as the same quantity?

Original research and citation
------------------------------

Yang, Sijie, et al. *Heat Resilience in Sight: Climate-Conditioned
Thermal Affordance of Streetscapes Across Cities and Seasons*.
Workshop draft. Reproduction code lives in
``examples/research_cases/heat_resilience_in_sight.py``.

This page is an eight-city **application**, not a validation of VATA,
UTCI, or SHR.

What UrbanCode owns
-------------------

Committed summary tables, city-month charts, robustness / domain
tables, and provenance. Tutorial code stays on ``uc.*`` only for
objects that already exist. There is no public SHR or climate-demand
helper in this release.

What the upstream project owns
------------------------------

The eight-city VATA panel, hourly Open-Meteo / SolarCal demand, Hong
Kong June–August calibration, SHR definition, robustness variants,
and domain-shift diagnostics.

Quantities
----------

* **VATA** is visual thermal affordance (0–5). It is not measured
  personal comfort and it is not UTCI.
* **UTCI** here is an **hourly climatological proxy** (ERA5-Land
  10–17 local, SolarCal open-sun MRT). It is not a street-canyon
  simulation.
* **SHR** is city-mean VATA minus climate-adjusted VATA need. It is
  not UTCI and not VATA.

Hong Kong June–August is a **normative** planning anchor
(``v_ref = 1.732``, ``d_ref = 7.991``), not a physiological
threshold. It is not equatorial Singapore and not Hong Kong's annual
mean.

Data and licensing
------------------

Git holds city / month / robustness **summaries** under
``examples/data/research_cases/heat_resilience_in_sight/``. Per-image
VATA (~892,466 rows), the ``hourly_v1`` climate cache, and raw JPEGs
are not in Git.

**Singapore panels are not interchangeable.** Heat Resilience in
Sight uses n = 21,772. Thermal Comfort in Sight uses the 92,233
survey set. ``svi_jh`` is Johannesburg, not Johor Bahru.

1. Read the annual table
------------------------

There is no public SHR helper. The committed CSV is the teaching
object.

::

   import pandas as pd

   annual = pd.read_csv(
       "examples/data/research_cases/heat_resilience_in_sight/"
       "annual_climate_vata.csv"
   )
   shown = annual[["city", "n", "shr", "v_bar"]].round(
       {"shr": 3, "v_bar": 3}
   )
   print(shown.to_string(index=False))

::

          city      n    shr  v_bar
   svi_capetown 169843  0.808  1.202
         svi_hk  16955  0.861  1.732
         svi_jh 172225  0.802  1.351
   svi_melbourne 226546 1.501  1.864
         svi_ny  54377  0.993  1.413
        svi_rio  55233 -0.191  1.362
         svi_sg  21772  0.082  1.957
      svi_tokyo 175515  0.954  1.459

``annual`` contains one summary row per city; ``shown`` keeps only
the sample size, resilience margin, and mean VATA columns. Singapore
is ``svi_sg``, n = 21,772, SHR ≈ 0.082, mean VATA
``v_bar`` ≈ 1.96. Rio (``svi_rio``) is negative (≈ −0.19). That is
an application of the Hong Kong JJA anchor, not a validation of
TCIS.

2. Look at one city
-------------------

::

   sg = annual[annual["city"] == "svi_sg"].iloc[0]
   print(int(sg["n"]), round(float(sg["shr"]), 3), round(float(sg["utci"]), 3))

::

   21772 0.082 34.642

``utci`` here is an hourly climatological proxy, not a street-canyon
simulation.

3. Monthly file
---------------

::

   monthly = pd.read_csv(
       "examples/data/research_cases/heat_resilience_in_sight/"
       "monthly_climate_vata.csv"
   )
   print(monthly.columns.tolist()[:8])
   print(len(monthly))

::

   ['month', 'n_days', 't_mean', 'rh', 'wind', 'utci', 'demand', 'utci_shade']
   96

Annual averages hide southern-summer deficits (Rio in January).
The charts below are drawn from these CSVs. Rebuild with
``python scripts/build_research_cases.py --case hris``.

Annual SHR
----------

.. figure:: /_static/research_cases/hris_annual_shr.png
   :alt: Annual streetscape heat resilience bars for eight cities
   :width: 100%

   Input: ``annual_climate_vata.csv``. Output: annual SHR bars.
   Singapore sits near the adequacy boundary; Rio is in deficit.
   This is an application of the Hong Kong JJA anchor, not a
   validation of TCIS.

Monthly heatmap
---------------

.. figure:: /_static/research_cases/hris_monthly_heatmap.png
   :alt: City-by-month SHR heatmap
   :width: 100%

   Input: ``monthly_climate_vata.csv``. Unit: SHR. Southern-summer
   deficits (Rio in January) are hidden by annual averages. Demand
   is an hourly climatological proxy.

Warming
-------

.. figure:: /_static/research_cases/hris_warming.png
   :alt: Annual SHR under present, plus 1.5 C, and plus 2.5 C
   :width: 100%

   Input: ``shr``, ``shr_plus15``, ``shr_plus25``. Supply is held
   fixed. Not a design code and not medical advice.

Robustness and domain shift
---------------------------

.. figure:: /_static/research_cases/hris_robustness.png
   :alt: Sign-stability table across calibration variants
   :width: 100%

   Input: ``robustness_sign_stability.csv``. Six cities stay in
   surplus across 18 variants. Singapore and Rio can flip sign.

.. figure:: /_static/research_cases/hris_domain_shift.png
   :alt: Fraction of images above the Singapore PCA envelope
   :width: 100%

   Input: ``domain_shift.csv``. Johannesburg and Cape Town sit
   farthest above the Singapore-trained feature envelope. This is a
   domain diagnostic, not a ranking of cities.

Interpretation
--------------

* High VATA means the TCIS model scored the photo as more thermally
  affording. It does not mean a person felt cooler.
* High UTCI means higher modelled heat stress at the city-centroid
  climatology. It does not score the photo.
* Positive SHR means city-mean VATA exceeds the Hong Kong JJA
  benchmark for that demand. Negative SHR is a supply shortfall
  relative to that benchmark, not a measured health outcome.

Limitations
-----------

* Summaries only; no per-image maps in this UrbanCode case.
* Hong Kong JJA anchor is normative.
* Open-sun SolarCal MRT is standardised, not local geometry.
* TCIS was trained on Singapore street-view photos.
* Not medical advice and not a design code.

Provenance and reproduction
---------------------------

The case writes ``provenance.json`` next to the figures. Receipts
include Singapore n, the TCIS 92,233 contrast, ``v_ref`` / ``d_ref``,
and cache ``hourly_v1``.

Related pages
-------------

* :doc:`thermal_comfort_in_sight`
* :doc:`/reference/recipes/climate/utci_real`
* :doc:`/concepts/image_observations`
