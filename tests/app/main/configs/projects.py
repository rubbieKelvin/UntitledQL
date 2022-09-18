from uql.model import ModelConfig
from uql.model import ForeignKey
from uql.model import SelectPermissionUnit
from uql.model import ModelPermissionConfig
from uql.constants import CellFlags
from uql.constants import RelationshipTypes

from main.models.users import User
from main.models.projects import Project

from django.db.models import Q

default = ModelConfig(
    model=Project,
    foreignKeys={"author": ForeignKey(model=User, type=RelationshipTypes.OBJECT)},
    permissions={
        "admin": lambda userID: ModelPermissionConfig(
            select=SelectPermissionUnit(
                row=Q(author__id=userID), column=CellFlags.ALL_COLUMNS
            ),
        ),
        "anonymous": lambda _: ModelPermissionConfig(
            select=SelectPermissionUnit(
                row=Q(is_deleted=False),
                column=[
                    "id",
                    "name",
                    "description",
                    "author",
                    "last_updated",
                    "is_archived",
                    "date_created",
                ],
            )
        ),
    },
)
