Architecture
============

UrbanCode is a façade. Named functions call one upstream library and
return a ``Layer``. Fusion writes ``IndicatorResult`` rows. The on-disk
City schema stays at version 1.

::

   StudyArea → City / Layer → AnalysisUnits
        → named function → Layer
        → fusion.aggregate / combine
        → IndicatorResult → plot / save / provenance

StreetRAG is a future downstream consumer.

The living extras table is :doc:`/reference/extras`.
