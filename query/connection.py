import psycopg2
from .settings import ENGINES
from .query import Query


class Connect:
    def __init__(self, engine, **kwargs):
        """
        Connects to a engine so the user can make queryies

        Args:
            engine (str): The engine string
        Raises:
            KeyError: Engine must be one of the following: `postgres`
        """
        if engine not in ENGINES.keys():
            raise KeyError('Engine not found, use one of the following: {}'.format(', '.join(ENGINES.keys())))
        try:
            self.__engine = ENGINES[engine](**kwargs)
        except TypeError as te:
            arguments = str(te).replace('__init__() missing 5 required positional arguments: ', '')
            raise TypeError('The following arguments are required for a new connection: {}'.format(arguments))

    def query(self, on_table):
        return Query(on_table=on_table, engine=self.__engine)
