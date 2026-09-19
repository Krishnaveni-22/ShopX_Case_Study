import pandas as pd
from pathlib import Path

def test_source_workbook_exists():
    assert Path("SAP-DataSet.xlsx").exists()

def test_expected_sheets():
    sheets = pd.ExcelFile("SAP-DataSet.xlsx").sheet_names
    expected = {"KNA1","LFA1","VBAK","VBAP","LIKP","LIPS","VTTK","VTTP"}
    assert expected.issubset(set(sheets))

def test_no_nulls_in_core_keys():
    sheets = pd.read_excel("SAP-DataSet.xlsx", sheet_name=None)
    for sheet, key in {
        "KNA1":"Customer ID", "VBAK":"Sales Document",
        "VBAP":"Sales Document", "LIKP":"Delivery Number",
        "LIPS":"Delivery Number", "VTTK":"Shipment Number",
        "VTTP":"Shipment Number"
    }.items():
        assert sheets[sheet][key].notna().all(), f"{sheet} has null key values"

def test_referential_integrity():
    s = pd.read_excel("SAP-DataSet.xlsx", sheet_name=None)
    assert set(s["VBAK"]["Customer ID"]).issubset(set(s["KNA1"]["Customer ID"]))
    assert set(s["VBAP"]["Sales Document"]).issubset(set(s["VBAK"]["Sales Document"]))
    assert set(s["LIKP"]["Sales Document"]).issubset(set(s["VBAK"]["Sales Document"]))
    assert set(s["VTTK"]["Delivery Number"]).issubset(set(s["LIKP"]["Delivery Number"]))

def test_no_duplicate_source_rows():
    s = pd.read_excel("SAP-DataSet.xlsx", sheet_name=None)
    for name, df in s.items():
        assert df.duplicated().sum() == 0, f"{name} contains duplicate rows"
