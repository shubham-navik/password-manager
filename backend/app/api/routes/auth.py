from fastapi import APIRouter, Depends, Response, status,Cookie, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.auth import RegisterRequest, UserResponse, LoginRequest
from app.services.auth_service import register_user ,login_user
from app.services.session_service import logout_user, logout_all_user_sessions
from app.api.dependencies import get_current_user

from app.api.rate_limit_dependencies import rate_limit_by_ip

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
    dependencies=[
        Depends(
            rate_limit_by_ip(
                limit=5,
                window_seconds=60,
                scope="register",
            )
        )
    ],
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
    dependencies=[
        Depends(
            rate_limit_by_ip(
                limit=5,
                window_seconds=60,
                scope="login",
            )
        )
    ],
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

@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    session_token: str | None = Cookie(
        default=None,
        alias="pm_session",
    ),
    db: AsyncSession = Depends(get_db),
):
    if session_token:
        await logout_user(
            db=db,
            token=session_token,
        )

    response.delete_cookie(
        key="pm_session",
        path="/",
        httponly=True,
        secure=False,
        samesite="lax",
    )
    response.status_code = 204
    return response

@router.post("/logout-all", status_code=204)
async def logout_all(
    response: Response,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await logout_all_user_sessions(
        db=db,
        user_id=current_user.id,
    )

    response.delete_cookie(
        key="pm_session",
        path="/",
        httponly=True,
        secure=False,
        samesite="lax",
    )

    response.status_code = 204
    return response    