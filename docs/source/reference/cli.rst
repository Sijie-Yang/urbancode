CLI
===

Real commands only. Each one calls a Python API.

::

   uc --version
   uc fetch --place "Punggol, Singapore" --layers streets,buildings,parks --out city
   uc network fetch --place "Punggol, Singapore" --out city
   uc imagery fetch --bbox west,south,east,north --out city
   uc svi comfort path/to.jpg --out comfort.csv

The first line prints ``urbancode <version>``. The three fetch commands
write a City directory and then report its layer count. The final
command writes a CSV with image-level TCIS scores; it does not create a
map until those rows have coordinates and are converted to a Layer.

Offline recipes plot committed fixtures instead of hitting the
network. See :doc:`/reference/recipes/cli/index`.

The comfort command needs ``urbancode[svi]``. Weights
download into the user cache, not the package tree.

A hidden ``streetview`` subcommand remains as an alias of ``svi``.
New scripts should call ``uc svi``.

There is no ``uc doctor`` command. Use
:func:`urbancode.backends.status`.
