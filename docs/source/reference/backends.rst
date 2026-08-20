Backends
========

``uc.backends.available``, ``info``, ``require``, ``status``, and
``explain`` report which extras are installed. Named functions load
their backend on first use. ``import urbancode`` does not import
GeoPandas, OSMnx, rasterio, or torch.

This is not ``uc.adapters`` (lazy re-exports) and not a package
catalog. For the four-tier ecosystem table see
:doc:`/reference/ecosystem`.

API: :doc:`/reference/api/backends`.
