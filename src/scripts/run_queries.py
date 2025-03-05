#!/usr/bin/env python3
import psycopg2
from tabulate import tabulate
import os
import sys

def run_query(cursor, query, title):
    """Run a query and print results in a formatted table"""
    cursor.execute(query)
    rows = cursor.fetchall()
    if rows:
        column_names = [desc[0] for desc in cursor.description]
        print(f"\n{title}")
        print(tabulate(rows, headers=column_names, tablefmt="pretty"))
        print(f"Total rows: {len(rows)}")
    else:
        print(f"\n{title}")
        print("No results found.")

def main():
    try:
        conn = psycopg2.connect(
            host="localhost",
            database="OntoDb",
            user="ontodb",
            password="admin"
        )
        cursor = conn.cursor()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print("====== OntoDb Database Explorer ======\n")
        
        run_query(cursor, "SELECT * FROM Product LIMIT 10;", "First 10 Products")
        run_query(cursor, "SELECT * FROM Store LIMIT 10;", "First 10 Stores")
        run_query(cursor, "SELECT * FROM Transactions LIMIT 10;", "First 10 Transactions")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
