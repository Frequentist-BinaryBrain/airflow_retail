FROM quay.io/astronomer/astro-runtime:12.6.0-python-3.10-base

# Switch to root user for installing packages
USER root

# Update apt repositories and install required packages including distutils
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# install soda into a virtual environment
# The command you've provided is used to install Soda (a data quality monitoring tool) into a virtual environment 
# to maintain isolation and ensure that your application or project doesn't interfere with other Python projects or system-wide dependencies

# By using a virtual environment, you ensure that the dependencies required by Soda (or any specific project) don't
# conflict with other Python projects or system-wide Python packages. This is particularly useful in environments where multiple 
# applications might require different versions of the same library.

# Install soda into a virtual environment
RUN python -m venv soda_venv && \
    source soda_venv/bin/activate && \
    pip install --no-cache-dir soda-core-bigquery==3.0.45 && \
    pip install --no-cache-dir soda-core-scientific==3.0.45 && \
    deactivate
# Optionally, you can set the environment variable for the virtual environment

RUN python -m venv dbt_venv && source dbt_venv/bin/activate && \
    pip install --no-cache-dir dbt-bigquery==1.5.3 && deactivate
# Your additional Dockerfile instructions go here