from prefect import flow, task

@task(log_prints=True)
def get_name(name):
    print(f"My name is {name}")
    
@flow(name='my-first-flow', log_prints=True)
def flow():
    get_name('Skye')
    print("My first prefect flow.")

if __name__ == '__main__' :
    flow()