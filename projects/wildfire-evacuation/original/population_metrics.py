"""Source excerpts from 1_Population (paper).ipynb.

Zero-based source cells: impute_missing_data (cell 19), calculate_population_metrics (cell 23).
The extracted function definitions are preserved without modification.
"""

import numpy as np


def impute_missing_data(gdf_pop_by_day):
    import pandas as pd
    import numpy as np
    
    # 找出需要处理的quadkey
    quadkey_counts = gdf_pop_by_day.groupby('quadkey')['ds'].nunique()
    total_unique_ds = len(gdf_pop_by_day['ds'].unique())
    problem_quadkeys = quadkey_counts[quadkey_counts != total_unique_ds].index
    
    # 创建结果DataFrame的副本
    gdf_pop_by_day_imputed = gdf_pop_by_day.copy()
    
    # 用于存储新行的列表
    new_rows = []
    
    for quadkey in problem_quadkeys:
        # 获取当前quadkey的数据
        quadkey_data = gdf_pop_by_day[gdf_pop_by_day['quadkey'] == quadkey].copy()
        all_dates = pd.DataFrame({'ds': gdf_pop_by_day['ds'].unique()})
        
        # 找出缺失的日期
        missing_dates = all_dates[~all_dates['ds'].isin(quadkey_data['ds'])]
        
        # 为每个缺失的日期创建新行
        for missing_date in missing_dates['ds']:
            new_row = quadkey_data.iloc[0].copy()
            new_row['ds'] = missing_date
            new_row[['n_baseline', 'n_crisis']] = np.nan
            new_rows.append(new_row)
    
    # 一次性添加所有新行
    if new_rows:
        gdf_pop_by_day_imputed = pd.concat([gdf_pop_by_day_imputed, pd.DataFrame(new_rows)], ignore_index=True)
    
    # 对每个quadkey进行移动平均填充
    for quadkey in problem_quadkeys:
        mask = gdf_pop_by_day_imputed['quadkey'] == quadkey
        quadkey_data = gdf_pop_by_day_imputed[mask].sort_values('ds').copy()
        
        # 处理缺失值
        for col in ['n_baseline', 'n_crisis']:
            values = quadkey_data[col].values
            missing_mask = np.isnan(values)
            
            if missing_mask.any():
                for i in range(len(values)):
                    if np.isnan(values[i]):
                        if i < 3:  # 前三个的特殊处理
                            next_valid = values[i:][~np.isnan(values[i:])]
                            if len(next_valid) >= 3:
                                values[i] = next_valid[:3].mean()
                            elif len(next_valid) > 0:
                                values[i] = next_valid.mean()
                        else:  # 使用移动平均
                            window_values = values[max(0, i-3):i]
                            window_values = window_values[~np.isnan(window_values)]
                            if len(window_values) > 0:
                                values[i] = window_values.mean()
                
                quadkey_data[col] = values
        
        # 使用布尔索引更新原始数据
        gdf_pop_by_day_imputed.loc[mask] = quadkey_data.values
    
    return gdf_pop_by_day_imputed.sort_values(['quadkey', 'ds']).reset_index(drop=True)


def calculate_population_metrics(gdf, baseline_col='n_baseline', crisis_col='n_crisis'):
    """
    计算人口数据的疏散率、涌入率和百分比变化
    
    参数:
    gdf : GeoDataFrame/DataFrame - 输入数据框
    baseline_col : str - 基准人口列名，默认为'n_baseline'
    crisis_col : str - 危机人口列名，默认为'n_crisis'
    
    返回:
    GeoDataFrame/DataFrame - 添加了新计算列的数据框
    """
    # 创建副本以避免修改原始数据
    result_gdf = gdf.copy()
    
    # 计算疏散率
    result_gdf['evacuation_rate'] = np.where(
        result_gdf[baseline_col] > result_gdf[crisis_col],
        (result_gdf[baseline_col] - result_gdf[crisis_col]) / result_gdf[baseline_col] * 100,
        0
    )
    
    # 计算涌入率
    result_gdf['influx_rate'] = np.where(
        result_gdf[baseline_col] < result_gdf[crisis_col],
        (result_gdf[crisis_col] - result_gdf[baseline_col]) / result_gdf[baseline_col] * 100,
        0
    )
    
    # 计算百分比变化
    result_gdf['percentage_change'] = (
        (result_gdf[crisis_col] - result_gdf[baseline_col]) / result_gdf[baseline_col] * 100
    )
    
    return result_gdf
