from app.dependencies.auth import get_current_user
from app.dependencies.services import get_user_service
from app.schemas.auth import UserResponse, UserCreate, UserCredentials, Token, RefreshRequest
from app.services.user import UserService
from fastapi.security import OAuth2PasswordBearer
from typing import Dict
from fastapi import APIRouter, Depends

user_controller = APIRouter(
    prefix='/auth',
    tags=['Authentication']
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@user_controller.get('/me', response_model=UserResponse)
async def get_profile(
    current_user: UserResponse = Depends(get_current_user),
)-> UserResponse:
    return current_user

@user_controller.post('/signup', response_model=UserResponse)
async def signup(
    payload: UserCreate,
    service: UserService = Depends(get_user_service)
) -> UserResponse:
    return await service.create_user(payload)

@user_controller.post('/login', response_model=Token)
async def login(
    payload: UserCredentials,
    service: UserService = Depends(get_user_service)
) -> Token:
    return await service.login_user(payload)

@user_controller.post('/refresh', response_model=Token)
async def refresh(
    payload: RefreshRequest,
    service: UserService = Depends(get_user_service)
) -> Token:
    return await service.token_service.refresh_token(payload.token)

@user_controller.post('/logout')
async def logout(
    current_user: UserResponse = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
    service: UserService = Depends(get_user_service)
) -> Dict[str, str]:
    await service.logout_user(token, current_user.id)
    return {
        "message": "Logged out successfully"
    }

