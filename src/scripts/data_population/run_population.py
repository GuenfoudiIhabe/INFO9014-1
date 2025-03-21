#!/usr/bin/env python3
import psycopg2
import os
import sys
import time
import random
from datetime import datetime, timedelta
import argparse

# Import modules with explicit paths to avoid relative import issues
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# Import modules rather than specific functions
import populate_store_data
import populate_staff_data  # Changed to import the whole module
from populate_product_data import populate_product_data
from populate_transaction_data import populate_transaction_data

def wait_for_db(host, dbname, user, password, port=5432, max_attempts=10):
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

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Populate database tables with sample data')
    parser.add_argument('--tables', nargs='+', choices=['all', 'store', 'product', 'staff', 'transaction'],
                      default=['all'], help='Specify which tables to populate')
    parser.add_argument('--host', default=os.environ.get('DB_HOST', 'localhost'),
                      help='Database host (default: localhost or DB_HOST env var)')
    parser.add_argument('--port', type=int, default=int(os.environ.get('DB_PORT', '5432')),
                      help='Database port (default: 5432 or DB_PORT env var)')
    parser.add_argument('--dbname', default=os.environ.get('DB_NAME', 'OntoDb'),
                      help='Database name (default: OntoDb or DB_NAME env var)')
    parser.add_argument('--user', default=os.environ.get('DB_USER', 'ontodb'),
                      help='Database user (default: ontodb or DB_USER env var)')
    parser.add_argument('--password', default=os.environ.get('DB_PASSWORD', 'admin'),
                      help='Database password (default: admin or DB_PASSWORD env var)')
    
    args = parser.parse_args()
    
    # Set seed for reproducibility
    random.seed(42)
    
    # Connect to the database
    if not wait_for_db(host=args.host, port=args.port, dbname=args.dbname, user=args.user, password=args.password):
        if args.host == 'localhost':
            print("\nTrying alternate Docker connection settings...")
            if not wait_for_db(host='postgres', port=args.port, dbname=args.dbname, user=args.user, password=args.password):
                print("Could not connect to database with alternate settings either.")
                return
            else:
                # Update host for future connections
                args.host = 'postgres'
        else:
            return
    
    # Connect to the database
    conn = psycopg2.connect(
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user=args.user,
        password=args.password
    )
    
    # Use autocommit to avoid transaction complexities
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Determine which tables to populate
        populate_all = 'all' in args.tables
        
        # Store data
        if populate_all or 'store' in args.tables:
            # Use the most direct and reliable method - just execute the module file
            # and capture its outputs
            file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'populate_store_data.py')
            print(f"Running store data module directly as a script: {file_path}")
            
            # Create a temporary connection for the subprocess to use
            db_params = {
                'host': args.host,
                'port': args.port,
                'dbname': args.dbname,
                'user': args.user,
                'password': args.password
            }
            
            # Execute the populate_store_data.py file as a subprocess
            import subprocess
            
            # Format database connection string for the subprocess
            connection_str = f"host={db_params['host']} port={db_params['port']} dbname={db_params['dbname']} user={db_params['user']} password={db_params['password']}"
            
            # Set environment variables for the subprocess
            env = os.environ.copy()
            env['DB_HOST'] = db_params['host']
            env['DB_PORT'] = str(db_params['port'])
            env['DB_NAME'] = db_params['dbname']
            env['DB_USER'] = db_params['user']
            env['DB_PASSWORD'] = db_params['password']
            
            # Run the populate_store_data.py script as a subprocess
            result = subprocess.run(
                [sys.executable, file_path],
                env=env,
                capture_output=True,
                text=True
            )
            
            print(f"Store data population output: {result.stdout}")
            
            if result.returncode != 0:
                print(f"Store data population error: {result.stderr}")
                raise Exception(f"Failed to run store data population script: {result.stderr}")
            
            # After running the script, query the database to get the data we need
            cursor.execute("SELECT category_id, category_name FROM StoreCategory")
            store_categories = cursor.fetchall()
            
            cursor.execute("SELECT region_id, region_name FROM StoreRegion")
            regions = cursor.fetchall()
            
            cursor.execute("SELECT store_id, store_name, store_category_id, region_id, address, phone, opening_date, data_source FROM Store")
            stores = cursor.fetchall()
            
            print(f"Retrieved {len(stores)} stores from database after population")
        else:
            # If not populating store data, we still need the stores for other relations
            cursor.execute("SELECT store_id, store_name, store_category_id, region_id, address, phone, opening_date, data_source FROM Store")
            stores = cursor.fetchall()
            
        # Product data
        if populate_all or 'product' in args.tables:
            currencies, product_categories, db_product_types, products = populate_product_data(cursor)
        else:
            # If not populating product data, we still need products for transactions
            cursor.execute("""
                SELECT product_id, product_name, type_id, detail, base_price, 
                       currency_id, is_seasonal, is_active, data_source 
                FROM Product
            """)
            products = cursor.fetchall()
        
        # Staff data
        if populate_all or 'staff' in args.tables:
            # Apply the same fix for staff module
            if hasattr(populate_staff_data, 'populate_staff_data'):
                roles, staff_members = populate_staff_data.populate_staff_data(cursor, stores)
            elif hasattr(populate_staff_data, 'populate_staff'):
                roles, staff_members = populate_staff_data.populate_staff(cursor, stores)
            elif hasattr(populate_staff_data, 'populate_staff_tables'):
                roles, staff_members = populate_staff_data.populate_staff_tables(cursor, stores)
            elif hasattr(populate_staff_data, 'main'):
                roles, staff_members = populate_staff_data.main(cursor, stores)
            else:
                # If none of the above work, use the first function found in the module
                module_functions = [f for f in dir(populate_staff_data) 
                                   if callable(getattr(populate_staff_data, f)) and not f.startswith('_')]
                if module_functions:
                    print(f"Using function {module_functions[0]} from populate_staff_data module")
                    roles, staff_members = getattr(populate_staff_data, module_functions[0])(cursor, stores)
                else:
                    raise ImportError("No suitable function found in populate_staff_data module")
        
        # Transaction data
        if populate_all or 'transaction' in args.tables:
            payment_methods, transactions, transaction_items = populate_transaction_data(cursor, stores, products)
        
        print("Data population complete!")
        
    except Exception as e:
        print(f"Error during data population: {str(e)}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
