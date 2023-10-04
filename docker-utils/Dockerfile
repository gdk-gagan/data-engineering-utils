FROM python:3.9

## Docker 101
# RUN pip install pandas

# WORKDIR /app
# COPY scripts/pipeline.py pipeline.py

# # ENTRYPOINT ["bash"]
# ENTRYPOINT ["python", "pipeline.py"]

# Dockerize the ingest script
RUN apt-get install wget
RUN pip install pandas sqlalchemy psycopg2

WORKDIR /app
COPY scripts/ingest_data.py ingest_data.py

ENTRYPOINT ["python", "ingest_data.py"]