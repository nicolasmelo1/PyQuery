# PyQuery
This a simple wraper around SQL meant for python. This heavily inspired by DJANGO ORM, the difference is that THIS IS NOT AN ORM. I intend to make queries easier for django developers and python developers. Without the need for using a full ORM and mapping each single table to a python class. 

# Example
Simple example and quickstart on how to use

```python
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

# data is lazy loaded, this means we just evaluate the data when needed
# Creates the query structure, and doesn't query anything
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
```

# ENGINE
Right now we only support `postgres`, but hopefully we will support more engines in the near future.

# JOINS
Joins are created automatically whenever you put double underscores
```python
connection.query('form_value').filter(form__name=2)
```

In this example form is a field from `form_value` table and `name` is a field from `form` table.
Sometimes the name of your field doesn't match the name of the table, for it you must use __join relations__.


__IMPORTANT:__
In order to work, `form` field on `form_value` table MUST end with `_id`. Also `form` table MUST have an `id` column.
Without this, joins don't work.

__Observation:__
You can use double underscores for anything, here we are covering select but this also works with `order_by` and `select` functions.

## Join Relations
The user can set dynamic join_relations directly in a query or in the connection for table joins. Let's go with the following example
```python
join_relations = {
    "form_value": {
        "form": "dynamic_forms"
    }
}   
```

The above example means that: __"When you are making a join with the `form` field and the table is `form_value`, we use the value `dynamic_forms` instead"__

### WHAT?
Let's dig deeper. When you do something like this:
```python
connection.query('form_value').filter(form__form__id=2)
```

Let's separate the string by each duble underscore, we get something like this: [form, form, id]
The first `form` is the name of the field in `form_value`, but this field is not from `form` database, instead it is from `dynamic_forms`. So in the SQL world we can translate to this:

```sql
SELECT *
FROM "form_value"
    INNER JOIN "dynamic_forms" ON "dyanmic_forms"."id" = "form_value"."form_id"
    INNER JOIN "form" ON "form"."id" = "dynamic_forms"."form_id"
WHERE "form"."id" = 2
```

Look that the second join, correctly references to `form` table, so we don't need to set any join relation for this field. But on on the `form` field in `form_value` table actually referes to `dynamic_forms` and not `form`.

Since your relations will probably never crash (only if you have the same column name for a table and the same table) you are safe defining it directly in the connection.

### To clarify

Okay, but what if `dynamic_forms` table `form` field references `foo` table?
In this case we would do something like the following:

```python
join_relations = {
    "form_value": {
        "form": "dynamic_forms"
    },
    "dynamic_forms": {
        "form": "foo"
    }
}   
```


