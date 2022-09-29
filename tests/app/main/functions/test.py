from uql.decorators.intent import intent
from rest_framework.request import Request


@intent()
def task(request: Request, args: dict):
    return {"message": "hello"}

@intent()
def task_two(request: Request, args: dict):
    return {"message": "hi"}
