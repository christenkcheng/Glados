from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
import configparser, os
from robot.libraries.BuiltIn import BuiltIn
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError, OperationalError

def run_query(db, query):
    """
    Run SQL query on targeted environment db and return results when appropriate.
    :param db:      The target database to execute on
    :param query:   SQL query to execute

    :return:    SELECT - A result set or None
                INSERT - (MySQL) The Primary Key value of the created row.
    """
    parser = configparser.RawConfigParser(allow_no_value=True)
    # Try to read the db_connection_info.ini file in the same folder
    try:
        script_dir = os.path.dirname(__file__)
        file_name = 'db_connection_info.ini'
        abs_file_path = os.path.join(script_dir, file_name)
        parser.readfp(open(abs_file_path))
    except:
        print('Could not open db_connection_info.ini file, check file location: ' + abs_file_path)
    db_type =   parser.get(db, 'db_type')
    user =      parser.get(db, 'user')
    password =  parser.get(db, 'password')
    host =      parser.get(db, 'host')
    port =      parser.get(db, 'port')
    db_name =   parser.get(db, 'db_name')
    schema =    parser.get(db, 'schema')
    convert_unicode = True
    sql_debug = False

    conn_str = db_type + user + ":" + password + "@" + host + ":" + port + "/" + db_name
    conn = None
    
    try:
        engine = create_engine(conn_str,
                                convert_unicode=convert_unicode,
                                echo=sql_debug,
                                poolclass=NullPool,
                                isolation_level="AUTOCOMMIT")
        conn = engine.connect()
        
        if schema != '': # schema needs to be set for some DBs.
            conn.execute('SET search_path TO ' + schema)
        
        print("Executing query:\n%s" % (query))
        
        results = conn.execute(query)
    except OperationalError as e:
        err_no = e.orig.args[0]
        err_msg = e.orig.args[1]
        if err_no == 2005:
            raise RuntimeError("Connection Failed: Database at \"%s\" was unreachable.\n\nException:\n%s: %s" % (conn_str, err_no, err_msg))
        raise RuntimeError(err_msg)
    except Exception as e:
        raise SQLAlchemyError("Caught exception while executing query:\n{q}\n\nSQL Exception:\n{e}".format(q=query, e=e))
    finally:
        try:
            conn.close()
        except:
            print("DB connection already terminated.")

    if results.returns_rows:
        return results.fetchall()
    elif results.is_insert:
        return results.inserted_primary_key
    
    return None




