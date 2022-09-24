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
from main.models.notes import Note

from django.db.models import Q

default = ModelConfig(
    model=User,
    allowedOperations=[ModelOperations.SELECT_ONE, ModelOperations.UPDATE],
    foreignKeys={"notes": ForeignKey(model=Note, type=RelationshipTypes.LIST)},
    permissions={
        "admin": lambda user: ModelPermissionConfig.fullaccess(),
        "user": lambda user: ModelPermissionConfig(
            select=SelectPermissionUnit(
                row=Q(is_active=True, id=user),
                column=[
                    "email",
                    "id",
                    "notes",
                ],
            ),
            update=UpdatePermissionUnit(
                column=[
                    "email",
                ],
                row=Q(is_active=True, id=user),
            ),
        ),
    },
)
