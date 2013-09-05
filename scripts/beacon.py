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

        # There are some other corruptions wrt countries.
        # Can't find a pattern so hard coding for now.
        if string == ('*650 $aIndonesia'):
            fid = 650
            val = "$aIndonesia"

        # 98020206
        if string == '*041 $aeng':
            fid = '041'
            val = '$aeng'

        # 9904450
        if string == '*041  fre':
            fid = '041'
            val = '$afre'

        # 9910747
        if string == '*041  lit':
            fid = '041'
            val = '$alit'

        # 9919074
        if string == '*651  $5458':
            fid = '651'
            val = '$a5458'

        # 9912757
        if string == '*651  8023':
            fid = '651'
            val = '$a8023'
        # 98020280
        if string == '*651  a6357':
            fid = '651'
            val = '$a6357'

        if string == '*020  $10.00 (pbk.)':
            fid = '020'
            val = '$a$10.00 (pbk.)'

        subklass_name = 'Field{0}'.format(fid)
        if subklass_name in globals():
            return globals()[subklass_name](fid, val)
        nofields = [
            # Ignore the extra French (?) geographic area fields for now.
            # c.f. 9912890
            '043',
            '710',
            '899',
            # Weird german extra fields (98020201)
            '029',
            '093',
            # Possibly investigate this UK cost field (98020204)
            '350',
            # Possibly investigate this UK ID field (98020215)
            '092',
            # These are US generic ID fields 9913178
            '019',
            # Possibly investigate UK name(?) fields (98020215)
            '761',
            # Possibly investigate this UK ID field (98020217)
            '090',
            # Who knows? (9913337)
            '782',
            # Meh (98020258)
            '793',
            # Some publisher (98020271)
            '265',
            # Some bool (9913198)
            '741',
            # Nonsense 9912760
            '690',
            ]
        if fid in nofields:
            return Field(fid, val)
        print subklass_name, fid
        print string, string == '*041 $aeng'
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
                        print self.__class__
                        raise
            else:
                try:
                    self.subvals[self.subfields[last_subcode]] += line
                except KeyError:
                    print self.__class__
                    raise

        for subcode, subfield in self.subfields.items():
            meth = getattr(self, 'parse_{0}'.format(subcode[1:]), None)
            if meth:
                if subfield in self.subvals:
                    self.subvals[subfield] = meth(self.subvals[subfield])



class SubField(Field):
    def __str__(self):
        val = "    " + "\n    ".join("{0}: {1}".format(k, v) for k, v in self.subvals.items())
        return "<Normarc Field({name}) Object>:\n{value}".format(
            name = self.name,
            value=val
            )


class Field003(SubField):
    name = "Control Number Identifier"
    subfields = {
        '$a': "Control Number Identifier"
        }


class Field005(SubField):
    name = "Date and Time of Latest Transaction"
    subfields = {
        '$a': "Date Time"
        }


class Field010(SubField):
    name = "Library of Congress Control Number"
    subfields = {
        '$a': "LC control number",
        '$o': 'UNKNOWN NUMER',
        }


class Field015(SubField):
    name = "National Bibliography Number"
    subfields = {
        '$a': "National bibliography"
        }


class Field020(SubField):
    name = 'International Standard Book Number'
    subfields = {
        '$a': 'International Standard Book Number',
        '$c': 'Terms of availability',
        '$z': 'Cancelled/Invalid ISBN',
        '$8': 'Field link and sequence number',
        }


class Field022(SubField):
    name = 'International Standard Serial Number'
    subfields = {
        '$a': 'International Standard Serial Number',
        }


class Field035(SubField):
    name = 'System Control Number'
    subfields = {
        '$a': 'System control number'
        }


class Field040(SubField):
    name = 'Cataloging Source'
    subfields = {
        '$a': 'Original cataloging agency',
        '$b': 'Language of cataloging',
        '$c': 'Transcribing agency',
        '$d': 'Modifying agency'
        }


class Field041(SubField):
    name = 'Language code of text/sound track or separate title'
    subfields = {
        '$a':'Language code of text/sound track or separate title',
        '$e': 'Language code of librettos',
        '$h': 'Language code of original',
        }

    def parse_a(self, value):
        return LANGS.get(value)


