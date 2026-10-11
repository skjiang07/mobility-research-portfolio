"""Source excerpts from 2_Movement (paper).ipynb.

Zero-based source cells: create_od_movement_gdf (cell 109).
The extracted function definitions are preserved without modification.
"""

import geopandas as gpd
from shapely.geometry import LineString


def create_od_movement_gdf(movement_df):
    """
    创建OD移动的GeoDataFrame
    
    Parameters:
    -----------
    movement_df : pandas.DataFrame
        包含移动数据的DataFrame，必须包含以下列：
        - start_quadkey, end_quadkey
        - n_baseline, n_crisis
        - start_latitude, start_longitude
        - end_latitude, end_longitude
    
    Returns:
    --------
    geopandas.GeoDataFrame
        处理后的GeoDataFrame，包含空间信息
    """
    # 按quadkey分组并计算总和
    od_movement = movement_df.groupby(
        ["start_quadkey", "end_quadkey"], 
        as_index=False
    )[["n_baseline", "n_crisis"]].sum()
    
    # 按crisis数量排序
    od_movement = od_movement.sort_values(by="n_crisis", ascending=False)
    
    # 合并起点信息
    od_movement = od_movement.merge(
        movement_df[["start_quadkey", "start_latitude", "start_longitude"]].drop_duplicates(),
        on="start_quadkey", 
        how="left"
    )
    
    # 合并终点信息
    od_movement = od_movement.merge(
        movement_df[["end_quadkey", "end_latitude", "end_longitude"]].drop_duplicates(),
        on="end_quadkey", 
        how="left"
    )
    
    # 创建geometry列
    od_movement["geometry"] = od_movement.apply(
        lambda row: LineString([
            (row["start_longitude"], row["start_latitude"]), 
            (row["end_longitude"], row["end_latitude"])
        ]), 
        axis=1
    )
    
    # 转换为GeoDataFrame并更改投影
    od_movement_gdf = gpd.GeoDataFrame(
        od_movement, 
        geometry="geometry", 
        crs="EPSG:4326"
    ).to_crs("EPSG:3857")
    
    return od_movement_gdf
