Capability catalog
==================

Generated from ``docs/source/catalog/capabilities.yaml``.
Status is one of ``stable``, ``experimental``, ``adapter-only``,
or ``planned``. ``planned`` items are never public exports.
A ``blocked`` row is a public function that cannot yet ship a
redistributable real-data recipe.

Do not hand-edit the table. Run ``python scripts/build_capabilities.py``.

See :doc:`/reference/recipes/index` for the case pages.

.. list-table::
   :header-rows: 1
   :widths: 32 14 12 18 24

   * - Function
     - Status
     - Extra
     - Backend
     - Recipe
   * - ``uc.load``
     - stable
     - vector
     - geopandas
     - :doc:`/reference/recipes/core/city_roundtrip_punggol`
   * - ``uc.fetch``
     - stable
     - network
     - osmnx
     - :doc:`/reference/recipes/core/fetch_punggol`
   * - ``uc.StudyArea.from_bbox``
     - stable
     - vector
     - pyproj
     - :doc:`/reference/recipes/core/study_area_punggol`
   * - ``uc.network.fetch``
     - stable
     - network
     - osmnx
     - :doc:`/reference/recipes/network/fetch_punggol`
   * - ``uc.network.centrality``
     - stable
     - network
     - networkx
     - :doc:`/reference/recipes/network/centrality_punggol`
   * - ``uc.network.accessibility``
     - stable
     - network
     - networkx
     - :doc:`/reference/recipes/network/accessibility_punggol`
   * - ``uc.network.clustering``
     - experimental
     - network
     - networkx
     - :doc:`/reference/recipes/network/clustering_punggol`
   * - ``uc.network.local_efficiency``
     - experimental
     - network
     - networkx
     - :doc:`/reference/recipes/network/local_efficiency_punggol`
   * - ``uc.imagery.read``
     - stable
     - imagery
     - rasterio
     - :doc:`/reference/recipes/imagery/read_punggol`
   * - ``uc.imagery.fetch``
     - stable
     - imagery
     - pystac-client
     - :doc:`/reference/recipes/imagery/fetch_punggol`
   * - ``uc.imagery.ndvi``
     - stable
     - imagery
     - rasterio
     - :doc:`/reference/recipes/imagery/ndvi_punggol`
   * - ``uc.imagery.ndwi``
     - stable
     - imagery
     - rasterio
     - :doc:`/reference/recipes/imagery/ndwi_punggol`
   * - ``uc.imagery.ndbi``
     - stable
     - imagery
     - rasterio
     - :doc:`/reference/recipes/imagery/ndbi_punggol`
   * - ``uc.imagery.slope``
     - stable
     - imagery
     - rasterio
     - :doc:`/reference/recipes/imagery/slope_punggol`
   * - ``uc.imagery.aspect``
     - stable
     - imagery
     - rasterio
     - :doc:`/reference/recipes/imagery/aspect_punggol`
   * - ``uc.imagery.hillshade``
     - stable
     - imagery
     - rasterio
     - :doc:`/reference/recipes/imagery/hillshade_punggol`
   * - ``uc.imagery.zonal_stats``
     - stable
     - imagery
     - rasterio
     - :doc:`/reference/recipes/imagery/zonal_stats_punggol`
   * - ``uc.climate.utci``
     - experimental
     - climate
     - pythermalcomfort
     - :doc:`/reference/recipes/climate/utci_real`
   * - ``uc.streetview.filename``
     - stable
     - streetview
     - pandas
     - :doc:`/reference/recipes/streetview/filename_punggol`
   * - ``uc.streetview.color``
     - experimental
     - streetview
     - opencv
     - :doc:`/reference/recipes/streetview/color_punggol`
   * - ``uc.images.from_table``
     - stable
     - vector
     - geopandas
     - :doc:`/reference/recipes/images/from_table_punggol`
   * - ``uc.streetview.as_layer``
     - stable
     - vector
     - geopandas
     - :doc:`/reference/recipes/streetview/as_layer_punggol`
   * - ``uc.streetview.fetch``
     - experimental
     - download
     - zensvi
     - blocked: zensvi/Mapillary imagery cannot be redistributed in the docs fixture; live-only
   * - ``uc.streetview.segmentation``
     - experimental
     - streetview
     - torch
     - blocked: torch SegFormer weights and redistributable precomputed masks are not in the repo; live/heavy only
   * - ``uc.streetview.object_detection``
     - experimental
     - streetview
     - torch
     - blocked: torch detector weights and redistributable boxes are not in the repo; live/heavy only
   * - ``uc.streetview.scene_recognition``
     - experimental
     - streetview
     - torch
     - blocked: Places365 weights and redistributable scores are not in the repo; live/heavy only
   * - ``uc.streetview.comfort``
     - compatibility
     - streetview
     - torch
     - blocked: Deprecated DataFrame entry; use uc.perception.thermal_affordance. Live/heavy only.
   * - ``uc.perception.thermal_affordance``
     - experimental
     - perception
     - torch
     - :doc:`/reference/recipes/perception/thermal_affordance_punggol`
   * - ``uc.fusion.aggregate``
     - stable
     - vector
     - geopandas
     - :doc:`/reference/recipes/fusion/aggregate_punggol`
   * - ``uc.fusion.aggregate_many``
     - stable
     - vector
     - geopandas
     - :doc:`/reference/recipes/fusion/aggregate_many_punggol`
   * - ``uc.fusion.combine``
     - stable
     - vector
     - pandas
     - :doc:`/reference/recipes/fusion/combine_punggol`
   * - ``uc.units.grid``
     - stable
     - vector
     - geopandas
     - :doc:`/reference/recipes/units/grid_punggol`
   * - ``uc.units.hexgrid``
     - stable
     - vector
     - shapely
     - :doc:`/reference/recipes/units/hexgrid_punggol`
   * - ``uc.units.from_layer``
     - stable
     - vector
     - geopandas
     - :doc:`/reference/recipes/units/from_layer_punggol`
   * - ``uc.imagery.utci``
     - compatibility
     - climate
     - pythermalcomfort
     - —
   * - ``uc.imagery.slope_degrees``
     - compatibility
     - imagery
     - rasterio
     - —
   * - ``uc.imagery.aspect_degrees``
     - compatibility
     - imagery
     - rasterio
     - —
   * - ``uc.network.download_network``
     - legacy
     - network
     - osmnx
     - —
   * - ``uc.network.save_network``
     - legacy
     - network
     - osmnx
     - —
   * - ``uc.network.load_saved_network``
     - legacy
     - network
     - osmnx
     - —
   * - ``uc.network.graph_to_gdf``
     - compatibility
     - network
     - osmnx
     - —
   * - ``uc.network.graph_from_gdf``
     - compatibility
     - network
     - momepy
     - —
   * - ``uc.network.closeness_centrality_radius``
     - legacy
     - network
     - networkx
     - —
   * - ``uc.network.betweenness_centrality_radius``
     - legacy
     - network
     - networkx
     - —
   * - ``uc.network.reachability_radius``
     - legacy
     - network
     - networkx
     - —
   * - ``uc.network.local_efficiency_radius``
     - legacy
     - network
     - networkx
     - —
   * - ``uc.network.clustering_coefficient_radius``
     - legacy
     - network
     - networkx
     - —
   * - ``uc.network.calculate_accessibility_metrics``
     - legacy
     - network
     - networkx
     - —
   * - ``uc.IndicatorResult.save``
     - stable
     - vector
     - pandas
     - :doc:`/reference/recipes/fusion/combine_punggol`
   * - ``uc.IndicatorResult.load``
     - stable
     - vector
     - pandas
     - :doc:`/reference/recipes/fusion/combine_punggol`
   * - ``uc.IndicatorResult.plot``
     - stable
     - viz
     - matplotlib
     - :doc:`/reference/recipes/fusion/combine_punggol`
   * - ``uc.IndicatorResult.to_layer``
     - stable
     - vector
     - geopandas
     - :doc:`/reference/recipes/fusion/combine_punggol`
   * - ``uc.adapters.osmnx``
     - adapter-only
     - network
     - osmnx
     - interop ``adapters/osmnx``
   * - ``uc.adapters.zensvi``
     - adapter-only
     - download
     - zensvi
     - interop ``adapters/zensvi``

