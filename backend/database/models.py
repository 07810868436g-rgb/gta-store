import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Базовый класс для всех таблиц
Base = declarative_base()

# Перечисление статусов для ключа
class KeyStatus(enum.Enum):
    AVAILABLE = "available"  # Ключ свободен и готов к продаже
    RESERVED = "reserved"    # Юзер нажал "Купить", ждем оплату (бронь)
    SOLD = "sold"            # Ключ успешно продан

class GameKey(Base):
    """
    Таблица для хранения цифровых ключей
    """
    __tablename__ = 'game_keys'

    # Уникальный номер в базе
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Идентификатор товара (например, "gta6_ru"), чтобы бот понимал, от какой это игры
    item_slug = Column(String, index=True, nullable=False)
    
    # Сам цифровой ключ (например, "XXXXX-YYYYY-ZZZZZ")
    key_value = Column(String, unique=True, nullable=False)
    
    # Текущий статус ключа
    status = Column(Enum(KeyStatus), default=KeyStatus.AVAILABLE, nullable=False)
    
    # Время, до которого действует бронь (если статус RESERVED)
    reserved_until = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<GameKey(item='{self.item_slug}', status='{self.status.name}')>"