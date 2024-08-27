'''
Name: ACFT Calculator
Author: SPC Montgomery, Amir
Date: 20230604

Objective: Import CSVs files with ACFT scores and calculate the individual scores and overall score based on sex and age

'''
import acftdatabase, math, filereader

class FlagCatcher:
    def __init__(self):
        self.flagged = False
        self.flags = []

class IndividualSoldier:
    def __init__(self, name="Name", age=0, sex="Sex", dl_out=0.0, pt_out=0.0, rpu_out=0.0, sdc_out=0.0, plank_out=0.0, run_out=0.0):
        self.name = name 
        self.age = age
        self.bracket = get_age_bracket(self.age)

        self.sex = sex
        self.deadlift_output = float(dl_out) # lbs
        self.deadlift_points = 0

        self.powerthrow_output = float(pt_out) # meters
        self.powerthrow_points = 0

        self.releasePU_output = float(rpu_out) # reps
        self.releasePU_points = 0

        self.sdc_output = sdc_out # time
        self.sdc_points = 0

        self.plank_output = plank_out # time
        self.plank_points = 0

        self.run_output = run_out # time
        self.run_points = 0

        self.total_points = 0

        self.flagged = False
        self.flags = []

    def calc_total_points(self):
        self.total_points = self.deadlift_points + self.powerthrow_points + self.releasePU_points + self.sdc_points + self.plank_points + self.run_points

    def soldier_to_csv(self):
        struct = [self.name, self.age, self.sex, f"{self.deadlift_output} ({self.deadlift_points})", f"{self.powerthrow_output} ({self.powerthrow_points})", f"{self.releasePU_output}, ({self.releasePU_points})", f"{self.sdc_output} ({self.sdc_points})", f"{self.plank_output} ({self.plank_points})", f"{self.run_output} ({self.run_points})"]
        return struct

    def print_soldier(self):
        print(f"""{self.name} | Sex: {self.sex} | Age: {self.age}
        Deadlift ({self.deadlift_output}): {self.deadlift_points}
        Powerthrow ({self.powerthrow_output}): {self.powerthrow_points}
        Release PU ({self.releasePU_output}): {self.releasePU_points}
        SDC ({self.sdc_output}): {self.sdc_points}
        Plank ({self.plank_output}): {self.plank_points}
        Run ({self.run_output}): {self.run_points}
        Total: {self.total_points}""")

class HighsLows:
    def __init__(self, age, sex):
        self.db = acftdatabase.init_database_connection()
        self.exercises = ["deadlift", "powerthrow", "releasePU", "sdc", "plank", "run"]

        self.age = get_age_bracket(age)

        self.deadlift_high = (self.db.query(f"SELECT output FROM deadlift_point_table WHERE sex='{sex}' AND age={self.age} AND score=100").fetchone())[0]
        self.deadlift_low = (self.db.query(f"SELECT output FROM deadlift_point_table WHERE sex='{sex}' AND age={self.age} AND score=0").fetchone())[0]

        self.powerthrow_high = (self.db.query(f"SELECT output FROM powerthrow_point_table WHERE sex='{sex}' AND age={self.age} AND score=100").fetchone())[0]
        self.powerthrow_low = (self.db.query(f"SELECT output FROM powerthrow_point_table WHERE sex='{sex}' AND age={self.age} AND score=0").fetchone())[0]

        self.releasePU_high = (self.db.query(f"SELECT output FROM releasePU_point_table WHERE sex='{sex}' AND age={self.age} AND score=100").fetchone())[0]
        self.releasePU_low = (self.db.query(f"SELECT output FROM releasePU_point_table WHERE sex='{sex}' AND age={self.age} AND score=0").fetchone())[0]

        self.sdc_high = (self.db.query(f"SELECT output FROM sdc_point_table WHERE sex='{sex}' AND age={self.age} AND score=100").fetchone())[0]
        self.sdc_low = (self.db.query(f"SELECT output FROM sdc_point_table WHERE sex='{sex}' AND age={self.age} AND score=0").fetchone())[0]

        self.plank_high = (self.db.query(f"SELECT output FROM plank_point_table WHERE sex='{sex}' AND age={self.age} AND score=100").fetchone())[0]
        self.plank_low = (self.db.query(f"SELECT output FROM plank_point_table WHERE sex='{sex}' AND age={self.age} AND score=0").fetchone())[0]

        self.run_high = (self.db.query(f"SELECT output FROM run_point_table WHERE sex='{sex}' AND age={self.age} AND score=100").fetchone())[0]
        self.run_low = (self.db.query(f"SELECT output FROM run_point_table WHERE sex='{sex}' AND age={self.age} AND score=0").fetchone())[0]

