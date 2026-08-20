ADR-004: IndicatorResult ≡ Observation
======================================

Status
   Mapping only. No Pydantic models in this repository.

Context
-------

UrbanCode named functions return Layers. StreetRAG stores
Observations (metric on an entity, with method, time, and
provenance). If the two shapes diverge, StreetRAG will invent a
second indicator formula or drop provenance.

Decision
--------

A future UrbanCode ``IndicatorResult`` **is** the StreetRAG
``Observation`` core. Same fields, same meaning. UrbanCode
**computes** them; StreetRAG **stores and retrieves** them.

Required core fields (draft):

* ``observation_id``, ``city_id``
* ``entity_level``, ``entity_id``
* ``metric_key``, ``value``, ``unit``
* ``measurement_scale``, ``direction``
* ``spatial_support``
* ``temporal.valid_from``, ``temporal.valid_to``
* ``scenario_id``
* ``method``, ``parameters``
* ``coverage``, ``uncertainty``, ``quality_flags``
* ``provenance_id``, ``artifact_ref``

Rules: missing value is not 0. A percentile does not replace the
raw value. Full table: :doc:`urban-package-v3`.

Consequences
------------

StreetRAG must not recompute NDVI, UTCI, or park access with a
private formula once the kernel exists. This round does not add
types or change Layer return values.

Out of scope this week
----------------------

No ``IndicatorResult`` class, no Observation writer, no copy of
StreetRAG models into ``urbancode/``.
