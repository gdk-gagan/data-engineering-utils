# Getting started with Prefect

Link to official tutorial - [Prefect tutorial](https://docs.prefect.io/latest/)

Step by step guide:
- Create a new environment
  ```bash 
  conda create --name prefect
  conda activate prefect
  ```

- Install prefect (using pip or conda) for the prefect template or install the complete requirements.txt for running the sample etl scripts.
  ```bash
  pip install prefect
  # or
  pip install -r requirements.txt
  ```

- Start postgres database locally in Docker. ([Instructions](https://github.com/gdk-gagan/data-engineering-utils/tree/main/docker-utils))
  
- Run the template script and start the prefect server locally to view the runs. 
  ```bash
  python prefect_template.py
  
  # Start prefect server
  prefect server start
  ```

- Checkout the `write_to_postgres_flow.py` script that uses prefect to ingest ny-taxi data from web to local postgres instance.

### Create flow code

This is done by adding `@task` and `@flow` decorators to your functions.
- Similary, create another script to ingest data from web to google cloud storage, GCS. `flows/etl_web_to_gcs.py`
- Refactor the script above, and add parameters for taxi service, month and year to run the flow for a specific service and time period. `flows/etl_web_to_gcs_parametrized`
- Create a script to deploy the parameterized code above in a docker container. `flows/docker_deploy.py`
- Create another script to ingest data from GCS to BigQuery, BQ. `flows/etl_gcs_to_bq.py`

### Create a deployment
- Until now we can have been running the flows from command line manually
- the next step is to use a prefect deployement that can trigger and schedule a flow run instead of manual running.
- A deploymeent is a server-side concept that encapsulates a flow 
  - allowing it to be triggered and scheduled via an API
- You can build a deployment via the CLI or a python script or prefect UI.
- On the CLI, the main steps in creating are a deployment are build and apply 
  1. Build : `prefect deployment build <filename.py>:<main flow> -n <deployment name>`
  ```bash prefect deployment build ./parametrized_flow.py:etl_parent_flow -n "Parametrized ETL"
  ```
   
  - This creates a deployment.yaml file that contains all the metadata that prefect requires to orchestrate this flow.
  - There is a parameters config in the yaml where you can input required params for the flow.
  - Add this for now - {"year": 2021, "months": [1,2], color:"green"}
- 2. Apply: `prefect deployment apply <deployment.yaml>`
  
  ```bash prefect deployment apply etl_parent_flow-deployment.yaml 
  ```
  - Creates a deployment based on the yaml file.

### Start an agent
- Now, in order execute the flow run from this deployment, we need an agent.
- Agents and work queues is another prefect concept that allows you to dictate what work goes where.
- So each deployment tells which work queue the flow goes to. 
- An agent is an extremently light weight python process and is living in your execution environment and is pulling from a work queue, 
- in our case, we are just running on local, so we start an agent on our local machine
- Start an agent - 
  ```bash 
  prefect agent start --work-queue "default"
  ``` 
(you can view work queues and its scehduled runs in the UI)
- you can have muliple work queues and a deployement specifices which work queue the flow is added to. 
- and you can use agents to orchestrate where in the execution environment you want flows to run
- There can be scenarios where your infrastructure has mulitple servers, for example a cloud deployment like a kubernetes server as well as a local development enviroment, in that case you can have separate work queues for different environments.

### Run the deployment or create a schedule
You can run a deployment ad hoc from the CLI or UI using a default agent or create a schedule from the UI, in flow script using cron or the CLI the deployment command when you create your deployment.
To add schedules - you can add via UI or command line using --cron "0 0 * * *" flag with the deployment command

### Setup job notifications
- after setting up deployments and agents, you can set up notifications.
- notifications are based on flow state (success, failed etc) or 
- infrastructure state (crashed etc) in case your execution env 
- that is running the agent crashes (example, runs out of memory)

### Running the flow in Docker
- Run the parametrized flow in Docker. We'll bake the code required for etl into the image itself. But there are lots of ways to do this, you can have  your prefect code in version control or S3, GCS or Azure blob storage.
- We are going to put our code in a Docker image, host it on Docker Hub, and run the container (baking it into the image). We'll also specify packages and other things - it'll save time down the road
- Create a Dockerfile. We ll use the prefect base image.
- Copy the flow code and required data into /opt/prefect/flows and /opt/prefect/data folder. That is where prefect looks for code and data by default.
- Create an account on docker hub to register images.
- Create the image from Dockerfile using following commands
  ```bash 
  docker image build -t madebyskye/prefect:de-zoomcamp . 
  ```
- Login to docker hub using CLI. (Very imp - browswer login doesn't allow to push images) If you get a resource denied error, check [this](https://stackoverflow.com/questions/41984399/denied-requested-access-to-the-resource-is-denied-docker)
   ```bash 
   docker login
   ```
- Now we have created an image and we can push it to dockerhub using 
    ```bash 
     docker image push madebyskye/prefect:de-zoomcamp
    ```
- You can view this in your [DockerHub](https://hub.docker.com/repository/docker/madebyskye/de-zoomcamp/general) account online
- Now we can deploy the prefect flow using docker using a python script.
- Create a prefect block for docker container specifying the image you created above (madebyskye/prefect:de-zoomcamp).
- Use the block code to create a python script, docker-deploy.py that deploys our pipeline.
- Run the python script - create a deployment flow 
- Prefect profiles - prefect allows you to create multiple profiles to work with multiple workspaces. In order to use the APIs for correct endpoint, you need to make sure that your config points to the correct workspace. [More on profiles and configs](https://docs.prefect.io/latest/guides/settings/)
   ```bash 
   prefect profile ls
   ```
   ```bash 
   #use a local Prefect server
  prefect config set PREFECT_API_URL="http://127.0.0.1:4200/api"
   ```

  This is required so that the docker container can interface with the prefect server which is running locally on our machine.

  - Now we need to create prefect agent on our machine locally in a subprocess
      ```bash
      prefect agent start -q default
      ```

    - Now we can run our flow. Either from UI or CLI. 
    Let's do it from CLI for now.
    ```bash
    prefect deployment run etl-parent-flow/docker-flow -p "year=2021" -p "months=[1,2]"
    ```

Reference: Amazing github repo here. [Prefect by discdiver](https://github.com/discdiver/prefect-zoomcamp/blob/main/README.md)