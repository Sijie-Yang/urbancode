``uc.streetview`` → ``uc.svi``
==============================

The official street-view namespace is ``uc.svi``. ``uc.streetview`` is a
compatibility alias: every public name is the same object.

::

   import urbancode as uc

   catalog = uc.svi.filename("examples/data/real/streetview/punggol")
   scores = uc.svi.comfort("photo.jpg", mode="image")  # deprecated DataFrame
   predictions = uc.perception.thermal_affordance(images)  # Layer, preferred
   city = uc.svi.fetch("Punggol, Singapore", source="kartaview")

Install extra: ``urbancode[svi]`` (``streetview`` and ``download`` remain
aliases). CLI: ``uc svi comfort path/to.jpg`` (``uc streetview comfort``
still works as a hidden alias).

``uc.svi.comfort()`` still returns a DataFrame and keeps the
``thermal_comfort`` column for one deprecation cycle. New code should
call ``uc.perception.thermal_affordance()``, which returns a Layer
whose canonical score is ``thermal_affordance`` (VATA). That score is
not measured personal comfort and not UTCI.

Do not import ``urbancode.svi.feature`` or ``urbancode.svi.perception``
in new code. Use ``urbancode.streetview.features`` and
``urbancode.perception``.
