#!/usr/bin/env python3
import random
from datetime import datetime, timedelta
import psycopg2
import os
import sys

def populate_staff_data(cursor, stores):
    """Populate Staff, StaffRole and Shift tables"""
    print("Populating staff data...")
    
    french_first_names = [
        "Alexandre", "Antoine", "Aurélie", "Camille", "Charlotte", "Claire", "Emma", "Etienne", 
        "François", "Gabriel", "Hugo", "Isabelle", "Jean", "Julien", "Léa", "Lucas", "Lucie", 
        "Marie", "Mathieu", "Nathalie", "Nicolas", "Olivier", "Philippe", "Pierre", "Sophie", 
        "Sylvie", "Théo", "Thomas", "Valentine", "Zoé"
    ]
    
    french_last_names = [
        "Bernard", "Blanc", "Bonnet", "Boucher", "Caron", "Charpentier", "Chevalier", "Dubois", 
        "Dupont", "Durand", "Fabre", "Fontaine", "Fournier", "Garnier", "Girard", "Laurent", 
        "Lefebvre", "Leroy", "Martin", "Mercier", "Michel", "Moreau", "Petit", "Richard", 
        "Robert", "Roux", "Simon", "Thomas", "Vincent", "Lambert"
    ]
    
    roles = [
        ('Cashier', 12.50),
        ('Barista', 14.00),
        ('Baker', 15.50),
        ('Manager', 20.00),
        ('Assistant Manager', 18.00)
    ]
    
    for name, rate in roles:
        cursor.execute(
            "INSERT INTO StaffRole (role_name, hourly_rate) VALUES (%s, %s) ON CONFLICT (role_name) DO NOTHING",
            (name, rate)
        )
    
    # Get role IDs
    cursor.execute("SELECT role_id, role_name FROM StaffRole")
    role_ids = {name: role_id for role_id, name in cursor.fetchall()}
    
    # Track used names to avoid duplicates
    used_names = set()
    
    # Create staff for each store
    staff_members = []
    for store_id, store_name, category_id, region_id, *_ in stores:
        # Determine mix of staff based on store category
        if 'BAK' in store_id:  # Bakery
            role_distribution = {
                'Cashier': random.randint(2, 3),
                'Baker': random.randint(2, 4),
                'Manager': 1
            }
        else:  # Coffee shop
            role_distribution = {
                'Cashier': random.randint(1, 2),
                'Barista': random.randint(2, 4),
                'Manager': 1,
                'Assistant Manager': random.randint(0, 1)
            }
        
        # Generate a unique name function
        def generate_unique_name():
            while True:
                first_name = random.choice(french_first_names)
                last_name = random.choice(french_last_names)
                name_pair = (first_name, last_name)
                if name_pair not in used_names:
                    used_names.add(name_pair)
                    return first_name, last_name
        
        # Create staff with the determined distribution
        for role, count in role_distribution.items():
            for _ in range(count):
                first_name, last_name = generate_unique_name()
                
                # Random hire date between store opening (let's assume 2 years ago for all) and now
                hire_date = datetime.now() - timedelta(days=random.randint(30, 730))
                hire_date_str = hire_date.strftime("%Y-%m-%d")
                
                staff_members.append((
                    first_name,
                    last_name,
                    role_ids[role],
                    store_id,
                    hire_date_str
                ))
    
    # Insert staff
    for staff in staff_members:
        cursor.execute(
            """INSERT INTO Staff 
               (first_name, last_name, role_id, store_id, hire_date)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING staff_id""",
            staff
        )
        
        staff_id = cursor.fetchone()[0]
        
        # Generate shifts for the past week for each staff member
        today = datetime.now().date()
        for day_offset in range(7):
            shift_date = (today - timedelta(days=day_offset)).strftime("%Y-%m-%d")
            
            # Not every staff works every day
            if random.random() < 0.7:  # 70% chance of working
                # Coffee shops and bakeries typically open early
                start_hour = random.randint(6, 10)
                shift_duration = random.randint(6, 9)  # 6-9 hour shifts
                
                start_time = f"{start_hour:02d}:00:00"
                end_time = f"{(start_hour + shift_duration):02d}:00:00"
                
                cursor.execute(
                    """INSERT INTO Shift
                       (staff_id, store_id, shift_date, start_time, end_time)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (staff_id, staff[3], shift_date, start_time, end_time)
                )
    
    print(f"Populated data for {len(staff_members)} staff members with shifts")
    return roles, staff_members

# Add this to enable running the script directly
if __name__ == "__main__":
    # Connection parameters
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', '5432'))
    dbname = os.environ.get('DB_NAME', 'OntoDb')
    user = os.environ.get('DB_USER', 'ontodb')
    password = os.environ.get('DB_PASSWORD', 'admin')
    
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
        # First get store data
        cursor.execute("SELECT store_id, store_name, store_category_id, region_id, address, phone, opening_date, data_source FROM Store")
        stores = cursor.fetchall()
        
        if not stores:
            print("No stores found in database. Please run populate_store_data.py first.")
            sys.exit(1)
            
        populate_staff_data(cursor, stores)
        print("Staff data population complete!")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
