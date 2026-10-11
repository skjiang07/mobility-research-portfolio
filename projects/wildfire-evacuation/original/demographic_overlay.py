"""Source excerpts from 1_Population (paper).ipynb.

Zero-based source cells: calculate_weighted_features (cell 37).
The extracted function definitions are preserved without modification.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import box


def calculate_weighted_features(df, lat_col, lon_col, quadkey_col, Social_demographic_cbg, buffer_size=1223):
    """
    计算给定位置点的人口统计特征的加权平均值
    
    参数:
    df: DataFrame，包含位置信息的数据框
    lat_col: str，纬度列名
    lon_col: str，经度列名
    quadkey_col: str，四叉树键列名
    Social_demographic_cbg: GeoDataFrame，包含人口统计数据的空间数据框
    buffer_size: float，缓冲区大小（米），默认1223米
    
    返回:
    GeoDataFrame，包含原始数据和计算得到的加权特征
    """
    # 选取并去重
    point_df = df[[lat_col, lon_col, quadkey_col]].drop_duplicates()
    
    # 创建 GeoDataFrame
    point_gdf = gpd.GeoDataFrame(
        point_df, 
        geometry=gpd.points_from_xy(point_df[lon_col], point_df[lat_col]),
        crs="EPSG:4326"  # WGS84
    )
    
    # 转换为 EPSG:3857（Web Mercator）
    point_gdf = point_gdf.to_crs(epsg=3857)
    
    # 创建正方形 buffer
    point_gdf['geometry'] = point_gdf.geometry.apply(lambda point: box(
        point.x - buffer_size, point.y - buffer_size,
        point.x + buffer_size, point.y + buffer_size
    ))
    
    # 进行空间匹配（计算交集）
    joined_gdf = gpd.overlay(Social_demographic_cbg, point_gdf, how='intersection')
    
    # 计算交集区域的面积
    joined_gdf['intersection_area'] = joined_gdf.geometry.area
    
    # 特殊处理 medianHHIncome 列
    if 'medianHHIncome' in joined_gdf.columns:
        joined_gdf['medianHHIncome'] = joined_gdf['medianHHIncome'].apply(
            lambda x: 250000 if x == '250,000+' else x
        )
    
    # 需要加权平均的特征列
    features = [
        'avgHouseholdSize', 'pctNonWhite(%)', 'pctUnemployment(%)', 'pctPoverty(%)', 
        'pctDisability(%)', 'pctElder(%)', 'pctBachelorBelow(%)', 'pctNoHealthInsurance(%)', 
        'pctFemale(%)', 'pctChildren(%)', 'pctCarOwnership(%)', 'pctHomeOwnership(%)', 
        'totalPopulation', 'medianHHIncome'
    ]
    
    # 计算加权平均值，跳过无效数据
    weighted_features = {}
    prefix = quadkey_col.split('_')[0]  # 获取前缀（start 或 end）
    
    for feature in features:
        # 转换为数值类型，非数值转为 NaN
        joined_gdf[feature] = pd.to_numeric(joined_gdf[feature], errors='coerce')
        
        # 过滤掉 NaN 行
        valid_rows = joined_gdf.dropna(subset=[feature])
        
        # 计算加权值
        valid_rows[f'weighted_{feature}'] = valid_rows[feature] * valid_rows['intersection_area']
        
        # 计算最终加权平均
        weighted_features[f'{prefix}_{feature}'] = (
            valid_rows.groupby(quadkey_col)[f'weighted_{feature}'].sum() / 
            valid_rows.groupby(quadkey_col)['intersection_area'].sum()
        )
    
    # 转换为 DataFrame
    weighted_df = pd.DataFrame(weighted_features)
    
    # 合并回原始 GeoDataFrame
    result_gdf = point_gdf.merge(weighted_df, on=quadkey_col, how='left')
    
    return result_gdf
