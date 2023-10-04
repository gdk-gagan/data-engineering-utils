# Docker
The goal is to create a simple python script that ingests data from web to a local postgres instance running on docker and bake the script in the same image.

## Getting started with Docker

- Install [docker] for your environment. (https://docs.docker.com/get-docker/)
- Try basic commands - to run pre-built docker images for ubuntu and python.
  ```bash 
    - $ docker run hello-world
    - $ docker run -it ubuntu bash 
    - $ docker run -it  python:3.9 #opens python terminal
    - $ docker run -it --entrypoint=bash  python:3.9 # opens bash
    ```
- You can build custom images, push to a public registry like dockerhub or just run it in docker as well. To build custom imgaes, create a new file called `Dockerfile`. Basically log your workflow steps that you perform to execute tasks locally (like creating a directory, installing software, copying scripts, running scripts)
    - To build an image using given Dockerfile 
      `docker build -t <image_name>:<tag> <dockerfile_path>`
    
      ```bash 
        # Build image (in same folder as Dockerfile)
        $ docker build -t myfirstcontainer:gdk . 
        # Run the image
        $ docker run -it myfirstcontainer:gdk
      ```
- Push the image to DockerHub [Link to deploy_with_docker] - `TODO`
  
- Useful Docker CLI commands - 
    ```bash 
    # The docker ps command only shows running containers by default. To see all containers, use the -a (or --all) flag
    $ docker ps 
 
    # To stop one or more running containers:
    $ docker stop [OPTIONS] CONTAINER [CONTAINER...]

    # Kill containers
    $ docker kill <container_id>
    ```

###  Postgres in Docker
Instead of installing postgres locally, we can run it in a docker container. To interact with postgres, we can use pgcli (CLI-interface) or pdamin (GUI-based interface). Each component can be run either locally or in a docker container. We need to consider networking in our architecture so that these components can talk to each other. 

1. Run PostGRES using the pre-built `postgres:13` image: Postgres image needs certain configurations for docker, 
   - `-e`: environment variables (for user, password and database name)
   - `-v`: mapping volume - a folder on the host machine to a folder in the container, called mounting
   - `-p`: mapping a port on the host machine to a port on the container, so that we can send a request to postgres like a sql query and get a response
   - `Note`: for mapping volume, docker needs full path on the host folder

    ```bash
    docker run -it \
        -e POSTGRES_USER="root" \
        -e POSTGRES_PASSWORD="root" \
        -e POSTGRES_DB="ny_taxi" \
        -v /Users/gdk/Projects/de-zoomcamp/week-1/ny_taxi_postgres_data:/var/lib/postgresql/data \
        -p 5432:5432 \
    postgres:13
    ```
    Running this command creates a new folder `ny_taxi_postgres_data` for your local postgres database to store files.

2. CLI for Postgres

    Installing `pgcli`

    ```bash
    pip install pgcli
    ```

    If you have problems installing `pgcli` with the command above, try this:

    ```bash
    conda install -c conda-forge pgcli
    # or
    pip install -U mycli
    ```

    Using `pgcli` to connect to Postgres

    ```bash
    pgcli -h localhost -p 5432 -u root -d ny_taxi
    ```

3. Run `pgAdmin` in docker  
   Refer official docs for [docker pgadmin](https://hub.docker.com/r/dpage/pgadmin4/). It does not provide much info on what environment variables for required for pgadmin. (Taking the cmd from Alexey's notes.)
    ```bash 
    docker run -it \
    -e PGADMIN_DEFAULT_EMAIL="root@root.com" \
    -e PGADMIN_DEFAULT_PASSWORD="root" \
    -p 8080:80 \
    dpage/pgadmin4
    ```

   - If you connect to localhost postgres on the above `pgadmin`, you cannot connect. 
   - Localhost for a container is the container itself.
   - Cz the localhost refers to the `pgadmin` container and there is no postgres inside that container. 
   - In order to access postgres, we need to make the postgres container discoverable to the `pgadmin` container. 
   - This can be achieved by setting up networks. Lookup - `docker network create`
  
4. Shut down the old containers and create a new network
    ```bash
    docker network create pg-network
    ```

5. Run the old containers with `--network` and `--name`  (to discover resources within the network) tags
    ```
    docker run -it \
        -e POSTGRES_USER="root" \
        -e POSTGRES_PASSWORD="root" \
        -e POSTGRES_DB="ny_taxi" \
        -v $(pwd)/ny_taxi_postgres_data:/var/lib/postgresql/data \
        -p 5432:5432 \
        --network=pg-network \
        --name pg-database \
    postgres:13
    ```

    ```
    docker run -it \
    -e PGADMIN_DEFAULT_EMAIL="root@root.com" \
    -e PGADMIN_DEFAULT_PASSWORD="root" \
    -p 8080:80 \
    --network=pg-network \
    --name pg-admin \
    dpage/pgadmin4
    ```

6. Now, login to pgadmin from your browswer and you should be able to see your `ny_taxi` database.

### Running a python script in Docker

Create a python script to ingest data from web to postgres. Create a new docker image containing the script. Run the script in your new container. We'll use the new york taxi data.

1. Create a python script in jupyter that downloads data from the web, reads as a dataframe, connects to postgres and inserts data in postgres db. Refer `notebooks/ingest-web-to-postgres.ipynb`
   
2. Refactor the notebook into a python script `scripts/ingest.py`. Helpful VSCode shortcuts for refactoring,

    Select all arguments: `Cmd+Shift+L` and `Cmd+Shift+Right` arrow

3. Run the script locally
   
  ```bash
  URL="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
  python scripts/ingest_data.py \
    --user=root \
    --password=root \
    --host=localhost \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_data \
    --url=${URL}
```
   Note:
   - `--host=localhost` : let's test on localhost for now, later we'll covert it to docker
   - `--password=root` : not the best way to enter passwords as the commands get saved in bash history
   

 4. Let's dockerize. Create a Dockerfile. Install required libraries in docker and copy the script. Create a docker image called `taxi_ingest` and tag for version `v001`
    ```bash
    docker build -t taxi_ingest:v001 .
    ```

 5. Run `postgres` in docker as above. Run the `taxi_ingest` docker container with the required parameters in the same network
    
    ```bash 
    URL="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
    docker run -it \
    --network pg-network \
    taxi_ingest:v001 \
        --user=root \
        --password=root \
        --host=pgdatabase \
        --port=5432 \
        --db=ny_taxi \
        --table_name=yellow_taxi_data \
        --url=${URL}
    ```

    Note: 
    
    - If you do not use `-it` (interactive) flag, you cannot kill the container from the terminal. You ll have to use `docker kill <container-id>` in another terminal.
    - Docker params come before the image and image params are after the image.
    - We need to run the container in the network so that it connect to postgres.
    
  
-----
Tidbits : `Python http server`

You can start a local http server using python for local testing.

    ```bash
     python -m http.server
     ```
    
- go to localhost:8000 to view all files in the folder
- If you have already downloaded data on your machine, docker can download it from your machine instead of the internet which is much faster. You can replace the URL with `<your-ipv4-address>/<file.csv>`
- ifconfig for your ip address, eth0 for wifi

Use the following command for local testing
```bash
URL="http://10.0.0.42:8000/data/yellow_tripdata_2021-01.csv.gz"
docker run -it \
--network pg-network \
taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pgdatabase \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_data \
    --url=${URL}
```
----
### Creating a docker-compose file
  Till now, we created different docker containers using CLI. We can use docker-compose to combine the docker commands for postgres and pgadmin and ingest script, 
  - create a yaml file, `docker-compose.yaml` and use docker compose to build a single image.
  - create a docker-compose.yaml file.
  - it has services (each for a docker image), for each service, we have image name and associated enviroment vars.
  - ALL SERVICES DEFINED IN DOCKER-COMPOSE ARE PART OF THE SAME NETWORK AUTOMATICALLY. NO NEED TO CREATE NETWORKS
  - Stop postgres and pgadmin containers.
  - Build a new image using `docker compose up`.
  - Run the ingest.py in docker-compose as follows,

```bash
URL="https://github.com/DataTalksClub/nyc-tlc-data/releases/download/yellow/yellow_tripdata_2021-01.csv.gz"
 docker run -it \
  --network week-1_default \
 taxi_ingest:v001 \
    --user=root \
    --password=root \
    --host=pgdatabase \
    --port=5432 \
    --db=ny_taxi \
    --table_name=yellow_taxi_data \
    --url=${URL}
```

-----
Tip: 
- Run docker in detach mode using -d : `docker-compose up -d` . This runs docker in the backgroud and gives the terminal back for use.
- To shut down : docker-compose down
- `TODO` - How to persist database connections in pg-admin?

References:
The amazing DE-Zoomcamp course - [Github](https://github.com/DataTalksClub/data-engineering-zoomcamp/tree/main/week_1_basics_n_setup)