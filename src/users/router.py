from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session

from .models import User
from .schemas import UserRegisterSchema, UserResponseSchema
from .tasks import send_email_after_successful_registration

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/registration/", response_model=UserResponseSchema)
async def register_user(
    new_user: UserRegisterSchema,
    session: AsyncSession = Depends(get_async_session),
):
    phone_query = select(User).where(User.phone_number == new_user.phone_number)
    phone_result = await session.execute(phone_query)
    if phone_result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Телефон уже зарегистрирован"
        )

    email_query = select(User).where(User.email == new_user.email)
    email_result = await session.execute(email_query)
    if email_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email уже зарегистрирован")

    db_user = User(
        email=new_user.email,
        phone_number=new_user.phone_number,
        name=new_user.name,
    )
    db_user.set_password(new_user.password)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    send_email_after_successful_registration.delay(db_user.email)
    return db_user
