from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import RegisterRequest, UserResponse, LoginRequest
from app.services.auth_service import register_user ,login_user
from app.api.dependencies import get_current_user


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.get(
    "/me",
    response_model=UserResponse,
)
async def get_me(
    current_user=Depends(get_current_user),
):
    return current_user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await register_user(
        db=db,
        email=request.email,
        password=request.password,
    )

    return user


@router.post(
    "/login",
    response_model=UserResponse,
)
async def login(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user, token = await login_user(
        db=db,
        email=request.email,
        password=request.password,
    )

    response.set_cookie(
        key="pm_session",
        value=token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=43200,
        path="/",
    )

    return user