class Field042(SubField):
    name = 'Authentication Code'
    subfields = {
        '$a': 'Authentication code'
        }


class Field050(SubField):
    name = 'Library of Congress Call Numbe'
    subfields = {
        '$a': 'Classification Number',
        '$b': 'Item Number'
        }


class Field082(SubField):
    name = 'Dewey Decimal Classification Number'
    subfields = {
        '$a': 'Classification Number'
        }


class Field086(SubField):
    name = 'Government Document Classification Number'
    subfields = {
        '$a': 'Classification Number'
        }


class Field100(SubField):
    name = 'Main Entry-Personal Name'
    subfields = {
        '$a': 'Personal Name'
        }


class Field110(SubField):
    name = 'Main Entry-Corporate Name'
    subfields = {
        '$a': 'Corporate Name',
        '$6': 'Linkage',
        }


class Field111(SubField):
    name = 'Main Entry-Meeting Name'
    subfields = {
        '$a': 'Meeting Name',
        '$6': 'Linkage',
        }


class Field130(SubField):
    name = 'Main Entry-Uniform Title'
    subfields = {
        '$a': 'Uniform Title',
        '$6': 'Linkage',
        }



class Field210(SubField):
    name = 'Abbreviated Title'
    subfields = {
        '$a': 'Abbreviated Title',
        '$6': 'Linkage',
        }


class Field222(SubField):
    name = 'Key Title'
    subfields = {
        '$a': 'Key Title',
        '$6': 'Linkage',
        }


class Field240(SubField):
    name ='Uniform Title'
    subfields = {
        '$a': 'Uniform Title',
        '$l': 'Language of a work',
        # We think german extra title field (9911083)
        '$w': 'Extra Title',
        }

    def parse_l(self, value):
        real_languages = [
            'English',
            'French'
            ]
        if value in LANGS:
            return LANGS[value]
        if value in real_languages:
            return value
        return countries[value]


class Field245(SubField):
    name ='Title Statement'
    subfields = {
        '$a': 'Title',
        '$6': 'Linkage',
        }


class Field246(SubField):
    name ='Varying form of Title'
    subfields = {
        '$a': 'Title proper/short title',
        '$b': 'Remainder of title',
        '$c': 'EXTRA BEACON FIELD',
        }


class Field250(SubField):
    name ='Edition Statement'
    subfields = {
        '$a': 'Edition',
        '$b': 'Remainder of edition statement'
        }


class Field260(SubField):
    name = 'Publication, Distribution, etc. (Imprint)'
    subfields = {
        '$a': 'Place of publication, distribution, etc',
        '$b': 'Name of publisher, distributor, etc.',
        '$c': 'Date of publication, distribution, etc.',
        '$6': 'Linkage'
        }


class Field263(SubField):
    name = 'Projected Publication Date'
    subfields = {
        '$a': 'Projected publication date'
        }


