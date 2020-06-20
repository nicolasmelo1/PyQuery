from .settings import (
    WHERE_SPECIAL_ARGUMENTS, AUTOMATIC_JOINS_PLACEHOLDER, 
    FIELD_FORMAT, SELECT_FORMAT, JOIN_CLAUSE_FORMAT, WHERE_CLAUSE_FORMAT, WHERE_AND_CONNECTOR_FORMAT,
    WHERE_EQUAL_OPERATION_FORMAT, ORDER_BY_CLAUSE_FORMAT, ORDER_BY_ASC_FORMAT, ORDER_BY_DESC_FORMAT,
    LIMIT_FORMAT,VALUE_STRING_FORMAT, VALUE_LIST_FORMAT, VALUE_TUPLE_FORMAT, VALUE_NULL_FORMAT, VALUE_DATETIME_FORMAT,
    VALUE_SINGLE_QUOTE_FORMAT, DISTINCT_CLAUSE_FORMAT, FIELD_OR_TABLES_FORMAT
)

from datetime import datetime
import math
import random


class BaseQuery:
    def __init__(self, on_table, engine):
        self.engine = engine
        self.on_table = on_table
        # first value of the tuple is the original table name, the second, the value we are using
        self.fields_table_relations={
            '':dict(table_name=on_table, is_alias=False)
        }

    def _format_db_tables_names(self, value):
        """
        A single key of fields_table_relations dict

        Args:
            value (dict) a singe dict of the fields_table_relations dict
        """
        if value['is_alias']:
            return value['table_name']
        else:
            return self._format_field_or_tables(value['table_name'])

    def _format_field_or_tables(self, value):
        return FIELD_OR_TABLES_FORMAT.format(value)

    def __create_table_name_alias(self, table_name):
        """
        Creates a new alias for the table
        """
        alias = 'TA{}'.format(str(random.randint(1,100)))
        invalid_aliases = [value['table_name'] for value in self.fields_table_relations.values()]
        while alias in invalid_aliases:
            alias = 'TA{}'.format(str(random.randint(1,100)))
        return alias

    def _get_table_name_or_alias(self, query_path, table_name):
        if query_path in self.fields_table_relations:
            return self.fields_table_relations[query_path]

        if table_name in [value['table_name'] for value in self.fields_table_relations.values()]:
            self.fields_table_relations[query_path] = {
                'table_name': self.__create_table_name_alias(table_name),
                'is_alias': True
            }
        else:
            self.fields_table_relations[query_path] = {
                'table_name': table_name,
                'is_alias': False
            }
        return self.fields_table_relations[query_path]
        
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
        to_table_join = self.fields_table_relations['']
        reference_string_list = list()

        for index, join in enumerate(joins):
            # creates a reference of the path to the fields so something like
            # depends_on__group__company and so on, with this path we can reuse the created aliases
            reference_string_list.append(join)
            reference_string = '__'.join(reference_string_list)
            from_table_join = to_table_join
            
            # automatically creates alias
            to_table_join_name = self.join_relations.get(from_table_join['table_name'], {}).get(join, join)
            to_table_join = self._get_table_name_or_alias(reference_string, to_table_join_name)
            
            join_clause = JOIN_CLAUSE_FORMAT.format(
                join=join, 
                from_table_join=self._format_db_tables_names(from_table_join),
                to_table_join=FIELD_OR_TABLES_FORMAT.format(to_table_join_name),
                to_table_join_name_or_alias=self._format_db_tables_names(to_table_join),
                alias=to_table_join['table_name'] if to_table_join['is_alias'] else ''
            )

            if join_clause not in self.query_joins:
                self.query_joins.append(join_clause)
        return self._format_db_tables_names(to_table_join)
    
    def _format_db_fields(self, value):
        """
        Formats each database field based on a default VALUE_CLAUSE
        """
        table_name = self._format_db_tables_names(self.fields_table_relations[''])

        splitted_value = value.split(AUTOMATIC_JOINS_PLACEHOLDER)
        if len(splitted_value) > 1:
            # Handle automatic join operations
            joins = splitted_value[:-1]
            table_name = self.__format_joins(joins)

        values_to_use = splitted_value[-2:]
        value = FIELD_FORMAT.format(
            table=table_name, 
            field=self._format_field_or_tables(values_to_use[-1])
        )
    
        
        return value

    def format_db_values(self, value):
        if type(value) == str:
            value = VALUE_STRING_FORMAT.format(value.replace("'",VALUE_SINGLE_QUOTE_FORMAT))

        if type(value) == list:
            value = VALUE_LIST_FORMAT.format(', '.join([str(self.format_db_values(val)) for val in value]))

        if type(value) == datetime:
            value= VALUE_STRING_FORMAT.format(value.strftime(VALUE_DATETIME_FORMAT))
        
        if type(value) == tuple:
            value = '{}'.format(', '.join([str(self.format_db_values(val)) for val in value]))

        if type(value) == self.__class__:
            value = self.format_db_values(list(value))

        if value == None:
            value = VALUE_NULL_FORMAT
            
        return value

