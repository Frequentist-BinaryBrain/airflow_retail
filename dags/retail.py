from airflow.decorators import dag, task
from datetime import datetime, timedelta

from airflow.providers.google.cloud.transfers.local_to_gcs import LocalFilesystemToGCSOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateEmptyDatasetOperator

from astro import sql as aql
from astro.files import File
from airflow.models.baseoperator import chain
from astro.sql.table import Table, Metadata
from astro.constants import FileType
from include.dbt.cosmos_config import DBT_PROJECT_CONFIG, DBT_CONFIG
from cosmos.airflow.task_group import DbtTaskGroup
from cosmos.constants import LoadMode
from cosmos.config import ProjectConfig, RenderConfig

@dag(
    start_date=datetime(2023,1,1),
    schedule = None,
    catchup=False,
    tags=['retail'],
)

def retail():
    upload_csv_to_gcs = LocalFilesystemToGCSOperator(
        task_id="upload_csv_to_gcs",
        src='/usr/local/airflow/include/dataset/online_Retail.csv',
        dst='raw/online_Retail.csv', # this is path how our csv file gets saved in GCS
        bucket='datapineline_storage',
        gcp_conn_id='gcp',
        mime_type='text/csv'
    )
    
    # Create an empty Dataset (schema equivalent)
    create_retail_dataset = BigQueryCreateEmptyDatasetOperator(
        task_id = 'create_retail_dataset',
        dataset_id='retail',
        gcp_conn_id='gcp',
    )
    
    # Create the task to load the file into a BigQuery raw_invoices table
    gcs_to_raw = aql.load_file(
        task_id='gcs_to_raw',
        input_file=File(
            path = 'gs://datapineline_storage/raw/online_Retail.csv',
            conn_id='gcp',
            filetype=FileType.CSV,
            
        ),
        output_table=Table(
            name='raw_invoices',
            conn_id='gcp',
            metadata=Metadata(schema='retail')
        ),
        use_native_support=False,
    )
    
    # Isolation of Dependencies: When a task requires specific libraries or a Python version that is different from the one 
    # running in the Airflow worker, using @task.external_python helps isolate these dependencies.
    
    # In the Airflow DAG, when you use @task.external_python(python='/usr/local/airflow/soda_venv/bin/python'), 
    # you're telling Airflow to use the Python interpreter from the virtual environment (/usr/local/airflow/soda_venv/bin/python) 
    # inside the container.
    # This ensures that the task is executed with the specific dependencies installed in the virtual environment that was set up 
    # in the Docker container, like soda-core.
    
    @task.external_python(python='/usr/local/airflow/soda_venv/bin/python')
    def check_load(scan_name='check_load', checks_subpath='sources'):
        from include.soda.check_function import check

        return check(scan_name, checks_subpath)
    
    # Breakdown of the Path:
    # /usr/local/airflow: This is the base directory for the Airflow instance in your Docker container.
    # /usr/local/airflow/soda_venv/: This is the location where the virtual environment soda_venv was created.
    # /usr/local/airflow/soda_venv/bin/python: This is the Python executable inside the virtual environment, which will be used for running the task.
    
    
    #TO integrate dbt with airflow we will use COSMOS open source
    
    transform = DbtTaskGroup(
        group_id='transform', #name of the group
        project_config=DBT_PROJECT_CONFIG, #comes from the cosmos file
        profile_config=DBT_CONFIG, #comes from the cosmos file
        render_config=RenderConfig(   #to know how to fetch these dbt models
            load_method=LoadMode.DBT_LS,
            select=['path:models/transform']
        )
    )
    
    
    @task.external_python(python='/usr/local/airflow/soda_venv/bin/python')
    def check_transform(scan_name='check_transform', checks_subpath='transform'):
        from include.soda.check_function import check

        return check(scan_name, checks_subpath)
    
    report = DbtTaskGroup(
        group_id='report',
        project_config=DBT_PROJECT_CONFIG,
        profile_config=DBT_CONFIG,
        render_config=RenderConfig(
            load_method=LoadMode.DBT_LS,
            select=['path:models/report']
        )
    )
    
    
    @task.external_python(python='/usr/local/airflow/soda_venv/bin/python')
    def check_report(scan_name='check_report', checks_subpath='report'):
        from include.soda.check_function import check

        return check(scan_name, checks_subpath)
    
retail()