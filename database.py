from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

Base = declarative_base()


class Tokens(Base):
    """Создание таблицы для записи полученных от API токенов."""
    __tablename__ = 'tokens'
    id = Column('id', Integer, primary_key=True)
    access_token = Column('access_token', String)
    refresh_token = Column('refresh_token', String)
    expires_in = Column('expires_in', Integer)

    def __init__(self, access_token, refresh_token, expires_in):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_in = expires_in

    def __repr__(self):
        return (f'{self.id} - {self.access_token} '
                f'- {self.refresh_token} {self.expires_in}')


engine = create_engine('sqlite:///tgdb.db')
Base.metadata.create_all(bind=engine)


def db_insert_query(access_token, refresh_token, expires_in):
    """Функция для записи данных полученных от API в базу."""
    with Session(autoflush=False, bind=engine) as session:
        query = Tokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in
        )
        session.add(query)
        session.commit()


def db_select_query():
    """Получение из базы данных последней записи."""
    with Session(autoflush=False, bind=engine) as session:
        return session.query(Tokens).order_by(Tokens.id.desc()).first()
