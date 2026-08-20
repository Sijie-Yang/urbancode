CLI
===

Real commands only. Each one calls a Python API.

::

   uc --version
   uc fetch --place "Punggol, Singapore" --layers streets,buildings,parks --out city
   uc network fetch --place "Punggol, Singapore" --out city
   uc imagery fetch --bbox west,south,east,north --out city
   uc streetview comfort path/to.jpg --out comfort.csv

Offline recipes plot committed fixtures instead of hitting the
network. See :doc:`/reference/recipes/cli/index`.

The comfort command needs ``urbancode[streetview]``. Weights
download into the user cache, not the package tree.

A deprecated ``svi`` subcommand still exists as a hidden alias of
``streetview``. New scripts should call ``uc streetview``.

There is no ``uc doctor`` command. Use
:func:`urbancode.backends.status`.
