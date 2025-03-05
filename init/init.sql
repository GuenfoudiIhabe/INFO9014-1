-- Initialize database structure for OntoDb

-- Create Product table
CREATE TABLE IF NOT EXISTS Product (
    product_id INT PRIMARY KEY,
    product_category VARCHAR(255) NOT NULL,  
    product_type VARCHAR(255),              
    product_detail VARCHAR(255),             
    unit_price DECIMAL(10,2) NOT NULL
);

-- Create Store table
CREATE TABLE IF NOT EXISTS Store (
    store_id INT PRIMARY KEY,
    store_location VARCHAR(255)
);

-- Create Transactions table
CREATE TABLE IF NOT EXISTS Transactions (
    sale_id INT PRIMARY KEY,
    transaction_id INT,
    transaction_date DATE,
    transaction_time TIME,
    transaction_qty INT,
    store_id INT,
    product_id INT,
    FOREIGN KEY (store_id) REFERENCES Store(store_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

-- Add comments to tables
COMMENT ON TABLE Product IS 'Products from both bakery and coffee shop';
COMMENT ON TABLE Store IS 'Store locations';
COMMENT ON TABLE Transactions IS 'All sales transactions';