class Insert(BaseQuery):
    def bulk_insert(self, values, column_names=None):
        """
        This is optimize to be quicker than insert, all your arguments EXCEPTS column names must be a list of values
        To be easier you can use it like this:
        >>> connection.query('form_value').bulk_insert(values=[[1,2], [3,4], [4,5]], column_names=['column_a', 'column_b'])

        Use with the * for positional arguments

        Args:
            column_names (list): the column names as a list

        Returns:
            bool: returns True if everything went fine
        """
        values = tuple(list(value) for value in values)
        columns = column_names if column_names else self.columns
        maximum_number_of_values_per_iteration = 999
        iterations = math.ceil(len(values)/maximum_number_of_values_per_iteration)

        self.engine.connect()
        for iteration in range(0, iterations):
            iteration_values = values[iteration*maximum_number_of_values_per_iteration : (iteration+1)*maximum_number_of_values_per_iteration]
            query = self._format_insert(tuple(iteration_values), columns)
            self.engine.execute(query)
        self.engine.commit()
        return True

    def insert(self, **kwargs):
        """
        Inserts an handful amount of data in the database

        Returns:
            [type]: [description]
        """
        columns = kwargs.keys()
        values = list(kwargs.values())
        query = self._format_insert(values, columns)
        print(query)
        #self.engine.save(query)
        return True


    def _format_insert(self, values, columns):
        INSERT_CLAUSE = 'INSERT INTO "{}" ({}) VALUES {}'
        return INSERT_CLAUSE.format(
            self.on_table, 
            ', '.join(['"{}"'.format(column) for column in columns]),
            self.format_db_values(values)
        )


class Select(BaseQuery):
    """
    Class responsible for handling select statements.
    """
    def __init__(self, join_relations, *args, **kwargs):
        self.join_relations = join_relations
        self.query_select = ['*']
        self.query_distinct = ''
        self.query_orders = []
        self.query_where = []
        self.query_limit = ''
        self.query_joins = []
        super(Select, self).__init__(*args, **kwargs)

    @property
    def __get_query(self):
        query = SELECT_FORMAT.format(
            select=', '.join(self.query_select),
            distinct=DISTINCT_CLAUSE_FORMAT,
            froms=self.on_table
        )
        
        joins = '{} '.format(' '.join(self.query_joins)) if self.query_joins else ''
        where = WHERE_CLAUSE_FORMAT.format(where_conditions=WHERE_EQUAL_OPERATION_FORMAT.join(self.query_where)) if self.query_where else ''
        orders = ORDER_BY_CLAUSE_FORMAT.format(order_by_conditions=', '.join(self.query_orders)) if self.query_orders else ''
        limit = self.query_limit

        query = query + joins + where + orders + limit
        return query

    @property
    def query(self):
        return self.__get_query


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

    def distinct(self):
        self.query_distinct = DISTINCT_CLAUSE_FORMAT
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
            select_clause = self._format_db_fields(value)
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
            
            where_field = self._format_db_fields(key)

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
            order_clause = self._format_db_fields(value)
            order_clause = '{} {}'.format(order_clause, asc_or_desc)
            if order_clause not in self.query_orders:
                self.query_orders.append(order_clause)

        return self

    def force(self):
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

class Query(Insert, Select):
    def __repr__(self):
        return str(self.force())

    def __getstate__(self):
        return self.force()

    def __iter__(self):
        return iter(self.force())

    def __bool__(self):
        return bool(self.force())

    def __getitem__(self, k):
        return self.force()[k]

    @property
    def columns(self):
        """
        Returns all of the columns of the current table that you are connected to

        Returns:
            list: list with each column_name of your table as string
        """
        query = SELECT_FORMAT.format(
            select='*',
            distinct='',
            froms=self.on_table
        )
        self.engine.connect()
        query = query + LIMIT_FORMAT.format(num=0)
        cursor = self.engine.execute(query)
        column_names = [description[0] for description in cursor.description]
        self.engine.close()
        return column_names
