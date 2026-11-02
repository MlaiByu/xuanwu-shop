from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.responses import success
from app.database import get_db
from app.models.user import User
from app.schemas.address import AddressCreate, AddressOut, AddressUpdate
from app.services import address_service

router = APIRouter(prefix="/addresses", tags=["收货地址"], dependencies=[Depends(get_current_user)])


@router.get("", summary="地址列表")
def list_addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return success([AddressOut.model_validate(a) for a in address_service.list_addresses(db, user)])


@router.post("", summary="新增地址")
def create_address(payload: AddressCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return success(AddressOut.model_validate(address_service.create_address(db, user, payload)))


@router.put("/{address_id}", summary="编辑地址")
def update_address(
    address_id: int, payload: AddressUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return success(AddressOut.model_validate(address_service.update_address(db, user, address_id, payload)))


@router.delete("/{address_id}", summary="删除地址")
def delete_address(address_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address_service.delete_address(db, user, address_id)
    return success()


@router.patch("/{address_id}/default", summary="设为默认地址")
def set_default(address_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return success(AddressOut.model_validate(address_service.set_default(db, user, address_id)))
