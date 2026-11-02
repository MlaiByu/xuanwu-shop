from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.responses import success
from app.database import get_db
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["分类"])


@router.get("", summary="分类树")
def list_categories(db: Session = Depends(get_db)):
    return success(category_service.build_tree(db))
