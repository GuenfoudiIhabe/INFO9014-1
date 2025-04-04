# OntoDb Project

## Quick Start Guide

Follow these steps in order to set up and run the OntoDb project:

### Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Required Python packages: `psycopg2`, `pandas`, `tqdm`, `tabulate`

### Step 1: Setup the Database

Run the setup script to start the PostgreSQL database in Docker:

```bash
python setup_database.py
```

### Step 2: Populate the Database

Run the following scripts in this order:

```bash
# Option 1: Run all population scripts at once (recommended)
python src/scripts/data_population/run_population.py

# Option 2: Run individual population scripts
python src/scripts/data_population/populate_store_data.py
python src/scripts/data_population/populate_product_data.py
python src/scripts/data_population/populate_staff_data.py
python src/scripts/data_population/populate_transaction_data.py
```

### Step 3: Run Queries

Verify the database and run analytical queries:

```bash
python src/scripts/run_queries.py
```

## Connection Details

If needed, here are the default database connection parameters:
- Host: localhost
- Port: 5432
- Database: OntoDb
- Username: ontodb
- Password: admin

## Docker Environment

If running in a Docker environment, use 'postgres' as the host instead of 'localhost'.

