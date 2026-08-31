Thermal Comfort in Sight
========================

Urban question
--------------

Where do street photos look thermally affording, and how does that
compare with vegetation, built-up surface, and UTCI — without treating
those quantities as the same thing?

Original research and citation
------------------------------

Yang, Sijie, et al. 2024. *Thermal Comfort in Sight: Thermal Affordance
and its Visual Assessment for Sustainable Streetscape Design*.
`arXiv:2410.11887 <https://arxiv.org/abs/2410.11887>`__.
Code: `Thermal-Comfort-In-Sight <https://github.com/Sijie-Yang/Thermal-Comfort-In-Sight>`__.

The paper's method is IF → VPI → VATA. VATA is visual thermal
affordance. It is not measured personal thermal comfort and it is not
UTCI.

What UrbanCode owns
-------------------

Study area, image Layer, perception Layer, analysis units, indicator
table, fusion, maps, and provenance. Tutorial code stays on ``uc.*``.

What the upstream project owns
------------------------------

The TCIS architecture, trained weights, feature-stat file, and the
IF / VPI / VATA definitions. UrbanCode calls that backend; it does
not re-train the model.

Data and licensing
------------------

**Flagship store.** 92,233 real Singapore street-view JPEGs remain on
Alienware at ``D:\\svi_singapore_92233_resized_version``, with a copy
on ``ual-chark`` at ``/data/sijie/svi_data/svi_sg_92233``. UrbanCode
registers those directories as an external image store. Raw imagery
is not in Git and is not assumed redistributable.

Smoke stages 10 / 100 / 1000 ran on Alienware (RTX 3070 Ti Laptop).
The full 92,233 TCIS run finished on ``ual-chark`` (RTX 5090):
92,233 / 92,233 rows, 0 failed, 23.03 img/s, ~67 min. Git holds
receipts and the parquet SHA-256 under
``examples/data/research_cases/thermal_comfort_in_sight_singapore/``.
The parquet itself is not in Git. See the audit note in that folder.

This 92,233 survey set is not the Heat Resilience in Sight Singapore
panel (n = 21,772).

**Tiny fixture.** Eight geotagged Wikimedia Commons photos inside the
Punggol 2 km pocket (CC BY-SA 4.0) stay as an offline API smoke
contract. They are a ground-photo out-of-distribution demonstration,
not the flagship research result. Do not read them as a Punggol
census or a city-scale VATA map.

Photos for the fixture live in ``examples/data/real/streetview/``.
TCIS weights are not in the repository; full mode downloads them
to the user cache.

1. Load the pocket and the eight photos
---------------------------------------

The catalog JSON has three cities. Filter to Punggol so image IDs
stay unique.

::

   import pandas as pd
   import urbancode as uc

   catalog = pd.read_json("examples/data/real/streetview/catalog.json")
   punggol = catalog[catalog["city_id"] == "punggol"]
   print(len(punggol))

::

   8

::

   city = uc.load("examples/data/real/punggol", lazy=True)
   photos = uc.images.from_table(
       punggol,
       view_type="streetview",
       image_root="examples/data/real/streetview",
   )
   print(photos.kind, photos.metadata["n_images"])
   photos.plot()

::

   vector 8

``photos`` is an eight-row point ``Layer`` in EPSG:4326. The plot
shows its observation locations; it does not imply coverage between
those points. This is not a neighbourhood census.

2. Offline: read committed VATA scores
--------------------------------------

You do not need torch to inspect the fixture scores.

::

   scores = pd.read_csv(
       "examples/data/research_cases/thermal_comfort_in_sight/"
       "predictions.csv"
   )
   print(scores["thermal_affordance"].agg(["count", "mean", "min", "max"]).round(3))

::

   count    8.000
   mean     2.371
   min      1.783
   max      2.985

VATA is a 0–5 model score of visual thermal affordance. It is not
measured comfort and not UTCI.

3. Optional: run the model
--------------------------

::

   vata = uc.perception.thermal_affordance(photos)

``photos`` is the image/coordinate input layer. ``vata`` is a point
``Layer`` with model outputs such as ``thermal_affordance`` attached
to images that ran successfully. It is not a continuous comfort
surface; plot or aggregate it only after inspecting failures and
sample coverage.

Needs ``urbancode[svi]``. First full run downloads weights
into the user cache. ``mode=case`` in
``python scripts/build_research_cases.py --mode case`` reuses the
CSV above.

4. Fuse onto units and compare with NDVI
----------------------------------------

