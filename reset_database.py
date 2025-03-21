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

def reset_database():
    """Reset the PostgreSQL database by recreating containers"""
    print("Resetting PostgreSQL database...")
    
    # Change to the config directory
    compose_file = os.path.join('config', 'docker-compose.yml')
    
    # Check if compose file exists
    if not os.path.exists(compose_file):
        print(f"Error: Docker Compose file not found at: {compose_file}")
        return False
    
    # Stop and remove containers
    try:
        print("Stopping existing containers...")
        subprocess.run(
            ['docker-compose', '-f', compose_file, 'down'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Remove the volume to ensure clean state
        print("Removing database volume...")
        subprocess.run(
            ['docker', 'volume', 'rm', 'config_postgres_data'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Restart containers
        print("Starting containers with clean database...")
        result = subprocess.run(
            ['docker-compose', '-f', compose_file, 'up', '-d', 'postgres'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error starting database: {result.stderr}")
            return False
        
        print("Database container started successfully with clean state!")
        return True
    except Exception as e:
        print(f"Error executing docker commands: {str(e)}")
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
    
    # Confirm reset
    response = input("This will reset your database and DELETE ALL DATA. Continue? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Reset the database
    if not reset_database():
        return
    
    # Wait for the database to be ready
    if not wait_for_db(host='localhost', dbname='OntoDb', user='ontodb', password='admin'):
        return
    
    print("\n===== Database has been reset! =====")
    print("\nYou can now run your scripts:")
    print("- python src/scripts/load_data.py")
    print("- python src/scripts/run_queries.py")

if __name__ == "__main__":
    main()
