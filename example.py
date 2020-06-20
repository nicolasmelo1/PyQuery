from query.connection import Connect

conn = Connect(
    'postgres', 
    port=5432,
    host='db_host', 
    database='db_name', 
    user='db_user', 
    password='db_password',
    join_relations={
        'form':{
            'depends_on': 'form'
        }
    }
)

#############
#           #
# EXAMPLE 1 #
#           #
#############
migrate_data_ids = [1,2,3]

# data is lazy loaded only this means we just evaluate the data when needed
# Creates the query structure, and doesn't load anything
fields_to_recover_data = conn.query('field').filter(id___in=migrate_data_ids)

# evaluate the data only when retrieving it, so this is when we hit the database
print(fields_to_recover_data)


#############
#           #
# EXAMPLE 2 #
#           #
#############
# In this example uses the value of a query in a second query, evaluates only once, 
# you are not using `new_results` for anything.
results = conn.query('form_value').select('id', flat=True).limit(2)
new_results = conn.query('form_value').filter(id___in=results)

# you can also use .force() to force evaluation
new_results = conn.query('form_value').filter(id___in=results.force())
