from uql.model import ModelConfig
from uql.model import ForeignKey
from uql.model import InsertPermissionUnit
from uql.model import UpdatePermissionUnit
from uql.model import SelectPermissionUnit
from uql.model import DeletePermissionUnit
from uql.model import ModelPermissionConfig
from uql.constants import CellFlags
from uql.constants import RelationshipTypes
from uql.constants import ModelOperations

from main.models.users import User
from main.models.projects import Project

from django.db.models import Q

default = ModelConfig(
    model=User,
    allowedOperations=ModelOperations.all(),
    foreignKeys={"projects": ForeignKey(model=Project, type=RelationshipTypes.LIST)},
    permissions={
        "admin": lambda userID: ModelPermissionConfig(
            select=SelectPermissionUnit(row=True, column=CellFlags.ALL_COLUMNS),
        ),
        "anonymous": lambda _: ModelPermissionConfig(
            select=SelectPermissionUnit(
                row=Q(
                    is_active=True,
                ),
                column=["email", "role", "id", "projects", "is_active"],
            ),
            insert=InsertPermissionUnit(
                column=["email", "is_active"],
                requiredFields=["email"],
            ),
            update=UpdatePermissionUnit(
                column=["email", "is_active"],
                row=True,
            ),
            delete=DeletePermissionUnit(row=True),
        ),
    },
)
