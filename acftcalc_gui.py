'''
Name: ACFT Calculator - GUI
Author: SPC Montgomery, Amir
Date: 20240607

Objective: Handle a Tkinter GUI

'''

import shutil
from time import sleep
import tkinter as tk # module
import os
from tkinter import ttk # styling
from tkinter import font as tkFont
from tkinter import messagebox # popups
from tkinter import filedialog # file handling
from tkinter import simpledialog
import tempfile

import argon2
import acftcalculator as acftcalc # calculate stuff
import acft_objmgr as objmgr # manage the thingies
import acft_encrypt as acftcrypt # do database encryption
import rosterdatabase
import client_phandler as handler

# RichText provided by Bryan Oakley: https://stackoverflow.com/questions/63099026/fomatted-text-in-tkinter
class RichText(tk.Text): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        default_font = tkFont.nametofont(self.cget("font"))

        em = default_font.measure("m")
        default_size = default_font.cget("size")
        bold_font = tkFont.Font(**default_font.configure())
        italic_font = tkFont.Font(**default_font.configure())
        h1_font = tkFont.Font(**default_font.configure())

        bold_font.configure(weight="bold")
        italic_font.configure(slant="italic")
        h1_font.configure(size=int(default_size*2), weight="bold")

        self.tag_configure("bold", font=bold_font)
        self.tag_configure("italic", font=italic_font)
        self.tag_configure("h1", font=h1_font, spacing3=default_size)

        lmargin2 = em + default_font.measure("\u2022 ")
        self.tag_configure("bullet", lmargin1=em, lmargin2=lmargin2)

    def insert_bullet(self, index, text):
        self.insert(index, f"\u2022 {text}", "bullet")

