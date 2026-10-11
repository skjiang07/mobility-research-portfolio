# Wildfire evacuation: Palisades and Eaton fires

**Published research:** Shangkun Jiang et al. (2026), *Wildfire evacuation analysis using facebook data: Evidence from Palisades and Eaton fires*, Transportation Research Part D, 158, 105456. [Read the article](https://doi.org/10.1016/j.trd.2026.105456).

## Research problem

Emergency planners need to understand how population displacement, departure patterns, and destinations vary across fire-affected communities. This study develops an integrated framework using Facebook population and movement aggregates during the 2025 Palisades and Eaton fires, combines structural damage with displacement, and cross-checks selected patterns with an independent GPS dataset.

## My contribution

I carried out the hands-on work end to end: data collection and preparation, geospatial processing, methodology implementation, software, analysis, validation, visualization, and manuscript preparation. The published paper retains its coauthor credits. Its contribution statement specifically credits me with software, methodology, data curation, formal analysis, validation, visualization, investigation, conceptualization, and writing.

## Runnable methods demonstration

[The synthetic demonstration](demo/evacuation_metrics_demo.py) implements selected published equations using small invented tile-time and OD tables. It is a newly prepared example for this portfolio, not the original research notebook or a reproduction of the article's results.

| Component | Method shown |
| --- | --- |
| Population displacement | `P = (crisis - baseline) / baseline`; `E = max(-P, 0)` |
| Departure curve | `F = max(baseline - crisis, 0)`; `C(t) = 100 * cumulative_sum(F) / total_sum(F)` within each tile |
| Damage-Evacuation Disparity Index | `DEDI = max(0, D - E) / (1 - D)`, with `0 <= D < 1` |
| Evacuation-related OD selection | Origin in an evacuation/warning zone; destination outside the zone or in another zone farther from the fire |

Population deficits can include the same absent population in successive time slices. The cumulative curve follows the article's aggregate metric; it is not a cumulative count of distinct people departing. DEDI identifies an aggregate damage-response mismatch and does not establish voluntary noncompliance or individual behavior. Geometry-based zone membership and distance from the fire are provided as prepared inputs in this small example.

## Run

From this project directory with Python 3.10 or newer:

```bash
python -m pip install -r requirements.txt
python demo/evacuation_metrics_demo.py
python -m unittest discover -s tests -v
```

The demonstration reads no external files, performs no downloads, and uses no real Facebook or GPS observations. All counts, locations, zone labels, and dates are invented. It rejects missing/invalid counts and duplicate tile-time keys instead of silently imputing them. Undefined cumulative departure shares and zero-baseline OD changes remain missing.

## Data and full-study requirements

The published article states that the authors do not have permission to share the data. No Facebook population or movement records, GPS observations, derived restricted tables, or publisher PDF are distributed here. Reproducing the study requires authorized data access, preprocessing and privacy-suppression handling, evacuation-zone/time layers, fire perimeters, CAL FIRE structural damage data, land-use inputs, and the complete original analysis workflow.

The research uses approximately 2.4 km grid cells and 8-hour temporal intervals. Suppression, noise, spatial smoothing, missing data, platform selection, geographic aggregation, and destination land-use approximation affect interpretation. Population decline is an evacuation-related proxy; it does not identify every resident's decision. These limitations are central to using the metrics for planning.

## Provenance

The example was prepared from the published methodology, specifically Sections 3.1–3.3 and Eqs. (1)–(5), with coding-assistant support. The paper's full coauthor list and source are available through the DOI above. This portable example demonstrates selected methods and does not claim to recreate the original code or published outputs.
