'''
Name: ACFT Database
Author: SPC Montgomery, Amir
Date: 20240604

Objective: Create a SQLite3 database for ACFT scores

'''

import sqlite3, re, csv, os
from os import path

class DatabaseManager:
    def __init__(self, db):
        self.conn = sqlite3.connect(db)
        self.conn.commit()
        self.cur = self.conn.cursor()

    def query(self, arg):
        self.cur.execute(arg)
        self.conn.commit()
        return self.cur
    
    def is_empty(self):
        self.cur.execute('SELECT name FROM sqlite_master')
        res = self.cur.fetchall()
        return len(res) == 0 # True return if empty
    
    def execute_many(self, table, data):
        command = f"INSERT INTO {table} VALUES(?, ?, ?, ?)"
        self.cur.executemany(command, data)
        self.conn.commit()
        return self.cur
    
    def __del__(self):
        self.conn.close()

def convert_scoring_list(list): # only for use for converting a list of ['Age', 'Sex', 'Output', 'Score']
    return [int(list[0]), list[1], float(list[2]), int(list[3])]

def get_scoring_data(exercise, directory):
    big_data = []

    exercise_file = f"{exercise}_csv.csv"
    exercise_file = os.path.join(directory, os.path.normcase(exercise_file))

    with open(exercise_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
            big_data.append(convert_scoring_list(row))
    
    return big_data

def pull_exercise(input): # input should be exercise_csv.csv, just remove _csv.csv
    csv_name = r"(\w+)_csv.csv"
    full_name = re.compile(csv_name)

    m = full_name.search(input)

    if m:
        return m.group(1)
    
    return -1        

def fill_empty_database(directory, events, dbmgr):
    # Fill the empty databases with the ACFT scoring system
    '''
    Age,Sex,Output,Score

    exercise_point_table
    age | sex    | output | score
    17  | male   | x      | x
    17  | female | x      | x
    22  | male   | x      | x
    22  | female | x      | x

    '''
    for i in range(len(events)): # for each exercise in the event_scoring table
        #exercise = pull_exercise(scoring(i))
        exercise = events[i]

        table_name = f"{exercise}_point_table"
        
        # create a table "CREATE TABLE {table_name}(age, sex, output, score)"
        create_table_command = f"CREATE TABLE {table_name}(age, sex, output, score)"
        dbmgr.query(create_table_command)

        # get scores and insert into the table
        big_data = get_scoring_data(exercise, directory) # ['Age', 'Sex', 'Output', 'Score']
        #print(big_data)
        dbmgr.execute_many(table_name, big_data)
        '''for i in range(len(big_data)): 
            value_string = f"INSERT INTO {table_name} VALUES({int(big_data[i][0])}, {big_data[i][1]}, {big_data[i][2]}, {int(big_data[i][3])})"
            dbmgr.query(value_string)'''

def close_database_connection(dbmgr):
    dbmgr.__del__()

def init_database_connection():
    main_directory = os.getcwd()
    events = ["deadlift", "plank", "powerthrow", "releasePU", "run", "sdc"]

    # db_string = os.path.normcase(os.path.join(main_directory, "Scoring/acftdatabase.db"))
    #print(db_string)
    db_string = path.abspath(path.join(path.dirname(__file__), 'acftdatabase.db')) # path to included database
    dbmgr = DatabaseManager(db_string) # Implicitly creates db file if not found.
    
    # check if the database is empty
    empty_check = dbmgr.is_empty()
    if empty_check: # might need to change this, but if I'm including the database in the package...
        fill_empty_database(os.path.join(main_directory, os.path.normcase("Scoring")), events, dbmgr)

    return dbmgr