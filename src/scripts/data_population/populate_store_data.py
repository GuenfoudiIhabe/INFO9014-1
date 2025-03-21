#!/usr/bin/env python3
import pandas as pd
import random
from datetime import datetime, timedelta
import psycopg2
import os
import sys

def populate_store_data(cursor):
    """Populate Store, StoreCategory, and StoreRegion tables"""
    print("Populating store data...")
    
    # Ensure store categories exist
    categories = [
        ('Bakery', 'Traditional French bakery'),
        ('Coffee Shop', 'Modern coffee and pastry shop')
    ]
    
    for name, description in categories:
        cursor.execute(
            "INSERT INTO StoreCategory (category_name, description) VALUES (%s, %s) ON CONFLICT (category_name) DO NOTHING",
            (name, description)
        )
    
    # Get category IDs
    cursor.execute("SELECT category_id, category_name FROM StoreCategory")
    store_categories = cursor.fetchall()
    bakery_id = next(cat_id for cat_id, name in store_categories if name.lower() == 'bakery')
    coffee_id = next(cat_id for cat_id, name in store_categories if name.lower() == 'coffee shop')
    
    # Ensure regions exist
    regions = [
        ('Paris', 'France'),
        ('Lyon', 'France'),
        ('Marseille', 'France'),
        ('Toulouse', 'France'),
        ('Nice', 'France')
    ]
    
    for name, country in regions:
        cursor.execute(
            "INSERT INTO StoreRegion (region_name, country) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            (name, country)
        )
    
    # Get region IDs
    cursor.execute("SELECT region_id, region_name FROM StoreRegion")
    regions = cursor.fetchall()
    
    # Create stores with more realistic data
    stores = [
        # Bakery stores
        ('BAK001', 'Le Pain Quotidien', bakery_id, regions[0][0], '23 Rue Saint-Michel', '+33145789012', '2018-05-12', 'bakery'),
        ('BAK002', 'Boulangerie Moderne', bakery_id, regions[1][0], '45 Avenue Victor Hugo', '+33478123456', '2019-03-22', 'bakery'),
        ('BAK003', 'La Mie Dorée', bakery_id, regions[2][0], '12 Rue de la République', '+33491234567', '2017-11-08', 'bakery'),
        ('BAK004', 'Aux Délices du Pain', bakery_id, regions[3][0], '78 Rue Alsace-Lorraine', '+33561234567', '2020-02-15', 'bakery'),
        ('BAK005', 'Maison du Boulanger', bakery_id, regions[4][0], '34 Avenue Jean Médecin', '+33493456789', '2019-08-30', 'bakery'),
        
        # Coffee shops
        ('COF001', 'Café Express', coffee_id, regions[0][0], '78 Boulevard Haussmann', '+33142567890', '2020-01-15', 'coffee_shop'),
        ('COF002', 'Le Petit Café', coffee_id, regions[1][0], '34 Rue Garibaldi', '+33472345678', '2019-07-19', 'coffee_shop'),
        ('COF003', 'Arômes & Saveurs', coffee_id, regions[2][0], '56 La Canebière', '+33496789012', '2021-02-28', 'coffee_shop'),
        ('COF004', 'Café de la Place', coffee_id, regions[3][0], '22 Place du Capitole', '+33567890123', '2018-11-05', 'coffee_shop'),
        ('COF005', 'Le Café Azur', coffee_id, regions[4][0], '15 Promenade des Anglais', '+33498765432', '2021-04-10', 'coffee_shop')
    ]
    
    # Insert stores with ON CONFLICT DO NOTHING to avoid duplicates
    for store in stores:
        cursor.execute(
            """INSERT INTO Store 
               (store_id, store_name, store_category_id, region_id, address, phone, opening_date, data_source) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (store_id) DO NOTHING""",
            store
        )
    
    print(f"Populated data for {len(stores)} stores")
    return store_categories, regions, stores

# Ensure the function is explicitly exposed at the module level
# This helps with module imports in some Python environments
__all__ = ['populate_store_data']

# Make sure to provide a global variable to capture the return values
store_categories = None
regions = None
stores = None

# Add this to enable running the script directly
if __name__ == "__main__":
    # Connection parameters
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', '5432'))
    dbname = os.environ.get('DB_NAME', 'OntoDb')
    user = os.environ.get('DB_USER', 'ontodb')
    password = os.environ.get('DB_PASSWORD', 'admin')
    
    print(f"Running populate_store_data script with connection: {host}:{port} {dbname}")
    
    # Connect to the database
    conn = psycopg2.connect(
        host=host,
        port=port,
        dbname=dbname,
        user=user,
        password=password
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    try:
        # Run the function and save results to global variables
        store_categories, regions, stores = populate_store_data(cursor)
        print("Store data population complete!")
        print(f"Populated: {len(store_categories)} categories, {len(regions)} regions, {len(stores)} stores")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()
