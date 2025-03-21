import pandas as pd
import random
import psycopg2
import os
import sys

def populate_product_data(cursor):
    """Populate Product, ProductCategory, ProductType and Currency tables"""
    print("Populating product data...")
    
    currencies = [
        ('EUR', 'Euro', '€'),
        ('USD', 'US Dollar', '$')
    ]
    
    for code, name, symbol in currencies:
        cursor.execute(
            "INSERT INTO Currency (currency_code, currency_name, symbol) VALUES (%s, %s, %s) ON CONFLICT (currency_code) DO NOTHING",
            (code, name, symbol)
        )
    
    cursor.execute("SELECT currency_id FROM Currency WHERE currency_code = 'EUR'")
    eur_currency_id = cursor.fetchone()[0]
    
    categories = [
        ('Pastry', 'Sweet and savory pastry products'),
        ('Bread', 'Traditional and artisanal breads'),
        ('Coffee', 'Coffee beverages and espresso-based drinks'),
        ('Tea', 'Hot and cold tea beverages'),
        ('Sandwich', 'Fresh made sandwiches'),
        ('Cake', 'Cakes and desserts')
    ]
    
    for name, description in categories:
        cursor.execute(
            "INSERT INTO ProductCategory (category_name, description) VALUES (%s, %s) ON CONFLICT (category_name) DO NOTHING",
            (name, description)
        )
    
    cursor.execute("SELECT category_id, category_name FROM ProductCategory")
    product_categories = {name: cat_id for cat_id, name in cursor.fetchall()}
    
    product_types = {
        product_categories['Pastry']: [
            ('Croissant', 'Traditional French breakfast pastry with a buttery, flaky texture'),
            ('Pain au Chocolat', 'Chocolate-filled pastry made with the same dough as croissants'),
            ('Eclair', 'Oblong pastry filled with cream and topped with chocolate icing'),
            ('Danish', 'Sweet pastry made with multiple layers of butter and dough')
        ],
        product_categories['Bread']: [
            ('Baguette', 'Traditional French bread with a crisp crust and chewy interior'),
            ('Sourdough', 'Naturally leavened bread with a slightly tangy flavor'),
            ('Brioche', 'Enriched bread with eggs and butter for a soft, tender crumb'),
            ('Rye Bread', 'Hearty bread made with rye flour')
        ],
        product_categories['Coffee']: [
            ('Espresso', 'Concentrated coffee brewed by forcing hot water through finely-ground coffee beans'),
            ('Cappuccino', 'Coffee beverage with espresso, steamed milk, and milk foam'),
            ('Latte', 'Coffee with espresso and a generous amount of steamed milk'),
            ('Filter Coffee', 'Coffee brewed by passing hot water through ground coffee in a filter')
        ],
        product_categories['Tea']: [
            ('Green Tea', 'Unoxidized tea leaves with a fresh, grassy flavor'),
            ('Black Tea', 'Fully oxidized tea leaves with a robust flavor'),
            ('Herbal Infusion', 'Non-tea herbal blends with various flavors and properties'),
            ('Chai Tea', 'Spiced tea blend with various aromatic spices')
        ],
        product_categories['Sandwich']: [
            ('Ham & Cheese', 'Classic sandwich with ham and cheese on French bread'),
            ('Vegetarian', 'Plant-based sandwich with fresh vegetables and spreads'),
            ('Chicken', 'Poultry-based sandwich with various toppings'),
            ('Tuna', 'Tuna salad sandwich with mayonnaise and vegetables')
        ],
        product_categories['Cake']: [
            ('Chocolate', 'Rich cake with chocolate flavoring and frosting'),
            ('Fruit', 'Cake with fruit elements, either baked in or as topping'),
            ('Cheesecake', 'Cream cheese-based dessert with a graham cracker crust'),
            ('Opera', 'French layered cake with coffee and chocolate flavors')
        ]
    }
    
    # Insert product types
    for category_id, types in product_types.items():
        for type_name, description in types:
            cursor.execute(
                """INSERT INTO ProductType 
                   (type_name, category_id, description) 
                   VALUES (%s, %s, %s) 
                   ON CONFLICT (type_name, category_id) DO NOTHING""",
                (type_name, category_id, description)
            )
    
    # Get product type IDs
    cursor.execute("""
        SELECT t.type_id, t.type_name, c.category_name 
        FROM ProductType t 
        JOIN ProductCategory c ON t.category_id = c.category_id
    """)
    db_product_types = cursor.fetchall()
    
    # Generate some sample products
    products = []
    
    # For bakery products
    for i, (type_id, type_name, category_name) in enumerate(
        [t for t in db_product_types if t[2] in ['Pastry', 'Bread', 'Sandwich', 'Cake']]
    ):
        for j in range(1, 4):  # 3 products per type
            product_id = f"B{i*3+j:03d}"
            detail = f"{type_name} Variety {j}"
            price = round(random.uniform(1.5, 8.0), 2)
            
            products.append((
                product_id,
                f"{type_name}: {detail}",
                type_id,
                detail,
                price,
                eur_currency_id,
                random.choice([True, False]) if random.random() < 0.2 else False,  # 20% chance of seasonal
                True,
                'bakery'
            ))
    
    # For coffee shop products
    for i, (type_id, type_name, category_name) in enumerate(
        [t for t in db_product_types if t[2] in ['Coffee', 'Tea']]
    ):
        sizes = ['Small', 'Regular', 'Large'] if category_name in ['Coffee', 'Tea'] else ['']
        
        for j, size in enumerate(sizes):
            product_id = f"C{i*3+j+1:03d}"
            detail = f"{size} {type_name}" if size else type_name
            # Price increases with size
            base_price = random.uniform(2.0, 3.5)
            price = round(base_price * (1 + j * 0.25), 2)  # 25% price increase per size
            
            products.append((
                product_id,
                f"{type_name}: {detail}",
                type_id,
                detail,
                price,
                eur_currency_id,
                random.choice([True, False]) if random.random() < 0.2 else False,  # 20% chance of seasonal
                True,
                'coffee_shop'
            ))
    
    # Insert products
    for product in products:
        cursor.execute(
            """INSERT INTO Product 
               (product_id, product_name, type_id, detail, base_price, currency_id, is_seasonal, is_active, data_source)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (product_id) DO NOTHING""",
            product
        )
    
    print(f"Populated data for {len(products)} products")
    return currencies, product_categories, db_product_types, products

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
        populate_product_data(cursor)
        print("Product data population complete!")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        cursor.close()
        conn.close()
