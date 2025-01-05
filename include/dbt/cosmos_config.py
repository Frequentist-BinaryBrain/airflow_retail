from cosmos.config import ProfileConfig, ProjectConfig
from pathlib import Path

#Specifies what profile to be used 
DBT_CONFIG = ProfileConfig(
    profile_name='retail',
    target_name='dev',
    profiles_yml_filepath=Path('/usr/local/airflow/include/dbt/profiles.yml')
)

# specified where the dbt project is]
DBT_PROJECT_CONFIG = ProjectConfig(
    dbt_project_path='/usr/local/airflow/include/dbt/',
)