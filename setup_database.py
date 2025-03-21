#!/usr/bin/env python3
import os
import sys
import subprocess
import time
import psycopg2

def check_docker_running():
    """Check if Docker is running on the system"""
    try:
        result = subprocess.run(['docker', 'info'], 
                               stdout=subprocess.PIPE, 
                               stderr=subprocess.PIPE,
                               text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def start_database():
    """Start the PostgreSQL database using Docker Compose"""
    print("Starting PostgreSQL database using Docker Compose...")
    
    # Change to the config directory
    compose_file = os.path.join('config', 'docker-compose.yml')
    
    # Check if compose file exists
    if not os.path.exists(compose_file):
        print(f"Error: Docker Compose file not found at: {compose_file}")
        return False
    
    # Run docker-compose up
    try:
        result = subprocess.run(
            ['docker-compose', '-f', compose_file, 'up', '-d', 'postgres'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error starting database: {result.stderr}")
            return False
        
        print("Database container started successfully!")
        return True
    except Exception as e:
        print(f"Error executing docker-compose: {str(e)}")
        return False

def wait_for_db(host, dbname, user, password, port=5432, max_attempts=30):
    """Wait for database to be available"""
    print(f"Waiting for PostgreSQL to be ready at {host}:{port}...")
    
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
            print(f"Successfully connected to database '{dbname}'")
            return True
        except psycopg2.OperationalError:
            print(f"Waiting for database... attempt {attempt}/{max_attempts}")
            time.sleep(3)
    
    print("Database connection failed after multiple attempts.")
    return False

def main():
    # Check if Docker is running
    if not check_docker_running():
        print("Error: Docker does not appear to be running.")
        print("Please start Docker and try again.")
        return
    
    # Start the database
    if not start_database():
        return
    
    # Wait for the database to be ready
    if not wait_for_db(host='localhost', dbname='OntoDb', user='ontodb', password='admin'):
        return
    
    print("\n===== Database is ready! =====")
    print("\nYou can now run your scripts:")
    print("- python src/scripts/load_data.py")
    print("- python src/scripts/run_queries.py")
    print("\nOr run the Docker application container:")
    print("docker-compose -f config/docker-compose.yml up app")

if __name__ == "__main__":
    main()
