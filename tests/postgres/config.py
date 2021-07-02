from tests.settings import PostgresSettings

def create_connection():
    return psycopg2.connect(
        port=PostgresSettings.port,
        host=PostgresSettings.host, 
        database=PostgresSettings.database,
        user=PostgresSettings.user, 
        password=PostgresSettings.password
    )