from credentials import hostname, dbname, username, password
import pymysql

def create_conn():
    """
    Connect to the MySQL database using the credentials provided.

    Returns:
        pymysql.connections.Connection: Connection object if successful, None otherwise.
    """
    try:
        connection = pymysql.connect(user=username,
                                     password=password,
                                     host=hostname,
                                     database=dbname)
        return connection
    except pymysql.Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

def execute_scalar(connection, query, params=None):
    """
    Executes a query that returns a single value.

    Args:
        connection (pymysql.connections.Connection): Database connection.
        query (str): SQL query to execute.
        params (tuple, optional): Tuple of values to be used as parameters in
                                  the query.

    Returns:
        Any: The first value of the first row in the result set, or None if the
             result set is empty.
    """
    cursor = connection.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()[0]
    cursor.close()
    return result

def execute_query(connection, query, fetch=True, params=None):
    """
    Executes a query and optionally fetches the result set.

    Args:
        connection (pymysql.connections.Connection): Database connection.
        query (str): SQL query to execute.
        fetch (bool, optional): Whether to fetch the result set. Defaults to True.
        params (tuple, optional): Tuple of values to be used as parameters in the query.

    Returns:
        List[Tuple]: List of tuples representing the result set if fetch is True,
                     None otherwise.
    """
    cursor = connection.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall() if fetch else None
    cursor.close()
    return result

def conditions_to_where_clause(conditions):
    """
    Converts a list of conditions to a WHERE clause string.

    Args:
        conditions (List[str]): List of conditions for the WHERE clause.

    Returns:
        str: WHERE clause string.
    """
    where_clause = []
    for i in range(0, len(conditions), 2):
        where_clause.append(f"{conditions[i]} = %s")
    return " AND ".join(where_clause)

def update_column(connection, table, column, value, conditions):
    """
    Updates a column in a table with a specified value for the given conditions.

    Args:
        connection (pymysql.connections.Connection): Database connection.
        table (str): Table name to update.
        column (str): Column name to update.
        value (Any): New value for the column.
        conditions (List[str]): List of conditions to be applied in the WHERE clause.
    """
    cursor = connection.cursor()

    for condition_values in conditions:
        query = f"""
            UPDATE {table}
            SET {column} = {value}
            WHERE {conditions_to_where_clause(conditions)};
        """
        cursor.execute(query, condition_values)

    connection.commit()
    cursor.close()

def update_column_with_conditions(connection, table, column, value, conditions_list):
    """
    Updates a column in a table with a specified value for multiple sets of conditions.

    Args:
        connection (pymysql.connections.Connection): Database connection.
        table (str): Table name to update.
        column (str): Column name to update.
        value (Any): New value for the column.
        conditions_list (List[Tuple]): List of tuples containing conditions to
                                       be applied in the WHERE clause.
    """
    cursor = connection.cursor()

    for conditions in conditions_list:
        where_clause = " AND ".join([f"{col} = %s" for col, _ in conditions])
        query = f"""
            UPDATE {table}
            SET {column} = {value}
            WHERE {where_clause};
        """
        cursor.execute(query, tuple(val for _, val in conditions))

    connection.commit()
    cursor.close()
