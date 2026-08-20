Street view
===========

Urban question
--------------

How colourful is a licensed Punggol street photo, and how do
model scores become a point Layer on a grid?

Result first
------------

.. figure:: /_static/recipes/streetview/color_punggol.png
   :alt: Colorfulness of the licensed Punggol street photo
   :width: 100%

   OpenCV Colorfulness for the committed Commons photo. This is a
   pixel statistic, not a comfort score and not a neighbourhood
   census.

What you will learn
-------------------

* The official namespace is ``uc.streetview``.
  Perception scores now live in ``uc.perception``. Window-view
  photos are ``uc.images`` with ``view_type="windowview"``.
* The pipeline from catalog to Layer to units.
* Which steps are live, which are precomputed.
* Responsible-use limits.

Installation
------------

::

   pip install "urbancode[streetview]"

``color`` needs OpenCV. Model functions need torch. Live fetch
needs provider credentials and accepts the ``download`` extra alias.

UrbanCode API
-------------

* :func:`urbancode.streetview.fetch` — live-only; not redistributed
* :func:`urbancode.streetview.filename`
* :func:`urbancode.streetview.color`
* :func:`urbancode.streetview.segmentation`
* :func:`urbancode.streetview.object_detection`
* :func:`urbancode.streetview.scene_recognition`
* :func:`urbancode.streetview.comfort`
* :func:`urbancode.streetview.as_layer`

Use ``uc.streetview``. The compatibility alias is documented only
in :doc:`/migration/svi-to-streetview`.

Backend stack
-------------

.. list-table::
   :header-rows: 1
   :widths: 22 24 22 16 16

   * - Package
     - Responsibility
     - Called by UrbanCode
     - Direct use?
     - Status
   * - ZenSVI
     - Mapillary / KartaView / Amsterdam download
     - ``streetview.fetch``
     - Yes
     - integrated (live)
   * - streetlevel
     - unofficial Google path
     - ``source='google'``
     - Yes
     - experimental adapter
   * - Pillow / OpenCV
     - I/O and pixel stats
     - filename, color
     - Yes
     - integrated
   * - PyTorch / torchvision
     - model inference
     - segmentation, detection, comfort
     - Yes
     - integrated
   * - Places365
     - scene labels
     - scene_recognition
     - no
     - packaged labels
   * - TCIS
     - comfort scores
     - comfort
     - no
     - packaged weights

Pipeline
--------

Acquire → validate metadata → image features → segmentation →
detection → scene → comfort → geolocate → ``as_layer`` →
``fusion.aggregate``.

Each step should record input path, lon/lat, heading if known,
timestamp, provider, model name/version, and missingness.
``segmentation``, ``object_detection``, ``scene_recognition``, and
``comfort`` are experimental and **blocked for offline docs**: torch
weights and redistributable precomputed artifacts are not in this
repository. Run them live with ``urbancode[streetview]``. Do not
treat a placeholder PNG as a result.

.. figure:: /_static/recipes/streetview/filename_punggol.png
   :alt: Street-view catalog contact sheet
   :width: 100%

   ``filename`` lists files. It does not score perception.

.. figure:: /_static/recipes/streetview/as_layer_punggol.png
   :alt: Street-view points. Illustrative locations stay labelled.
   :width: 100%

   Only geotagged rows are observations. Illustrative coordinates
   stay ``location_quality="illustrative"``.

The four model functions have no offline result figure. See
:doc:`/reference/capabilities` for the blocked reason.

Responsible use
---------------

* Provider licenses forbid committing fetched Mapillary / Google
  frames in this repository.
* Faces and plates may appear in street photos; do not treat the
  fixture as a privacy-cleared survey.
* A handful of Commons photos is not geographic coverage.
* Capture dates are inconsistent.
* Models shift across cities and camera types.
* One photo does not represent a neighbourhood.

Reading the result
------------------

* Colorfulness follows saturation in that frame.
* Coverage maps after aggregation will be sparse. Missing is null.
* Combined street-experience maps remain illustrative samples.
  See :doc:`/workflows/street_experience`.

Limitations
-----------

* ``streetview.fetch`` is blocked for offline docs.
* Precomputed masks are not a substitute for re-running the model
  when weights change.
* Sampling bias is the dominant error, not the color formula.

Related pages
-------------

* Recipes: :doc:`/reference/recipes/streetview/filename_punggol`,
  :doc:`/reference/recipes/streetview/as_layer_punggol`
* Workflow: :doc:`/workflows/street_experience`
* API: :doc:`/reference/api/streetview`
* Migration: :doc:`/migration/svi-to-streetview`

Use UrbanCode when photo features must join a City grid.
Use ZenSVI or OpenCV directly when you are only downloading or
debugging one image.
