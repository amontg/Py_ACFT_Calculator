'''
Name: Roster Database
Author: SPC Montgomery, Amir
Date: 20230610

Objective: Create a SQLite3 database for given rosters

'''

import sqlite3, os, acftcalculator

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
    
    def execute_many(self, table, data): # values will be a full csb
        command = f"INSERT INTO {table} VALUES(?, ?, ?, ?)"
        self.cur.executemany(command, data)
        self.conn.commit()
        return self.cur
    
    def insert_unencrypteddata(self, data):
        command = f"INSERT INTO roster VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        self.cur.execute(command, data)
        self.conn.commit()
        return self.cur
    
    def insert_encrypteddata(self, data):
        command = f"INSERT INTO encrypted_roster VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        self.cur.execute(command, data)
        self.conn.commit()
        return self.cur
    
    def insert_hashnsalt(self, hashed_pw, salt):
        command = f"INSERT INTO encryption VALUES(1, ?, ?)"
        data = [hashed_pw, salt]
        self.cur.execute(command, data)
        self.conn.commit()
        return self.cur
    
    def new_tables(self):
        create_new_table(self)
    
    def __del__(self):
        self.conn.close()

def csb_to_db(roster, soldier_db):
    '''
        roster.soldier_dict = {
            "name": csb,
            "name": csb,
        }
    '''
    
    create_new_table(soldier_db)

    for profile in roster.soldier_dict.values():
        # INSERT INTO table
        #print(profile)
        find_string = f"SELECT rowid FROM roster WHERE name='{profile.name}'"
        find_val = soldier_db.query(find_string)
        if find_val.fetchone() != None:
            update_line = f"UPDATE roster SET age={profile.age}, sex='{profile.sex}', total={profile.total_points}, deadlift_out={profile.deadlift_output}, deadlift_points={profile.deadlift_points}, powerthrow_out={profile.powerthrow_output}, powerthrow_points={profile.powerthrow_points}, releasePU_out={profile.releasePU_output}, pushup_points={profile.releasePU_points}, sdc_out={profile.sdc_output}, sdc_points={profile.sdc_points}, plank_out={profile.plank_output}, plank_points={profile.plank_points}, run_out={profile.run_output}, run_points={profile.run_points} WHERE name='{profile.name}'"
            soldier_db.query(update_line)
        else:
            insert_line = f"INSERT INTO roster VALUES{profile.name, profile.age, profile.sex, profile.total_points, profile.deadlift_output, profile.deadlift_points, profile.powerthrow_output, profile.powerthrow_points, profile.releasePU_output, profile.releasePU_points, profile.sdc_output, profile.sdc_points, profile.plank_output, profile.plank_points, profile.run_output, profile.run_points}"
            #print(insert_line)
            soldier_db.query(insert_line)

def db_to_csb(active_roster, soldier_db, scoring_db):
    # for each line, make a csb with the information
    get_records_line = "SELECT name, age, sex, deadlift_out, powerthrow_out, releasePU_out, sdc_out, plank_out, run_out FROM roster"
    for row in soldier_db.query(get_records_line):
        # row raw = ['Name', 'Age', 'Sex', 'Deadlift', 'Powerthrow', 'ReleasePU', 'SDC', 'Plank', 'Run']
        csb = acftcalculator.create_soldier_profile([row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8]], scoring_db)
        active_roster.add_soldier(csb, csb.name)

    return active_roster
        
def create_new_table(db):
    # CREATE TABLE roster(name, age, sex, total, deadlift_out, deadlift_points, powerthrow_out, powerthrow_points, pushup_out, pushup_points, sdc_out, sdc_points, plank_out, plank_points)
    db.query("CREATE TABLE IF NOT EXISTS roster(name, age, sex, total, deadlift_out, deadlift_points, powerthrow_out, powerthrow_points, releasePU_out, pushup_points, sdc_out, sdc_points, plank_out, plank_points, run_out, run_points)")
    db.query("CREATE TABLE IF NOT EXISTS encryption(encrypted INTEGER, hash TEXT, salt BLOB)") # True/False, Hashed PW, Salt

def close_database_connection(dbmgr):
    dbmgr.__del__()

def init_database_connection(db):
    #events = ["deadlift", "plank", "powerthrow", "releasePU", "run", "sdc"]
    dbmgr = DatabaseManager(os.path.normcase(db)) # Implicitly creates db file if not found.
    return dbmgr
