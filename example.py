from query.connection import Connect

connection = Connect(
    'postgres', 
    port=5432,
    host='db_host', 
    database='db_name', 
    user='db_user', 
    password='db_password'
)
results = connection.query('example').select('id', flat=True).first().run()
