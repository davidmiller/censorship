"""
Processing script to convert Beacon data from NORMARC format.
"""
import sys
import csv

import ffs
from iso3166 import countries

HERE = ffs.Path.here()
DATA = HERE / '../data'
LANGFILE = DATA / 'marc.langcodes.json'
BEACON = DATA / 'beacon'
BEACONRAW = BEACON / 'raw/data'

LANGS = LANGFILE.json_load()


class Field(object):
    subfields = None

    def __init__(self, field_id, value):
        self.field_id = field_id
        self.value = value
        if self.subfields:
            self.subvals = {}
            self.parse_subfields()

    def __str__(self):
        return "<Normarc Field({field_id}) Object>: {value}".format(
            field_id=self.field_id,
            value=self.value
            )

    @classmethod
    def fromstring(klass, string):
        """
        Return a field from the string representation.

        Format is:
        *(<?Field ID>\d{3})(<?Frist indicator>[\d ])(<?Second indicator>[\d ])(<?Field>.*)
        """
        # We don't do anything with indicators, so dump 'em
        fid = string[1:4]
        val = string[6:]

        # Some records, notably 98019558
        # don't actually conform to the standard with
        # What appears to be extra author names:
        # c.f.
        # http://www.ifex.org/egypt/2000/01/21/government_issues_decree_to_close/
        if string.startswith('*7400$a'):
            fid = 740
            val = string[5:]

        subklass_name = 'Field{0}'.format(fid)
        if subklass_name in globals():
            return globals()[subklass_name](fid, val)
        print subklass_name
        raise ValueError('No Subklass')

    def parse_subfields(self):
        """
        Parse the value passed in to form our subfields

        Return: None
        Exceptions: None
        """
        raw_lines = [l.strip() for l in self.value.split('\n')]
        last_subcode = None
        for line in raw_lines:
            if line.startswith('$'):
                subcode, subval = line[:2], line[2:]
                prev_subcode = last_subcode
                last_subcode = subcode
                try:
                    self.subvals[self.subfields[subcode]] = subval
                except KeyError: # Assume this to be a textual $ usage :S
                    if subcode not in self.subfields:
                        last_subcode = prev_subcode
                        if last_subcode is None:
                            print self.__class__
                            raise
                        self.subvals[self.subfields[last_subcode]] += line
                    else:
                        raise
            else:
                try:
                    self.subvals[self.subfields[last_subcode]] += line
                except KeyError:
                    raise

        for subcode, subfield in self.subfields.items():
            meth = getattr(self, 'parse_{0}'.format(subcode[1:]), None)
            if meth:
                self.subvals[subfield] = meth(self.subvals[subfield])


class SubField(Field):
    def __str__(self):
        val = "    " + "\n    ".join("{0}: {1}".format(k, v) for k, v in self.subvals.items())
        return "<Normarc Field({name}) Object>:\n{value}".format(
            name = self.name,
            value=val
            )


class Field020(SubField):
    name = 'International Standard Book Number'
    subfields = {
        '$a': 'International Standard Book Number'
        }


class Field041(SubField):
    name = 'Language code of text/sound track or separate title'
    subfields = {'$a':'Language code of text/sound track or separate title'}

    def parse_a(self, value):
        return LANGS.get(value)


class Field100(SubField):
    name = 'Main Entry-Personal Name'
    subfields = {
        '$a': 'Personal Name'
        }


class Field110(SubField):
    name = 'Main Entry-Corporate Name'
    subfields = {
        '$a': 'Corporate Name'
        }


class Field260(SubField):
    name = 'Publication, Distribution, etc. (Imprint)'
    subfields = {
        '$a': 'Place of publication, distribution, etc',
        '$b': 'Name of publisher, distributor, etc.',
        '$c': 'Date of publication, distribution, etc.'
        }


class Field240(SubField):
    name ='Uniform Title'
    subfields = {
        '$a': 'Uniform Title',
        '$l': 'Language of a work'
        }

    def parse_l(self, value):
        if value in LANGS:
            return LANGS[value]
        return countries[value]


class Field245(SubField):
    name ='Title Statement'
    subfields = {
        '$a': 'Title'
        }


class Field250(SubField):
    name ='Edition Statement'
    subfields = {
        '$a': 'Edition'
        }


class Field300(SubField):
    name = 'Physical Description'
    subfields = {
        '$a': 'Extent',
        '$c': 'Dimensions'
        }


class Field310(SubField):
    name = 'Current Publication Frequency'
    subfields = {
        '$a': 'Current publication frequency'
        }


class Field362(SubField):
    name = 'Dates of Publication and/or Sequential Designation'
    subfields = {
        '$a': 'Dates of Publication and/or Sequential Designation'
        }


class Field440(SubField):
    name = 'Series Statement/Added Entry-Title'
    subfields = {
        '$a': 'Series Title',
        '$v': 'Volume Number'
        }


class Field500(SubField):
    name = 'General Note'
    subfields = {
        '$a': 'General Note'
        }


class Field503(SubField):
    name = 'Censorship Note'
    subfields = {
        '$a': 'Note'
        }


class Field505(SubField):
    name = 'Formatted Contents Note'
    subfields = {
        '$a': 'Formatted contents note'
        }


class Field506(SubField):
    name = 'Restrictions on Access Note'
    subfields = {
        # Note this is overloaded to mean Censoring Body in Beacon
        '$a': 'Terms Governing Access',
        # Note this is overloaded to mean Censoring Body in Beacon
        '$b': 'Jurisdiction',
        # Note this is overloaded to mean Legal Reference in Beacon
        '$e': 'Authorization',
        # Note this is overloaded to mean Extent of censorship in Beacon
        '$3': 'Materials Specified'
        }

