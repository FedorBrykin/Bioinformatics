from prefect import flow, task


@task
def say_hello(name: str) -> str:
    message = f"Hello, {name}!"
    print(message)
    return message


@task
def say_world() -> str:
    message = "Hello, World!"
    print(message)
    return message


@flow(name="Hello World")
def hello_world_flow():
    say_world()
    say_hello("Prefect")


if __name__ == "__main__":
    hello_world_flow()
