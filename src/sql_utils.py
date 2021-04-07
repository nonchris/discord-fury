#built in
import sqlite3
from sqlite3 import Error

#own files
import data.config as config

"""
YES - This code IS vulnerable for SQL injections - I know it's is flawed...

BUT: there is no direct user-input passed into these statements
All string entries are hardcoded / mapped trough a dict that is controlled via user input as key
and every integer comes directly from the discord API

So there should be nothing to worry about.
If you detect a weakness, please open an issue on GitHub
Or if you're interested into doing a rewrite using SQLAlchemy, sure! Let's work together ^^

I might do this on my own at some point, but not now...
"""


def get_sql(setting, table_name, column="setting", name=None):
    """
    Every list contained in the dicts has the follwoing parameters:
    [0] CREATE TABLE
    [1] Basic INSERT INTO   - full line
    [2] Basic SELECT *     - selects all
    [3] Select WHERE =      - searches for string in column
    """

    sql_switch = {
            "setting": [
                """
                CREATE TABLE IF NOT EXISTS "{0}" (
                key INTEGER PRIMARY KEY,
                setting text,  
                value text,     
                value_id integer, 
                set_date date, 
                table_version integer
                )
                """.format(table_name),
                

                """ INSERT INTO "{0}"
                (setting, value, value_id, set_date, table_version)
                VALUES(?,?,?,?,?)
                """.format(table_name),

                """ SELECT * FROM {0}; """.format(table_name),

                """ SELECT * FROM {0} WHERE {1} = '{2}'; """.format(table_name, column, name),
                
                """ DELETE FROM {0} WHERE {1} = {2}; """.format(table_name, column, name),
                ],

            "created_channels": [
                """
                CREATE TABLE IF NOT EXISTS "{0}" (
                type text,      
                channel_id integer PRIMARY KEY, 
                linked_id integer,
                set_date date, 
                table_version integer
                )
                """.format(table_name),
                

                """ INSERT INTO "{0}"
                (type, channel_id, linked_id, set_date, table_version)
                VALUES(?,?,?,?,?)
                """.format(table_name),

                """ SELECT * FROM {0}; """.format(table_name),

                """ SELECT * FROM {0} WHERE {1} = {2}; """.format(table_name, column, name),
                
                """ DELETE FROM {0} WHERE {1} = {2}; """.format(table_name, column, name),
                ],

        }

    return (sql_switch[setting])



class DbConn:

    def __init__(self, db_file, server_id, scheme):

    #def create_connection(self, db_file):
        """create a db connection to SQLite"""
        #check if type is correct - needed cause names could break the code eg "/" in name
        tns = {
            "setting": f"s{server_id}",
            "created_channels": f"ch{server_id}"
        }   

        try: 
            int(server_id)
            self.file_name = db_file
            self.table_name = tns[scheme]
            self.scheme = scheme
            self.table_sql = get_sql(self.scheme, self.table_name)
            self.con = None
        except:
            raise TypeError("The table creation needs a server id")

        try:
            self.con = sqlite3.connect(self.file_name)
            #print("connected")
            self.cur = self.con.cursor()
            self.create_server_table()
            #print("currrrr")
            #self.create_server_table()
        except Error as e:
            print(e)
        
        #return self.conn


    def create_server_table(self):
        """
        TABLE NAME: The Server ID
        setting: setting of the setting (e.g. pub-channel)
        value: value of the setting (e.g. channel name)
        value_id: id of that object (e.g. channel ID)
        set_date: date this setting was made
        table_version: saves the current (db access structure)
        -> if there is an update you can locate lines that were made with 1.0 access to update them
        """
        #print("called")
        try:
            #self.cur = self.conn.cursor()
            self.cur.execute(self.table_sql[0])
            return True
        except Error as e:
            print(e)

    #writing to server table
    def write_server_table(self, entry: tuple):
        #print("write")
        job = self.table_sql[1]
        #print("starting")
        #self.cur = conn.cursor()
        #print(job)
        self.cur.execute(job, entry)
        #print("comm")
        self.con.commit()


    def read_server_table(self) -> list:
        #print("read")
        job = self.table_sql[2]
        
        self.cur.execute(job)
        self.all_rows = self.cur.fetchall()
        #print("fetched")
        return self.return_values()


    def search_table(self, value="", column="setting") -> list:
        """
        Search for a specific value in a column
        WHERE column = setting -> returns a list containing objects with search results
        """
        #refreshing sql code, because we've got a new parameter for sql code
        self.table_sql = get_sql(self.scheme, self.table_name, name=value, column=column)
        job = self.table_sql[3]
        #print(job)
        self.cur.execute(job)
        #gettings rows
        self.all_rows = self.cur.fetchall()
        #getting return value
        return self.return_values()


    def remove_line(self, name, column="setting"):
        #refresh sql
        self.table_sql = get_sql(self.scheme, self.table_name, column=column, name=name)
        job = self.table_sql[4]

        self.cur.execute(job)
        self.con.commit()
        #print("deleted")


    def return_values(self) -> list:
        """
        Gets the return values from a separate class
        Objects in list will be class object with entries as values
        """
        self.entries = []
        for line in list(self.all_rows):
            entry = SQL_to_Obj(self.scheme, line)
            self.entries.append(entry)
        return self.entries


#class SQL_return:
class SQL_to_Obj:
    """
    Takes the SQL entries (tuples) and builds an object
    """
    def __init__(self, scheme, entry: tuple):
        """
        Switches between object "style" according to table style
        """
        self.entry = entry
        make_object = {
            "settings": self.settings(),
            "created_channels": self.created_channels()
        }

    def settings(self):
        #print(type(self.entry[2]))
        self.setting = self.entry[1]
        self.value = self.entry[2]
        self.value_id = self.entry[3]
        self.date = self.entry [4]

    def created_channels(self):
        #print(type(self.entry[2]))
        self.type = self.entry[0]
        self.channel = self.entry[1]
        self.linked_channel = self.entry[2]
        self.date = self.entry[3]

