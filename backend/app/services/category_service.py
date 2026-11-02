"""分类业务（需求 FR-A-02）。

规则：层级上限 3 级；禁止自指与成环；含子分类或含商品的分类禁止删除。
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import BizException, ErrorCode
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate

MAX_LEVEL = 3


def get_or_404(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise BizException(ErrorCode.NOT_FOUND, "分类不存在")
    return category


def get_descendant_ids(db: Session, category_id: int) -> list[int]:
    """返回自身及全部后代分类 id，用于列表筛选包含子分类。"""
    result: list[int] = []
    queue = [category_id]
    while queue:
        current = queue.pop(0)
        result.append(current)
        children = db.scalars(select(Category.id).where(Category.parent_id == current)).all()
        queue.extend(children)
    return result


def build_tree(db: Session) -> list[CategoryOut]:
    categories = db.scalars(select(Category).order_by(Category.sort, Category.id)).all()
    nodes = {
        c.id: CategoryOut(id=c.id, name=c.name, parent_id=c.parent_id, level=c.level, sort=c.sort)
        for c in categories
    }
    roots: list[CategoryOut] = []
    for c in categories:
        node = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id].children.append(node)
        else:
            roots.append(node)
    return roots


def _check_parent(db: Session, parent_id: int | None, self_id: int | None = None) -> int:
    """返回新节点的 level，并校验父节点合法性与成环。"""
    if parent_id is None:
        return 1
    if self_id is not None and parent_id == self_id:
        raise BizException(ErrorCode.PARAM_CONFLICT, "父分类不能是自身")

    parent = get_or_404(db, parent_id)
    if parent.level >= MAX_LEVEL:
        raise BizException(ErrorCode.PARAM_CONFLICT, f"分类最多支持 {MAX_LEVEL} 级")

    if self_id is not None:
        # 沿父链向上找，遇到自身即成环
        current = parent
        visited: set[int] = set()
        while current is not None:
            if current.id == self_id:
                raise BizException(ErrorCode.PARAM_CONFLICT, "不能把分类移动到其子分类下")
            if current.id in visited:
                raise BizException(ErrorCode.PARAM_CONFLICT, "分类数据存在环，请联系管理员")
            visited.add(current.id)
            current = db.get(Category, current.parent_id) if current.parent_id else None
    return parent.level + 1


def _check_sibling_name(db: Session, name: str, parent_id: int | None, self_id: int | None = None) -> None:
    """同级分类名唯一（G10、FR-A-02）。"""
    cond = Category.name == name
    cond = cond & (Category.parent_id.is_(None) if parent_id is None else Category.parent_id == parent_id)
    if self_id is not None:
        cond = cond & (Category.id != self_id)
    if db.scalar(select(Category.id).where(cond).limit(1)):
        raise BizException(ErrorCode.ALREADY_EXISTS, "同级下已存在同名分类")


def create(db: Session, payload: CategoryCreate) -> Category:
    level = _check_parent(db, payload.parent_id)
    _check_sibling_name(db, payload.name, payload.parent_id)
    category = Category(
        name=payload.name, parent_id=payload.parent_id, sort=payload.sort, level=level
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update(db: Session, category_id: int, payload: CategoryUpdate) -> Category:
    category = get_or_404(db, category_id)
    level = _check_parent(db, payload.parent_id, self_id=category_id)
    _check_sibling_name(db, payload.name, payload.parent_id, self_id=category_id)

    category.name = payload.name
    category.parent_id = payload.parent_id
    category.sort = payload.sort

    # 父级变化 → 级联更新整棵子树 level（一次批量查询，避免逐个 db.get）
    if level != category.level:
        delta = level - category.level
        descendant_ids = get_descendant_ids(db, category_id)
        descendants = list(
            db.scalars(select(Category).where(Category.id.in_(descendant_ids))).all()
        )
        for node in descendants:
            if node.level + delta > MAX_LEVEL:
                raise BizException(ErrorCode.PARAM_CONFLICT, "移动后将超过分类层级上限")
        for node in descendants:
            node.level += delta

    db.commit()
    db.refresh(category)
    return category


def delete(db: Session, category_id: int) -> None:
    category = get_or_404(db, category_id)
    has_children = db.scalar(select(Category.id).where(Category.parent_id == category_id).limit(1))
    if has_children:
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "该分类存在子分类，无法删除")

    has_products = db.scalar(select(Product.id).where(Product.category_id == category_id).limit(1))
    if has_products:
        # 下架商品同样视为占用（附录 A8）
        raise BizException(ErrorCode.STATE_UNAVAILABLE, "该分类下存在商品，无法删除")

    db.delete(category)
    db.commit()
