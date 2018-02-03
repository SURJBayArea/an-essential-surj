
# Essential ActionNetwork Tools

Tools for working with the Action Network API

## Action Network Import People

Takes NationBuilder or other csv file, mapping tags and fields.

    an-import-people.py

### Usage

    usage: an-import-people.py [-h] [--group GROUP] [--start START]
                               [--end END | --count COUNT] [--verbose]
                               [--unsubscribed] [--force] [--dry_run]
                               [profile] inputFile
    
    Import activities in .csv format (native NationBuilder import)
    
    positional arguments:
      profile               The profile name in an_profiles.py
      inputFile             Importable CSV file
    
    optional arguments:
      -h, --help            show this help message and exit
      --group GROUP, -g GROUP
                            Action Network Group
      --start START, -s START
                            First row to process (starting at 1)
      --end END, -e END     Last row to process
      --count COUNT, -c COUNT
                            Number of rows to process
      --verbose, -v         Show data
      --unsubscribed, -u    Include unsubscribed users
      --force, -f           Force subscribe of existing users
      --dry_run, -d         Process imported data but don't send to Action     Network
  
## Installation

REST Navigator is a library for interacting with HAL+JSON APIs of which OSDI conforms. See https://github.com/deontologician/restnavigator.

    sudo python3 -m pip install restnavigator 

