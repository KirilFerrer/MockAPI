# Contains persistence operations for mock runtime items.
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.storage.models.mock_item import MockItem


def get_mock_items(db: Session, resource_key: str) -> list[MockItem]:
    query = (
        select(MockItem)
        .where(MockItem.resource_key == resource_key)
        .order_by(MockItem.id.asc())
    )
    return db.scalars(query).all()


def get_mock_item(
    db: Session,
    resource_key: str,
    item_id: str,
) -> MockItem | None:
    query = select(MockItem).where(
        MockItem.resource_key == resource_key,
        MockItem.item_id == str(item_id),
    )
    return db.scalars(query).first()


def create_mock_item(
    db: Session,
    *,
    resource_key: str,
    item_id: str,
    data: dict,
) -> MockItem:
    mock_item = MockItem(
        resource_key=resource_key,
        item_id=str(item_id),
        data=data,
    )
    db.add(mock_item)
    db.commit()
    db.refresh(mock_item)

    return mock_item


def create_mock_items(
    db: Session,
    *,
    resource_key: str,
    items: list[dict],
    id_field: str,
) -> list[MockItem]:
    mock_items = [
        MockItem(
            resource_key=resource_key,
            item_id=str(item[id_field]),
            data=item,
        )
        for item in items
    ]

    db.add_all(mock_items)
    db.commit()

    for mock_item in mock_items:
        db.refresh(mock_item)

    return mock_items


def update_mock_item(
    db: Session,
    mock_item: MockItem,
    *,
    item_id: str,
    data: dict,
) -> MockItem:
    mock_item.item_id = str(item_id)
    mock_item.data = data
    db.commit()
    db.refresh(mock_item)

    return mock_item


def delete_mock_item(db: Session, mock_item: MockItem) -> None:
    db.delete(mock_item)
    db.commit()


def delete_mock_items(
    db: Session,
    resource_key: str | None = None,
) -> int:
    query = delete(MockItem)
    if resource_key is not None:
        query = query.where(MockItem.resource_key == resource_key)

    result = db.execute(query)
    db.commit()

    return int(result.rowcount or 0)
