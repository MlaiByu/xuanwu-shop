"""收货地址业务（需求 FR-U-09）。"""
from sqlalchemy import exists, select, update
from sqlalchemy.orm import Session

from app.core.errors import BizException, ErrorCode
from app.models.address import Address
from app.models.user import User
from app.schemas.address import AddressCreate, AddressUpdate


def _get_owned(db: Session, user: User, address_id: int) -> Address:
    address = db.scalar(
        select(Address).where(Address.id == address_id, Address.user_id == user.id)
    )
    if address is None:
        # 他人地址或不存在一律 404，防止枚举（需求 §4）
        raise BizException(ErrorCode.NOT_FOUND)
    return address


def list_addresses(db: Session, user: User) -> list[Address]:
    return list(
        db.scalars(
            select(Address).where(Address.user_id == user.id).order_by(
                Address.is_default.desc(), Address.id
            )
        ).all()
    )


def create_address(db: Session, user: User, payload: AddressCreate) -> Address:
    has_address = db.scalar(select(exists().where(Address.user_id == user.id)))
    if not has_address:
        payload.is_default = True  # 首个地址自动设为默认

    if payload.is_default:
        db.execute(update(Address).where(Address.user_id == user.id).values(is_default=False))

    address = Address(user_id=user.id, **payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


def update_address(db: Session, user: User, address_id: int, payload: AddressUpdate) -> Address:
    address = _get_owned(db, user, address_id)
    was_default = address.is_default

    if payload.is_default:
        # 设为默认：先取消其他默认，保证唯一
        if not was_default:
            db.execute(update(Address).where(Address.user_id == user.id).values(is_default=False))
    elif was_default:
        # 取消当前默认：必须保证"有地址必有默认"，避免出现无默认地址的不一致状态
        other = db.scalar(
            select(Address)
            .where(Address.user_id == user.id, Address.id != address_id)
            .order_by(Address.id)
            .limit(1)
        )
        if other is None:
            payload.is_default = True  # 唯一地址不允许取消默认
        else:
            other.is_default = True  # 剩余第一条补位为默认

    for field, value in payload.model_dump().items():
        setattr(address, field, value)
    db.commit()
    db.refresh(address)
    return address


def delete_address(db: Session, user: User, address_id: int) -> None:
    address = _get_owned(db, user, address_id)
    db.delete(address)
    db.flush()
    if address.is_default:
        # 删除默认地址后，把剩余地址中 id 最小的一条设为默认
        next_default = db.scalar(
            select(Address).where(Address.user_id == user.id).order_by(Address.id).limit(1)
        )
        if next_default:
            next_default.is_default = True
    db.commit()


def set_default(db: Session, user: User, address_id: int) -> Address:
    address = _get_owned(db, user, address_id)
    db.execute(update(Address).where(Address.user_id == user.id).values(is_default=False))
    address.is_default = True
    db.commit()
    db.refresh(address)
    return address
