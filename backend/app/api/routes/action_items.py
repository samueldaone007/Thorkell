from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ActionItem, Conversation
from app.schemas import ActionItemCreate, ActionItemOut, ActionItemUpdate

router = APIRouter(tags=["action-items"])


@router.post(
    "/conversations/{conversation_id}/action-items",
    response_model=ActionItemOut,
    status_code=201,
)
def create_action_item(
    conversation_id: str, payload: ActionItemCreate, db: Session = Depends(get_db)
) -> ActionItem:
    if db.get(Conversation, conversation_id) is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    item = ActionItem(
        conversation_id=conversation_id,
        text=payload.text,
        assignee=payload.assignee,
        source="manual",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/action-items/{item_id}", response_model=ActionItemOut)
def update_action_item(
    item_id: str, payload: ActionItemUpdate, db: Session = Depends(get_db)
) -> ActionItem:
    item = db.get(ActionItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Action item not found")
    if payload.text is not None:
        item.text = payload.text
    if "assignee" in payload.model_fields_set:
        item.assignee = payload.assignee
    if payload.done is not None:
        item.done = payload.done
    db.commit()
    db.refresh(item)
    return item


@router.delete("/action-items/{item_id}", status_code=204)
def delete_action_item(item_id: str, db: Session = Depends(get_db)) -> Response:
    item = db.get(ActionItem, item_id)
    if item is not None:
        db.delete(item)
        db.commit()
    return Response(status_code=204)
