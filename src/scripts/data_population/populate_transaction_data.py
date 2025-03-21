#!/usr/bin/env python3
import random
from datetime import datetime, timedelta
from tqdm import tqdm
import psycopg2
import os
import sys

def populate_transaction_data(cursor, stores, products):
    """Populate Transaction, TransactionItem and PaymentMethod tables"""
    print("Populating transaction data...")
    
    # Ensure payment methods exist
    payment_methods = [
        ('Cash', 'Physical currency'),
        ('Credit Card', 'Visa, MasterCard, Amex, etc.'),
        ('Debit Card', 'Bank cards that deduct directly from accounts'),
        ('Mobile Payment', 'Apple Pay, Google Pay, etc.')
    ]
    
    for name, description in payment_methods:
        cursor.execute(
            "INSERT INTO PaymentMethod (method_name, description) VALUES (%s, %s) ON CONFLICT (method_name) DO NOTHING",
            (name, description)
        )
    
    # Get payment method IDs
    cursor.execute("SELECT payment_method_id, method_name FROM PaymentMethod")
    payment_method_ids = {name: pm_id for pm_id, name in cursor.fetchall()}
    
    # Get EUR currency ID
    cursor.execute("SELECT currency_id FROM Currency WHERE currency_code = 'EUR'")
    eur_currency_id = cursor.fetchone()[0]
    
    # Group products by data source
    bakery_products = [p for p in products if p[8] == 'bakery']
    coffee_products = [p for p in products if p[8] == 'coffee_shop']
    
    # Get staff for each store
    store_staff = {}
    for store_id, *_ in stores:
        cursor.execute("SELECT staff_id FROM Staff WHERE store_id = %s", (store_id,))
        staff = [s[0] for s in cursor.fetchall()]
        if staff:
            store_staff[store_id] = staff
    
    # Generate transactions
    transactions = []
    transaction_items = []
    
    # Dates for the past month
    today = datetime.now().date()
    dates = [(today - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(30)]
    
    # Transaction count total to show a progress bar
    total_transactions = sum(100 if 'BAK' in store[0] else 150 for store in stores)
    
    with tqdm(total=total_transactions, desc="Generating transactions") as pbar:
        for store_id, store_name, category_id, *_ in stores:
            # Each store gets different number of transactions based on type
            num_transactions = 100 if 'BAK' in store_id else 150
            
            # Products relevant to this store
            relevant_products = bakery_products if 'BAK' in store_id else coffee_products
            
            # Staff for this store
            staff = store_staff.get(store_id, [])
            if not staff:
                continue  # Skip if no staff
            
            for i in range(num_transactions):
                transaction_id = f"{'B' if 'BAK' in store_id else 'C'}TX{len(transactions) + 1:05d}"
                transaction_date = random.choice(dates)
                
                # Time distribution based on business hours
                hour_weights = [1] * 24  # Initialize weights
                # Bakeries are busier in morning, coffee shops throughout day
                for h in range(24):
                    if 'BAK' in store_id:
                        if 6 <= h <= 10:  # Morning rush for bakeries
                            hour_weights[h] = 10
                        elif 11 <= h <= 14:  # Lunch
                            hour_weights[h] = 7
                        elif h < 6 or h > 19:  # Closed hours
                            hour_weights[h] = 0
                    else:  # Coffee shop
                        if 7 <= h <= 11:  # Morning coffee
                            hour_weights[h] = 9
                        elif 12 <= h <= 15:  # Lunch hour
                            hour_weights[h] = 7
                        elif 16 <= h <= 18:  # Afternoon
                            hour_weights[h] = 5
                        elif h < 6 or h > 20:  # Closed hours
                            hour_weights[h] = 0
                
                # Select hour based on weights
                hour = random.choices(range(24), weights=hour_weights)[0]
                minute = random.randint(0, 59)
                second = random.randint(0, 59)
                transaction_time = f"{hour:02d}:{minute:02d}:{second:02d}"
                
                payment_method_id = random.choices(
                    list(payment_method_ids.values()),
                    weights=[0.35, 0.30, 0.25, 0.10]  # Cash more common in bakery/cafe
                )[0]
                
                staff_id = random.choice(staff)
                
                # Each transaction has 1-4 items
                num_items = random.choices([1, 2, 3, 4], weights=[0.4, 0.3, 0.2, 0.1])[0]
                transaction_products = random.sample(relevant_products, min(num_items, len(relevant_products)))
                
                total_amount = 0
                transaction_items_batch = []
                
                for j, product in enumerate(transaction_products):
                    product_id, _, _, _, base_price, *_ = product
                    
                    # Convert base_price to float to avoid decimal.Decimal incompatibility
                    base_price = float(base_price)
                    
                    quantity = random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]
                    
                    # Apply discount sometimes
                    discount_percent = 0.0
                    if random.random() < 0.1:  # 10% chance of discount
                        discount_percent = random.choice([5.0, 10.0, 15.0])
                    
                    # Calculate item total
                    item_price = base_price * (1 - discount_percent / 100)
                    item_total = round(item_price * quantity, 2)
                    total_amount += item_total
                    
                    sale_id = f"{transaction_id}_{j+1}"
                    
                    transaction_items_batch.append((
                        transaction_id,
                        product_id,
                        quantity,
                        base_price,
                        discount_percent,
                        item_total,
                        sale_id
                    ))
                
                # Add transaction with its total
                transactions.append((
                    transaction_id,
                    store_id,
                    transaction_date,
                    transaction_time,
                    payment_method_id,
                    staff_id,
                    round(total_amount, 2),
                    eur_currency_id,
                    'bakery' if 'BAK' in store_id else 'coffee_shop'
                ))
                
                # Extend transaction_items list
                transaction_items.extend(transaction_items_batch)
                
                pbar.update(1)
    
    # Batch insert transactions
    print(f"Inserting {len(transactions)} transactions")
    for transaction in tqdm(transactions, desc="Inserting transactions"):
        cursor.execute(
            """INSERT INTO Transaction
               (transaction_id, store_id, transaction_date, transaction_time, 
                payment_method_id, staff_id, total_amount, currency_id, data_source)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (transaction_id) DO NOTHING""",
            transaction
        )
    
    # Batch insert transaction items
    print(f"Inserting {len(transaction_items)} transaction items")
    for item in tqdm(transaction_items, desc="Inserting transaction items"):
        cursor.execute(
            """INSERT INTO TransactionItem
               (transaction_id, product_id, quantity, unit_price, discount_percent, item_total, sale_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (sale_id) DO NOTHING""",
            item
        )
    
    print(f"Populated data for {len(transactions)} transactions with {len(transaction_items)} items")
    return payment_methods, transactions, transaction_items

if __name__ == "__main__":
    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', '5432'))
    dbname = os.environ.get('DB_NAME', 'OntoDb')
    user = os.environ.get('DB_USER', 'ontodb')
    password = os.environ.get('DB_PASSWORD', 'admin')
    
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
        cursor.execute("SELECT store_id, store_name, store_category_id, region_id, address, phone, opening_date, data_source FROM Store")
        stores = cursor.fetchall()
        
        if not stores:
            print("No stores found in database. Please run populate_store_data.py first.")
            sys.exit(1)
            
        cursor.execute("""
            SELECT product_id, product_name, type_id, detail, base_price, 
                   currency_id, is_seasonal, is_active, data_source 
            FROM Product
        """)
        products = cursor.fetchall()
        
        if not products:
            print("No products found in database. Please run populate_product_data.py first.")
            sys.exit(1)
            
        populate_transaction_data(cursor, stores, products)
        print("Transaction data population complete!")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
