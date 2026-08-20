ADR-007: Scenario and memory policy
===================================

Status
   Accepted as policy. No scenario directory exists in City v1.

Context
-------

StreetRAG distinguishes baseline from scenario and keeps
SpatialMemory (“why we called”). If a session wrote over the
baseline City, the next session would lose the factual extract.

Decision
--------

* **UrbanCode owns** baseline vs scenario **data** on disk
  (``observations/baseline/`` vs ``observations/scenarios/<id>/``
  in the v3 draft).
* **StreetRAG owns** session memory and the rationale for a call.
* A session **never overwrites** the baseline. Scenarios are
  additive.

Consequences
------------

``city.save`` today still writes a single v1 City. Future export
must copy baseline layers and write scenario observations beside
them, not replace them. StreetRAG memory files are out of
UrbanCode.

Out of scope this week
----------------------

No scenario writer, no SpatialMemory schema in this repo, no
Punggol end-to-end GAC demo.
