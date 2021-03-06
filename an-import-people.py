#!/usr/bin/env python3
# sudo python3 -m pip install restnavigator

# restnavigator:
#     Library for interacting with HAL+JSON APIs of which OSDI conforms
# Docs at https://github.com/deontologician/restnavigator
#

import argparse
import json
import csv
import time
import logging
import sys
import os.path
from datetime import datetime
from restnavigator import Navigator, exc
import string

# Find your token at Start Organizing > Details > API & Sync

############################################################
#  usage: import_an_people.py ... inputfile
#
default_chapter = "SURJ Demo Chapter"
default_no = "no,n,false,n/a,off,0,Not at this time"

parser = argparse.ArgumentParser(description='Import people from a NationBuilder or MailChimp Export (CSV)')
group = parser.add_mutually_exclusive_group()
parser.add_argument('--group', '-g', default=default_chapter, metavar='GRP',
                    help='Action Network Group. Also profile name in an_profiles.py.')
parser.add_argument('--start', '-s', default=1, type=int, metavar='N',
                    help='First row to process (starting at 1)')
group.add_argument('--end', '-e', type=int, metavar='N', help='Last row to process')
group.add_argument('--count', '-c', type=int, metavar='N', help='Number of rows to process')
parser.add_argument('--verbose', '-v', action="store_true", help="Show data")
parser.add_argument('--unsubscribed', '-u', action="store_true", help="Include unsubscribed users")
parser.add_argument('--force', '-f', action="store_true", help="Force subscribe of existing users")
parser.add_argument('--dryrun', '-d', action="store_true",
                    help="Process imported data but don't send to Action Network")
parser.add_argument('--no', '-n', type=str, default=default_no, metavar='NOS',
                    help="Comma separated strings that mean no tag (for tag columns)")
parser.add_argument('--logfile', '-l', type=str, default="-",
                    help="Activity log")
parser.add_argument('--skip', action="store_true", help="Skip importing earlier imports (as per log file)")
parser.add_argument('inputFile', help='Importable CSV file')

args = parser.parse_args()

CONFIG_CHAPTER = args.group
CONFIG_IMPORTFILE = args.inputFile
CONFIG_VERBOSE = args.verbose
CONFIG_FORCE_SUBSCRIBED = args.force
CONFIG_START_INDEX = args.start
CONFIG_INCLUDE_UNSUBSCRIBED = args.unsubscribed
CONFIG_DRY_RUN = args.dryrun
CONFIG_SKIP = args.skip
CONFIG_LOGFILE = args.logfile
CONFIG_NO = {key: i for i, key in enumerate(args.no.lower().split(','))}  # {'no':0, 'FALSE':1 ... }

MAXINDEX = 1000000
if args.end is not None:
    CONFIG_END_INDEX = args.end
elif args.count is not None:
    CONFIG_END_INDEX = CONFIG_START_INDEX + args.count - 1
else:
    CONFIG_END_INDEX = MAXINDEX

####
# Log file 
#
skip_item = {}

if not CONFIG_LOGFILE or CONFIG_LOGFILE == '-':
    log_fh = sys.stdout
    if CONFIG_SKIP:
        raise Warning("Option --skip ignored for stdin")
else:
    if not os.path.isfile(CONFIG_LOGFILE):
        log_fh = open(CONFIG_LOGFILE, 'w')
    else:
        if not CONFIG_SKIP:
            raise Exception("{}: File exists. Use --skip or remove file.".format(CONFIG_LOGFILE))
     
        # Remember items to skip
        with open(CONFIG_LOGFILE, 'r') as existing_logfile:
            # [999] VERB ABC DEF -> ('[999]', 'VERB', 'ABC DEF")
            while True: 
                log_line = existing_logfile.readline()
                if not log_line:
                    break
                log_line_tokens = log_line.split(None, 2)
                if len(log_line_tokens) >= 2:
                    verb = log_line_tokens[1]
                    if verb == 'OK' or verb == 'SKIP':
                        itemid = int(log_line_tokens[0][1:-1])
                        skip_item[itemid] = verb

        log_fh = open(CONFIG_LOGFILE, 'a')

####################################

'''
CONFIG_PROFILEs file contains:
profiles = {
    "SURJ Action"       : "12343132412341341234123412342342",
    "SURJ Bay Area"     : "12343132412341341234123412342342"
    }
'''
import an_profiles
api_token = an_profiles.profiles.get(CONFIG_CHAPTER, "Not Found")
if api_token == "Not Found":
    assert api_token != "Not Found", CONFIG_CHAPTER + ": API Token not found"
