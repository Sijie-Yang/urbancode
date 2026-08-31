uc svi comfort
=====================

Question
--------

How do you run TCIS comfort from the CLI?

This command is **live/heavy**. Torch weights are not redistributed
in the docs fixture, so there is no offline result figure.

Installation
------------

``pip install "urbancode[svi]"``

Command
-------

::

   uc svi comfort path/to.jpg --out comfort.csv

``path/to.jpg`` is one input image and ``comfort.csv`` is the output
table. A successful run writes one row of TCIS scores; the command may
download model weights on first use. No scores are shown here because
the repository does not contain a redistributable offline model run.

Related pages
-------------

* API: :func:`urbancode.svi.comfort`
* Domain: :doc:`/domains/streetview`
* Catalog: :doc:`/reference/capabilities`
