from .settings import (
    WHERE_SPECIAL_ARGUMENTS, AUTOMATIC_JOINS_PLACEHOLDER, 
    FIELD_FORMAT, SELECT_FORMAT, JOIN_CLAUSE_FORMAT, WHERE_CLAUSE_FORMAT, WHERE_AND_CONNECTOR_FORMAT,
    WHERE_EQUAL_OPERATION_FORMAT, ORDER_BY_CLAUSE_FORMAT, ORDER_BY_ASC_FORMAT, ORDER_BY_DESC_FORMAT,
    LIMIT_FORMAT,VALUE_STRING_FORMAT, VALUE_LIST_FORMAT, VALUE_TUPLE_FORMAT, VALUE_NULL_FORMAT
)

from datetime import datetime
import math


class BaseQuery:
    def __init__(self, on_table, engine):
        self.engine = engine
        self.on_table = on_table
        self.join_relations = dict()
        self.joins = []

    def format_db_values(self, value):
        if type(value) == str:
            value = "'{}'".format(value.replace("'","''"))

        if type(value) == list:
            value = '({})'.format(', '.join([str(self.format_db_values(val)) for val in value]))

        if type(value) == datetime:
            value= "'{}'".format(value.strftime('%Y-%m-%d %H:%M:%S'))
        
        if type(value) == tuple:
            value = '{}'.format(', '.join([str(self.format_db_values(val)) for val in value]))

        if value == None:
            value = 'NULL'
        return value

