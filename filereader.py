'''
Name: File Reader
Author: SPC Montgomery, Amir
Date: 20230604

Objective: Read/write CSVs for ACFT Calculator

entry format: ['Name', 'Age', 'Sex', 'Deadlift', 'Powerthrow', 'ReleasePU', 'SDC', 'Plank', 'Run']
    
'''

import csv

def get_soldier_data():
    big_data = []
    input_file = "/home/amir.j.montgomery92/Desktop/Python/Code/ACFT Calculator/Data Analysis/example_input.csv"

    with open(input_file, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
            #print(row)
            big_data.append(row)

    return big_data