#!/bin/bash

echo "🚀 Initializing Airflow..."

# Initialize the database
echo "📊 Initializing Airflow database..."
airflow db init

# Create admin user
echo "👤 Creating admin user..."
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin

echo "✅ Airflow initialization complete!"
