#!/usr/bin/env python3
#

import csv
import sys

if len(sys.argv) <= 1:
    print(f"Usage: {sys.argv[0]} filename.csv")
    print("Calculate custom field from timestamp")
    exit(-1)

filename_csv = sys.argv[1]

with open(filename_csv, newline='') as csvfile:
     reader = csv.DictReader(csvfile)
     for row in reader:
         email=row['Email']
         timestamp_date=row['Timestamp (EST)'][0:10]
         intro_commit_form_date=row['intro_commit_form_date']
         if intro_commit_form_date != timestamp_date:
             print(f"{email},{timestamp_date}")
         