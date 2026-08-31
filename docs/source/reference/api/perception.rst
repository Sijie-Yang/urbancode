Perception
==========

Human-perception scores from city photos. Street view and window view
are both valid inputs. Importing this module does not import torch.
Need ``urbancode[perception]`` to run a model.

.. autofunction:: urbancode.perception.thermal_affordance

``thermal_affordance`` is VATA: visual thermal affordance from the
TCIS model. It is not measured personal thermal comfort and it is not
UTCI. ``uc.svi.comfort()`` remains as a deprecated DataFrame
entry and keeps ``thermal_comfort`` as a one-cycle alias.

See also
--------

* Recipe: :doc:`/reference/recipes/perception/thermal_affordance_punggol`
* Research case: :doc:`/workflows/research_cases/thermal_comfort_in_sight`
* Migration: :doc:`/migration/streetview-to-svi`
