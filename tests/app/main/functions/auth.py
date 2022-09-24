import re
from main.models.users import User
from uql.decorators.intent import intent
from rest_framework.request import Request
from rest_framework.authtoken.models import Token
from uql.model import ModelConfig

emailregex = re.compile(
    r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"
)


@intent(requiredArgs=("email", "password"))
def signup(request: Request, args: dict):
    email = args["email"]
    password = args["password"]

    if not re.fullmatch(emailregex, email):
        raise ValueError('invalid email "{email}"')

    if len(password) < 5:
        raise ValueError("password lenght should be >= 5")

    # user
    user = User(email=email)
    user.set_password(password)
    user.save()

    # token
    token: Token = Token.objects.create(user=user)

    mconf: ModelConfig = ModelConfig.getConfig(User)
    sr = mconf.createSerializerClass(user.role)

    return {"user": sr(user).data, "token": token.key}


@intent(requiredArgs=("email", "password"))
def login(request: Request, args: dict):
    email = args["email"]
    password = args["password"]

    user: User = User.objects.get(email=email, is_active=True)
    if not user.check_password(password):
        raise PermissionError("Invalid password")
    mconf: ModelConfig = ModelConfig.getConfig(User)
    sr = mconf.createSerializerClass(user.role)

    token, _ = Token.objects.get_or_create(user=user)

    return {"user": sr(user).data, "token": token.key}
