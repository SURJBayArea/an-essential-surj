
# Essential ActionNetwork Tools

Tools for working with the Action Network API

## Action Network Import People

Takes NationBuilder or other csv file, mapping tags and fields.

    an-import-people.py

### Usage

    usage: an-import-people.py [-h] [--group GRP] [--start N]
                            [--end N | --count N] [--verbose] [--unsubscribed]
                            [--force] [--dryrun] [--no NOS] [--logfile LOGFILE]
                            [--skip]
                            inputFile

    Import people from a NationBuilder or MailChimp Export (CSV)

    positional arguments:
        inputFile             Importable CSV file

    optional arguments:
        -h, --help            show this help message and exit
        --group GRP, -g GRP   Action Network Group. Also profile name in
                                an_profiles.py.
        --start N, -s N       First row to process (starting at 1)
        --end N, -e N         Last row to process
        --count N, -c N       Number of rows to process
        --verbose, -v         Show data
        --unsubscribed, -u    Include unsubscribed users
        --force, -f           Force subscribe of existing users
        --dryrun, -d          Process imported data but don't send to Action Network
        --no NOS, -n NOS      Comma separated strings that mean no tag (for tag
                                columns)
        --logfile LOGFILE, -l LOGFILE
                                Activity log
        --skip                Skip importing earlier imports (as per log file)

  
## Installation

REST Navigator is a library for interacting with HAL+JSON APIs of which OSDI conforms. See https://github.com/deontologician/restnavigator.

    sudo python3 -m pip install restnavigator 

