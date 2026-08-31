Extras
======

Install extras are defined in ``pyproject.toml``. The teaching table
is :doc:`/getting_started/installation`.

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Extra
     - What it unlocks
   * - ``vector``
     - GeoPandas, Shapely, City I/O, :doc:`/domains/units`, :doc:`/domains/fusion`
   * - ``network``
     - OSMnx, NetworkX, :doc:`/domains/network`
   * - ``imagery``
     - rasterio, STAC, :doc:`/domains/imagery`
   * - ``climate``
     - :func:`urbancode.climate.utci`
   * - ``svi``
     - :doc:`/domains/streetview`
   * - ``perception``
     - :func:`urbancode.perception.thermal_affordance`
   * - ``research``
     - Research-case extras (perception + svi + climate + viz)
   * - ``spatial-stats``
     - Phase 2 dependency group; no public stats API yet
   * - ``viz``
     - matplotlib
   * - ``standard``
     - vector + network + imagery + climate + viz
   * - ``all``
     - standard + svi + perception + survey + graph
   * - ``docs``
     - Sphinx
   * - ``dev``
     - pytest and linters

``streetview`` and ``download`` remain install aliases of ``svi``.
``gallery`` is an alias of ``viz``. Torch is not in ``standard``.

There is no ``uc doctor`` command. Use
:func:`urbancode.backends.status`.
