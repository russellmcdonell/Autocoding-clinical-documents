'''
The Solution Specific common data.
'''

# pylint: disable=invalid-name, line-too-long

import re

# Required for solution specific document preparation
listMarkers = []				# The list of list markers that identify a list item
hyphenatedWords = set()			# The set of hyphenated words that should be preserved in labels/headings

tisHyphen = re.compile(r'(\w+)-(\w+)', re.IGNORECASE)
preHyphen = re.compile(r'\s+-(\w+)', re.IGNORECASE)
postHyphen = re.compile(r'(\w+)-\s+', re.IGNORECASE)
hasColon = re.compile(r':')
noColon = re.compile(r':\s+$')
addPeriod = re.compile(r'([^.])\s*$')
allCAPS = re.compile(r'^([A-Z\s]*[A-Z])([:.\s]*)$')
tisCLINICAL = re.compile(r'^\s*CLINICAL')
tisINFORMATION = re.compile(r'\b' + r'INFORMATION\s*:')


# Required for solution specific coding completion
solution = {}           # A dictionary of various state variables


# Required for solution specific analysis
# Some fixed MethaThesaurus codes
cervixUteri = 'C0007874'
endomStructure = 'C0014180'
normalCervixCode = 'C0567243'
normalEndomCode = 'C0237029'
noAbnormality = 'C0559229'

AIHWprocedure = {}      # The dictionary of AIHW Procedure codes with matching description
AIHWfinding = {}        # The dictionary of AIHW Finding codes with matching description
Site = {}               # The dictionary of MetaThesaurus Site codes with matching SNOMED-CT code/description/site/subsite
Finding = {}            # The dictionary of MetaThesaurus Finding codes with matching SNOMED-CT code/description/AIHW codes for each Site
Procedure = {}          # The dictionary of MetaThesaurus Procedure codes with matching SNOMED-CT code/description/rank for each Site/AIHW codes for each Site
SiteImplied = {}        # The dictionary of concepts and the concept (must be Site) that they imply
FindingImplied = {}     # The dictionary of concepts and the concept (must be Finding) that they imply
SiteRestrictions = {}   # The dictionary of Findings and the restricted set of Site(s) that they can be paired with
SiteImpossible = {}     # The dictionary of Findings and the set of Site(s) that they can not be paired with
SiteRank = {}           # The dictionary of Findings and associated dictionary of Site(s) with their associated likelyhood rank
SiteDefault = {}        # The dictionary of Findings and associated default Sites
DiagnosisImplied = {}   # The dictionary of concepts and two concepts (must be Site and Finding) that they imply
ProcedureImplied = {}   # The dictionary of concepts and Procedure concepts that they imply
ProcedureDefined = {}   # The dictionary of Procedure concepts and two concepts (must be Procedure and Site) that mean that this produre must have happened

# Report data
historyProcedure = {}   # The dictionary of history procedures (key: location of procedure code in clinical document, value: concept)
hysterectomy = set()    # The set of a hysterectomy procedures
otherProcedure = set()  # The set of non-hysterectomy procedures
grid = []               # The list of Diagnoses to report (Site/Finding pairs with AIHW S/E/O code)
reportS = None          # The most important S code
reportE = None          # The most important E code
reportO = None          # The most important O code
reportAIHWprocedure = {}    # The dictionary of the AIHW procedure to report
reportSN_CTprocedure = {}   # The dictionary of the SNOMED_CT procedure to report
ReportSites = []        # The list of Report site sequence concepts
