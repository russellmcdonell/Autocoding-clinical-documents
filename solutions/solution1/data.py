'''
The Solution Specific common data.
'''

# pylint: disable=invalid-name, line-too-long

import re

listMarkers = []				# The list of list markers that identify a list item
hyphenatedWords = []			# The list of hyphenated words that should be preserved in labels/headings

tisHyphen = re.compile(r'(\w+)-(\w+)', re.IGNORECASE)
preHyphen = re.compile(r'\s+-(\w+)', re.IGNORECASE)
postHyphen = re.compile(r'(\w+)-\s+', re.IGNORECASE)
hasColon = re.compile(r':')
noColon = re.compile(r':\s+$')
addPeriod = re.compile(r'([^.])\s*$')
allCAPS = re.compile(r'^([A-Z\s]*[A-Z])([:.\s]*)$')
tisCLINICAL = re.compile(r'^\s*CLINICAL')
tisINFORMATION = re.compile(r'\b' + 'INFORMATION\s*:')
