import wireup

from src.database import provide_db_session, provide_main_database


def create_container() -> wireup.AsyncContainer:
    return wireup.create_async_container(
        injectables=[
            provide_main_database,
            provide_db_session,
        ],
    )
