from django.db.models import Q

def permissionConfig(
        select_column: str|list[str] = None,
        select_row: bool|Q = None,
        insert_column: str|list[str] = None,
        insert_row: bool|Q = None,
        delete_column: str|list[str] = None,
        delete_row: bool|Q = None,
        update_column: str|list[str] = None,
        update_row: bool|Q = None,
        base_column: str|list[str]='__all__',
        base_row: bool|Q=True,
    ):
    select_column = base_column if select_column is None else select_column
    select_row = base_row if select_row is None else select_row
    insert_column = base_column if insert_column is None else insert_column
    insert_row = base_row if insert_row is None else insert_row
    delete_column = base_column if delete_column is None else delete_column
    delete_row = base_row if delete_row is None else delete_row
    update_column = base_column if update_column is None else update_column
    update_row = base_row if update_row is None else update_row
    return dict(
        base=dict(
            column=base_column,
            row=base_row,
        ),
        select=dict(
            column=select_column,
            row=select_row,
        ),
        update=dict(
            column=update_column,
            row=update_row,
        ),
        delete=dict(
            column=delete_column,
            row=delete_row,
        ),
        insert=dict(
            column=insert_column,
            row=insert_row,
        ),
    )

class UnrestModelMeta:
    ur_foriegn_keys = {}
    ur_permissions = {}
