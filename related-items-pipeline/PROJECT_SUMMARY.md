# Related Items Pipeline - Project Summary

## 🎯 Project Overview
A complete Python-based data pipeline for analyzing Shopify order data and generating product recommendations based on co-purchase patterns.

## 📁 Complete File Structure

```
related-items-pipeline/
├── 📄 README.md                    # Comprehensive setup and usage guide
├── 📄 PROJECT_SUMMARY.md           # This file - project overview
├── 🐳 docker-compose.yml           # Local dev setup (Postgres + Airflow)
├── 📋 requirements.txt             # Python dependencies
├── ⚙️ config.py                    # Configuration settings
├── 🚀 start.sh                     # Startup script (executable)
├── 🧪 test_pipeline.py             # End-to-end pipeline testing
│
├── 📊 dags/                        # Airflow DAGs
│   └── related_items_dag.py       # Main pipeline orchestration
│
├── 🐍 src/                         # Python scripts (ETL logic)
│   ├── extract.py                  # Reads CSV and groups items by order
│   ├── load.py                     # Inserts data into Postgres
│   ├── transform.py                # Builds item association matrix
│   └── recommend.py                # Outputs JSON and writes to Postgres
│
├── 🗄️ db/                          # Database schema
│   └── init.sql                    # SQL file for schema initialization
│
└── 📁 data/                        # Data files
    ├── orders.csv                  # Sample Shopify export file
    └── related_items.json          # Generated recommendations (output)
```

## 🔧 Core Components

### 1. Data Pipeline Scripts (`src/`)
- **`extract.py`**: CSV reader that groups items by order number
- **`load.py`**: Database loader using SQLAlchemy with duplicate prevention
- **`transform.py`**: Co-occurrence matrix builder with confidence calculations
- **`recommend.py`**: Results exporter to JSON and PostgreSQL

### 2. Airflow Orchestration (`dags/`)
- **`related_items_dag.py`**: 4-task pipeline with proper dependencies
- **Tasks**: extract_csv_data → load_to_postgres → generate_matrix → export_results

### 3. Database Schema (`db/`)
- **`init.sql`**: Creates 4 tables with foreign keys and indexes
- **Tables**: orders, items, order_items, related_items
- **Features**: Cascade deletion, unique constraints, performance indexes

### 4. Infrastructure (`docker-compose.yml`)
- **PostgreSQL 13**: Database server on port 5432
- **Airflow 2.7.1**: Workflow orchestration on port 8080
- **SequentialExecutor**: Suitable for local development
- **Health checks**: Ensures services are ready before proceeding

## 🚀 Quick Start Commands

```bash
# 1. Start all services
cd related-items-pipeline
./start.sh

# 2. Access Airflow UI
# Open http://localhost:8080 (admin/admin)

# 3. Test individual components
python src/extract.py
python src/load.py
python src/transform.py
python src/recommend.py

# 4. Run full pipeline test
python test_pipeline.py

# 5. Stop services
docker-compose down
```

## 📊 Expected Output

### JSON Output (`data/related_items.json`)
```json
{
  "DT-MiniMaxx-V2": [
    ["DPSS-FOR-11", 0.86],
    ["EGR-FOR-11", 0.71]
  ]
}
```

### Database Query Results
```sql
SELECT * FROM related_items WHERE base_sku = 'DT-MiniMaxx-V2';
-- Returns confidence scores for related products
```

## 🎯 Key Features

✅ **Complete ETL Pipeline**: Extract → Transform → Load  
✅ **Airflow Orchestration**: Automated workflow management  
✅ **PostgreSQL Integration**: Robust data storage with constraints  
✅ **Co-purchase Analysis**: Confidence-based recommendations  
✅ **Docker Deployment**: Easy local development setup  
✅ **Comprehensive Testing**: End-to-end validation  
✅ **Production Ready**: Proper error handling and logging  
✅ **Extensible Design**: Easy to modify and extend  

## 🔍 Technical Details

- **Language**: Python 3.8+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Orchestration**: Apache Airflow
- **Containerization**: Docker & Docker Compose
- **Data Processing**: Pandas for CSV handling
- **Algorithm**: Co-occurrence matrix with confidence scoring
- **Output Formats**: JSON file + PostgreSQL table

## 🧪 Testing & Validation

The project includes:
- **Unit testing**: Each script can run independently
- **Integration testing**: `test_pipeline.py` validates the entire flow
- **Data validation**: Checks for data integrity and completeness
- **Error handling**: Comprehensive exception handling throughout

## 🚀 Production Considerations

- Change default credentials
- Use environment variables for sensitive data
- Implement proper logging and monitoring
- Consider scaling with CeleryExecutor
- Add data validation and quality checks
- Implement backup and recovery procedures

## 📚 Documentation

- **README.md**: Complete setup and usage guide
- **Code comments**: Inline documentation in all Python files
- **SQL comments**: Schema documentation in init.sql
- **Configuration**: Centralized settings in config.py

## 🎉 Ready to Use!

The pipeline is fully functional and ready for:
1. **Local development** and testing
2. **Learning** ETL pipeline concepts
3. **Production deployment** with modifications
4. **Customization** for different data sources
5. **Extension** with additional analytics

Simply run `./start.sh` and start exploring!
