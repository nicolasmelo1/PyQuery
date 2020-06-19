from query.connection import Connect

connection = Connect(
    'postgres', 
    port=5432,
    host='db_host', 
    database='db_name', 
    user='db_user', 
    password='db_password'
)
results = connection.query('form_value').select('id', flat=True).limit(2)
new_results = connection.query('form_value').filter(id___in=results)
print(new_results)
