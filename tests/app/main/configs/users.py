from uql.model import ModelConfig
from uql.model import ForeignKey
from uql.model import InsertCheck
from uql.model import PermissionUnit
from uql.model import ModelPermissionConfig
from uql.constants import CellFlags
from uql.constants import RelationshipTypes
from uql.constants import ModelOperations

from main.models.users import User
from main.models.projects import Project

from django.db.models import Q

default = ModelConfig(
    model=User,
    allowedOperations=ModelOperations.readonly_and_single_write(),
    foreignKeys={"projects": ForeignKey(model=Project, type=RelationshipTypes.LIST)},
    permissions={
        "admin": lambda userID: ModelPermissionConfig(
            select=PermissionUnit(row=True, column=CellFlags.ALL_COLUMNS),
        ),
        "anonymous": lambda _: ModelPermissionConfig(
            select=PermissionUnit(
                row=Q(
                    is_active=True,
                ),
                column=["email", "role", "id", "projects", "is_active"],
            ),
            insert=InsertCheck(
                column=["email", "is_active"],
                requiredFields=["email"],
            ),
        ),
    },
)