class Field300(SubField):
    name = 'Physical Description'
    subfields = {
        '$a': 'Extent',
        '$b': 'Other Physical Details',
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


class Field490(SubField):
    name = "Series Statement"
    subfields = {
        '$a': 'Series Statement',
        '$v': 'Volume/sequential designation'
        }

class Field500(SubField):
    name = 'General Note'
    subfields = {
        '$a': 'General Note'
        }


class Field502(SubField):
    name = 'Dissertation Note'
    subfields = {
        '$a': 'Dissertation Note'
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


class Field510(SubField):
    name = 'Citation/References Note'
    subfields = {
        '$a': 'Name of source',
        '$c': 'Location within source'
        }


class Field515(SubField):
    name = 'Numbering Peculiarities Note'
    subfields = {
        '$a': 'Numbering Peculiarities Note'
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


class Field533(SubField):
    name = 'Reproduction Note'
    subfields = {
        '$a': 'Type of reproduction',
        '$b': 'Place of reproduction',
        '$c': 'Agency responsible for reproduction',
        '$d': 'Date of reproduction',
        '$e': 'Physical description of reproduction',
        '$f': 'Series statement of reproduction'
        }


class Field546(SubField):
    name = 'Language Note'
    subfields = {
        '$a': 'Language Note'
        }


class Field580(SubField):
    name = 'Linking Entry Complexity Note'
    subfields = {
        '$a': 'Linking Entry Complexity Note'
        }


class Field610(SubField):
    name = 'Subject Added Entry-Corporate Name'
    subfields = {
        '$a': 'Corporate name or jurisdiction name as entry element',
        }


class Field630(SubField):
    name = 'Subject Added Entry-Uniform Title'
    subfields = {
        '$a': 'Uniform Title',
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
        '$a': 'Country',
        '$x': 'Geographic Subdivision',
        '$y': 'Chronological Subdivision',
        '$6': 'Linkage',
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
        6357: 'United States',
        8046: 'Sweeden',
        8051: 'United Kingdom',
        6322: 'Canada',
        6138: 'Haiti',
        8050: 'USSR (until December 1991)',
        5531: 'Guinea',
        8013: 'Austria',
        8028: 'Greenland',
        5000: 'Africa',
        6414: 'Argentina',
        6127: 'Cuba',
        5117: 'Burundi',
        8029: 'Hungary',
        5422: 'Comoros',
        8011: 'Albania',
        6430: 'Ecuador',
        8018: 'Cyprus',
        6420: 'Brazil',
        7130: 'Japan',
        8015: 'Bulgaria',
        8000: 'Europe',
        0000: 'Universal',
        6459: 'Uruguay',
        8043: 'Romania',
        8052: 'Holy See (Vatican)',
        6243: 'Mexico',
        5547: 'Niger',
        7124: 'Hong Kong Special Administrative Region of China',
        6000: 'Americas',
        7520: 'Cambodia',
        5467: 'Zimbabwe',
        8042: 'Portugaul',
        8100: 'Eastern Europe',
        8033: 'Italy',
        7000: 'Asia',
        6200: 'Central America',
        6236: 'Guatemala',
        8039: 'Northern Ireland',
        8024: 'German Democratic Republic (from 1949 until October 1991)',
        8019: 'Czechoslovakia (until December 1992)',
        8056: 'Czech Republic',
        6429: 'COUNTRY UNKNOWN',
        7151: 'Tibet (China)',
        7144: 'Korea, Republic of',
        5100: 'Middle Africa',
        7215: 'Armenia',
        9021: 'New Zealand',
        5400: 'Southern Africa',

        }

    def parse_a(self, val):
        try:
            ccode = int(val)
            return self.countries[int(val)]
        except ValueError:
            inverted = dict([ (v, k) for k, v in self.countries.iteritems( ) ])
            if val in inverted:
                return inverted[val]
            raise ValueError("I have no idea what to make of " + val)


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


class Field711(SubField):
    name = 'Added Entry-Meeting Name'
    subfields = {
        '$a': 'Meeting name or jurisdiction name as entry element',
        '$c': 'Location of meeting',
        '$d': 'Date of meeting',
        '$n': 'Number of part/section/meeting'
        }


class Field730(SubField):
    name = 'Added Entry-Uniform Title'
    subfields = {
        '$a': 'Uniform Title',
        '$n': 'Number of part/section of a work',
        }


class Field740(SubField):
    name = 'Added Entry-Uncontrolled Related/Analytical Title'
    subfields = {
        '$a': 'Uncontrolled related/analytical title'
        }


class Field752(SubField):
    name = 'Added Entry-Hierarchical Place Name'
    subfields = {
        '$a': 'Country or larger entity',
        '$d': 'City',
        }


class Field770(SubField):
    name = 'Supplement/Special Issue Entry'
    subfields = {
        '$t': 'Title',
        '$l': 'UNKNOWN NUMBER',
        }


class Field780(SubField):
    name = 'Preceding Entry'
    subfields = {
        '$a': 'Main entry heading'
        }


class Field785(SubField):
    name = 'Succeeding Entry'
    subfields = {
        '$t': 'Title'
        }


class Field830(SubField):
    name = 'Series Added Entry-Uniform Title'
    subfields = {
        '$a': 'Uniform Title'
        }


class Field880(SubField):
    name = 'Alternative Graphic Representation'
    subfields = {
        '$a': 'Alternative Graphic Representation'
        }



class Record(object):
    def __init__(self, record_id, fields=[]):
        self.record_id = record_id
        self.fields = fields

    def __str__(self):
        fields = "\n".join(str(f) for f in self.fields)
        return """=======================================
<Normarc Record Object> {record_id}\n{fields}
=======================================""".format(
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
