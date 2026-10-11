# Source provenance

All notebook cell indices below are zero-based. Original function/class bodies are preserved unless an adaptation is explicitly described. Research data, execution state and saved outputs are omitted.

| Project | Original sources | Treatment |
| --- | --- | --- |
| GTFS | `Travel Time Cal - V2-For use.ipynb`; `SpaceMeanSpeed.ipynb` | Curated cells with explicit input/output path adapters and source references; historical parameter settings retained |
| Hurricane Ian | `Revise_TTR.ipynb`, cell 17; `Model_data_prepare.ipynb`, cell 26 | PTI and rainfall helper bodies preserved; imports explicit; no downstream exploratory transformations |
| Mobility bias | `SR_RR_Bias.ipynb`; `Representativenss metric.ipynb` | Selected sampling and spatial metric bodies preserved; imports explicit |
| GeoAI | `MIT_Stay_algorithm-AllUsers.ipynb`, cells 47/49/50/84/87/88; `Stay purpose infer - paper version 6.ipynb`, cells 16/17 | Dataset, model, loss, segmentation, evaluation, prompts and payload bodies preserved; imports explicit |
| Wildfire | `1_Population (paper).ipynb`, cells 19/23/37; `2_Movement (paper).ipynb`, cell 109 | Population imputation/metrics, demographic overlay and OD geometry function bodies preserved; imports explicit; example inputs invented |

The synthetic demonstration scripts, their tests, repository documentation, and automation scripts were added during portfolio preparation with coding-assistant support. They make methods accessible but are not evidence that those new scripts produced the published results.

The wildfire `evacuation_metrics_demo.py` was prepared separately from the published article, Sections 3.1–3.3 and Equations 1–5. The `original_source_example.py` illustration calls the preserved notebook functions on invented inputs. The selected notebooks establish the provenance of these excerpts; they are not represented as a verified snapshot of the complete final study workflow.

The project author reports carrying out the hands-on research workflow end to end. Coauthors retain the credits recorded in the papers. Publications and original source files remain the authority for the studies' methods and findings.