else:
    if CONFIG_VERBOSE:
        print("[PREP] an_profiles: {}: API Token found".format(CONFIG_CHAPTER), file=log_fh)

aep = 'https://actionnetwork.org/api/v2/people/'

tag_mapping_file = 'maptags-curated.csv'

# Indicates which tags to map to
chapter_import = CONFIG_CHAPTER

AN = Navigator.hal(aep)
AN.headers['OSDI-API-Token'] = api_token


#################################################################
# Migration helper functions

def get_primary_address(row_primary):
    return get_address(row_primary, 'primary')

def get_billing_address(row_billing):
    return get_address(row_billing, 'billing')

def get_user_submitted_address(row_user_submitted):
    return get_address(row_user_submitted, 'user_submitted')

def get_address(row_address, address_type):
    _address = {}

    _address_lines = []
    if row_address.get(address_type + '_address1','') != '':
        _address_lines.append(row_address[address_type + '_address1'])
    if row_address.get(address_type + '_address2','') != '':
        _address_lines.append(row_address[address_type + '_address2'])
    if row_address.get(address_type + '_address3','') != '':
        _address_lines.append(row_address[address_type + '_address3'])
    if _address_lines:
        _address["address_lines"] = _address_lines

    if row_address.get(address_type + '_city','') != '':
        _address["locality"] = row_address[address_type + '_city']
    if row_address.get(address_type + '_state','') != '':
        _address["region"] = row_address[address_type + '_state']
    if row_address.get(address_type + '_zip','') != '':
        _address["postal_code"] = row_address[address_type + '_zip']

    return _address

def get_action_network_tags():
    ''' Return dict of tags from Action Network for the group we are on
        WARNNG: Only returns tags that have been used so far in group
    '''
    _rn = Navigator.hal('https://actionnetwork.org/api/v2/tags')
    _rn.headers['OSDI-API-Token'] = api_token

    _osdi_tags = _rn['osdi:tags']

    _an_tags = {}
    for tag in _osdi_tags:
        tag_name = tag.state['name']
        _an_tags[tag_name] = True

    return _an_tags

def get_tag_mapping(_importFile, _chapter):
    ''' .csv file:
    old_tag                               new_tags                  SURJ Action
    #maestro_upload                       IGNORE                    Maestro
    #trump-organize                       "#Trump,?Organizing"
    #NYC_Skills_Photo	                  ?Photo Video
    #SURJ Action - Phone Bank - Training  "?Phone Bank,!Training Phone Bank"
    '''
    _map = {}
    with open(_importFile, 'r') as file:
        _reader = csv.DictReader(file)
        if _chapter not in _reader.fieldnames:
            logging.warning("Could not find {} in {}".format(_chapter,str(_reader.fieldnames)))
        else:
            for _row in _reader:
                #print 'MAPPING:', _row['old_tag'], _row['new_tags'], _row[_chapter]
                _new_tags = []
                for new_tag in _row['new_tags'].split(","):
                    _new_tags.append(new_tag.strip())
                if _row[_chapter] != '':
                    if _new_tags[0] == 'IGNORE':
                        _new_tags = []
                    for new_tag in _row[_chapter].split(","):
                        _new_tags.append(new_tag.strip())

                _map[_row['old_tag']] = _new_tags  # an array

    return _map


found_old_tag_already = {}
def map_person_tags(tag_list):
    ''' Look through a comma separated string of old tags
        to find new tags.
        tag_mapping[old_tag]:
        IGNORE - there are no new replacement tags
        tag1 - there is one replacement tag
        tag2, tag3 - there are two replacement tags
        Returns list of tags to add
    '''
    _new_tags = []
    for old_tag in tag_list.split(","):
        old_tag = old_tag.strip()
        if old_tag == "":
            continue
        # Just because the tag doesn't exist doesn't mean it's not defined
        if old_tag not in tag_mapping:
            if old_tag not in found_old_tag_already:
                warn_str = "WARNING: Unknown tag not mapped: <{}>".format(old_tag)
                print(warn_str)
                logging.warning(warn_str)
                found_old_tag_already[old_tag] = True
            continue
        if not tag_mapping[old_tag]:
            continue
        #print "Map_tags from <" + old_tag + "> to ", str(tag_mapping[old_tag])
        if tag_mapping[old_tag][0] == 'IGNORE':
            continue
        _new_tags += tag_mapping[old_tag]

    return _new_tags

