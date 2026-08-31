Network
=======

Urban question
--------------

Which Punggol streets sit on many shortest paths, and how many other
nodes can you reach on foot?

Result first
------------

.. figure:: /_static/recipes/network/centrality_punggol.png
   :alt: Betweenness and closeness on the Punggol walk graph
   :width: 100%

   Betweenness and closeness on the committed OSM walk graph.
   High betweenness near the pocket edge is often a boundary effect.

What you will learn
-------------------

* The five public network functions and their units.
* What OSMnx and NetworkX each compute.
* How radius changes reachability.
* Why momepy morphology names are not UrbanCode APIs yet.

Installation
------------

::

   pip install "urbancode[network]"

This installs OSMnx, NetworkX, GeoPandas, and momepy. The example below
is offline because it reads the committed GraphML layer.

UrbanCode API
-------------

* :func:`urbancode.network.fetch`
* :func:`urbancode.network.centrality`
* :func:`urbancode.network.accessibility`
* :func:`urbancode.network.clustering` (experimental)
* :func:`urbancode.network.local_efficiency` (experimental)

Legacy ``*_radius`` helpers stay on the API page as compatibility.

::

   import urbancode as uc

   city = uc.load("examples/data/real/punggol", lazy=True)
   reach = uc.network.accessibility(
       city["streets"], radius=150, metric="reachability"
   )
   print(reach.kind, reach.data.number_of_nodes())
   reach.plot()

::

   graph 1425

``reach`` is a graph ``Layer``. Its 1,425 nodes carry a
``reachability`` count measured within 150 m of network length; the
plot remains node/edge support until ``uc.fusion.aggregate`` is called.

Backend stack
-------------

.. list-table::
   :header-rows: 1
   :widths: 20 24 20 18 18

   * - Package
     - Responsibility
     - Called by UrbanCode
     - Direct use needed?
     - Status
   * - OSMnx
     - OSM download, simplify, GraphML
     - ``network.fetch``
     - Yes, custom queries
     - integrated
   * - NetworkX
     - traversal, centrality
     - centrality, accessibility, clustering, efficiency
     - Yes
     - integrated
   * - momepy
     - ``gdf_to_nx`` on the legacy graph path
     - ``graph_from_gdf``
     - Yes, morphology
     - integrated (interchange only)
   * - GeoPandas / Shapely
     - node/edge frames
     - aggregate
     - Yes
     - integrated
   * - cityseer, Pandana, r5py
     - multi-scale / transit access
     - no
     - Yes
     - planned

Indicators
----------

A. Centrality (betweenness)
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Which segments lie on more shortest paths?
:func:`urbancode.network.centrality` with the betweenness metric.
Values are graph-theoretic, not traffic. ``normalized`` and
``radius`` follow NetworkX. The pocket boundary truncates paths.

Recipe: :doc:`/reference/recipes/network/centrality_punggol`.

B. Centrality (closeness)
~~~~~~~~~~~~~~~~~~~~~~~~~

Closeness is inverse farness, not betweenness. Disconnected
components are handled by the NetworkX definition used in the
function. Same figure as betweenness.

C. Accessibility (reachability)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. figure:: /_static/recipes/network/accessibility_punggol.png
   :alt: Network reachability at 150 m and 500 m
   :width: 100%

   Node count within a graph-length cutoff. Radius is metres of
   network length, not a door-to-door walk and not jobs access.

Recipe: :doc:`/reference/recipes/network/accessibility_punggol`.
Workflow: :doc:`/workflows/green_accessibility`.

D. Clustering
~~~~~~~~~~~~~

.. figure:: /_static/recipes/network/clustering_punggol.png
   :alt: Local clustering on the Punggol walk graph
   :width: 100%

   Watts–Strogatz local clustering. Degree-1 and degree-2 street
   nodes are often zero. This is not a social-network clustering
   story.

Recipe: :doc:`/reference/recipes/network/clustering_punggol`.

E. Local efficiency
~~~~~~~~~~~~~~~~~~~

.. figure:: /_static/recipes/network/local_efficiency_punggol.png
   :alt: Local efficiency on the Punggol walk graph
   :width: 100%

   Latora–Marchiori local efficiency: do neighbours stay connected
   if a node is removed? This is redundancy, not traffic speed.

Recipe: :doc:`/reference/recipes/network/local_efficiency_punggol`.

Sensitivity
-----------

The accessibility recipe shows 150 m and 500 m. Larger radii raise
node counts and flatten local contrast. Betweenness with a radius
is a different metric from unbounded betweenness.

Reading the result
------------------

* Internal grids show higher reachability than waterfront dead-ends.
* Edge betweenness is often the cut of the 2 km box.
* Clustering near 0 is normal on tree-like street nodes.

Limitations
-----------

* The committed graph is a clipped extract, not a live refresh.
* Metrics are not travel-time or public-transport access.
* momepy street-morphology functions are not wrapped.

Related pages
-------------

* Fetch recipe: :doc:`/reference/recipes/network/fetch_punggol`
* Workflows: :doc:`/workflows/green_accessibility`,
  :doc:`/workflows/multi_city_comparison`
* API: :doc:`/reference/api/network`
* Upstream: `OSMnx <https://osmnx.readthedocs.io/>`__,
  `NetworkX <https://networkx.org/>`__,
  `momepy <https://docs.momepy.org/>`__

Use UrbanCode when network scores must join imagery on the same
units.
Use OSMnx / NetworkX directly when you need a custom filter or
algorithm.
