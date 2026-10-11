"""Selected original within-area spatial-representation functions.

Extracted from Shangkun Jiang's research notebook. Function bodies are preserved;
imports are explicit and notebook execution, paths, outputs, and data are omitted.
Coordinates must use a suitable projected CRS. The historical n_sim=2 default
is exploratory and is not a claim about the submitted manuscript's settings.
"""
import random

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from sklearn.neighbors import NearestNeighbors


def compute_aknnd(points_gdf, k=5):

    coords = np.array([[geom.x, geom.y] for geom in points_gdf.geometry])

    if len(coords) <= k:
        return np.nan

    nn = NearestNeighbors(n_neighbors=k+1)
    nn.fit(coords)

    distances, _ = nn.kneighbors(coords)

    knn = distances[:, 1:k+1]

    return knn.mean()


def random_points_in_polygon(polygon, n):

    minx, miny, maxx, maxy = polygon.bounds

    points = []

    while len(points) < n:

        p = Point(
            random.uniform(minx, maxx),
            random.uniform(miny, maxy)
        )

        if polygon.contains(p):
            points.append(p)

    return points


def random_points_in_polygons(polygons_gdf, n):

    polygons = polygons_gdf.copy()

    polygons["area"] = polygons.geometry.area

    probs = polygons["area"] / polygons["area"].sum()

    chosen = np.random.choice(polygons.index, size=n, p=probs)

    pts = []

    for idx in chosen:

        poly = polygons.loc[idx, "geometry"]

        pts.extend(random_points_in_polygon(poly, 1))

    return pts


def evaluate_unit(emp_points, res_polygons, k=5, n_sim=2):

    Ci = len(emp_points)

    if Ci <= k or len(res_polygons) == 0:
        return None

    r_i = compute_aknnd(emp_points, k)

    h_vals = []
    M_vals = []

    for _ in range(n_sim):

        sim_points = random_points_in_polygons(res_polygons, Ci)

        sim_gdf = gpd.GeoDataFrame(
            geometry=sim_points,
            crs=emp_points.crs
        )

        h_i = compute_aknnd(sim_gdf, k)

        if pd.notna(h_i):

            h_vals.append(h_i)

            M = np.exp(-abs(r_i / h_i - 1))

            M_vals.append(M)

    return {
        "Ci": Ci,
        "r_i": r_i,
        "h_i_mean": np.mean(h_vals),
        "M_i_mean": np.mean(M_vals)
    }
