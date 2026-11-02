from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin
from app.core.responses import success
from app.database import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["管理端-分类"], dependencies=[Depends(get_current_admin)])


@router.get("", summary="分类树（含层级）")
def admin_list_categories(db: Session = Depends(get_db)):
    return success(category_service.build_tree(db))


@router.post("", summary="新增分类")
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    return success(category_service.create(db, payload))


@router.put("/{category_id}", summary="编辑分类")
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    return success(category_service.update(db, category_id, payload))


@router.delete("/{category_id}", summary="删除分类")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category_service.delete(db, category_id)
    return success()
