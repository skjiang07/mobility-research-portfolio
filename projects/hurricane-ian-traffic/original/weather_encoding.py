"""Original ordinal rainfall helper, Model_data_prepare.ipynb cell 26.
Preserved body. Caller must supply nonmissing strings; not a weather ingestion pipeline.
"""
def encode_precipitation(desc):
    if 'rain' not in desc.lower():
        return 0
    elif 'light rain' in desc.lower():
        return 1
    elif 'moderate rain' in desc.lower():
        return 2
    elif 'heavy intensity rain' in desc.lower():
        return 3
    elif 'very heavy rain' in desc.lower():
        return 4
    else:
        return 0
