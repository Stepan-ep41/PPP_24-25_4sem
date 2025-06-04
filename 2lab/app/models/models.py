from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


# Создаём базовый класс для моделей
Base = declarative_base()


# Определяем таблицу User
class User(Base):
    # Имя таблицы
    __tablename__ = 'Users'
    # Колонки таблицы
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)