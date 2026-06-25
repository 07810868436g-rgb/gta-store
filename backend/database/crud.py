from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import GameKey, KeyStatus

async def reserve_key(session: AsyncSession, item_slug: str) -> str | None:
    """
    Безопасно резервирует 1 ключ для пользователя.
    Использует блокировку строки для защиты от двойной продажи (Race Condition).
    """
    
    # Шаг 1: Ищем один доступный ключ и жестко блокируем эту строку базы от других запросов
    # skip_locked=True означает, что если другой покупатель уже "схватил" этот ключ 
    # миллисекундой ранее, мы просто возьмем следующий свободный.
    stmt = (
        select(GameKey)
        .where(GameKey.item_slug == item_slug, GameKey.status == KeyStatus.AVAILABLE)
        .limit(1)
        .with_for_update(skip_locked=True) 
    )
    
    result = await session.execute(stmt)
    key_obj = result.scalar_one_or_none()
    
    # Если ключей нет (все раскупили)
    if not key_obj:
        return None 
        
    # Шаг 2: Меняем статус на "Забронирован" и ставим таймер на 15 минут
    key_obj.status = KeyStatus.RESERVED
    key_obj.reserved_until = datetime.utcnow() + timedelta(minutes=15)
    
    # Шаг 3: Сохраняем изменения в базе
    await session.commit()
    
    # Возвращаем само значение ключа (например, "XXXXX-YYYYY-ZZZZZ")
    return key_obj.key_value

async def mark_key_as_sold(session: AsyncSession, key_value: str):
    """
    Окончательно помечает ключ как проданный после успешной оплаты.
    """
    stmt = select(GameKey).where(GameKey.key_value == key_value)
    result = await session.execute(stmt)
    key_obj = result.scalar_one_or_none()
    
    if key_obj:
        key_obj.status = KeyStatus.SOLD
        await session.commit()