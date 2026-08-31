Recipes
=======

One runnable case per public command. Scripts live in
``examples/recipes/``. Pages stay under Reference; this is not a sixth
user path.

The index is generated from ``docs/source/catalog/capabilities.yaml``.
Each page follows the same template: urban question, result figure,
installation, input contract, code, output contract, interpretation,
parameters, failure modes, backends, and related Domain / API /
Workflow / Dataset links.

Blocked catalog rows (live-only or non-redistributable sources) are
listed in :doc:`/reference/capabilities` and do not get a fake case.

.. toctree::
   :maxdepth: 2

   core/index
   units/index
   network/index
   imagery/index
   climate/index
   streetview/index
   images/index
   perception/index
   fusion/index
   cli/index
