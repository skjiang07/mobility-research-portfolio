# Spatial representativeness of mobility data

**Status:** submitted manuscript; this portfolio page is a methods and code showcase. It does not claim a published article or a full replication package.

## Research problem

A large mobility sample can still misrepresent where people live. This work assesses two dimensions: whether sample counts track population **between geographic areas**, and whether inferred residences resemble residential geography **within an area**. The research compares mobility datasets in Florida and California at county, census tract, and census block group scales.

## My contribution

I carried out the hands-on work end to end: data preparation, residence inference, geospatial processing, metric development, statistical and spatial analysis, validation, visualization, and manuscript preparation. The manuscript retains its coauthor credits; these samples focus on my implementation.

## Code to review

| File | What it demonstrates |
| --- | --- |
| [Original sampling functions](original/sampling_representation.py) | Sampling rates and population-normalized relative representation |
| [Original spatial functions](original/spatial_representativeness.py) | Average k-nearest-neighbor distances, area-weighted residential sampling, and Monte Carlo comparison |
| [Runnable synthetic demonstration](demo/representation_demo.py) | Small, deterministic examples of both dimensions, without restricted data |

The first two files contain selected function bodies from the original notebooks. The demonstration is a new, simplified example prepared for this portfolio and is clearly separated from the research code.

## Core methods

- Sampling rate: `SR_i = sample_i / population_i`.
- Relative representation: `RR_i = (sample_i / total_sample) / (population_i / total_population)`. `RR = 1` indicates proportional coverage; values above or below 1 indicate overrepresentation or underrepresentation.
- Within-area score: `M_i = exp(-abs(r_i / h_i - 1))`, where `r_i` is the observed average k-nearest-neighbor distance and `h_i` is its simulated residential reference. Scores are averaged over reference draws. `M = 1` indicates matching distance scales, which does not prove demographic representativeness.
- The wider analysis examines spatial scale, sampling intensity, sociodemographic associations, and residual spatial dependence. The selected functions illustrate the metric layer rather than the complete modeling workflow.

## Run the demonstration

From this project directory with Python 3.10 or newer:

```bash
python -m pip install -r requirements.txt
python demo/representation_demo.py
python -m unittest discover -s tests -v
```

All inputs are invented in the demonstration. It prints metrics for four artificial districts and compares uniformly distributed and clustered point patterns in an artificial square. It performs no downloads and reads no research files.

To use the original spatial functions with your own authorized data, also install `requirements-original-spatial.txt`. Supply GeoDataFrames in a suitable projected coordinate reference system. They require valid, positive-area residential polygons and more than `k` points. The historical notebook default of two simulations is exploratory; select and document adequate Monte Carlo draws for a new analysis.

## Data access and limitations

Original commercial mobility records, inferred device residences, provider-derived tables, and manuscript files are omitted. Reproducing the study requires authorized provider data, Census population/geographic inputs, residential-area geometry, and the remaining processing and modeling stages. Provider terms and access conditions apply independently of this code.

Coverage does not establish that devices correspond one-to-one with residents. Residence inference, provider sampling, geographic aggregation, the residential reference distribution, and `k` can affect results. The portable demonstration uses dense NumPy distances and a simple square reference; original functions use scikit-learn and residential polygons. Neither the toy output nor these extracts reproduce manuscript results.

## Provenance

The original extracts come from `3_Code/SR_RR_Bias.ipynb` (sampling-rate and relative-representation functions) and `3_Code/Representativenss metric.ipynb` (within-area metric functions). Notebook paths, execution state, saved outputs, and data are excluded. Function bodies are preserved; imports and documentation were made explicit. The synthetic demonstration and its checks were added during portfolio preparation with coding-assistant support.
