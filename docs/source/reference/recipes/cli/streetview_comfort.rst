uc streetview comfort
=====================

Question
--------

How do you run TCIS comfort from the CLI?

This command is **live/heavy**. Torch weights are not redistributed
in the docs fixture, so there is no offline result figure.

Installation
------------

``pip install "urbancode[streetview]"``

Command
-------

::

   uc streetview comfort path/to.jpg --out comfort.csv

Related pages
-------------

* API: :func:`urbancode.streetview.comfort`
* Domain: :doc:`/domains/streetview`
* Catalog: :doc:`/reference/capabilities`