def get_age_bracket(age):
    # brackets are 17-21, 22-26, 27-31, 32-36, 37-41, 42-46, 47-51, 52-64, 57-61, 62+
    slider = math.floor((age - 17) / 5)
    bracket = 17 + (5 * slider)
    if bracket > 62:
        bracket = 62

    return bracket

def get_database():
    dbmgr = acftdatabase.init_database_connection()
    return dbmgr

def time_to_float(input): # input as a string "00:00"
    input = input.replace(":", ".")
    return float(input)

def float_to_time(input):
    input = str(input)
    input = input.replace(".", ":")
    min, sec = input.split(":")
    while len(min) < 2:
        min = f"0{min}"
    
    while len(sec) < 2:
        sec = f"{sec}0"

    return f"{min}:{sec}"

def calculate_scores(csb, dbmgr):
    # events = ["deadlift", "powerthrow", "releasePU", "sdc", "plank", "run"]
    # SELECT score FROM exercise_point_table WHERE age = csb.bracket AND sex = X AND output = X
    # exercise_point_table(age, sex, output, score)

    # deadlift
    score_string = f"SELECT score FROM deadlift_point_table WHERE age = {csb.bracket} AND sex = '{csb.sex}' AND output <= {csb.deadlift_output}"
    score = (dbmgr.query(score_string)).fetchone()
    deadlift_score = 0 if score == "None" or score == None else (score)[0]
    #print(deadlift_score[0])
    csb.deadlift_points = deadlift_score

    # powerthrow
    score_string = f"SELECT score FROM powerthrow_point_table WHERE age = {csb.bracket} AND sex = '{csb.sex}' AND output <= {csb.powerthrow_output} LIMIT 1"
    score = (dbmgr.query(score_string)).fetchone()
    powerthrow_score = 0 if score == "None" or score == None else (score)[0]
    #print(powerthrow_score[0])
    csb.powerthrow_points = powerthrow_score

    # releasePU
    score_string = f"SELECT score FROM releasePU_point_table WHERE age = {csb.bracket} AND sex = '{csb.sex}' AND output <= {csb.releasePU_output} LIMIT 1"
    score = (dbmgr.query(score_string)).fetchone()
    releasePU_score = 0 if score == "None" or score == None else (score)[0]
    #print(releasePU_score[0])
    csb.releasePU_points = releasePU_score

    # sdc
    score_string = f"SELECT score FROM sdc_point_table WHERE age = {csb.bracket} AND sex = '{csb.sex}' AND output >= {csb.sdc_output} LIMIT 1"
    score = (dbmgr.query(score_string)).fetchone()
    sdc_score = 0 if score == "None" or score == None else (score)[0]
    #print(sdc_score[0])
    csb.sdc_points = sdc_score

    # plank
    score_string = f"SELECT score FROM plank_point_table WHERE age = {csb.bracket} AND sex = '{csb.sex}' AND output <= {csb.plank_output} LIMIT 1"
    score = (dbmgr.query(score_string)).fetchone()
    plank_score = 0 if score == "None" or score == None else (score)[0]
    #print(plank_score)
    csb.plank_points = plank_score

    # run
    score_string = f"SELECT score FROM run_point_table WHERE age = {csb.bracket} AND sex = '{csb.sex}' AND output >= {csb.run_output} LIMIT 1"
    score = (dbmgr.query(score_string)).fetchone()
    run_score = 0 if score == "None" or score == None else (score)[0]
    #print(run_score[0])
    csb.run_points = run_score

    csb.calc_total_points()

    #return csb

