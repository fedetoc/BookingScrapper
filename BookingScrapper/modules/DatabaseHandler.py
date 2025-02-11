import sqlite3
import os

class DatabaseHandler:
    __connection = None
    __cursor = None
    __tbl_create_queries = None
    __common_queries = {
        "CreateTableWithDefinition": "CREATE TABLE {TABLE_NAME} ({TABLE_DEFS})",
        "CheckIfTableExist": "SELECT name FROM sqlite_master WHERE name='{TABLE_NAME}'",
        "SelectAllFieldsFromATable": "SELECT * FROM {TABLE_NAME}",
        "InsertMultipleRowsToTable": "INSERT INTO {TABLE_NAME} VALUES({QUESTION_MARKS})",
        "ObtenerNombreColumnas": "SELECT name FROM PRAGMA_TABLE_INFO('{TABLE_NAME}');",
        "EliminarTablaSiExiste": "DROP TABLE IF EXISTS {TABLE_NAME}",
        "ObtenerValorMaximoDeCol": "SELECT MAX({COL_NAME}) FROM {TABLE_NAME}",
        "ObtenerCantidadFilasDeTabla": "SELECT COUNT(*) FROM {TABLE_NAME}"
    }

    def __init__(self, db:str, create_dir:str = None, schema_defs: dict = None):
        try:
            db_name = db
            if not create_dir is None and not os.path.exists(create_dir):
                os.mkdir(create_dir)
            self.db_name, self.__connection, self.__cursor = self.__connect_to_db(create_dir + '/' + db)
            if not schema_defs is None:
                self.__tbl_create_queries = self.__construct_table_creation_queries(schema_defs)
        except Exception as err:
            raise(err)

    def __del__(self):
        self.close_connection()

    def __connect_to_db(self, db:str):
        db_str = db
        if db_str[-3:] != ".db":
            db_str = db_str + ".db"
        try:
            con = sqlite3.connect(db_str)
            cur = con.cursor()
            print(f'Conectado satisfactoriamente a db {db_str}')
        except sqlite3.Error as err:
            raise(self.__construct_sqlite_exception(err, "conectar a db"))
            return (None, None)
        return (db_str, con, cur)

    def __construct_table_creation_queries(self, schema_defs: dict):
        create_queries = {}
        for dic_key in list(schema_defs.keys()):
            columns_def_str = ""
            tbl_def = schema_defs[dic_key]
            it = 0
            for col_def in tbl_def:
                columns_def_str = columns_def_str + " ".join(col_def)
                if it < len(tbl_def)-1:
                    columns_def_str = columns_def_str + ", "
                it = it + 1
            create_queries[dic_key] = self.__common_queries["CreateTableWithDefinition"] \
                                        .replace('{TABLE_NAME}', dic_key) \
                                        .replace('{TABLE_DEFS}', columns_def_str)
        return create_queries

    def __table_exists_in_db(self, table_name:str):
        if self.__connection is None:
            raise(Exception(f'No db connection, no se puede verificar si la tabla {table_name} existe'))
        query = self.__common_queries["CheckIfTableExist"].replace('{TABLE_NAME}', table_name)
        res = self.__cursor.execute(query).fetchone()
        if res is None:
            return False
        return True

    def __construct_sqlite_exception(self, err, accion:str):
        error_code = err.sqlite_errorcode
        error_name = err.sqlite_errorname
        return Exception(f'Ocurrio un error al intentar {accion}: Codigo {error_code}. Nombre {error_name}')

    def create_tables(self, schema_defs:dict = None):
        tbl_defs = {}
        if schema_defs is None:
            if self.__tbl_create_queries is None:
                raise(Exception("No se ha cargado una definición de esquema para esta instancia"))
                return
        else:
            self.__tbl_create_queries = self.__construct_table_creation_queries(schema_defs)
        for tbl in list(self.__tbl_create_queries.keys()):
            if self.__table_exists_in_db(tbl) == False:
                try:
                    query = self.__tbl_create_queries[tbl]
                    self.__cursor.execute(query)
                    print(f'Tabla {tbl} creada satisfactoriamente')
                except sqlite3.Error as err:
                    raise(self.__construct_sqlite_exception(err, f'crear tabla {tbl} con query {query}'))
                    break;
            else:
                print(f'La tabla {tbl} ya existe en esta db. Procediendo a siguiente.')
        return

    def insert_into_table(self, tbl:str, data:list[tuple]):
        if self.__table_exists_in_db(tbl) == False:
            raise(Exception(f'La tabla {tbl} no existe en la presente base de datos'))
            return
        query = self.__common_queries["InsertMultipleRowsToTable"] \
                .replace('{TABLE_NAME}', tbl) \
                .replace('{QUESTION_MARKS}', "".ljust(len(data[0]), "?").replace("?", "?, ")[:-2])
        try:
            print("Insertando registros...")
            self.__cursor.executemany(query, data)
            self.__connection.commit()
        except sqlite3.Error as err:
            raise(self.__construct_sqlite_exception(err, f'insertar registros en tabla {tbl}'))
        print(f'Se han insertado {len(data)} registros en la tabla {tbl}')

    def get_all_cols_and_rows_from_tbl(self, tbl:str, include_colnames = False):
        if self.__table_exists_in_db(tbl) == False:
            raise(Exception(f'La tabla {tbl} no existe en la presente base de datos'))
            return
        query = self.__common_queries["SelectAllFieldsFromATable"] \
                 .replace('{TABLE_NAME}', tbl)
        try:
            exec_res = self.__cursor.execute(query)
            results = exec_res.fetchall()
            if include_colnames==True:
                colnames_query = self.__common_queries["ObtenerNombreColumnas"] \
                                    .replace('{TABLE_NAME}', tbl)
                exec_colnames_res = self.__cursor.execute(colnames_query)
                colnames_res = exec_colnames_res.fetchall()
                results = (results, [col[0] for col in colnames_res])
        except sqlite3.Error as err:
            raise(self.__construct_sqlite_exception(err, f'seleccionar registros en tabla {tbl}'))
            return None
        return results

    def get_max_of_a_col(self, col:str, tbl:str):
        query = self.__common_queries["ObtenerValorMaximoDeCol"] \
                .replace('{COL_NAME}', col) \
                .replace('{TABLE_NAME}', tbl)
        try:
            exec_res = self.__cursor.execute(query)
            result = exec_res.fetchone()[0]
        except sqlite3.Error as err:
            raise(self.__construct_sqlite_exception(err, f'seleccionar registros en tabla {tbl}'))
            return None
        return result

    def get_row_count(self, tbl:str):
        query = self.__common_queries["ObtenerCantidadFilasDeTabla"] \
                .replace('{TABLE_NAME}', tbl)
        try:
            exec_res = self.__cursor.execute(query)
            result = exec_res.fetchone()[0]
        except sqlite3.Error as err:
            raise(self.__construct_sqlite_exception(err, f'seleccionar registros en tabla {tbl}'))
            return None
        return result

    
    def eliminate_tables(self, tbl_list:list):
        for tbl in tbl_list:
            query = self.__common_queries["EliminarTablaSiExiste"].replace('{TABLE_NAME}', tbl)
            try:
                self.__connection.execute(query)
                print(f'La tabla {tbl} fue eliminada correctamente')
            except sqlite3.Error as err:
                raise(self.__construct_sqlite_exception(err, f'eliminar la tabla {tbl}'))
                return

    def close_connection(self):
        if not self.__cursor is None:
            self.__cursor.close()
        if not self.__connection is None:
            self.__connection.close()