class windows(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.wm_title("ACFT Calculator") # window title

        self.minsize(0, 300)
        self.resizable(0, 0)

        self.container = tk.Frame(self, padx=5, pady=10) # frame and container
        self.container.grid(column=0, row=0, sticky="NSEW")
        
        self.container.grid_rowconfigure(0, weight=1) # location of container with grid manager
        self.container.grid_columnconfigure(0, weight=1)

        self.objmgr = objmgr.Roster()
        self.given_password = ""
        self.server_savename = ""
        self.oldsave_file = []

        self.frames = {} # frame dictionary

        self.enterstats_frame = None
        self.refresh_enterstats()

        self.viewstats_frame = None

        self.dbmgr = acftcalc.get_database() # get dbmgr

        self.protocol("WM_DELETE_WINDOW", lambda: check_save())

        def check_save():
            wannasave = messagebox.askyesnocancel(title="Information", message="Unsaved Data", detail="Do you want to save this file?")
            if wannasave == True:
                save_roster(True)
            elif wannasave == False:
                encrypt_loaded()
                self.destroy()
            # else do nothing

        # save database
        def save_roster(close=False, serversend=False): # save the file, if retfile=True return the saved filename
            if len(self.objmgr.soldier_list()) > 0: # if i have soldiers in my database, go thru saving procedure
                newsave_file = ""
                
                # ask for filename to save file as, make a loop until they save into file name or deny saving
                wannasave = True
                while (wannasave == True): # if wannasave remains true, loop back
                    newsave_file = filedialog.asksaveasfilename(parent=self.container, title="Save Roster...", initialdir=os.getcwd(), confirmoverwrite=tk.TRUE, defaultextension=".db", filetypes=[("Database files", ".db")])
                    
                    # if given an actual file/name to save to 
                    if type(newsave_file) == str and newsave_file != "":
                        try:
                            roster_db = rosterdatabase.init_database_connection(newsave_file)

                            rosterdatabase.csb_to_db(self.objmgr, roster_db)
                            
                            break # saving is done, exit loop
                        except:
                            messagebox.showerror(title="Error", message="Invalid Database", detail="There was something wrong with saving your database.\nPlease check your entries and try again..")
                            continue # start the loop over because of error
                    else:
                        wannasave = messagebox.askyesno(title="Information", message="Invalid Filename", detail="You didn't give a valid file name. Do you want to save it to a file?")
                        # need to re-encrypt db if exists, because the db actually changes mid-session. should this be changed?
                        if wannasave == False:
                            # need to check for if opened from oldsave_file, then encrypt it
                            if len(self.oldsave_file) > 0:
                                encrypt_loaded()

                            break
                        else:
                            continue # restart loop with wannasave either true or false based on the yesno box
            else:
                messagebox.showinfo(title=None, message="You have no soldiers to save.")
                return None
            
            encrypt_choice = messagebox.askyesno(title=None, message="Do you wish to encrypt this file?")
            if encrypt_choice:
                if acftcrypt.check_encrypt(roster_db) == 1:
                    acftcrypt.encrypt_data(roster_db)
                else:
                    password_window = PasswordBox(True, self)
                    password_window.wait_window()
                                
                    acftcrypt.get_hash_n_salt(self.given_password, roster_db)
                    acftcrypt.encrypt_data(roster_db)
            else: # double check to make sure the file doesn't already have an encryption set up. Delete if so
                if acftcrypt.check_encrypt(roster_db) == 1:
                    acftcrypt.remove_encryption_info(roster_db)

            if serversend == True:
                return newsave_file

            if close == False and serversend == False:
                close = messagebox.askyesno(title="Information", message="Close Application", detail="You saved your database. Do you want to close the application?")
            
            if close: # only close if wanted to close
                rosterdatabase.close_database_connection(roster_db)
                self.destroy()

        def send_roster():
            '''
            ask if also save local
            if yes
                save local
                send to server with local name
            if no
                make temp file
                ask encrypt
                send to server with (ask name)
            '''
            if len(self.objmgr.soldier_list()) > 0:
                socket = handler.connect_to_server()
                filename_window = SavenameDialog(self)      # ask for name
                filename_window.wait_window()               # wait til name

                save_local = messagebox.askyesno(title=None, message="Do you also want to save this file locally?")

                if save_local == True:
                    close = messagebox.askyesno(title=None, message="Do you want to close after saving?")

                    file = save_roster(close, True)
                    if file == None:
                        handler.disconnect_server(socket)
                        return None

                    handler.send_to_server(str.encode(file), socket, str.encode(self.server_savename))

                else:
                    temp_dir = tempfile.TemporaryDirectory()
                    file = temp_dir.name + "\\tmp_db.db"
                    print(file)

                    roster_db = rosterdatabase.init_database_connection(file)  # make it a db
                    rosterdatabase.csb_to_db(self.objmgr, roster_db)           # enter data to db

                    encrypt_choice = messagebox.askyesno(title=None, message="Do you wish to encrypt this file?")
                    if encrypt_choice == True:
                        password_window = PasswordBox(True, self)
                        password_window.wait_window()
                                    
                        acftcrypt.get_hash_n_salt(self.given_password, roster_db)
                        acftcrypt.encrypt_data(roster_db)   # encrypt the data before send

                    handler.send_to_server(str.encode(file), socket, str.encode(self.server_savename)) # send the file
                    rosterdatabase.close_database_connection(roster_db)             # close the database
                    shutil.rmtree(temp_dir.name, ignore_errors=True)                                    # delete the temp_dir

                handler.disconnect_server(socket)
            else:
                messagebox.showinfo(title=None, message="You have no soldiers to save.")
                return None

            close = messagebox.askyesno(title=None, message="Do you wish to close the program?")
            if close == True:
                self.destroy()
        
        def encrypt_loaded():
            for i in self.oldsave_file:
                roster_db = rosterdatabase.init_database_connection(i)
                                    
                if acftcrypt.check_encrypt(roster_db) == 1:
                    acftcrypt.encrypt_data(roster_db)

        # open database
        def open_roster(decision):
            if decision == "new":
                self.objmgr = None
                self.objmgr = objmgr.Roster()

            newopen_file = filedialog.askopenfilename(parent=self.container, title="Open Roster...", initialdir=os.getcwd(), filetypes=[("Database files", ".db")])
            if type(newopen_file) == str and newopen_file != "":
                self.oldsave_file.append(newopen_file)

                try:
                    roster_db = rosterdatabase.init_database_connection(newopen_file)
                    if acftcrypt.check_encrypt(roster_db) == 1:
                        # get password
                        password_window = PasswordBox(False, self)
                        password_window.wait_window()
                        acftcrypt.decrypt_data(roster_db, self.given_password)

                    # check if we have the regular roster
                    check_roster_line = "SELECT name FROM sqlite_master WHERE type='table' AND name='roster'"
                    check_roster_exist = roster_db.query(check_roster_line)
                    if len(check_roster_exist.fetchone()) == 1:
                        self.objmgr = rosterdatabase.db_to_csb(self.objmgr, roster_db, self.dbmgr)
                        rosterdatabase.close_database_connection(roster_db)
                        self.show_stats()
                except argon2.exceptions.VerifyMismatchError: 
                    messagebox.showerror(title="Incorrect Password", message="You entered an incorrect password.")
                #except:
                #    messagebox.showerror(title="Invalid File", message="You chose an invalid file.", detail="Please select a different file.")
            else:
                messagebox.showinfo(title="Information", message="Invalid File", detail="You didn't select a valid file.")

        def clear_table():
            self.objmgr = None
            self.objmgr = objmgr.Roster()

            self.show_stats()

        # menus
        '''
        Options
            └ Save
            └ Open
                └ ... and add
                └ ... new
                
        
        '''
        self.option_add('*tearOff', tk.FALSE)
        self.menu_bar = tk.Menu(self) # menu bar
        self['menu'] = self.menu_bar

        menu_options = tk.Menu(self.menu_bar)
        self.menu_bar.add_cascade(menu=menu_options, label="Options") # Options cascade in menu bar

        menu_options.add_command(label="Clear Entries", command=lambda: clear_table())
        # menu_options.add_command(label="Save", command=lambda: save_roster())
        
        menu_save = tk.Menu(menu_options)
        menu_options.add_cascade(menu=menu_save, label="Save")
        menu_save.add_command(label="... locally", command=lambda: save_roster())
        menu_save.add_command(label="... to server", command=lambda: send_roster())

        menu_open = tk.Menu(menu_options)
        menu_options.add_cascade(menu=menu_open, label="Open") # Open options cascade in option cascade
        menu_open.add_command(label="... and add", command=lambda: open_roster("add"))
        menu_open.add_command(label="... new", command=lambda: open_roster("new"))
    
    def refresh_enterstats(self): # destroys the frame to enter information, then remakes it fresh. is there a better way to refresh a frame?
        if self.enterstats_frame is not None:
            self.enterstats_frame.destroy()

        self.enterstats_frame = EnterStats(self.container, self)
        self.frames[EnterStats] = self.enterstats_frame
        frame = self.frames[EnterStats]
        frame.grid(column=0, row=0, sticky="NSEW")

    def show_stats(self): # destroys the frame to display stats, then remakes it with new data. 
        if self.viewstats_frame is not None:
            self.viewstats_frame.destroy()
        
        self.viewstats_frame = ViewStats(self.container, self)
        self.frames[ViewStats] = self.viewstats_frame
        frame = self.frames[ViewStats]
        frame.grid(column=0, row=3, sticky="NSEW")

class SavenameDialog(tk.Toplevel):
    def __init__(self, passback, *args, **kwargs):
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.wm_title("Filename")

        self.minsize(0, 0)
        self.resizable(0, 0)
        self.con_pady=5
        self.con_padx=5
        self.entry_width=15

        self.container = tk.Frame(self, padx=5, pady=10) # frame and container, top left
        self.container.grid(column=0, row=0, sticky="NSEW")
        
        self.container.grid_rowconfigure(0, weight=1) # location of container with grid manager
        self.container.grid_columnconfigure(0, weight=1)

        self.entry1_label = ttk.Label(self.container, text="Enter Filename: ")
        self.entry1_label.grid(column=0, row=0, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.entry1_entry = ttk.Entry(self.container, width=self.entry_width)
        self.entry1_entry.grid(column=1, row=0, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        def process_name(): # send name back to parent frame
            given_name = self.entry1_entry.get()
            passback.server_savename = given_name
            self.destroy()
            
        self.enter_button = ttk.Button(
            self.container,
            text="Enter",
            command=lambda: process_name()
        )
        self.enter_button.grid(column=0, row=3, columnspan=2, padx=self.con_padx, pady=self.con_pady)


class PasswordBox(tk.Toplevel):
    def __init__(self, new, passback, *args, **kwargs): # init PassBox (self[none], new[T/F], passback[frame that wants the information])
        tk.Toplevel.__init__(self, *args, **kwargs)
        self.wm_title("Password")
    
        self.minsize(0, 0)
        self.resizable(0, 0)
        self.con_pady=5
        self.con_padx=5
        self.entry_width=15

        self.container = tk.Frame(self, padx=5, pady=10) # frame and container, top left
        self.container.grid(column=0, row=0, sticky="NSEW")
        
        self.container.grid_rowconfigure(0, weight=1) # location of container with grid manager
        self.container.grid_columnconfigure(0, weight=1)

        self.entry1_label = ttk.Label(self.container, text="Enter Password: ")
        self.entry1_label.grid(column=0, row=0, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.entry1_entry = ttk.Entry(self.container, show="*", width=self.entry_width)
        self.entry1_entry.grid(column=1, row=0, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        if new: # if adding a new password (True/False), add in a verify password field
            self.entry2_label = ttk.Label(self.container, text="Verify: ")
            self.entry2_label.grid(column=0, row=1, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
            self.entry2_entry = ttk.Entry(self.container, show="*", width=self.entry_width)
            self.entry2_entry.grid(column=1, row=1, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        def empty(entry): #func to clear an entry field
            entry.delete(0, "end")

        def process_pass(): # double check new passwords, send it back to parent frame if passed
            given_password = self.entry1_entry.get()
            if new:
                verify_password = self.entry2_entry.get()
                if given_password != verify_password:
                    messagebox.showerror(message="Mismatched Passwords", detail="You must enter matching passwords.", command=empty(self.entry2_entry))
                    return # exit process pass
            
            passback.given_password = given_password
            self.destroy()
            
        self.enter_button = ttk.Button(
            self.container,
            text="Enter",
            command=lambda: process_pass()
        )
        self.enter_button.grid(column=0, row=3, columnspan=2, padx=self.con_padx, pady=self.con_pady)

class EnterStats(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.columnconfigure(0, minsize=0)

        self.label = ttk.Label(self, text="Enter Soldier ACFT Statistics")
        self.label.grid(column=0, row=0, padx=10, pady=10)
        
        self.sub_frame_widths = 300 # consistent frame widths, but I like letting it fill itself in if need be
        self.con_padx = 5
        self.con_pady = 5

        # personal data frame
        self.personal_data = ttk.Frame(
            self,
            borderwidth=2,
            relief='sunken',
            padding="5 10 5 10", # left top right bottom
        )
        self.personal_data.grid(column=0, row=1, sticky="nsew")
        #personal_data.grid_propagate(0) # widgets inside don't grow, want to let them grow to fit parent frame

        self.name_label = ttk.Label(self.personal_data, text="Name (Last, First MI)") # name label
        self.name_label.grid(column=0, row=0, padx=self.con_padx, pady=self.con_pady)
        self.soldier_name = tk.StringVar()
        self.name_entry = ttk.Entry(self.personal_data, width=20, textvariable=self.soldier_name)
        self.name_entry.grid(column=0, row=1, padx=self.con_padx, pady=self.con_pady)

        self.age_label = ttk.Label(self.personal_data, text="Age") # age label
        self.age_label.grid(column=1, row=0, padx=self.con_padx, pady=self.con_pady)
        #age_label.pack() - don't use pack() if using widget.grid(), and we use .grid() because better
        self.soldier_age = tk.IntVar()
        self.age_entry = ttk.Entry(self.personal_data, width=3, textvariable=self.soldier_age)
        self.age_reg = (controller.register(validate_numbers), '%d', '%i', '%P', 17, 99)
        self.age_entry.config(validate='key', validatecommand=self.age_reg)
        self.age_entry.grid(column=1, row=1, padx=self.con_padx, pady=self.con_pady)

        self.sex_label = ttk.Label(self.personal_data, text="Sex") # sex label
        self.sex_label.grid(column=2, row=0, padx=self.con_padx, pady=self.con_pady)
        self.soldier_sex = tk.StringVar()
        self.sex_selection = ttk.Combobox(self.personal_data, width=8, state="readonly", textvariable=self.soldier_sex)
        self.sex_selection['values'] = ('Male', 'Female')
        self.sex_selection.grid(column=2, row=1, padx=self.con_padx, pady=self.con_pady)

        # acft event output frame
        self.acft_outputs = ttk.Frame(
            self,
            borderwidth=2,
            relief="sunken",
            padding = "5 5 5 5", # left top right bottom
            #width=self.sub_frame_widths
        )
        # acft_outputs.pack(fill=tk.NONE, expand=1, padx=con_padx, pady=con_pady)
        self.acft_outputs.grid(column=0, row=2, sticky="nsew")
        # acft_outputs.grid_propagate(0)

        # deadlift
        self.deadlift_label = ttk.Label(self.acft_outputs, text="Deadlift", justify=tk.CENTER)
        self.deadlift_label.grid(column=0, row=0, padx=self.con_padx, pady=self.con_pady, sticky="nsew")
        self.soldier_deadlift_output = tk.IntVar()
        self.deadlift_entry = ttk.Entry(self.acft_outputs, width=3, textvariable=self.soldier_deadlift_output)
        self.deadlift_entry.grid(column=0, row=1, padx=self.con_padx, pady=self.con_pady, sticky="nsew")

        # powerthrow
        self.powerthrow_label = ttk.Label(self.acft_outputs, text="Powerthrow", justify=tk.CENTER)
        self.powerthrow_label.grid(column=1, row=0, padx=self.con_padx, pady=self.con_pady, sticky="nsew")
        self.soldier_powerthrow_output = tk.StringVar()
        self.powerthrow_entry = ttk.Entry(self.acft_outputs, width=5, textvariable=self.soldier_powerthrow_output)
        self.powerthrow_entry.grid(column=1, row=1, padx=self.con_padx, pady=self.con_pady, sticky="nsew")

        # hand-release PU
        self.releasePU_label = ttk.Label(self.acft_outputs, text="Push-Ups", justify=tk.CENTER)
        self.releasePU_label.grid(column=2, row=0, padx=self.con_padx, pady=self.con_pady, sticky="nsew")
        self.soldier_releasePU_output = tk.IntVar()
        self.releasePU_entry = ttk.Entry(self.acft_outputs, width=3, textvariable=self.soldier_releasePU_output)
        self.releasePU_entry.grid(column=2, row=1, padx=self.con_padx, pady=self.con_pady, sticky="nsew")
    
        def create_validation_command(spinbox):
            return (controller.register(lambda reason, spbox=spinbox: find_nearest_value(reason, spbox)), '%V')

        # sdc
        self.sdc_label = ttk.Label(self.acft_outputs, text="Sprint, Drag, Carry", justify=tk.CENTER)
        self.sdc_label.grid(column=0, row=2, padx=self.con_padx, pady=self.con_pady, sticky="nsew")
        self.soldier_sdc_timeval = tk.StringVar()
        self.sdc_spinbox = ttk.Spinbox(self.acft_outputs, textvariable=self.soldier_sdc_timeval, width=5)
        self.sdc_spinbox['values'] = get_time_list(3) # get the spinlist for up to 3 minutes, current practice is to set spinboxes to fail time for sdc
        self.sdc_spinbox.config(validate='all', validatecommand=create_validation_command(self.sdc_spinbox))
        self.sdc_spinbox.bind("<Return>", lambda e: find_nearest_value("Return", self.sdc_spinbox))
        self.sdc_spinbox.grid(column=0, row=3, padx=self.con_padx, pady=self.con_pady, sticky="nsew")

        # plank
        self.plank_label = ttk.Label(self.acft_outputs, text="Plank", justify=tk.CENTER)
        self.plank_label.grid(column=1, row=2, padx=self.con_padx, pady=self.con_pady, sticky="nsew")
        self.soldier_plank_timeval = tk.StringVar()
        self.plank_spinbox = ttk.Spinbox(self.acft_outputs, textvariable=self.soldier_plank_timeval, width=5)
        self.plank_spinbox['values'] = get_time_list(4) # max for all ages
        self.plank_spinbox.config(validate='all', validatecommand=create_validation_command(self.plank_spinbox))
        self.plank_spinbox.bind("<Return>", lambda e: find_nearest_value("Return", self.plank_spinbox))
        self.plank_spinbox.grid(column=1, row=3, padx=self.con_padx, pady=self.con_pady, sticky="nsew")

        # run
        self.run_label = ttk.Label(self.acft_outputs, text="2mi. Run", justify=tk.CENTER)
        self.run_label.grid(column=2, row=2, padx=self.con_padx, pady=self.con_pady)
        self.soldier_run_timeval = tk.StringVar()
        self.run_spinbox = ttk.Spinbox(self.acft_outputs, textvariable=self.soldier_run_timeval, width=5)
        self.run_spinbox['values'] = get_time_list(25) # highest fail time rounded up
        self.run_spinbox.config(validate='all', validatecommand=create_validation_command(self.run_spinbox))
        self.run_spinbox.bind("<Return>", lambda e: find_nearest_value("Return", self.run_spinbox))
        self.run_spinbox.grid(column=2, row=3, padx=self.con_padx, pady=self.con_pady, sticky="nsew")

        def calculate_soldier(): # output ['Name', 'Age', 'Sex', 'Deadlift', 'Powerthrow', 'ReleasePU', 'SDC', 'Plank', 'Run']
            try:
                soldier_profile = [
                    self.soldier_name.get(),
                    self.soldier_age.get(),
                    self.soldier_sex.get(),
                    self.soldier_deadlift_output.get(),
                    self.soldier_powerthrow_output.get(),
                    self.soldier_releasePU_output.get(),
                    self.soldier_sdc_timeval.get(),
                    self.soldier_plank_timeval.get(),
                    self.soldier_run_timeval.get()
                ]
            except:
                messagebox.showerror(title="Invalid Inputs", detail="Recheck your inputs and try again.")
                return

            #print(soldier_profile) # print if you wanna see stuff
            csb = acftcalc.create_soldier_profile(soldier_profile, controller.dbmgr)
            if csb.name != 0:
                if csb.flagged:
                    error_message = "Your input had errors."
                    detail_message = ""
                    for i in range(len(csb.flags)):
                        detail_message = f"{detail_message}    - {csb.flags[i]}\n"
                    messagebox.showerror(title="Invalid Inputs", message=f"{error_message}", detail=f"{detail_message}") # add loop, or leave as is to edit?
                
                #acftcalc.calculate_scores(csb, controller.dbmgr)
                controller.objmgr.add_soldier(csb, csb.name)

                #controller.die_stats()
                controller.show_stats()
                controller.refresh_enterstats()
                separate_one = ttk.Separator(parent, orient=tk.HORIZONTAL)
                separate_one.grid(column=0, row=2, sticky="NSEW")
                #csb.print_soldier()
            else:
                messagebox.showerror(title="Invalid Inputs", detail="You didn't even give this soldier a name.\nTry again.")

        self.calculate_button = ttk.Button(
            self,
            text="Calculate and Add Soldier",
            command=lambda: calculate_soldier()
        )
        self.calculate_button.grid(column=0, row=4, pady=5)

class ViewStats(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.columnconfigure(0, minsize=300)

        self.label = tk.Label(self, text="Soldier Statistics")
        self.label.grid(column=0, row=0, padx=10, pady=0)

        # app has its own soldier roster, to be exported as need be
        #self.objmgr = objmgr.Roster()

        # big stat frame
        self.stat_frame = ttk.Frame(
            self,
            borderwidth=2,
            relief="sunken",
            padding="5 10 5 10" # left top right bottom
        )
        self.stat_frame.grid(column=0, row=1, padx=0, pady=10, sticky="NSEW")

        # list box of selectable names
        self.soldier_list_label = ttk.Label(self.stat_frame, text="Soldiers")
        self.soldier_list_label.grid(column=0, row=0)

        # SESSION-SPECIFIC OBJECT MANAGER
        self.soldier_list = controller.objmgr.soldier_list()
        self.soldier_list_var = tk.StringVar(value=self.soldier_list)
        self.soldier_listbox = tk.Listbox(self.stat_frame, height=20, width=18, listvariable=self.soldier_list_var)
        self.soldier_listbox.grid(column=0, row=0, columnspan=1)

        # scrollbar for listbox
        self.soldier_list_scroller = ttk.Scrollbar(self.stat_frame, orient=tk.VERTICAL, command=self.soldier_listbox.yview)
        self.soldier_list_scroller.grid(column=1, row=0, sticky="NS")
        self.soldier_listbox.configure(yscrollcommand=self.soldier_list_scroller.set, selectmode="browse")

        def get_name(*args): # get list
            if len(self.soldier_listbox.curselection()) > 0:
                key = self.soldier_listbox.curselection()[0]
                self.show_frame(self.soldier_list[key])
                #print(soldier_list[key])

        # Set event bindings for when the selection in the listbox changes
        self.soldier_listbox.bind('<<ListboxSelect>>', get_name)

        def init_editer(*args):
            if len(self.soldier_listbox.curselection()) > 0:
                key = self.soldier_listbox.curselection()[0]
                csb = controller.objmgr.ret_soldier(self.soldier_list[key])
                EditSoldier(csb, controller.objmgr, controller)

        self.edit_soldier = ttk.Button(
            self.stat_frame,
            text="Edit",
            command=lambda: init_editer(),
        )
        self.edit_soldier.grid(column=3, row=2)

        def delete_name(*args):
            if len(self.soldier_listbox.curselection()) > 0:
                key = self.soldier_listbox.curselection()[0]
                self.frames.pop(self.soldier_list[key])
                controller.objmgr.del_soldier(self.soldier_list[key])
                controller.show_stats()

        self.delete_soldier = ttk.Button(
            self.stat_frame,
            text="Delete",
            command=lambda: delete_name()
        )
        self.delete_soldier.grid(column=4, row=2)

        self.frames = {}

        for Soldier in controller.objmgr.soldier_dict:
            frame = IndiSoldierFrame(self.stat_frame, self, controller.objmgr.soldier_dict[Soldier])

            self.frames[controller.objmgr.soldier_dict[Soldier].name] = frame
            frame.grid(column=3, row=0, columnspan=3, sticky="NSEW")
            self.soldier_listbox.selection_clear(0, "end")
            self.soldier_listbox.selection_set(self.soldier_list.index(frame.data.name))

    def show_frame(self, args = None): # swap the active soldier being shown, each soldier has its own subframe (IndiSoldierFrame) under the others
        if args:
            #print(self.frames)
            frame = self.frames[args]
        else:
            frame = frame[0]

        #print(frame)
        frame.tkraise()

class IndiSoldierFrame(ttk.Frame): # frame for each individual soldier to display under show stats frame
        def __init__(self, parent, controller, csb):
            ttk.Frame.__init__(self, parent)
            self.borderwidth = 0
            self.padding="5 10 5 10"
            self.grid(column=0, row=0, sticky="NSEW")

            self.data = csb
        
            #indi_soldier_frame.grid(column=2, columnspan=3, row=0, sticky="NSEW")

            self.text = RichText(self, width=20, height=20)
            self.text.grid(column=0, row=0, sticky="NSEW")

            # display statistics in the frame (object manager better?)
            self.flagmarker = "(!) "
            #print(self.data.flags)
            self.text.insert("end", f"{self.flagmarker if self.data.flagged == True else ''}{self.data.name}\n")
            self.text.insert("end", f"{self.data.age}, {self.data.sex}\n\n")

            self.text.insert("end", f"Total Points: {self.data.total_points}\n\n")

            self.text.insert("end", f"[ Deadlift ]\n")
            self.text.insert("end", f"Weight: {self.data.deadlift_output} lbs\n")
            self.text.insert("end", f"Points: {self.data.deadlift_points} Points\n\n")

            self.text.insert("end", f"[ Powerthrow ]\n")
            self.text.insert("end", f"Distance: {self.data.powerthrow_output} m.\n")
            self.text.insert("end", f"Points: {self.data.powerthrow_points} Points\n\n")

            self.text.insert("end", f"[ Push-Ups ]\n")
            self.text.insert("end", f"Reps: {self.data.releasePU_output}\n")
            self.text.insert("end", f"Points: {self.data.releasePU_points} Points\n\n")

            self.text.insert("end", f"[ SDC ]\n")
            self.text.insert("end", f"Time: {self.data.sdc_output}\n")
            self.text.insert("end", f"Points: {self.data.sdc_points} Points\n\n")

            self.text.insert("end", f"[ Plank ]\n")
            self.text.insert("end", f"Time: {self.data.plank_output}\n")
            self.text.insert("end", f"Points: {self.data.plank_points} Points\n\n")

            self.text.insert("end", f"[ 2mi. Run ]\n")
            self.text.insert("end", f"Time: {self.data.run_output}\n")
            self.text.insert("end", f"Points: {self.data.run_points} Points\n\n")

            self.text.configure(state="disabled")

class EditSoldier(tk.Tk): # window to edit the soldier if needed
    def __init__(self, csb, objmgr, controller, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        self.soldier = csb
        self.roster = objmgr
        self.controller = controller

        self.wm_title(f"{self.soldier.name}")

        self.minsize(0, 300)
        self.resizable(0, 0)
        #self.grid_propagate(0)
        #self.pack_propagate(0)
        self.con_pady=5
        self.con_padx=5
        self.entry_width=7

        self.container = tk.Frame(self, padx=5, pady=10) # frame and container
        self.container.grid(column=0, row=0, sticky="NSEW")
        
        self.container.grid_rowconfigure(0, weight=1) # location of container with grid manager
        self.container.grid_columnconfigure(0, weight=1)

        self.age_label = ttk.Label(self.container, text="Age: ")
        self.age_label.grid(column=0, row=0, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.age_var = tk.StringVar()
        self.age_entry = ttk.Entry(self.container, textvariable=self.age_var, width=self.entry_width, justify=tk.RIGHT)
        self.age_entry.insert(0, f"{self.soldier.age}")
        self.age_entry.grid(column=1, row=0, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        self.sex_label = ttk.Label(self.container, text="Sex: ")
        self.sex_label.grid(column=2, row=0, sticky="NSE", padx=self.con_padx, pady=self.con_pady)
        self.sex_var = tk.StringVar()
        self.sex_combobox = ttk.Combobox(self.container, textvariable=self.sex_var, state="readonly", width=self.entry_width)
        self.sex_combobox['values'] = ("Male", "Female")
        self.sex_combobox.set(self.sex_combobox['values'][self.sex_combobox['values'].index(self.soldier.sex)])
        self.sex_combobox.grid(column=3, row=0, sticky="NSE", padx=self.con_padx, pady=self.con_pady)

        self.deadlift_label = ttk.Label(self.container, text="Deadlift: ")
        self.deadlift_label.grid(column=0, row=2, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.deadlift_var = tk.StringVar()
        self.deadlift_entry = ttk.Entry(self.container, textvariable=self.deadlift_var, width=self.entry_width, justify=tk.RIGHT)
        self.deadlift_entry.insert(0, f"{int(self.soldier.deadlift_output)}")
        self.deadlift_entry.grid(column=1, row=2, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        self.powerthrow_label = ttk.Label(self.container, text="Powerthrow: ")
        self.powerthrow_label.grid(column=0, row=3, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.powerthrow_var = tk.StringVar()
        self.powerthrow_entry = ttk.Entry(self.container, textvariable=self.powerthrow_var, width=self.entry_width, justify=tk.RIGHT)
        self.powerthrow_entry.insert(0, f"{self.soldier.powerthrow_output}")
        self.powerthrow_entry.grid(column=1, row=3, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        self.releasePU_label = ttk.Label(self.container, text="Push-Ups: ")
        self.releasePU_label.grid(column=0, row=4, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.releasePU_var = tk.IntVar()
        self.releasePU_entry = ttk.Entry(self.container, textvariable=self.releasePU_var, width=self.entry_width, justify=tk.RIGHT)
        self.releasePU_entry.insert(0, f"{int(self.soldier.releasePU_output)}")
        self.releasePU_entry.grid(column=1, row=4, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        def create_validation_command(spinbox):
            return (self.register(lambda reason, spbox=spinbox: find_nearest_value(reason, spbox)), '%V')

        self.sdc_label = ttk.Label(self.container, text="SDC: ")
        self.sdc_label.grid(column=0, row=5, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.sdc_var = tk.StringVar()
        self.sdc_spinbox = ttk.Spinbox(self.container, textvariable=self.sdc_var, width=self.entry_width, justify=tk.RIGHT)
        self.sdc_spinbox['values'] = get_time_list(3)
        self.sdc_spinbox.config(validate='all', validatecommand=create_validation_command(self.sdc_spinbox))
        self.sdc_spinbox.bind("<Return>", lambda e: find_nearest_value("Return", self.sdc_spinbox))
        self.sdc_spinbox.insert(0, f"{acftcalc.float_to_time(self.soldier.sdc_output)}")
        self.sdc_spinbox.grid(column=1, row=5, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        self.plank_label = ttk.Label(self.container, text="Plank: ")
        self.plank_label.grid(column=0, row=6, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.plank_var = tk.StringVar()
        self.plank_spinbox = ttk.Spinbox(self.container, textvariable=self.plank_var, width=self.entry_width, justify=tk.RIGHT)
        self.plank_spinbox['values'] = get_time_list(5)
        self.plank_spinbox.config(validate='all', validatecommand=create_validation_command(self.plank_spinbox))
        self.plank_spinbox.bind("<Return>", lambda e: find_nearest_value("Return", self.plank_spinbox))
        self.plank_spinbox.insert(0, f"{acftcalc.float_to_time(self.soldier.plank_output)}")
        self.plank_spinbox.grid(column=1, row=6, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        self.run_label = ttk.Label(self.container, text="2mi. Run: ")
        self.run_label.grid(column=0, row=7, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)
        self.run_var = tk.StringVar()
        self.run_spinbox = ttk.Spinbox(self.container, textvariable=self.run_var, width=self.entry_width, justify=tk.RIGHT)
        self.run_spinbox['values'] = get_time_list(25)
        self.run_spinbox.config(validate='all', validatecommand=create_validation_command(self.plank_spinbox))
        self.run_spinbox.bind("<Return>", lambda e: find_nearest_value("Return", self.run_spinbox))
        self.run_spinbox.insert(0, f"{acftcalc.float_to_time(self.soldier.run_output)}")
        self.run_spinbox.grid(column=1, row=7, sticky="NSEW", padx=self.con_padx, pady=self.con_pady)

        self.separator_one = ttk.Separator(self.container, orient=tk.HORIZONTAL)
        self.separator_one.grid(column=0, row=1, sticky="NSEW", columnspan=4, padx=self.con_padx, pady=self.con_pady)

        self.separator_two = ttk.Separator(self.container, orient=tk.HORIZONTAL)
        self.separator_two.grid(column=0, row=8, sticky="NSEW", columnspan=4, padx=self.con_padx, pady=self.con_pady)

        def update_and_close():
            updated_soldier = [
                self.soldier.name,
                self.age_entry.get(),
                self.sex_combobox.get(),
                self.deadlift_entry.get(),
                self.powerthrow_entry.get(),
                self.releasePU_entry.get(),
                self.sdc_spinbox.get(),
                self.plank_spinbox.get(),
                self.run_spinbox.get()
            ]

            new_csb = acftcalc.create_soldier_profile(updated_soldier, controller.dbmgr)
            #new_csb = acftcalc.calculate_scores(csb, controller.dbmgr)
            #print(updated_soldier)
            if new_csb.flagged:
                error_message = "Your input had errors."
                detail_message = ""
                for i in range(len(new_csb.flags)):
                    detail_message = f"{detail_message}    - {new_csb.flags[i]}\n"
                messagebox.showerror(parent=self.container, title="Invalid Inputs", message=f"{error_message}", detail=f"{detail_message}")
            else:
                self.roster.update_soldier(new_csb, self.soldier.name)
                self.controller.show_stats()
                self.destroy()

        self.save_changes = ttk.Button(
            self.container,
            text="Save Changes",
            command=lambda: update_and_close()
        )
        self.save_changes.grid(column=1, row=9, columnspan=2, padx=self.con_padx, pady=self.con_pady)

        
# bind spinboxes to try and find the closest value to whats in the spinbox on 'Return' key (.keycode 36) or FocusOut event
def find_nearest_value(reason, spinbox): # values = ['00:00', '00:01', '00:02', ... ], input = 'X:XX' - 'XX:XX'
    #print(reason)
    if reason == "focusout" or reason == "Return":
        try:
            user_input = spinbox.get()
            values = spinbox['values']

            time = user_input.split(":")
            min, sec = time[0], time[1]
            while len(min) != 2:
                min = f"0{min}"
            
            while len(sec) != 2:
                sec = f"{sec}0"
            
            new_time = f"{min}:{sec}"
            if new_time in values:
                spinbox.delete(0, "end")
                spinbox.insert(0, new_time)
            
            return True
        except:
            # print("Bad input...")
            return True
    else:
        return True

def get_time_list(max_time): # store values in seconds, divide by 60 for time, return ['00:00', '00:01', '00:02', ... ]
            max_time *= 60 # get time as minutes, multiply by 60
            i = 0
            time_list = []

            while i <= max_time:
                min = int(i/60)
                sec = i%60

                time = f"{0 if min < 10 else ''}{min}:{0 if sec < 10 else ''}{sec}"
                #print(time)
                i += 1
                time_list.append(time)

            return time_list

def validate_numbers(action, index, input, min, max): # given input, want only min or max
    #print(f"{action}, {index}, {input}, {min}, {max}")

    if int(action) == 1 and input.isdigit():
        input = int(input)
        if int(index) == 1 and input >= int(min) and input <= int(max):
            return True
        elif int(index) == 0:
            return True
        else:
            return False
    elif int(action) == 0:
        return True
    else:
        return False
def main(): # initialize the GUI
    mainWindow = windows()
    mainWindow.mainloop()

if __name__ == "__main__":
    main()