::

   units = uc.units.grid(city, cell_size=250)
   result = uc.fusion.aggregate(
       photos, units, stat="count", indicator="photo_count"
   )
   ndvi = uc.fusion.aggregate(
       uc.imagery.ndvi(city.layers["sentinel2"]),
       units, stat="mean", indicator="ndvi",
   )
   compared = uc.fusion.combine(units, result, ndvi)
   print(len(compared.records), result.to_pandas()["value"].notna().sum())
   compared.plot(indicator="photo_count")

::

   162 3

``compared`` has two records per unit, but only three
``photo_count`` cells contain observations. ``combine`` preserves
those nulls and the plot hatches them.

Empty cells stay hatched / null. Do not treat them as 0. The
figures below were drawn by a docs builder; copy the blocks above,
not that file.

Input inspection
----------------

.. figure:: /_static/research_cases/tcis_inputs.png
   :alt: Contact sheet of eight licensed Punggol street photos
   :width: 100%

   Input: eight Commons JPEGs. Output: contact sheet. Unit: image.
   These are the observations. They are not a neighbourhood sample
   frame. Do not read this sheet as “Punggol streets”.

.. figure:: /_static/research_cases/tcis_sampling_context.png
   :alt: Eight photo points on Punggol streets and buildings
   :width: 100%

   Input: image Layer from ``uc.images.from_table``. Output: point
   map with streets, buildings, water, boundary, scale, and locator.
   Spatial support: geotagged points. Empty areas have no photo.

Model output
------------

.. figure:: /_static/research_cases/tcis_image_features.png
   :alt: TCIS initial features on the eight photo points
   :width: 100%

   Input: TCIS initial features (IF). Output: point maps.
   Vegetation / sky / building shares are model features, not a
   field survey. Do not treat them as land-cover fractions for the
   whole cell.

.. figure:: /_static/research_cases/tcis_vpi.png
   :alt: Selected TCIS visual perception indicators
   :width: 100%

   Input: VPI heads. Output: point maps on a 0–5 score scale.
   ``visual_comfort`` is a VPI head, not VATA. These are not
   measured temperature, sun, humidity, or wind.

Spatial aggregation
-------------------

.. figure:: /_static/research_cases/tcis_thermal_affordance.png
   :alt: VATA on photo points and 250 m units with empty cells hatched
   :width: 100%

   Input: ``thermal_affordance`` Layer. Output: points plus mean on
   250 m units. Unit: score 0–5. Unobserved units are hatched, not
   drawn as 0. This is not a Singapore or Punggol VATA surface.

``uc.fusion.aggregate_many()`` writes VATA, perceived shading, and
perceived greenery into one ``IndicatorResult``.

Cross-domain comparison
-----------------------

.. figure:: /_static/research_cases/tcis_cross_domain.png
   :alt: VATA, UTCI, NDVI, and NDBI compared on the same units
   :width: 100%

   Input: VATA points, Sentinel-2 NDVI/NDBI, and UTCI from observed
   Open-Meteo weather plus a modelled MRT proxy. Output: four maps
   and two scatter plots. Scatter titles say correlation only.
   Do not read a slope as causation. Do not call the MRT proxy a
   measured spatial weather field.

Interpretation
--------------

* High VATA means the TCIS model scored the photo as more thermally
  affording. It does not mean a person felt cooler.
* High UTCI means higher modelled heat stress at that weather time
  and MRT proxy. It does not mean the photo looks stressful.
* The two can move together or apart. That is a comparison, not a
  validation of either quantity.

Limitations
-----------

* n = 8 licensed photos. Coverage is those points only.
* Commons geosearch is not a survey GPS.
* TCIS was trained on Singapore street-view photos in the Thermal
  Affordance Dataset, not on this Commons sample.
* UTCI here uses a documented NDVI/NDBI MRT proxy, not a measured
  mean radiant temperature field.
* Weather and Sentinel-2 dates differ.
* Not medical advice and not a design code.

Provenance and reproduction
---------------------------

The case writes ``indicator_result.csv`` and ``provenance.json``
next to the figures. Receipts include image checksums, TCIS model
id / revision / weight hashes when the model ran, UrbanCode
version, and the sample-size warning.

Related API recipes
-------------------

* :doc:`heat_resilience_in_sight`
* :doc:`/reference/recipes/images/from_table_punggol`
* :doc:`/reference/recipes/perception/thermal_affordance_punggol`
* :doc:`/reference/recipes/fusion/aggregate_many_punggol`
* :doc:`/reference/recipes/climate/utci_real`
* :doc:`/concepts/image_observations`
