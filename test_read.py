import pandas as pd

file = "SAP-DataSet.xlsx"

sheets = pd.read_excel(file, sheet_name=None)

for name, df in sheets.items():
    print(name)
    print(df.shape)
    print()