class Select(BaseQuery):
    """
    Class responsible for handling select statements.
    """
    def __init__(self, *args, **kwargs):
        self.query_select = ['*']
        self.query_orders = []
        self.query_where = []
        self.query_limit = ''
        self.query_joins = []
        super(Select, self).__init__(*args, **kwargs)

    @property
    def __get_query(self):
        query = SELECT_FORMAT.format(
            select=', '.join(self.query_select), 
            froms=self.on_table
        )
        
        joins = '{} '.format(' '.join(self.query_joins)) if self.query_joins else ''
        where = WHERE_CLAUSE_FORMAT.format(where_conditions=WHERE_EQUAL_OPERATION_FORMAT.join(self.query_where)) if self.query_where else ''
        orders = ORDER_BY_CLAUSE_FORMAT.format(order_by_conditions=', '.join(self.query_orders)) if self.query_orders else ''
        limit = self.query_limit

        query = query + joins + where + orders + limit
        return query

    def __format_joins(self, joins):
        """
        Handle all of the joins it must do for the query to succeed

        The user can set dynamic join_relations to get the right table. Let's go with the following example
        >>> {
            "form_value": {
                "form": "dynamic_forms"
            }
        }   

        The above example means: "When you are making a join with the `form` field and the table is `form_value`, we use the value `dynamic_forms` instead""

        WHAT?

        Let's dig deeper:
        When you do something like this:

        >>> connection.query('form_value').filter(form__form__id=2).run()

        Let's separate the string by each duble underscore, we get something like this: [form, form, id]
        The first `form` is the name of the field in `form_value`, but this field is not from `form` database, instead
        it is from `dynamic_forms`, we get the correct value on each join

        SO we get something like this
        INNER JOIN "dynamic_forms" ON "dyanmic_forms"."id" = "form_value"."form_id"
        INNER JOIN "form" ON "form"."id" = "dynamic_forms"."form_id"

        Look that the second field, correctly references to "form" table, so we don't need to set any join relation for
        this field. Okay, but what if `dynamic_forms` `form` field references `foo` table?

        We would do something like the following:
        >>> {
            "form_value": {
                "form": "dynamic_forms"
            }
            "dynamic_forms": {
                "form": "foo"
            }
        }   
        """
        to_table_join = None

        for index, join in enumerate(joins):
            if index == 0:
                from_table_join = self.on_table
            elif to_table_join:
                from_table_join = to_table_join

          
            to_table_join = self.join_relations.get(from_table_join, {}).get(join, join)

            join_clause = JOIN_CLAUSE_FORMAT.format(
                join=join, 
                from_table_join=from_table_join,
                to_table_join=to_table_join
            )

            if join_clause not in self.query_joins:
                self.query_joins.append(join_clause)

    def __format_db_fields(self, value):
        """
        Formats each database field based on a default VALUE_CLAUSE
        """

        splitted_value = value.split(AUTOMATIC_JOINS_PLACEHOLDER)
        if len(splitted_value) > 1:

            # Handle automatic join operations
            joins = splitted_value[:-1]
            self.format_joins(joins)

        # handle where
        values_to_use = splitted_value[-2:]
        if len(values_to_use) > 1:
            value = FIELD_FORMAT.format(table=values_to_use[0], field=values_to_use[1])
        else:
            value = FIELD_FORMAT.format(table=self.on_table, field=values_to_use[0])
        
        return value

    def first(self):
        """
        Returns the first element of the query, sets limit as 1
        """
        return self.limit(1)

    def limit(self, number):
        """
        Sets your desired limit to the query

        Args:
            number (int): the limit number

        Returns:
            self: this object so you can concatenate with other functions
        """
        self.query_limit = LIMIT_FORMAT.format(num=number)
        return self

    def select(self, *args, **kwargs):
        """
        Expects the each column names as string. You can also make joins in your select using double undersocores
        like '__'

        You need to define order_by like the following example:
        >>> connection.query('example_db_name').select('id').run()
        >>> connection.query('example_db_name').select('id', 'name').run()

        Or if you need to order by joins you define it like this:
        >>> connection.query('example_db_name').select('connectedfield__id').run()

        In this example `connectedfield` would be a field of `example_db_name` table, and the `id` you are ordering
        is the id on `connectedfield` table.

        Args:
            flat (bool, optional): You can set flat=True if you are retrieving only one option field. Defaults to False
        """    
        # you can retrieve flat values so instead of tuples like this [(1,), (2,)] 
        # you get your results as a nice flat list like [1,2]
        # this just works if you only set ONE argument in the select
        self._flat = kwargs.get('flat', False) and len(args) == 1

        # you can obviously have multiple selects, but everytime you do it resets the select clause
        # so use just one
        self.query_select = []

        for value in args:
            select_clause = self.__format_db_fields(value)
            if select_clause not in self.query_select:
                self.query_select.append(select_clause)
        return self

    def filter(self, **kwargs): 
        """
        You need to define filters like the following example:
        >>> connection.query('example_db_name').filter(id=2).run()

        Or if you need to make any joins you define it like this:
        >>> connection.query('example_db_name').filter(connectedfield__id=2).run()

        In this example `connectedfield` would be a field of `example_db_name` table, and the `id` you are making 
        where condition is the id on `connectedfield` table.
        """       
        for key, value in kwargs.items():
            where_operation =  WHERE_SPECIAL_ARGUMENTS.get(key.split(AUTOMATIC_JOINS_PLACEHOLDER)[-1], WHERE_EQUAL_OPERATION_FORMAT)

            if where_operation != WHERE_EQUAL_OPERATION_FORMAT:
                key = AUTOMATIC_JOINS_PLACEHOLDER.join(key.split(AUTOMATIC_JOINS_PLACEHOLDER)[:-1])
            
            where_field = self.__format_db_fields(key)

            value = self.format_db_values(value)
            if where_field not in self.query_where:
                self.query_where.append(where_field + where_operation + str(value))

        return self

    def order_by(self, *args):
        """
        Expects the each column names as string. You can also make joins in your order using double undersocores
        like '__'

        You need to define order_by like the following example:
        >>> connection.query('example_db_name').order_by('id').run()
        >>> connection.query('example_db_name').order_by('id', 'name').run()

        Or if you need to order by joins you define it like this:
        >>> connection.query('example_db_name').order_by('connectedfield__id').run()

        In this example `connectedfield` would be a field of `example_db_name` table, and the `id` you are ordering
        is the id on `connectedfield` table.
        """    
        if any([type(value) != str for value in args]):
            raise TypeError('Your arguments MUST be str type')
        
        for value in args:
            asc_or_desc = ORDER_BY_ASC_FORMAT
            if value[0] == '-':
                asc_or_desc = ORDER_BY_DESC_FORMAT
                value = value[1:]
            order_clause = self.__format_db_fields(value)
            order_clause = '{} {}'.format(order_clause, asc_or_desc)
            if order_clause not in self.query_orders:
                self.query_orders.append(order_clause)

        return self

    def run(self):
        """
        Runs a SELECT type of query

        Returns:
            list/tuple: List or tuple of results
        """
        query = self.__get_query

        result = self.engine.fetch(query)
        
        if getattr(self, '_flat', False):
            result = [value[0] for value in result]
        return result
      

class Query(Select):
    def __init__(self, *args, **kwargs):
        self.join_relations = dict()
        super(Query, self).__init__(*args, **kwargs)


    @property
    def columns(self):
        """
        Returns all of the columns of the current table that you are connected to

        Returns:
            list: list with each column_name of your table as string
        """
        query = SELECT_FORMAT.format(
            select='*',
            froms=self.on_table
        ) 
        query = query + LIMIT_FORMAT.format(num=0)
        cursor = self.engine.execute(query)
        column_names = [description[0] for description in cursor.description]
        self.engine.close()
        return column_names

   
