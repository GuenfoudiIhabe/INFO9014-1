#!/usr/bin/env python3
import psycopg2
from tabulate import tabulate
import os
import sys
import time

def wait_for_db(host, dbname, user, password, port=5432, max_attempts=5):
    """Wait for database to be available, with improved error handling"""
    print(f"Trying to connect to PostgreSQL at {host}:{port}...")
    
    for attempt in range(1, max_attempts + 1):
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname, 
                user=user, 
                password=password
            )
            conn.close()
            print(f"Successfully connected to database '{dbname}' on {host}:{port}")
            return True
        except psycopg2.OperationalError as e:
            print(f"Waiting for database... attempt {attempt}/{max_attempts}")
            print(f"Error: {str(e).strip()}")
            time.sleep(3)
    
    print("\nDatabase connection failed! Please check:")
    print("1. Is PostgreSQL running? You may need to start Docker containers:")
    print("   docker-compose -f config/docker-compose.yml up -d")
    print("2. Are the connection details correct?")
    print(f"   Host: {host}, Port: {port}, Database: {dbname}, User: {user}")
    print("3. If running locally, ensure PostgreSQL is installed and running")
    return False

def run_query(cursor, query, title):
    """Run a query and print results in a formatted table"""
    try:
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
    except Exception as e:
        print(f"\n{title}")
        print(f"Error executing query: {str(e)}")

def show_table_data(cursor, table_name):
    """Show the first 10 rows from a specific table"""
    try:
        # First get column count to see if table exists and has data
        cursor.execute(f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '{table_name.lower()}'")
        column_count = cursor.fetchone()[0]
        
        if column_count == 0:
            print(f"\nTable {table_name} not found or has no columns.")
            return
            
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        row_count = cursor.fetchone()[0]
        
        query = f"SELECT * FROM {table_name} LIMIT 10"
        table_title = f"First 10 rows from {table_name} (Total rows: {row_count})"
        run_query(cursor, query, table_title)
    except Exception as e:
        print(f"\nError querying table {table_name}: {str(e)}")

def main():
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', '5432'))
    dbname = os.environ.get('DB_NAME', 'OntoDb')
    user = os.environ.get('DB_USER', 'ontodb')
    password = os.environ.get('DB_PASSWORD', 'admin')
    
    # First try with provided/default settings
    if not wait_for_db(host=host, port=port, dbname=dbname, user=user, password=password):
        # If Docker is running, try with 'postgres' as hostname (Docker service name)
        if host == 'localhost':
            print("\nTrying alternate Docker connection settings...")
            if not wait_for_db(host='postgres', port=port, dbname=dbname, user=user, password=password):
                print("Could not connect to database with alternate settings either.")
                return
            else:
                # Update host for future connections
                host = 'postgres'
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=dbname,
            user=user,
            password=password
        )
        cursor = conn.cursor()
        
        os.system('cls' if os.name == 'nt' else 'clear')
        print("====== OntoDb Database Content Verification ======\n")
        
        # Define all tables to query based on init.sql
        tables = [
            'StoreCategory',
            'StoreRegion',
            'Store',
            'ProductCategory',
            'ProductType',
            'Currency',
            'Product',
            'StaffRole',
            'Staff',
            'PaymentMethod',
            'Transaction',
            'TransactionItem',
            'Shift'  # Added Shift table that was missing
        ]
        
        # Show table counts first for a quick overview
        print("Database Tables Overview:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"- {table}: {count} rows")
            except Exception as e:
                print(f"- {table}: Error - {str(e)}")
        
        print("\n====== Detailed Table Contents ======")
        # Show data from each table
        for table in tables:
            show_table_data(cursor, table)
        
        # Also run the original analytical queries
        print("\n\n====== Analytical Queries ======\n")
        
        # Store related queries
        run_query(cursor, """
            SELECT s.store_id, s.store_name, c.category_name, r.region_name, s.data_source 
            FROM Store s
            JOIN StoreCategory c ON s.store_category_id = c.category_id
            JOIN StoreRegion r ON s.region_id = r.region_id
            LIMIT 10;
        """, "Stores with Categories and Regions")
        
        # Product related queries
        run_query(cursor, """
            SELECT p.product_id, p.product_name, pt.type_name, pc.category_name, 
                   p.base_price, c.currency_code, p.data_source
            FROM Product p
            JOIN ProductType pt ON p.type_id = pt.type_id
            JOIN ProductCategory pc ON pt.category_id = pc.category_id
            JOIN Currency c ON p.currency_id = c.currency_id
            LIMIT 10;
        """, "Products with Categories and Types")
        
        # Transaction summary
        run_query(cursor, """
            SELECT data_source, COUNT(*) AS transaction_count, 
                   SUM(total_amount) AS total_sales
            FROM Transaction
            GROUP BY data_source;
        """, "Transaction Summary by Data Source")

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
