from uql.model import ModelConfig
from uql.model import ForeignKey
from uql.model import InsertPermissionUnit
from uql.model import UpdatePermissionUnit
from uql.model import SelectPermissionUnit
from uql.model import ModelPermissionConfig

from uql.constants import RelationshipTypes
from uql.constants import ModelOperations

from main.models.users import User
from main.models.notes import Note

from django.db.models import Q
from rest_framework.request import Request


def _note_user_insert_check(req: Request, _set: dict[str, str]):
    user: User = req.user
    author = _set["author"]
    name = _set["name"]

    return (author == str(user.pk)) and (len(name or "") > 0)


default = ModelConfig(
    model=Note,
    allowedOperations=[
        ModelOperations.INSERT,
        ModelOperations.SELECT_MANY,
        ModelOperations.SELECT_ONE,
        ModelOperations.UPDATE,
    ],
    foreignKeys={"author": ForeignKey(model=User, type=RelationshipTypes.OBJECT)},
    permissions={
        "admin": lambda _: ModelPermissionConfig.fullaccess(),
        "user": lambda user: ModelPermissionConfig(
            select=SelectPermissionUnit(
                row=Q(author=user, is_deleted=False),
                column=[
                    "id",
                    "name",
                    "content",
                    "starred",
                    "author",
                    "last_updated",
                    "date_created",
                    "is_archived",
                ],
            ),
            insert=InsertPermissionUnit(
                column=["name", "content", "author"],
                requiredFields=["name", "author"],
                check=_note_user_insert_check,
            ),
            update=UpdatePermissionUnit(
                column=[
                    "name",
                    "content",
                    "starred",
                    "last_updated",
                    "is_archived",
                ],
                row=Q(is_deleted=False, author=user),
            ),
        ),
    },
)
