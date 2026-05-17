from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.favorite import Favorite
from app.models.scenic import Scenic
from app.utils.response import success, error
from app.utils.security import decode_token
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/favorite", tags=["收藏"])
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    payload = decode_token(credentials.credentials)
    if not payload:
        return None
    return int(payload.get("sub"))


@router.post("/add")
def add_favorite(
    scenic_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user_id = get_current_user(credentials)
    if not user_id:
        return error(1005, "Token 已过期")

    scenic = db.query(Scenic).filter(Scenic.id == scenic_id, Scenic.is_active == 1).first()
    if not scenic:
        return error(2001, "景点不存在")

    existing = db.query(Favorite).filter(
        Favorite.user_id == user_id, Favorite.scenic_id == scenic_id
    ).first()
    if existing:
        return error(2002, "已收藏该景点")

    fav = Favorite(user_id=user_id, scenic_id=scenic_id)
    db.add(fav)
    db.commit()
    return success({"scenicId": scenic_id}, "收藏成功")


@router.post("/remove")
def remove_favorite(
    scenic_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user_id = get_current_user(credentials)
    if not user_id:
        return error(1005, "Token 已过期")

    fav = db.query(Favorite).filter(
        Favorite.user_id == user_id, Favorite.scenic_id == scenic_id
    ).first()
    if not fav:
        return error(2003, "未收藏该景点")

    db.delete(fav)
    db.commit()
    return success({"scenicId": scenic_id}, "取消收藏成功")


@router.get("/list")
def list_favorites(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user_id = get_current_user(credentials)
    if not user_id:
        return error(1005, "Token 已过期")

    favs = (
        db.query(Favorite)
        .filter(Favorite.user_id == user_id)
        .order_by(Favorite.id.desc())
        .all()
    )

    items = []
    for fav in favs:
        scenic = db.query(Scenic).filter(Scenic.id == fav.scenic_id).first()
        if scenic:
            items.append({
                "id": scenic.id,
                "name": scenic.name,
                "category": scenic.category,
                "region": scenic.region,
                "location": scenic.location,
                "price": scenic.price,
                "image": scenic.image,
                "description": scenic.description,
                "tags": scenic.tags or [],
                "favoritedAt": str(fav.created_at) if fav.created_at else None,
            })

    return success({"list": items, "total": len(items)})


@router.get("/check")
def check_favorite(
    scenic_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    user_id = get_current_user(credentials)
    if not user_id:
        return error(1005, "Token 已过期")

    fav = db.query(Favorite).filter(
        Favorite.user_id == user_id, Favorite.scenic_id == scenic_id
    ).first()
    return success({"favorited": fav is not None})
