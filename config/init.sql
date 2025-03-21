
CREATE TABLE IF NOT EXISTS StoreCategory (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS StoreRegion (
    region_id SERIAL PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    country VARCHAR(50) DEFAULT 'France'
);

CREATE TABLE IF NOT EXISTS Store (
    store_id VARCHAR(50) PRIMARY KEY,
    store_name VARCHAR(100) NOT NULL,
    store_category_id INT NOT NULL,
    region_id INT NOT NULL,
    address VARCHAR(255),
    phone VARCHAR(20),
    opening_date DATE,
    data_source VARCHAR(50) NOT NULL, -- 'bakery' or 'coffee_shop'
    FOREIGN KEY (store_category_id) REFERENCES StoreCategory(category_id),
    FOREIGN KEY (region_id) REFERENCES StoreRegion(region_id)
);

-- Product hierarchies
CREATE TABLE IF NOT EXISTS ProductCategory (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS ProductType (
    type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    category_id INT NOT NULL,
    description TEXT,
    FOREIGN KEY (category_id) REFERENCES ProductCategory(category_id),
    UNIQUE (type_name, category_id)
);

CREATE TABLE IF NOT EXISTS Currency (
    currency_id SERIAL PRIMARY KEY,
    currency_code CHAR(3) NOT NULL UNIQUE,
    currency_name VARCHAR(50) NOT NULL,
    symbol VARCHAR(5)
);

CREATE TABLE IF NOT EXISTS Product (
    product_id VARCHAR(50) PRIMARY KEY,
    product_name VARCHAR(255) NOT NULL,
    type_id INT NOT NULL,
    detail VARCHAR(255),
    base_price DECIMAL(10,2) NOT NULL,
    currency_id INT NOT NULL,
    is_seasonal BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    data_source VARCHAR(50) NOT NULL, -- 'bakery' or 'coffee_shop'
    FOREIGN KEY (type_id) REFERENCES ProductType(type_id),
    FOREIGN KEY (currency_id) REFERENCES Currency(currency_id)
);

-- Staff and shifts for a more complex model
CREATE TABLE IF NOT EXISTS StaffRole (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    hourly_rate DECIMAL(10,2) NOT NULL
);

CREATE TABLE IF NOT EXISTS Staff (
    staff_id SERIAL PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role_id INT NOT NULL,
    store_id VARCHAR(50) NOT NULL,
    hire_date DATE NOT NULL,
    FOREIGN KEY (role_id) REFERENCES StaffRole(role_id),
    FOREIGN KEY (store_id) REFERENCES Store(store_id)
);

CREATE TABLE IF NOT EXISTS Shift (
    shift_id SERIAL PRIMARY KEY,
    staff_id INT NOT NULL,
    store_id VARCHAR(50) NOT NULL,
    shift_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    FOREIGN KEY (staff_id) REFERENCES Staff(staff_id),
    FOREIGN KEY (store_id) REFERENCES Store(store_id)
);

-- Transaction-related tables
CREATE TABLE IF NOT EXISTS PaymentMethod (
    payment_method_id SERIAL PRIMARY KEY,
    method_name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

CREATE TABLE IF NOT EXISTS Transaction (
    transaction_id VARCHAR(50) PRIMARY KEY,
    store_id VARCHAR(50) NOT NULL,
    transaction_date DATE NOT NULL,
    transaction_time TIME NOT NULL,
    payment_method_id INT,
    staff_id INT,
    total_amount DECIMAL(10,2),
    currency_id INT,
    data_source VARCHAR(50) NOT NULL, -- 'bakery' or 'coffee_shop'
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (payment_method_id) REFERENCES PaymentMethod(payment_method_id),
    FOREIGN KEY (staff_id) REFERENCES Staff(staff_id),
    FOREIGN KEY (currency_id) REFERENCES Currency(currency_id)
);

CREATE TABLE IF NOT EXISTS TransactionItem (
    item_id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(50) NOT NULL,
    product_id VARCHAR(50) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0,
    item_total DECIMAL(10,2) NOT NULL,
    sale_id VARCHAR(50) UNIQUE, -- Preserve original sale_id for reference
    FOREIGN KEY (transaction_id) REFERENCES Transaction(transaction_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

-- Default data
INSERT INTO Currency (currency_code, currency_name, symbol) 
VALUES ('EUR', 'Euro', '€'), ('USD', 'US Dollar', '$')
ON CONFLICT (currency_code) DO NOTHING;

INSERT INTO StoreCategory (category_name, description)
VALUES ('Bakery', 'Traditional French bakery'),
       ('Coffee Shop', 'Modern coffee and pastry shop')
ON CONFLICT (category_name) DO NOTHING;

INSERT INTO ProductCategory (category_name)
VALUES ('Pastry'), ('Bread'), ('Coffee'), ('Tea'), ('Sandwich'), ('Cake')
ON CONFLICT (category_name) DO NOTHING;

INSERT INTO PaymentMethod (method_name)
VALUES ('Cash'), ('Credit Card'), ('Debit Card'), ('Mobile Payment')
ON CONFLICT (method_name) DO NOTHING;

INSERT INTO StoreRegion (region_name, country)
VALUES ('Paris', 'France'), ('Lyon', 'France'), ('Marseille', 'France')
ON CONFLICT DO NOTHING;

INSERT INTO StaffRole (role_name, hourly_rate)
VALUES ('Cashier', 12.50), ('Barista', 14.00), ('Baker', 15.50), ('Manager', 20.00)
ON CONFLICT (role_name) DO NOTHING;
