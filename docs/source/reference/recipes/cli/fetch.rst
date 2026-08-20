uc fetch
========

Question
--------

Which OSM layers would ``uc fetch`` write for Punggol?

Expected output
---------------

.. figure:: /_static/recipes/cli/fetch.png
   :alt: Punggol streets, buildings, and parks as the uc fetch output contract
   :width: 100%

   Offline stand-in for ``uc fetch --place 'Punggol, Singapore'``.
   Live download is Tier 2.

Installation
------------

``pip install "urbancode[network]"``

Related pages
-------------

* API: :func:`urbancode.fetch.fetch`
* Domain: :doc:`/domains/vector`
* Script: ``examples/recipes/cli/fetch.py``
* Dataset: :doc:`/reference/datasets`
