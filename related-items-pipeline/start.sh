#!/bin/bash

echo "🚀 Starting Related Items Pipeline Services..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it and try again."
    exit 1
fi

echo "✅ Docker and docker-compose are available"
echo ""

# Start services
echo "🐳 Starting PostgreSQL and Airflow..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."

# Wait for PostgreSQL to be ready
echo "   Waiting for PostgreSQL..."
until docker-compose exec -T postgres pg_isready -U airflow > /dev/null 2>&1; do
    sleep 2
done
echo "   ✅ PostgreSQL is ready"

# Wait for Airflow to be ready
echo "   Waiting for Airflow..."
until curl -s http://localhost:8080/health > /dev/null 2>&1; do
    sleep 5
done
echo "   ✅ Airflow is ready"

echo ""
echo "🎉 Services are running!"
echo ""
echo "📊 Access Points:"
echo "   - Airflow UI: http://localhost:8080"
echo "   - PostgreSQL: localhost:5432"
echo ""
echo "🔑 Default Credentials:"
echo "   - Airflow: admin / admin"
echo "   - PostgreSQL: airflow / airflow"
echo ""
echo "📁 Project Structure:"
echo "   - DAGs: ./dags/"
echo "   - Source Code: ./src/"
echo "   - Data: ./data/"
echo "   - Database Schema: ./db/"
echo ""
echo "🧪 To test the pipeline:"
echo "   1. Open http://localhost:8080 in your browser"
echo "   2. Login with admin/admin"
echo "   3. Find 'related_items_pipeline' DAG"
echo "   4. Click the play button to trigger it"
echo ""
echo "🔧 To run individual components:"
echo "   python src/extract.py      # Extract CSV data"
echo "   python src/load.py         # Load to database"
echo "   python src/transform.py    # Generate associations"
echo "   python src/recommend.py    # Export results"
echo ""
echo "🧪 To run full pipeline test:"
echo "   python test_pipeline.py"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo ""
echo "📖 For more information, see README.md"
