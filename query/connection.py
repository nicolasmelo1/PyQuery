import psycopg2
from .settings import ENGINES
from .query import Query


class Connect:
    def __init__(self, engine, join_relations=dict(), **kwargs):
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
        self.join_relations = join_relations 

    def query(self, on_table, join_relations=dict()):
        if not join_relations:
            join_relations = self.join_relations
        return Query(on_table=on_table, engine=self.__engine, join_relations=join_relations)
