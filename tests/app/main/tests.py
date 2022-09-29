from uql.views import UQLView
from uql.tests.infrastructure import Request

from core.config import Config
from django.test import TestCase
from main.models.users import User


def uqlinputdata(intent: str, fields: str | dict = None, args: dict = None) -> dict:
    return {"intent": intent, "fields": fields, "args": args}


class DocsTestCase(TestCase):
    def setUp(self) -> None:
        self.uql = UQLView(Config).usingInfrastructure
        pass

    def test_docs(self):
        res = self.uql(Request(method="get"))
        function_list = res.data.keys()
        self.assertIn("models.user.find", function_list)
        self.assertIn("functions.task", function_list)
        self.assertIn("functions.task_two", function_list)


class ModelFuntionsTestCase(TestCase):
    def setUp(self) -> None:
        self.uql = UQLView(Config).usingInfrastructure
        pass

    def test_select(self):
        client: User = User(email="test@google.com")
        client.save()

        res = self.uql(
            Request(
                user=client,
                data=uqlinputdata(
                    "models.user.find",
                    args={"where": {"email": {"_eq": client.email}}},
                    fields={"email": True},
                ),
            )
        )
        data: dict = res.data.get("data", {})
        self.assertEqual(data.get("email"), client.email)


class IntentTestCase(TestCase):
    def setUp(self) -> None:
        self.uql = UQLView(Config).usingInfrastructure
        pass

    def test_multiple_intent(self):
        res = self.uql(
            Request(
                data=[
                    uqlinputdata("functions.task", fields="$all"),
                    uqlinputdata("functions.task_two", fields="$all"),
                ]
            )
        )
        data = [i.get("data", {}).get("message") for i in res.data]
        self.assertListEqual(data, ["hello", "hi"])
