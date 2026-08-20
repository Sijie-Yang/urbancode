City Landscape in Sight (Phase 2)
=================================

This page is a design contract. UrbanCode does not export the APIs
below in this release. Do not treat the names as installed functions.

Urban question
--------------

How do window views score on six human-perception dimensions, and
how do those scores vary by floor and neighbourhood?

Original research and citation
------------------------------

Yang, Sijie, et al. 2026. *City Landscape in Sight*.
`arXiv:2606.15198 <https://arxiv.org/abs/2606.15198>`__.
Code: `City-Landscape-In-Sight <https://github.com/Sijie-Yang/City-Landscape-In-Sight>`__.
Processed imagery and weights:
`sijiey/City-Landscape-In-Sight <https://huggingface.co/datasets/sijiey/City-Landscape-In-Sight>`__.

The project has 12,334 Wuhan window views, 499 survey samples, and
six perception dimensions. Raw property-platform images must not be
redistributed. Only processed imagery, derived tables, trained
weights, and clearly licensed tiny fixtures may enter UrbanCode.

What UrbanCode will own
-----------------------

Orchestration on the same objects as Thermal Comfort in Sight:
image Layer, perception Layer, analysis units, indicator table,
fusion, maps, and provenance.

What the upstream project owns
------------------------------

Window-view model weights, pairwise survey design, TrueSkill
ratings, and the six-dimension definitions.

Phase 2 API names
-----------------

These names are planned. They are not public exports.

.. list-table::
   :header-rows: 1
   :widths: 40 60

   * - Planned name
     - Role
   * - ``images.from_table(..., view_type="windowview")``
     - Already valid on the images contract. No extra API.
   * - ``perception.window_view``
     - Six-dimension inference from a window-view Layer.
   * - ``survey.rank_pairwise``
     - Pairwise ranks; TrueSkill stays in a backend.
   * - ``units.h3``
     - Nested H3 cells with globally stable IDs.
   * - spatial-block CV groups
     - A grouping contract for spatial cross-validation.
   * - ``stats.local_moran``
     - Local Moran's I on an IndicatorResult.
   * - ``stats.hotspots``
     - Hotspot classification on an IndicatorResult.

Formal dimensions: ``prefer``, ``monotonous``, ``quiet``,
``extensive``, ``vivid``, ``oppressive``.

Backends planned for that extra set: h3-py, libpysal, esda, Torch,
scikit-learn, TrueSkill. They will not sit in the core extra.

Intended pipeline
-----------------

pairwise survey → TrueSkill → image and structural features → H3
sampling → spatial CV → six-dimension inference → H3 aggregation →
autocorrelation / hotspots → floor-level analysis → design-support
map.

Data and licensing
------------------

Do not commit original property-platform photographs. Phase 2 may
use the project's processed imagery, derived tables, trained
weights, and a tiny licensed fixture only.

Why this waits
--------------

Thermal Comfort in Sight already has a weights contract and a
perception entry. City Landscape still needs H3, TrueSkill, and
spatial-stats contracts. Implementing those without a finished
first case would add empty shells.

Related pages
-------------

* :doc:`thermal_comfort_in_sight`
* :doc:`/concepts/image_observations`
* :doc:`/development/roadmap`
