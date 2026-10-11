"""Selected original sampling-rate and relative-representation functions.

Extracted from Shangkun Jiang's research notebook, with imports made explicit.
Function bodies are preserved. No research data or notebook outputs are included.
See ../README.md for provenance, interpretation, and demo usage.
"""
import numpy as np


def compute_sampling_ratio(gdf, acs_col, gravy_col="GravyPop", out_col="SR_Gravy"):
    """Compute sampling ratio = GravyPop / ACSPop, with NaN where ACS is missing or zero."""
    gdf[acs_col] = gdf[acs_col].astype(float).astype("Int64")
    invalid = gdf[acs_col].isna() | (gdf[acs_col] == 0)
    gdf[out_col] = np.where(invalid, np.nan, gdf[gravy_col] / gdf[acs_col])
    return gdf


def compute_rr(
    df,
    gravy_col="GravyPop",
    pop_col=None,
    rr_col="RR_Gravy",
    condition=None
):
    """
    Compute Relative Representation (RR):

    RR_i = (Gravy_i / sum Gravy) / (Pop_i / sum Pop)

    Parameters
    ----------
    df : DataFrame or GeoDataFrame
    gravy_col : str
        Device count column
    pop_col : str
        Population column (must be provided)
    rr_col : str
        Output column name
    condition : boolean mask or None
        Optional filter condition (e.g., df["SR_Gravy"] < 0.2)

    Returns
    -------
    DataFrame with RR column
    """

    if pop_col is None:
        raise ValueError("You must provide population column name.")

    # 可选筛选
    if condition is not None:
        df = df[condition].copy()
    else:
        df = df.copy()

    total_gravy = df[gravy_col].sum()
    total_pop = df[pop_col].sum()

    df[rr_col] = np.where(
        (df[pop_col].isna()) | (df[pop_col] == 0),
        np.nan,
        (df[gravy_col] / total_gravy) /
        (df[pop_col] / total_pop)
    )

    return df
