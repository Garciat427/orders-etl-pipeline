"""
Airflow DAG for Shopify orders data pipeline.
Processes orders data and generates product recommendations.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import sys
import os

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from extract import extract_orders_from_csv
from load import DatabaseLoader
from transform import ItemAssociationTransformer
from recommend import RecommendationExporter


# Default arguments for the DAG
default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Define the DAG
dag = DAG(
    'related_items_pipeline',
    default_args=default_args,
    description='Process Shopify orders and generate product recommendations',
    schedule_interval=None,  # Manual trigger only
    catchup=False,
    tags=['shopify', 'recommendations', 'etl'],
)


def extract_csv_data(**context):
    """Extract data from CSV file."""
    csv_path = os.path.join(
        os.path.dirname(__file__), '..', 'data', 'ordersData.csv'
    )
    
    orders_data = extract_orders_from_csv(csv_path)
    
    if not orders_data:
        raise ValueError("No data extracted from CSV")
    
    # Store data in XCom for next task
    context['task_instance'].xcom_push(
        key='orders_data',
        value=orders_data
    )
    
    return f"Extracted {len(orders_data)} orders with items"


def load_to_postgres(**context):
    """Load extracted data into PostgreSQL."""
    # Get data from previous task
    orders_data = context['task_instance'].xcom_pull(
        task_ids='extract_csv_data',
        key='orders_data'
    )
    
    if not orders_data:
        raise ValueError("No orders data received from extract task")
    
    # Load data into database
    loader = DatabaseLoader()
    loader.create_tables_if_not_exist()
    loader.load_orders_data(orders_data)
    loader.close()
    
    return f"Loaded {len(orders_data)} orders into PostgreSQL"


def generate_matrix(**context):
    """Generate item association matrix and confidence scores."""
    # Generate recommendations
    transformer = ItemAssociationTransformer()
    confidence_scores = transformer.transform_data()
    transformer.close()
    
    if not confidence_scores:
        raise ValueError("No confidence scores generated")
    
    # Store results in XCom for next task
    context['task_instance'].xcom_push(
        key='confidence_scores',
        value=confidence_scores
    )
    
    total_associations = sum(len(related) for related in confidence_scores.values())
    return f"Generated {total_associations} item associations for {len(confidence_scores)} items"


def export_results(**context):
    """Export recommendations to JSON and PostgreSQL."""
    try:
        # Get data from previous task
        confidence_scores = context['task_instance'].xcom_pull(
            task_ids='generate_matrix',
            key='confidence_scores'
        )
        
        if not confidence_scores:
            raise ValueError("No confidence scores received from transform task")
        
        # Export recommendations
        exporter = RecommendationExporter()
        json_path = exporter.export_recommendations(confidence_scores)
        exporter.close()
        
        # Force a simple return value
        result = f"Exported recommendations to {json_path} and PostgreSQL"
        print(f"Task completed successfully: {result}")
        return result
        
    except Exception as e:
        error_msg = f"Error in export_results: {str(e)}"
        print(error_msg)
        raise Exception(error_msg)


# Define tasks
extract_task = PythonOperator(
    task_id='extract_csv_data',
    python_callable=extract_csv_data,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_postgres',
    python_callable=load_to_postgres,
    dag=dag,
)

transform_task = PythonOperator(
    task_id='generate_matrix',
    python_callable=generate_matrix,
    dag=dag,
)

export_task = PythonOperator(
    task_id='export_results',
    python_callable=export_results,
    dag=dag,
)

# Define task dependencies
extract_task >> load_task >> transform_task >> export_task
