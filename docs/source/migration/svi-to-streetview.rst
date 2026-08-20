``uc.svi`` → ``uc.streetview``
==============================

The official street-view namespace is ``uc.streetview``. ``uc.svi`` is a
deprecated identity shim: every public name is the same object.

::

   import urbancode as uc

   scores = uc.streetview.comfort("photo.jpg", mode="image")  # deprecated DataFrame
   predictions = uc.perception.thermal_affordance(images)  # Layer, preferred
   city = uc.streetview.fetch("Punggol, Singapore", source="kartaview")

Install extra: ``urbancode[streetview]`` (``svi`` and ``download`` remain
aliases). CLI: ``uc streetview comfort path/to.jpg`` (``uc svi comfort``
still works).

``uc.streetview.comfort()`` still returns a DataFrame and keeps the
``thermal_comfort`` column for one deprecation cycle. New code should
call ``uc.perception.thermal_affordance()``, which returns a Layer
whose canonical score is ``thermal_affordance`` (VATA). That score is
not measured personal comfort and not UTCI.

Do not import ``urbancode.svi.feature`` or ``urbancode.svi.perception``
in new code. Use ``urbancode.streetview.features`` and
``urbancode.perception``.
