"""Original PTI helper from Revise_TTR.ipynb, cell 17 (zero-based).
Preserved function body; excludes downstream experiments and all data.
Uses speed_limit / fifth-percentile speed, a quantile approximation to PTI.
"""
import ast
import numpy as np
import pandas as pd

def add_pti_column(df_ttr: pd.DataFrame, inplace: bool = True) -> pd.DataFrame:
    """
    新增列 `pti`，按以下规则计算：
      • speed 为 NaN           → pti = NaN
      • speed 为标量           → pti = speed_limit / speed
      • speed 为列表           → 取列表非缺失值的 5th percentile (最低 5 %)，再用 speed_limit / p5
    """

    # ---------- 1. 解析 speed ----------
    def _parse(cell):
        if isinstance(cell, list):
            return cell
        if isinstance(cell, (int, float, np.number)):
            return float(cell)
        if pd.isna(cell):
            return np.nan
        try:                                     # 解析字符串形式 "[..]"
            val = ast.literal_eval(str(cell))
            return val
        except (ValueError, SyntaxError):
            return np.nan

    df_parsed = df_ttr.copy() if not inplace else df_ttr
    df_parsed['speed_parsed'] = df_parsed['speed'].apply(_parse)

    # ---------- 2. 计算 pti ----------
    def _pti(row):
        sp = row['speed_parsed']
        sl = row['speed_limit']

        # 缺失或非法
        if sp is np.nan or (isinstance(sp, float) and np.isnan(sp)):
            return np.nan

        # 标量
        if isinstance(sp, (int, float, np.number)):
            return np.nan if sp == 0 else sl / sp

        # 列表 / 数组
        if isinstance(sp, (list, np.ndarray)):
            numeric_vals = [v for v in sp
                            if isinstance(v, (int, float, np.number)) and not np.isnan(v)]
            if not numeric_vals:                 # 空列表或全 NaN
                return np.nan
            p5 = np.percentile(numeric_vals, 5)  # 最低 5 %
            return np.nan if p5 == 0 else sl / p5

        return np.nan                            # 其他类型

    df_parsed['pti'] = df_parsed.apply(_pti, axis=1)

    # ---------- 3. 清理并返回 ----------
    df_parsed.drop(columns='speed_parsed', inplace=True)
    return df_parsed
