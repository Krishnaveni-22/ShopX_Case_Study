from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

INPUT_FILE = Path("SAP-DataSet.xlsx")
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def clean_columns(df):
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    df = df.drop_duplicates()
    return df

def main():
    sheets = pd.read_excel(INPUT_FILE, sheet_name=None)
    sheets = {k: clean_columns(v) for k, v in sheets.items()}

    # Source tables
    kna1 = sheets["KNA1"]
    lfa1 = sheets["LFA1"]
    vbak = sheets["VBAK"]
    vbap = sheets["VBAP"]
    likp = sheets["LIKP"]
    lips = sheets["LIPS"]
    vttk = sheets["VTTK"]
    vttp = sheets["VTTP"]

    # Date conversion
    for df, cols in [
        (vbak, ["Order Date"]),
        (vbap, ["Delivery Date"]),
        (likp, ["Delivery Date"]),
        (lips, ["Delivery Date"]),
        (vttk, ["Shipment Date"]),
        (vttp, ["Shipment Date"]),
    ]:
        for col in cols:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Customers: KNA1 -> customers
    customers = kna1.rename(columns={
        "Customer ID":"customer_id", "Customer Name":"customer_name",
        "Country":"country", "Region":"region", "City":"city",
        "Postal Code":"postal_code", "Street Address":"street_address",
        "Phone Number":"phone_number", "Email Address":"email_address",
        "Language":"language_code", "Tax Number":"tax_number",
        "Customer Group":"customer_group", "Sales Organization":"sales_organization",
        "Distribution Channel":"distribution_channel", "Division":"division"
    })

    # Carriers: the supplied VTTK contains carrier names; LFA1 has vendor data
    # but no explicit key mapping to Carrier1/2/3. Therefore carrier dimension
    # is derived from the carrier values actually used in VTTK.
    carrier_names = sorted(vttk["Carrier"].dropna().astype(str).unique())
    carriers = pd.DataFrame({
        "carrier_id": [f"CARR{i+1:03d}" for i in range(len(carrier_names))],
        "carrier_name": carrier_names
    })
    carrier_map = dict(zip(carrier_names, carriers["carrier_id"]))
    vttk["carrier_id"] = vttk["Carrier"].map(carrier_map)

    # Orders: VBAK -> orders
    orders = vbak.rename(columns={
        "Sales Document":"order_id", "Order Date":"order_date",
        "Customer ID":"customer_id", "Order Type":"order_type",
        "Sales Organization":"sales_organization",
        "Distribution Channel":"distribution_channel",
        "Division":"division", "Order Status":"order_status"
    })

    # Order items: VBAP -> order_items
    order_items = vbap.rename(columns={
        "Sales Document":"order_id", "Item Number":"item_number",
        "Material Number":"product_id", "Quantity":"order_quantity",
        "Net Price":"unit_price", "Item Status":"item_status",
        "Delivery Date":"expected_delivery_date"
    })

    # Shipment header: VTTK joined to LIKP for delivery id
    shipments = vttk.rename(columns={
        "Shipment Number":"shipment_id", "Sales Document":"order_id",
        "Delivery Number":"delivery_id", "Shipment Date":"shipment_date",
        "Shipping Point":"shipping_point", "Shipment Status":"shipment_status",
        "Route":"route", "Shipping Type":"shipping_type",
        "Customer ID":"customer_id"
    })[
        ["shipment_id","order_id","delivery_id","carrier_id","shipment_date",
         "shipping_point","shipment_status","route","shipping_type","customer_id"]
    ]

    # Shipment items: VTTP -> shipment_items
    shipment_items = vttp.rename(columns={
        "Shipment Number":"shipment_id", "Item Number":"item_number",
        "Material Number":"product_id", "Shipped Quantity":"shipped_quantity",
        "Item Status":"item_status", "Delivery Number":"delivery_id",
        "Customer ID":"customer_id", "Sales Document":"order_id",
        "Sales Item":"sales_item", "Shipment Date":"shipment_date"
    })[
        ["shipment_id","item_number","product_id","shipped_quantity","item_status",
         "delivery_id","customer_id","order_id","sales_item","shipment_date"]
    ]

    # Delivery analytics at order level.
    # Assumption from the sample report: VBAP delivery date = expected date,
    # actual delivery date comes from delivery data. For multi-item orders,
    # use the latest expected/actual date so the order is complete.
    expected = order_items.groupby("order_id", as_index=False)["expected_delivery_date"].max()
    actual = lips.assign(
        actual_delivery_date=pd.to_datetime(lips["Delivery Date"], errors="coerce")
    ).groupby("Sales Document", as_index=False)["actual_delivery_date"].max()
    actual = actual.rename(columns={"Sales Document":"order_id"})
    ship = shipments.groupby("order_id", as_index=False).agg(
        shipment_date=("shipment_date","min"),
        carrier_id=("carrier_id","first")
    )

    analytics = orders[["order_id","customer_id","order_date"]].merge(
        ship, on="order_id", how="left"
    ).merge(expected, on="order_id", how="left").merge(actual, on="order_id", how="left")

    analytics["order_processing_days"] = (
        analytics["shipment_date"] - analytics["order_date"]
    ).dt.days
    analytics["delivery_time_days"] = (
        analytics["actual_delivery_date"] - analytics["shipment_date"]
    ).dt.days
    analytics["delivery_delay_days"] = (
        analytics["actual_delivery_date"] - analytics["expected_delivery_date"]
    ).dt.days
    analytics["on_time_flag"] = (analytics["delivery_delay_days"] <= 0).astype("Int64")
    analytics["delay_reason"] = analytics["delivery_delay_days"].apply(
        lambda x: "Late delivery" if pd.notna(x) and x > 0 else (
            "On time / early" if pd.notna(x) else "Missing date"
        )
    )

    # Export CSVs for easy inspection/loading
    outputs = {
        "customers": customers,
        "carriers": carriers,
        "orders": orders,
        "order_items": order_items,
        "shipments": shipments,
        "shipment_items": shipment_items,
        "delivery_analytics": analytics
    }
    for name, df in outputs.items():
        df.to_csv(OUTPUT_DIR / f"{name}.csv", index=False)

    # Validation report
    validation = {
        "source_sheet_count": len(sheets),
        "customers_rows": len(customers),
        "orders_rows": len(orders),
        "order_items_rows": len(order_items),
        "shipments_rows": len(shipments),
        "shipment_items_rows": len(shipment_items),
        "delivery_analytics_rows": len(analytics),
        "orders_missing_customer": int((~orders["customer_id"].isin(customers["customer_id"])).sum()),
        "order_items_missing_order": int((~order_items["order_id"].isin(orders["order_id"])).sum()),
        "shipments_missing_order": int((~shipments["order_id"].isin(orders["order_id"])).sum()),
        "analytics_missing_shipment_date": int(analytics["shipment_date"].isna().sum()),
        "analytics_missing_expected_date": int(analytics["expected_delivery_date"].isna().sum()),
        "analytics_missing_actual_date": int(analytics["actual_delivery_date"].isna().sum()),
        "analytics_duplicate_order_ids": int(analytics["order_id"].duplicated().sum())
    }
    pd.Series(validation).to_csv(OUTPUT_DIR / "validation_report.csv", header=["value"])
    print(pd.Series(validation))
    print("\nETL complete. CSV files are in ./output")

if __name__ == "__main__":
    main()
