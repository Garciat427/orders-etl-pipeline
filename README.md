# Related Items Pipeline

A complete Python-based data pipeline for analyzing Shopify order data and generating product recommendations based on co-purchase patterns.

## 🏗️ Project Overview

This pipeline processes historical Shopify order data to identify which products are frequently purchased together, generating confidence scores for product recommendations. The system uses Apache Airflow for orchestration and PostgreSQL for data storage.

## 📁 Project Structure

```
related-items-pipeline/
├── dags/                          # Airflow DAGs
│   └── related_items_dag.py      # Main pipeline DAG
├── src/                          # Python scripts (ETL logic)
│   ├── extract.py                # Reads CSV and groups items by order
│   ├── load.py                   # Inserts data into Postgres
│   ├── transform.py              # Builds item association matrix
│   └── recommend.py              # Outputs JSON and writes to Postgres
├── db/                           # Database schema
│   └── init.sql                  # SQL file for schema initialization
├── data/                         # Data files
│   ├── orders.csv                # Sample Shopify export file
│   └── related_items.json        # Generated recommendations (output)
├── docker-compose.yml            # Local dev setup (Postgres + Airflow)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

## 🐳 Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ (for local development)

### 1. Start Services

```bash
cd related-items-pipeline
docker-compose up -d
```

This will start:
- **PostgreSQL** on port 5432
- **Airflow** on port 8080

### 2. Access Airflow UI

- Open your browser and go to: http://localhost:8080
- Login with: `admin` / `admin`
- You should see the `related_items_pipeline` DAG

### 3. Run the Pipeline

1. In the Airflow UI, find the `related_items_pipeline` DAG
2. Click the "Play" button to trigger it manually
3. Monitor the execution in the DAG view

## 🔧 Local Development Setup

### Install Dependencies

```bash
cd related-items-pipeline
pip install -r requirements.txt
```

### Database Connection

The scripts use this default connection string:
```
postgresql://airflow:airflow@localhost:5432/airflow
```

### Run Scripts Individually

You can test each component separately:

```bash
# Extract data from CSV
python src/extract.py

# Load data into database
python src/load.py

# Transform data and generate associations
python src/transform.py

# Export recommendations
python src/recommend.py
```

## 📊 Database Schema

The pipeline creates and uses these tables:

### `orders`
- `id` (SERIAL PRIMARY KEY)
- `order_number` (VARCHAR, UNIQUE)
- `created_at` (TIMESTAMP)

### `items`
- `id` (SERIAL PRIMARY KEY)
- `sku` (VARCHAR, UNIQUE)
- `name` (TEXT)
- `created_at` (TIMESTAMP)

### `order_items`
- `id` (SERIAL PRIMARY KEY)
- `order_id` (INTEGER, FOREIGN KEY)
- `item_id` (INTEGER, FOREIGN KEY)
- `quantity` (INTEGER)
- `created_at` (TIMESTAMP)

### `related_items`
- `id` (SERIAL PRIMARY KEY)
- `base_sku` (VARCHAR, FOREIGN KEY)
- `related_sku` (VARCHAR, FOREIGN KEY)
- `confidence` (DECIMAL(5,4))
- `created_at` (TIMESTAMP)

## 🔄 Pipeline Flow

The pipeline consists of 4 main tasks:

1. **Extract CSV Data** (`extract_csv_data`)
   - Reads `data/orders.csv`
   - Groups items by order number
   - Outputs structured order data

2. **Load to PostgreSQL** (`load_to_postgres`)
   - Creates database tables if they don't exist
   - Inserts orders, items, and order_items
   - Prevents duplicates using ON CONFLICT

3. **Generate Matrix** (`generate_matrix`)
   - Builds co-occurrence matrix from order data
   - Calculates confidence scores: P(B|A) = co-occurrence(A,B) / count(A)
   - Returns top related items per base SKU

4. **Export Results** (`export_results`)
   - Saves recommendations as `data/related_items.json`
   - Clears and inserts into `related_items` table

## 📈 Understanding the Results

### Confidence Scores

The confidence score represents the probability that a customer will buy the related item given they bought the base item:

```
Confidence(A → B) = P(B | A) = Count(A and B together) / Count(A)
```

### Example Output

```json
{
  "DT-MiniMaxx-V2": [
    ["DPSS-FOR-11", 0.86],
    ["EGR-FOR-11", 0.71]
  ],
  "DPSS-FOR-11": [
    ["DT-MiniMaxx-V2", 0.83],
    ["EGR-FOR-11", 0.67]
  ]
}
```

This means:
- 86% of customers who buy "DT-MiniMaxx-V2" also buy "DPSS-FOR-11"
- 71% of customers who buy "DT-MiniMaxx-V2" also buy "EGR-FOR-11"

## 🗃️ Database Queries

### View All Recommendations

```sql
SELECT * FROM related_items ORDER BY base_sku, confidence DESC;
```

### Get Recommendations for Specific Item

```sql
SELECT * FROM related_items WHERE base_sku = 'DT-MiniMaxx-V2';
```

### Top Recommendations by Confidence

```sql
SELECT base_sku, related_sku, confidence 
FROM related_items 
ORDER BY confidence DESC 
LIMIT 10;
```

## 🚀 Customization

### Add New Data Sources

1. Modify `extract.py` to handle different file formats
2. Update the extraction logic in the DAG
3. Ensure data structure matches expected format

### Modify Recommendation Algorithm

1. Edit `transform.py` to change confidence calculation
2. Add support for additional metrics (lift, support, etc.)
3. Implement different association rules

### Change Database

1. Update connection strings in all scripts
2. Modify `init.sql` for your database system
3. Update SQLAlchemy engine configuration

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Ensure PostgreSQL is running: `docker-compose ps`
   - Check connection string in scripts
   - Verify database credentials

2. **DAG Not Appearing in Airflow**
   - Check DAG file syntax
   - Restart Airflow webserver
   - Verify file permissions

3. **Import Errors**
   - Ensure `src/` directory is in Python path
   - Check all dependencies are installed
   - Verify import statements

### Logs

- **Airflow logs**: Available in the Airflow UI under each task
- **Docker logs**: `docker-compose logs airflow-webserver`
- **Database logs**: `docker-compose logs postgres`

## 📝 Sample Data

The included `orders.csv` contains sample Shopify order data with:
- 10 orders
- 5 unique products
- Various quantities and combinations

You can replace this with your actual Shopify export data.

## 🔒 Security Notes

- Default credentials are for local development only
- Change passwords in production
- Consider using environment variables for sensitive data
- Implement proper access controls for production databases

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review Airflow and PostgreSQL logs
3. Open an issue in the repository
4. Check Airflow and SQLAlchemy documentation