def get_column_tags(columns):
    ''' Look through columns for potential tags
        Columns that are tag names start with an ASCII symbol or the prefix "tag:"
        For example, 
        | #Call Representatives	| ?Web Design | tag:Request Contact |
        Returns dict { 
            "#Call Representatives" : "#Call Representatives" ,
            "?Web Design"           : "?Web Design",
            "tag:Request Contact"   : "Request Contact"
        }
    '''
    _column_tags = {}
    for _col in columns:
        if _col.lower().startswith('tag:'):
            _column_tags[_col] = _col[4:]
        else:
            _firstletter = _col[0]
            if _firstletter != ' ' and string.punctuation.find(_firstletter) != -1:
                 _column_tags[_col] = _col
    
    return _column_tags
    
# These are the tags we looked up that are used in the current group
# but they don't represent all the available tags - especially
# the ones from the parent.
#tags_existing = get_action_network_tags()
#print tags_existing
#exit()

tag_mapping = get_tag_mapping(tag_mapping_file, _chapter=CONFIG_CHAPTER)

#print tag_mapping

starttime = datetime.now()
rowid = 0
activists = 0

with open(CONFIG_IMPORTFILE, 'r') as ifile:
    reader = csv.DictReader(ifile)
    column_tags = get_column_tags(reader.fieldnames)
    if column_tags and CONFIG_VERBOSE:
        print('[PREP] FOUND COLUMN TAGS: {}', column_tags, file=log_fh)
    for row in reader:
        rowid = rowid + 1

        if not CONFIG_START_INDEX <= rowid <= CONFIG_END_INDEX:
            continue

        if CONFIG_SKIP and rowid in skip_item:
            if CONFIG_VERBOSE:
                print("[{:0>3}] SKIP - ALREADY PROCESSED".format(rowid), file=log_fh)
            continue
    
        print("[{:0>3}] TRY {}, {} <{}> OPT-IN {} WITH TAGS {}".format(rowid,
                                                                   row.get('last_name'),
                                                                   row.get('first_name'),
                                                                   row['email'],
                                                                   row.get('email_opt_in'),
                                                                   row.get('tag_list')),
                                                                   flush=True, file=log_fh)

        # Action Network people import via an API must have an email
        # (exception is importnig a donation where AN will generate a fake email)
        if row['email'] == '':
            print("[{:0>3}] SKIP - NO EMAIL".format(rowid), file=log_fh)
            continue

        # Clear the new_person dict and set the only required field
        new_person = {
            "person" : {
                "email_addresses" : [{"address" : row['email']}]
            }
        }
        # We want to import folks that opt-out because if they have donations
        # they would get automatically subscribed.
        if row.get('email_opt_in') == 'FALSE':
            new_person["person"]["email_addresses"][0]["status"] = 'unsubscribed'
            if not CONFIG_INCLUDE_UNSUBSCRIBED:
                print("[{:0>3}] SKIP - UNSUBSCRIBED".format(rowid), file=log_fh)
                continue
        else:
            if CONFIG_FORCE_SUBSCRIBED:
                new_person["person"]["email_addresses"][0]["status"] = 'subscribed'

        # Add first and last name if available
        if row.get('last_name','') != '':
            new_person["person"]['family_name'] = row['last_name']
        if row.get('first_name','') != '':
            new_person["person"]['given_name'] = row['first_name']

        address = get_primary_address(row)
        if address:
            address["primary"] = True
            new_person["person"]["postal_addresses"] = [address]

        # In NationBuilder the billing address may have more detail than the
        # primary address
        address = get_billing_address(row)
        if address:
            if "postal_addresses" not in new_person["person"]:
                new_person["person"]["postal_addresses"] = []
            new_person["person"]["postal_addresses"].append(address)

        # NationBuilder Tag Mapping
        new_person["add_tags"] = []
        if 'tag_list' in row:
            new_person["add_tags"] = map_person_tags(row['tag_list'])

        # Column Tag Mapping
        for column, column_tag in column_tags.items():
            cell = row[column].lower()
            if cell != '' and not cell in CONFIG_NO:
                new_person["add_tags"].append(column_tag)
        # Note: new_person["add_tags"] may have duplicates

        custom_fields = {}
        # Other NationBuilder Columns
        if row.get('do_not_call','') == 'TRUE':
            custom_fields['do_not_call'] = row.get('do_not_call')
        if row.get('mobile_number','') != '' and \
           row.get('is_mobile_bad',"FALSE") == 'FALSE' and \
           row.get('mobile_opt_in','TRUE') == 'TRUE':
            custom_fields['mobile'] = row['mobile_number']
        if row.get('phone_number','') != '' and \
           row.get('do_not_call',"FALSE") == "FALSE":
            custom_fields['Phone'] = row['phone_number']

        # Mapping employer field to organization (custom field in AN)
        if row.get('employer','') != '':
            custom_fields['organization'] = row['employer']

        # Pull in social media handles NationBuilder may have (custom fields in AN)
        if row.get('facebook_username','') != '':
            custom_fields['facebook_username'] = row['facebook_username']
        if row.get('twitter_login','') != '':
            custom_fields['twitter_login'] = row['twitter_login']

        # MailChimp Columns
        if row.get('phone','') != '':
            custom_fields['Phone'] = row['phone']
        
        address = {}
        address_lines = []
        if row.get('address','') != '':
            address_lines.append(row['address'])
        if address_lines:
            address["address_lines"] = address_lines
        if row.get('city','') != '':
            address["locality"] = row['city']
        if row.get('state','') != '':
            address["region"] = row['state']
        if row.get('zip_code','') != '':
            address["postal_code"] = row['zip_code']
        if address:
            if "postal_addresses" not in new_person["person"]:
                new_person["person"]["postal_addresses"] = []
            new_person["person"]["postal_addresses"].append(address)

        # This request uses the Person Helper
        # (which doesn't support custom fields or multiple addresses?)
        response = {}
        user = {}
        if not CONFIG_DRY_RUN:
            an_self = AN['self']
            for tries in range(1,6):
                try:
                    user = an_self.create(new_person)  # Can throw a 503 Service Temporarily Unavailable error
                    response = user
                    break
                except exc.HALNavigatorError as inst:
                    print("[{:0>3}] Create Exception: HALNavigatorError: {}".format(rowid, inst), flush=True, file=log_fh)
                    print("[{:0>3}] Create Exception: Retrying after {} seconds".format(rowid, tries))
                    time.sleep(tries)
            if not response:
                print("[{:0>3}] FAIL Insert".format(rowid), flush=True, file=log_fh)
                continue

        # Need to do a Person PUT to add custom fields.
        if custom_fields:
            if 'tag_list' in custom_fields:
                del custom_fields['tag_list']
            if not CONFIG_DRY_RUN:
                response = {}
                for tries in range(1,5):
                    try:
                        response = user['self'].upsert({"custom_fields" : custom_fields})
                        break
                    except exc.HALNavigatorError as inst:
                        print("[{:0>3}] Upsert Exception: HALNavigatorError: {}".format(rowid, inst), flush=True, file=log_fh)
                        print("[{:0>3}] Upsert Exception: Retrying after {tries} seconds".format(rowid, tries=tries))
                        time.sleep(tries)
                if not response:
                    print("[{:0>3}] FAIL Upsert (Create OK)".format(rowid), flush=True, file=log_fh)
                    continue
            else:
                new_person["custom_fields"] = custom_fields

        activists = activists + 1

        if CONFIG_VERBOSE:
            if CONFIG_DRY_RUN:
                show_tree = new_person
            else:
                show_tree = response.state
                show_tree["add_tags"] = new_person["add_tags"]

            print("[{:0>3}] OK {dry}{tree}".format(rowid,
                                                    dry="DRY " if CONFIG_DRY_RUN else '',
                                                    tree=json.dumps(show_tree, indent=4)),
                  flush=True, file=log_fh)
        else:
           print("[{:0>3}] OK".format(rowid), flush=True, file=log_fh)
            

ENDTIME = datetime.now()
duration = ENDTIME - starttime
duration_microseconds = duration.seconds * 1000000 + duration.microseconds

act_per_second = ""
if activists > 0:
    act_per_second = "{:.0f}/sec.".format(1000000.0 / (duration_microseconds / activists))

print('{}: Processed {} activists in {} {}'.format(CONFIG_LOGFILE, activists, duration, act_per_second), file=sys.stderr)

if log_fh != sys.stdout:
    log_fh.close()