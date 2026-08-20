Network
=======

Need ``urbancode[network]``. Prefer :func:`urbancode.network.fetch` for new
code. Layer names: :doc:`/concepts/study_area_city_layer`.

.. autofunction:: urbancode.network.fetch
.. autofunction:: urbancode.network.centrality
.. autofunction:: urbancode.network.accessibility
.. autofunction:: urbancode.network.clustering
.. autofunction:: urbancode.network.local_efficiency

Advanced / compatibility
------------------------

.. autofunction:: urbancode.network.download_network
.. autofunction:: urbancode.network.save_network
.. autofunction:: urbancode.network.load_saved_network
.. autofunction:: urbancode.network.graph_to_gdf
.. autofunction:: urbancode.network.graph_from_gdf
.. autofunction:: urbancode.network.closeness_centrality_radius
.. autofunction:: urbancode.network.betweenness_centrality_radius
.. autofunction:: urbancode.network.reachability_radius
.. autofunction:: urbancode.network.local_efficiency_radius
.. autofunction:: urbancode.network.clustering_coefficient_radius
.. autofunction:: urbancode.network.calculate_accessibility_metrics

See also
--------

* Domain: :doc:`/domains/network`
* Recipes: :doc:`/reference/recipes/network/index`
* Workflow: :doc:`/workflows/green_accessibility`
