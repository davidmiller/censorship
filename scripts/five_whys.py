"""
First pass analysis of JSON data:

Extract the five whys: 

Who 
What
When 
Where 
Why

Dump these into a record format we can do initial visualisations of.
"""
import json
import sys

import ffs

HERE = ffs.Path.here()
DATA = HERE / '../data'
BEACON = DATA / 'beacon'

RECORD = {
    'who': None,
    'what': None,
    'when': None,
    'where': None,
    'why': None
}

def load_data():
    f = BEACON/'beacon.json'
    return f.json_load()

def to_record(data):
    """
    Try to locate the answer to each question in DATA.
    return as a new record.
    """
    record = RECORD.copy()
    for f in data['fields']:
        #Main entry personal name
        if f['field_id'] == '100': 
            record['who'] = f['subvals']['Personal Name']
        # Title Statement
        if f['field_id'] == '245':
            record['what'] = f['subvals']['Title']

        # Publication, distribution, etc
        if f['field_id'] == '260':
            try:
                record['when'] = f['subvals']['Date of publication, distribution, etc.']
            except KeyError:
                pass

        #Date/time note field
        if f['field_id'] == '518':
            try: 
                record['when'] = f['subvals']['Date/Time and Place of an Event Note']
            except KeyError:
                pass
#                print json.dumps(data, indent=2)
                 # print record
                 # sys.exit()
#    # print record
    return record

def main():
    """
    Entrypoint for extracting five whys:

    * Load the data
    * look for answers to our questions
    * Fill in for each record
    * Spit out as json

    Return: 0
    Exceptions: None
    """
    data = load_data()
    records = [to_record(i) for i in data]
    print json.dumps(records, indent=2)
    return 0

if __name__ == '__main__':
    sys.exit(main())
