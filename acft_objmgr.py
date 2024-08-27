'''
Name: ACFT Soldier-Object Manager
Author: SPC Montgomery, Amir
Date: 20240608

Objective: Manage soldier objects for acftcalc_gui
'''

'''
Roster = {
    "soldiername" = csb,
    "soldiername" = csb
}
'''

class Roster():
    def __init__(self):
        self.soldier_dict = {}
    
    def find_soldier(self, name):
        # search the dictionary
        for key,_ in self.soldier_dict:
            if key == name:
                print("Found the dude.")
    
    def add_soldier(self, csb, name):
        self.soldier_dict[name] = csb

    def del_soldier(self, name):
        self.soldier_dict.pop(name)
    
    def ret_soldier(self, name):
        return self.soldier_dict[name] # returns the full csb
    
    def update_soldier(self, csb, name):
        self.soldier_dict[name] = csb
        #print(csb)
    
    def soldier_list(self):
        soldier_names = []
        if len(self.soldier_dict) > 0:
            for key,_ in self.soldier_dict.items():
                soldier_names.append(key)
        
        #print(soldier_names)
        return soldier_names

        # how do we want to handle the names - maybe just raw


