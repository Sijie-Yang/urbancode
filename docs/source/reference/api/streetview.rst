Street view
===========

Official street-view namespace. Need ``urbancode[streetview]``.
Download helpers also accept the ``download`` extra alias. Compatibility
notes: :doc:`/migration/svi-to-streetview`.

.. autofunction:: urbancode.streetview.fetch
.. autofunction:: urbancode.streetview.filename
.. autofunction:: urbancode.streetview.color
.. autofunction:: urbancode.streetview.segmentation
.. autofunction:: urbancode.streetview.object_detection
.. autofunction:: urbancode.streetview.scene_recognition
.. autofunction:: urbancode.streetview.comfort
.. autofunction:: urbancode.streetview.as_layer

``comfort`` is deprecated. Prefer :func:`urbancode.perception.thermal_affordance`.
``as_layer`` wraps :func:`urbancode.images.from_table` with
``view_type="streetview"``.

See also
--------

* Domain: :doc:`/domains/streetview`
* Recipes: :doc:`/reference/recipes/streetview/index`
* Workflow: :doc:`/workflows/street_experience`
* Migration: :doc:`/migration/svi-to-streetview`
