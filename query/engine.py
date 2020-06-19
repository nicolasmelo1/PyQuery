import psycopg2


class Engine:
    def __init__(self):
        self.connection = None
    
    def validate_not_connected(self):
        if self.connection != None:
            raise AssertionError('Database connected, use `{}` method to close the connection to your databse'.format('.close()'))

    def validate_connected(self):
        if self.connection == None:
            raise AssertionError('Database not connected, use `{}` method to connect to your databse'.format('.connect()') )
    
    def connect(self):
        pass

    def close(self):
        pass

    def execute(self):
        pass

    def fetch(self):
        pass

    def commit(self):
        pass

class Postgres(Engine):
    def __init__(self, port, host, database, user, password):
        self.port = port
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        super(Postgres, self).__init__()

    def connect(self):
        #self.validate_not_connected()

        self.connection = psycopg2.connect(
            port=self.port,
            host=self.host, 
            database=self.database,
            user=self.user, 
            password=self.password
        )
        return self.connection
    
    def close(self):
        self.validate_connected()
        self.connection.close()
        return True
    
    def execute(self, query):
        self.validate_connected()
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor

    def fetch(self, query):
        self.connect()
        cursor = self.execute(query)
        result = cursor.fetchall()
        self.close()
        return result
    
    def save(self, query):
        self.connect()
        self.execute(query)
        self.connection.commit()
        self.close()

        return True