# Real dataset manifest

Every directory under `examples/data/real/` that contains analysis
inputs must include:

- `manifest.json`
- `LICENSE.md`
- `README.md`
- `checksums.sha256`

`manifest.json` must set `synthetic: false` and include:

- `dataset_id`
- `city_id`
- `place`
- `bbox` (west, south, east, north in the geographic CRS)
- `physical_extent` (metres, e.g. `{width: 2000, height: 2000}`)
- `geographic_crs`
- `metric_crs`
- `source`
- `source_uri`
- `license`
- `attribution`
- `acquired_at`
- `temporal_extent`
- `original_item_id`
- `processing_steps`
- `file_checksums`
- `generated_by`

Synthetic fixtures must live under `examples/data/contracts/` or
`tests/fixtures/synthetic/` and set `synthetic: true`. They must not
be used as real-city conclusions.
