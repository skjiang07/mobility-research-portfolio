# GeoAI-Act: stay detection and activity-purpose inference

**Status:** accepted full research paper, ACM GeoAI 2026. [Paper DOI](https://doi.org/10.1145/3849726.3856090). This is a selected code showcase, not a complete replication release.

## Research problem and contribution

Travel behavior analysis needs more than a stream of location points: it needs meaningful stops and activity context. This work combines sequence modeling for stay detection with structured spatial, temporal, and personal-history context for activity-purpose inference.

I carried out the hands-on research workflow end to end, including data preparation, model implementation, evaluation, spatial feature construction, experiments, visualization, and manuscript preparation. Coauthor credit remains with the paper; these extracts showcase my implementation.

## Code to review

| Source extract | What it demonstrates |
| --- | --- |
| [Sequence model](original/stay_model.py) | Per-user windows, variable-length batch padding and masks, positional encoding, a Transformer classifier, and masked cross-entropy |
| [Stay segments and evaluation](original/stay_segments.py) | Duration and sampling-gap rules, temporal intersection-over-union, and greedy one-to-one matching |
| [Purpose context](original/purpose_payload.py) | Structured context, constrained activity categories, missing-value handling, and separate training/inference messages |
| [Synthetic demonstration](demo/activity_demo.py) | Running the original segment and context functions on invented inputs |

The function and class bodies in `original/` are preserved from the research notebooks. Imports and module documentation were added. The demonstration and checks were added with coding-assistant support during portfolio preparation.

## Run

With Python 3.10 or newer, from this project directory:

```bash
python -m pip install -r requirements.txt
python demo/activity_demo.py
python -m unittest discover -s tests -v
```

The demonstration produces two artificial stay segments, interval matching scores, and a JSON context/message payload. It does not predict an activity purpose or call an external service. The separate model module requires `requirements-model.txt`; no trained weights, GPU, or API access is needed for the demonstration.

## Scope and limitations

The selected model defaults are historical notebook settings, not a claim about the accepted paper's final configuration. Full reproduction also requires authorized trajectories and labels, feature preprocessing, train/validation/test partitions, training and evaluation configurations, and trained artifacts. None of those data or weights are included here.

The segment functions expect valid timestamps, one consistent user-identifier type, and binary point labels. Supply an explicit empty schema when evaluating empty segment tables. Matching is greedy by IoU, rather than a globally optimal assignment. A stay interval's duration is the difference between its first and last observed point; data gaps and sampling frequency affect this measure. Activity-purpose labels and spatial context introduce further uncertainty.

## Provenance

- `MIT_Stay_algorithm-AllUsers.ipynb`: zero-based cells 47, 49, 50 (model), 84, 87, 88 (segments/evaluation).
- `Stay purpose infer - paper version 6.ipynb`: cells 16–17 (prompts and payload). The original rich-prompt selection is retained.

No personal trajectories, coordinates from research participants, user identifiers, API keys, notebook outputs, or publisher PDFs are distributed.
