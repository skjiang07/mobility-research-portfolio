# Mobility research portfolio — Shangkun Jiang

I develop data-driven methods for transportation monitoring, evacuation analysis, mobility-data quality, and travel behavior inference. This portfolio connects five research projects to selected implementation examples and small runnable demonstrations.

I carried out the hands-on work in these projects end to end, including data preparation, methodology and software development, analysis, validation, visualization, and manuscript preparation. Publications retain their coauthor credits. Each project explains my contribution, its code provenance, and the limits of the public sample.

## Explore the projects

| Project | Research status | Implementation to review |
| --- | --- | --- |
| [GTFS traffic monitoring](projects/gtfs-traffic-monitoring/) | Transportation Research Record, 2025 | Original GIS/travel-time notebooks; synthetic corridor demo |
| [Hurricane Ian traffic impacts](projects/hurricane-ian-traffic/) | International Journal of Disaster Risk Reduction, 2026 | Original metric helpers; synthetic regression discontinuity example |
| [Wildfire evacuation](projects/wildfire-evacuation/) | Transportation Research Part D, 2026 | Published-methods explanation and synthetic evacuation metrics |
| [Mobility-data representativeness](projects/mobility-data-bias/) | Submitted manuscript | Original sampling/spatial functions; synthetic bias assessment |
| [GeoAI activity inference](projects/geoai-activity-inference/) | Accepted full research paper, ACM GeoAI 2026 | Original Transformer, segment evaluation and context functions; synthetic demo |

Start with **GTFS traffic monitoring** for spatial processing and transportation measurement. **Hurricane Ian** illustrates statistical model specification and uncertainty. The other projects show disaster decision support, data-quality assessment, and machine learning implementation.

## Run all five demonstrations

With Python 3.10 or newer, from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/run_demos.py
python scripts/verify_portfolio.py
python scripts/run_checks.py
```

All demonstration inputs are invented. No external datasets, credentials, GPU, or paid services are required. Original GIS and Transformer modules have separate optional dependencies listed within their projects. They are source samples rather than complete runnable study pipelines.

## Reading this repository

**Original excerpts** preserve selected research function bodies or notebook cells, with documented import/path adaptations. **Synthetic demonstrations** were newly prepared with coding-assistant support to make selected methods easy to inspect and run. They are not the original study implementations or empirical findings. Tests check selected behavior and edge cases, not the validity of the papers' conclusions.

Published papers are linked through their DOIs. Restricted mobility data, real device identifiers, participant trajectories, saved notebook outputs, and publisher PDFs are excluded. This repository does not promise reproduction of published numerical results. See [data and reproducibility notes](docs/DATA_AND_REPRODUCIBILITY.md) and [source provenance](docs/PROVENANCE.md).

For background and publications, see [my personal website](https://skjiang07.github.io/).
