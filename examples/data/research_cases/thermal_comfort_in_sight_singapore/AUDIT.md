# Singapore SVI audit (Alienware store, ual-chark inference)

Read-only SSH audit of host `Alienware` (`DESKTOP-TU6QISA`) for the JPEG
store, then a separate full TCIS run on host `ual-chark` (RTX 5090).
No files on Alienware were modified or deleted. No credentials appear here.

## Store used for TCIS

| Field | Value |
| --- | --- |
| SVI root (JPEGs) | `D:\svi_singapore_92233_resized_version` on Alienware |
| Server copy | `ual-chark:/data/sijie/svi_data/svi_sg_92233` |
| Image count | 92,233 JPEG files |
| Total size | 7,714,781,524 bytes (~7.71 GB) |
| Mean file size | ~82 KB |
| Sample resolution | 1024×512 (30/30 sampled) |
| Format | JPEG |
| Filename pattern | `{image_id}_{longitude}_{latitude}.jpg` |
| Machine-local roots | kept on Alienware and ual-chark; not copied into Git |

Chunked copies of the same files exist (`_1_20000` … `_80001_92233`) plus `_seg` folders. Those are duplicates / segmentation derivatives. Inference should use the single 92,233 root only.

## Catalog / metadata on disk

| Path | What it contains | Missing |
| --- | --- | --- |
| `D:\svi_singapore_92233_all_csv\combined_data.csv` | filename, lon, lat, Cityscapes-like class fractions | heading, pitch, FOV, date, provider, panorama id, license |
| `D:\svi_singapore_92233_all_csv\all_image_scores.csv` | the above plus Places365-like scene probs and pixel stats | VATA / TCIS outputs, provider, capture date |
| Image filenames | `image_id`, longitude, latitude | heading, pitch, FOV, date, provider, pano id |

## Fields requested by the research contract

| Field | Present? | Source |
| --- | --- | --- |
| image_id | yes | filename stem before first `_` |
| longitude / latitude | yes | filename and CSV |
| heading / pitch / FOV | no | not in catalog |
| capture date | no | not in catalog |
| provider | no | not recorded |
| panorama ID | no | not recorded |
| original relative path | yes | filename in the resized root |
| license / redistribution | no | no LICENSE next to the images |

Do not invent provider, heading, or capture dates. Accessibility of the files on Alienware is not permission to redistribute them.

## Other Singapore photo stores (not this dataset)

| Path | Count | Size / resolution | Notes |
| --- | --- | --- | --- |
| `D:\svi_data\svi_sg` | 21,839 | ~6.96 GB, 2048×1024, pano-id names | Different 2024-06 set with `pid,lat,lng,heading,date`. Heat Resilience in Sight uses a 21,772-row panel from this family, not the 92,233 TCIS survey set. |
| `E:\GSV_dataset\Singapore` | 0 | empty | Not a backup of 92,233 |
| Full-resolution 92,233 originals | not found | — | D:, E:, and recycle bin had no original-size copy of the same filenames |

## Local models / environment

UrbanCode pins TCIS weights to Hugging Face revision `96dcfe0229542c280536dfb1994e4a4834d83c93`. SegFormer is pinned to `21b3847fae21ddee674abd31129307b6a1235bd9` with a matching Cityscapes processor. Places365 and Faster R-CNN hashes/enums are in `urbancode/streetview/data/`.

## Catalog built on Alienware

`examples/live/build_singapore_svi_catalog.py` registered the resized store.

| Field | Value |
| --- | --- |
| n_images | 92,233 |
| n_geolocated | 92,233 |
| parse errors | 0 |
| catalog_sha256 | `53ba69261b70d580c39a8cf24a33b640e8a3a6df3a3eb8412c5a309c9d3ba888` |
| heading / provider / date / pano id | still absent; not invented |

A second catalog built on ual-chark from the server JPEG copy has sha256 `05291ba0e8122f4ac7a9dfeed25d073528bb0672268fc6a8670079a886f0a6d8`. Git keeps the Alienware catalog checksum.

## Staged GPU runs (Alienware RTX 3070 Ti Laptop)

Smoke stages only. The laptop did **not** run the 92,233 job.

| Stage | Result | Notes |
| --- | --- | --- |
| 10 | passed, 0 failed | cold start ~0.14 img/s, 1.5 GB peak |
| 100 | passed, 0 failed | GPU inferred; receipt merged after a parquet geometry fix |
| 1000 | passed, 0 failed | 1.385 img/s, 722 s, ETA ~18.5 h for 92,233 |

Pinned revisions used: TCIS `96dcfe0229542c280536dfb1994e4a4834d83c93`, SegFormer `21b3847fae21ddee674abd31129307b6a1235bd9`.

## Full 92,233 run (ual-chark RTX 5090)

| Field | Value |
| --- | --- |
| Host | `ual-chark` |
| GPU | NVIDIA GeForce RTX 5090 (32 GB) |
| Success / failed | 92,233 / 0 |
| Rate | 23.03 img/s |
| Elapsed | 4004.871 s (~67 min) |
| Peak GPU memory | 3704.2 MB |
| Finished (UTC) | 2026-08-17T16:47:01 |
| Parquet | `/data/sijie/svi_data/tcis/svi_sg_92233/predictions.parquet` (47,940,801 bytes) |
| predictions_sha256 | `7a2cb62b7a680b3ac8638189f585cd8f6df7bba837c60d84db56fdd27ab14b86` |
| UrbanCode at run | 0.3.0.dev0 |

Git holds `predictions_receipt.json`, `predictions_run.json`, and `predictions_checksum.json`. The parquet and JPEGs stay off Git.

## License judgement

Raw 92,233 JPEGs stay on Alienware (and the ual-chark copy). Git receives only derived tables, manifests, checksums, and any thumbnails that are separately confirmed as redistributable. Manifests must say `raw imagery unavailable`. Do not describe the photos as redistributable.
