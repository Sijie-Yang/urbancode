Street-view imagery (SVI)
=========================

Official public namespace: ``uc.svi``. Need ``urbancode[svi]``.
Download helpers also accept the ``download`` extra alias.
The implementation module remains a compatibility alias; see
:doc:`/migration/streetview-to-svi`.

.. autofunction:: urbancode.svi.fetch
.. autofunction:: urbancode.svi.filename
.. autofunction:: urbancode.svi.color
.. autofunction:: urbancode.svi.segmentation
.. autofunction:: urbancode.svi.object_detection
.. autofunction:: urbancode.svi.scene_recognition
.. autofunction:: urbancode.svi.comfort
.. autofunction:: urbancode.svi.as_layer

``comfort`` is deprecated. Prefer :func:`urbancode.perception.thermal_affordance`.
``as_layer`` wraps :func:`urbancode.images.from_table` with
``view_type="streetview"``.

See also
--------

* Domain: :doc:`/domains/streetview`
* Recipes: :doc:`/reference/recipes/streetview/index`
* Workflow: :doc:`/workflows/street_experience`
* Migration: :doc:`/migration/streetview-to-svi`
