# Data and reproducibility

This release is a research portfolio of selected source excerpts and synthetic examples. It is not a full replication package for any paper.

| Project | Inputs required for full empirical reproduction | Public sample |
| --- | --- | --- |
| GTFS | Historical transit feeds, road/stops/intersection geometry, independent comparison observations and configuration | Curated notebook cells and an artificial straight-corridor demo |
| Hurricane Ian | Authorized mobility data, detector observations, segment geometry, weather and final modeling configuration | Original metric helpers and a new synthetic model illustration |
| Wildfire | Authorized Facebook population/movement aggregates, GPS data and disaster/land-use layers | Original population and spatial functions exercised on invented tables, plus a separate published-metrics example |
| Mobility bias | Authorized provider records, residence inference, Census and residential geography | Original metric functions and artificial counts/point patterns |
| GeoAI | Authorized trajectories/labels, preprocessing, split definitions, training settings and model artifacts | Original model/evaluation/context functions and invented segment inputs |

The wildfire article states that the authors do not have permission to share the data. Other providers' access and redistribution terms must also be satisfied independently of this repository. No record-level provider data or intermediate research datasets are distributed. Original research figures and labeled author manuscripts present aggregate findings, with their sources recorded in the asset inventory.

Original excerpts retain historical behavior and may require additional validation for new applications. Specific configuration differences and assumptions are documented in project READMEs. The synthetic examples use small datasets and simplified geometry; their outputs are not research findings. Successful unit checks demonstrate only the behaviors they test.

The portable examples require Python, NumPy, pandas, and statsmodels. Optional original spatial and Transformer modules require additional libraries. No trained weights, API access, provider authentication or research-file downloads are used by the demonstrations.

No software license is assigned in this initial showcase. Viewing public source does not grant a general reuse license. Paper copyrights and data-provider rights remain separate.

## Research figures and manuscripts

The project pages display original method diagrams and empirical result figures from the author's research files. These images are separate from the newly prepared synthetic code examples. Published studies use DOI links rather than distributing publisher PDFs. The mobility-bias project includes an unpublished author manuscript compiled from the latest supplied scientific source, with template author metadata restored from the same-title August 2026 source manuscript. GeoAI-Act includes the accepted author manuscript while the publisher record for its assigned DOI is pending.

The [asset inventory](research_assets.json) lists every public figure and manuscript with a content hash and source description. It supports source tracking, not empirical replication of the studies.
