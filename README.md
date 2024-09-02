# Py_ACFT_Calculator w/ Client-Server
 An ACFT Calculator, written in Python

- Allows the user to add, edit, delete, save, and load ACFT rosters (stored in SQLite databases). 
- Rosters can be individually password-protected and will be encrypted if protected. Clear-text if not.
- Rosters can be combined by loading a roster while having one active.
- Options menu allows a clean slate, save to database file, or open (open and add to active or open new.)
- Entries are 1) locked to their format (time, integers) and sanitized (the program will not allow for SQL injections in order for databases to be illegally accessed).

- ACFT Calculator functions as a client, with a remote Ubuntu Server allowing for remote saving.
- Client and Server written completely in C, Python implements CTypes for C function wrappers.
- Allows the user to save database files locally, remotely, or both, and encrypt for each option.
