#!/usr/bin/env python3
import pandas as pd
import psycopg2
import time
import sys
import os
from tqdm import tqdm

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def wait_for_db(host, dbname, user, password, max_attempts=10):
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(host=host, dbname=dbname, user=user, password=password)
            conn.close()
            return True
        except psycopg2.OperationalError:
            time.sleep(3)
    return False

def load_data():
    if not wait_for_db(host="localhost", dbname="OntoDb", user="ontodb", password="admin"):
        return
    
    data_path = os.path.join(os.path.dirname(__file__), '../../data/cleaned')
    bakery_path = os.path.join(data_path, "Bakery_sales_cleaned.csv")
    coffee_path = os.path.join(data_path, "Coffee_Shop_Sales_cleaned.csv")
    
    if not os.path.exists(bakery_path) or not os.path.exists(coffee_path):
        return
    
    df_bakery = pd.read_csv(bakery_path)
    df_coffee = pd.read_csv(coffee_path)
    df_merged = pd.concat([df_bakery, df_coffee], ignore_index=True)

    products = df_merged[["product_id","product_category","product_type","product_detail","unit_price"]].drop_duplicates()
    stores = df_merged[["store_id","store_location"]].drop_duplicates()
    transactions = df_merged[["sales_id","transaction_id","transaction_date","transaction_time","transaction_qty","store_id","product_id"]]

    conn = psycopg2.connect(host="localhost", dbname="OntoDb", user="ontodb", password="admin")
    conn.autocommit = True
    cursor = conn.cursor()

    for _, row in tqdm(stores.iterrows(), desc="Inserting stores", total=len(stores)):
        cursor.execute(
            "INSERT INTO Store (store_id, store_location) VALUES (%s, %s) ON CONFLICT (store_id) DO NOTHING",
            (row["store_id"], row["store_location"])
        )
    for _, row in tqdm(products.iterrows(), desc="Inserting products", total=len(products)):
        cursor.execute(
            "INSERT INTO Product (product_id, product_category, product_type, product_detail, unit_price) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (product_id) DO NOTHING",
            (row["product_id"], row["product_category"], row["product_type"], row["product_detail"], row["unit_price"])
        )
    for _, row in tqdm(transactions.iterrows(), desc="Inserting transactions", total=len(transactions)):
        cursor.execute(
            "INSERT INTO Transactions (sale_id, transaction_id, transaction_date, transaction_time, transaction_qty, store_id, product_id) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (sale_id) DO NOTHING",
            (row.sales_id, row.transaction_id, row.transaction_date, row.transaction_time, row.transaction_qty, row.store_id, row.product_id)
        )

    cursor.close()
    conn.close()

if __name__ == "__main__":
    load_data()
