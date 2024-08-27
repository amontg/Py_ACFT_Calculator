'''
Name: ACFT Encryption
Author: SPC Montgomery, Amir
Date: 20230611

Objective: Encrypt an ACFT database

    1. User enters password
    2. Create kdf Scrypt, derive key
    3. Hash key with hashlib.sha256()
    4. Store salt and key hash in Authentication table
    5. Pull row, encrypt each column (cipher_suite), update row with encrypted columns

    ->
    1. User enters password
    2. Create kdf Scrypt with stored salt, derive given_key
    3. Hash given_key with hashlib.sha256()
    4. Compare given_key with stored_key
    5. If authenticated, decrypt with given_key

'''

import argon2
from argon2 import PasswordHasher
from cryptography.fernet import Fernet
import base64, os
import acft_objmgr as objmgr

def get_hash_n_salt(given_password, roster_db):
    ph = PasswordHasher()
    salt = os.urandom(16)

    hashed_pw = ph.hash(given_password, salt=salt)
    roster_db.insert_hashnsalt(hashed_pw, salt)
    # then encrypt?
    # encrypt_data(roster_db)

def encrypt_data(roster_db):
    fetch_key = "SELECT hash, salt FROM encryption WHERE encrypted=1"

    key_return = (roster_db.query(fetch_key)).fetchone()
    stored_hash = key_return[0]

    cipher_suite = get_fernet_suite(stored_hash)

    # create an encrypted data table
    roster_db.query("CREATE TABLE encrypted_roster(name BLOB, age BLOB, sex BLOB, total BLOB, deadlift_out BLOB, deadlift_points BLOB, powerthrow_out BLOB, powerthrow_points BLOB, releasePU_out BLOB, pushup_points BLOB, sdc_out BLOB, sdc_points BLOB, plank_out BLOB, plank_points BLOB, run_out BLOB, run_points BLOB)")

    get_records_line = "SELECT * FROM roster"
    for row in roster_db.query(get_records_line):
        #print(row)
        encrypted_data = []
        for i in range(len(row)):
            item = str(row[i])
            encrypted_data.append(cipher_suite.encrypt(item.encode()))
        
        #insert_line = f"INSERT INTO encrypted_roster VALUES({encrypted_data[0]}, {encrypted_data[1]}, {encrypted_data[2]}, {encrypted_data[3]}, {encrypted_data[4]}, {encrypted_data[5]}, {encrypted_data[6]}, {encrypted_data[7]}, {encrypted_data[8]}, {encrypted_data[9]}, {encrypted_data[10]}, {encrypted_data[11]}, {encrypted_data[12]}, {encrypted_data[13]}, {encrypted_data[14]}, {encrypted_data[15]})"
        roster_db.insert_encrypteddata(encrypted_data)
    
    # delete unencrypted roster table
    roster_db.query("DROP TABLE IF EXISTS roster")

def check_encrypt(roster_db):
    check_line = f"SELECT encrypted FROM encryption"
    is_encrypted = roster_db.query(check_line).fetchone()
    if not is_encrypted:
        is_encrypted = 0
    else:
        is_encrypted = is_encrypted[0]

    return is_encrypted


def decrypt_data(roster_db, given_password):
    ph = PasswordHasher()

    get_line = f"SELECT * FROM encryption"
    stored_encryption = roster_db.query(get_line).fetchone()
    stored_hash, stored_salt = stored_encryption[1], stored_encryption[2]


    check = ph.verify(stored_hash, given_password)
    if check == True:
        decipher_suite = get_fernet_suite(stored_hash)
        # make the objmgr roster
        # decrypted_roster = objmgr.Roster()

        # for every row in encrypted_roster, decrypt
        roster_db.new_tables()
        get_records_line = "SELECT * FROM encrypted_roster"
        for row in roster_db.query(get_records_line):
            unencrypted_data = []
            for i in range(len(row)):
                item = (decipher_suite.decrypt(row[i])).decode()
                unencrypted_data.append(item)
            
            roster_db.insert_unencrypteddata(unencrypted_data)

        roster_db.query("DROP TABLE IF EXISTS encrypted_roster")

def get_fernet_suite(given_hash):
    fernet_key = base64.urlsafe_b64encode((given_hash[30:62]).encode())
    return Fernet(fernet_key)

def remove_encryption_info(roster_db):
    roster_db.query("DROP TABLE IF EXISTS encryption")
    roster_db.query("CREATE TABLE IF NOT EXISTS encryption(encrypted INTEGER, hash TEXT, salt BLOB)")