def catch_bad_input(input, cast, flagcatcher): # IE catch_bad_input(raw[0], 1)
    # castings: 1 = integer, 2 = float, 3 = time_to_float, 4 = none
    maybe_flag = str()
    try:
        if cast == 1:
            maybe_flag = "Bad Integer (Check Age, Deadlift, Push-Up Entries)"
            input = int(input)
        elif cast == 2:
            maybe_flag = "Bad Float (Check Powerthrow Entry)"
            input = float(input)
        elif cast == 3:
            maybe_flag = "Bad Time (Check SDC, Plank, 2mi. Run Entries)"
            if type(input) == str:
                input = time_to_float(input)
        else: # Sanitizing strings? No = ; INSERT DROP
            if '=' in input or ';' in input or 'INSERT' in input or 'DROP' in input:
                maybe_flag = "Bad String (Check Name)"
                input = ""
    except:
        #print(f"ERROR: Bad Input: {input}")
        flagcatcher.flagged = True
        flagcatcher.flags.append(maybe_flag) if maybe_flag not in flagcatcher.flags else None
        return None
    else:
        return input

def create_soldier_profile(raw, dbmgr): # raw = ['Name', 'Age', 'Sex', 'Deadlift', 'Powerthrow', 'ReleasePU', 'SDC', 'Plank', 'Run'] from a soldier CSV

    flagger = FlagCatcher()
    
    age = catch_bad_input(raw[1], 1, flagger) or 17
    sex = ((catch_bad_input(raw[2], 4, flagger)).lower()).title() or "Male"

    highlow = HighsLows(age, sex)

    name = catch_bad_input(raw[0], 4, flagger) or "Default Name"
    deadlift = catch_bad_input(raw[3], 1, flagger) or 140
    '''if deadlift > highlow.deadlift_high: 
        deadlift = highlow.deadlift_high 
    elif deadlift < highlow.deadlift_low:
        deadlift = highlow.deadlift_low'''

    powerthrow = catch_bad_input(raw[4], 2, flagger) or 6.0
    '''if powerthrow > highlow.powerthrow_high:
        powerthrow = highlow.powerthrow_high
    elif powerthrow < highlow.powerthrow_low:
        powerthrow = highlow.powerthrow_low'''

    releasePU = catch_bad_input(raw[5], 1, flagger) or 10
    '''if releasePU > highlow.releasePU_high:
        releasePU = highlow.releasePU_high
    elif releasePU < highlow.releasePU_low:
        releasePU = highlow.releasePU_low'''

    sdc = catch_bad_input(raw[6], 3, flagger) or 2.28
    '''if sdc > highlow.sdc_high:
        sdc = highlow.sdc_high
    elif sdc < highlow.sdc_low:
        sdc = highlow.sdc_low'''

    plank = catch_bad_input(raw[7], 3, flagger) or 1.30
    '''if plank > highlow.plank_high:
        plank = highlow.plank_high
    elif plank < highlow.plank_low:
        plank = highlow.plank_low'''

    run = catch_bad_input(raw[8], 3, flagger) or 22.0
    '''if run > highlow.run_high:
        run = highlow.run_high
    elif run < highlow.run_low:
        run = highlow.run_low'''

    #print(raw)

    csb = IndividualSoldier(name, age, sex, deadlift, powerthrow, releasePU, sdc, plank, run)
    if flagger.flagged == True:
        csb.flagged = True
        csb.flags = flagger.flags
        #csb.name = f"""{csb.name}"""

    calculate_scores(csb, dbmgr)
    
    return csb

def main():
    dbmgr = get_database()
    Amir_profile = ["Amir", "23", "Male", 340, "-- or 1=1", 41, "1:25", "-- or 1=1", "14:05"] # ['Name', 'Age', 'Sex', 'Deadlift', 'Powerthrow', 'ReleasePU', 'SDC', 'Plank', 'Run']
    csb = create_soldier_profile(Amir_profile)

    calculate_scores(csb, dbmgr)
    csb.print_soldier()
    print(csb.flags)
    

    '''
    #soldier_data = filereader.get_soldier_data()
    #print(soldier_data)

    for i in range(len(soldier_data)): # for each entry, calculate scores and print the soldier
        csb = create_soldier_profile(soldier_data[i])
        calculate_scores(csb, dbmgr)
        csb.print_soldier()
    '''
    
    acftdatabase.close_database_connection(dbmgr)

#main()