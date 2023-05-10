from credentials import hostname, dbname, username, password
import pymysql

# Connect to MySQL database
def create_conn():
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
    cursor = connection.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()[0]
    cursor.close()
    return result

def execute_query(connection, query, fetch=True, params=None):
    cursor = connection.cursor()
    cursor.execute(query, params)
    result = cursor.fetchall() if fetch else None
    cursor.close()
    return result

def conditions_to_where_clause(conditions):
    where_clause = []
    for i in range(0, len(conditions), 2):
        where_clause.append(f"{conditions[i]} = %s")
    return " AND ".join(where_clause)

def update_column(connection, table, column, value, conditions):
    cursor = connection.cursor()

    for condition_values in conditions:
        where_clause = conditions_to_where_clause(conditions)
        query = f"""
            UPDATE {table}
            SET {column} = {value}
            WHERE {where_clause};
        """
        cursor.execute(query, condition_values)

    connection.commit()
    cursor.close()