class Field518(SubField):
    name = 'Date/Time and Place of an Event Note'
    subfields = {
        # Note this is overloaded to mean Period of censorship in Beacon
        '$a': 'Date/Time and Place of an Event Note',
        # Note this is overloaded to mean Type of Material in Beaon
        '$3': 'Materials specified'
        }


class Field520(SubField):
    name = 'Summary, Etc.'
    subfields = {
        '$a': 'Summary, Etc'
        }


class Field650(SubField):
    name = 'Subject Added Entry-Topical Term'
    subfields = {
        '$a': 'Topical term or geographic name entry element',
        '$z': 'Geographic subdivision'
        }

# Beacon country code
class Field651(SubField):
    name = 'Country'
    subfields = {
        '$a': 'Country'
        }
    countries = {
        8048: 'Turkey',
        5311: 'Algeria',
        5325: 'Egypt',
        7327: 'Iran, Islamic Republic of',
        7329: 'Israel',
        7331: 'Jordan',
        7332: 'Kuwait',
        7334: 'Lebanon',
        5541: 'Mauritania',
        5442: 'Mauritius',
        5344: 'Morocco',
        7354: 'Palestine',
        7343: 'Quatar',
        7345: 'Saudi Arabia',
        5362: 'Tunisia',
        7352: 'United Arab Emirates',
        5118: 'Cameroon',
        9027: 'Solomon Islands',
        8053: 'Yugoslavia',
        5466: 'Zambia',
        6424: 'Chile',
        7439: 'Nepal',
        7355: 'Yemen',
        5412: 'Angola',
        9032: 'Vanuatu',
        7425: 'India',
        7441: 'Pakistan',
        7536: 'Malaysia',
        7447: 'Sri Lanka',
        8064: 'Russian Federation ',
        5259: 'Sudan',
        7553: 'Vietnam',
        5123: 'Democratic Republic of Congo',
        7348: 'Syria',
        5227: 'Ethiopia',
        8027: 'Greece',
        7516: 'Thailand',
        7117: 'China',
        5264: 'Tanzania, United Republic of',
        7216: 'Azerbaijan',
        5234: 'Kenya',
        5533: "Coted'Ivoire",
        5337: 'Libyan Arab Jamahiriya',
        5460: 'Swaziland',
        5536: 'Liberia',
        5446: 'Namibia',
        5128: 'Gabon',
        7526: 'Indonesia',
        5439: 'Malawi',
        6448: 'Peru',
        8071: 'Bosnia and Herzegovina',
        7230: 'Kazakhstan',
        5529: 'Gambia',
        8031: 'Ireland',
        8016: 'Belarus',
        7231: 'Kyrgyzstan',
        8045: 'Spain',
        5281: 'Eritrea',
        5532: 'Guinea-Bissau',
        5458: 'South Africa',
        8020: 'Denmark',
        8025: 'Germany',
        5548: 'Nigeria',
        9012: 'Australia',
        8041: 'Poland',
        8040: 'Norway',
        8023: 'France',
        8035: 'Luxembourg',
        8014: 'Belgium',
        8038: 'Netherlands',
        8060: 'Lithuania',
        8059: 'Latvia',
        8057: 'Estonia',

        }

    def parse_a(self, val):
        return self.countries[int(val)]

class Field691(SubField):
    name = 'Reason for censorship'
    subfields = {
        '$a': 'Reason'
        }


class Field692(SubField):
    name = 'Type of censorship'
    subfields = {
        '$a': 'Type'
        }


# Enquire what this means
class Field693(SubField):
    name = 'Unknown Beacon Field'
    subfields = {
        '$a': 'Something'
        }


class Field700(SubField):
    name = 'Added Entry-Personal Name'
    subfields = {
        '$a': 'Personal name',
        '$e': 'Relator term'
        }


class Field740(SubField):
    name = 'Added Entry-Uncontrolled Related/Analytical Title'
    subfields = {
        '$a': 'Uncontrolled related/analytical title'
        }


class Record(object):
    def __init__(self, record_id, fields=[]):
        self.record_id = record_id
        self.fields = fields

    def __str__(self):
        fields = "\n".join(str(f) for f in self.fields)
        return "<Normarc Record Object> {record_id}\n{fields}".format(
            record_id=self.record_id,
            fields=fields)


class NormarcReader(object):
    def __init__(self, path):
        self.path = path

    def __iter__(self):
        """
        Render the reader iterable
        """
        return self

    def next(self):
        """
        Return an individual record from the file.

        Return: Record
        Exceptions: StopIteration
        """
        end = False
        rid = int(self.path.readline())
        fields = []
        field = []
        while not end:
            line = self.path.readline()
            # Record ends
            if line.startswith('^'):
                end = True
                continue
            # New field
            if line.startswith('*'):
                if field: # Not the frist field?
                    fields.append(Field.fromstring('\n'.join(field)))
                    field = []
            field.append(line.strip())
            continue

        return Record(rid, fields=fields)


def main():
    """
    Entrypoint for Beacon conversoin

    Return:
    Exceptions:
    """
    for fname in sorted(BEACONRAW):
        fname = BEACONRAW/fname
        mreader = NormarcReader(fname)
        items = 0
        try:
            for record in mreader:
                print record
                items += 1
        except:
            print '** Items:', items
            raise
        break
    return 0


if __name__ == '__main__':
    sys.exit(main())
