'''
The common data for AutoCoding Clinical Documents
'''

# pylint: disable=invalid-name, line-too-long

import re

# This next section is plagurised from /usr/include/sysexits.h
EX_OK = 0        # successful termination
EX_WARN = 1        # non-fatal termination with warnings

EX_USAGE = 64        # command line usage error
EX_DATAERR = 65        # data format error
EX_NOINPUT = 66        # cannot open input
EX_NOUSER = 67        # addressee unknown
EX_NOHOST = 68        # host name unknown
EX_UNAVAILABLE = 69    # service unavailable
EX_SOFTWARE = 70    # internal software error
EX_OSERR = 71        # system error (e.g., can't fork)
EX_OSFILE = 72        # critical OS file missing
EX_CANTCREAT = 73    # can't create (user) output file
EX_IOERR = 74        # input/output error
EX_TEMPFAIL = 75    # temp failure; user is invited to retry
EX_PROTOCOL = 76    # remote error in protocol
EX_NOPERM = 77        # permission denied
EX_CONFIG = 78        # configuration error


progName = None             # The program name (stripped of .py)
inputDir = None             # The folder containing the clinical documents
inputFile = None            # The name of the clinical document to AutoCode
outputDir = None            # The name of the folder where the AutoCoding output will be created
MetaMapLiteHost = None      # The host name of the AutoCoding/MetaMapLite server
MetaMapLitePort = None      # The port for the MetaMapLite service on the AutoCoding/MetaMapLite server
MetaMapLiteURL = None       # The URL for the MetaMapLite service on the AutoCoding/MetaMapLite server
FlaskPort = None            # The port for the AutoCoding service on this server
solution = None             # The name of the solution for AutoCoding clinical documents
cleanPython = re.compile(r'\W+|^(?=\d)')  # Convert column names to valid Pandas variables
SolutionMetaThesaurus = {}  # The MetaThesaurus codes used in this solution
knownConcepts = set()       # The set of concepts known to be relevant to AutoCoding (from the configuration values)
sd = None                   # The Solution data model
sp = None                   # The Solution prepare module
sc = None                   # The Solution complete module
sa = None                   # The Solution analysis module

# Prepare
labels = []					# The list of regular expressions that should be replaced with new labels
terms = []					# The list of regular expressions that should be replaced with words
preambleMarkers = []		# A list of things that indicate that the following text in the text document is preamble (not the body of the text document)
preambleTerms = []			# The list of regular expressions that should be replaced with words in the preamble

# Complete
historyMarkers = []			# A list of things that indicate that the following sentences are history
preHistory = []				# A list of things that indicate that the following concepts are from a previous test
sectionMarkers = []			# A list of things that indicate that the following sentences are part of a specific section of the text document
equivalents = {}			# The dictionary of MetaThesaurus concepts and their autocoding equivalents (i.e. don't use X, we use Y)
butBoundaries = []			# A list of things that mark the end of a context when extending negation
preNegation = []			# A list of things that negate the following concept
immediatePreNegation = []	# A list of things that negate the immediately following concept
postNegation = []			# A list of things that negate the preceeding concept and any exception
immediatePostNegation = []	# A list of things that negate the immediately preceeding concept and any exception
preAmbiguous = []			# A list of things that make the following concept ambiguous
immediatePreAmbiguous = []	# A list of things that make the immediately following concept ambiguous
postAmbiguous = []			# A list of things that make the preceeding concept ambigous and any exception
immediatePostAmbiguous = []	# A list of things that make the immediately preceeding concept ambigous and any exception
preModifiers = []			# The list of MetaThesaurus concepts that get modified to another concept when preceded by specific words or phrases
postModifiers = []			# The list of MetaThesaurus concepts that get modified to another concept when followed by specific words or phrases
sentenceConcepts = []		# The list of concept and the regular expressions that represent those concepts, that are check on a sentence by sentence basis
grossNegation = []			# A list of pairs of things that negate all concept between these two markers
sentenceNegationLists = {}	# The lists of lower concepts in a sentence that need to be made ambiguous because of a negated instance of the higher concept
documentNegationLists = {}	# The lists of lower concepts anywhere in the document that need to be made ambiguous because of a negated instance of the higher concept
sentenceConceptSequenceSets = []	# The list of higher concepts and their asscociated concept sequence set that are checked on a sentence by sentence basis
sentenceConceptSets = []	# The list of higher concepts and their associated concept set that are checked on a sentence by sentence basis
inSentenceConceptSets = {}	# The dictionary of concepts that exist in one or more of the sentence concept sets and the list of sentence concept sets this concept exits in
documentConceptSequenceSets = []	# The list of higher concepts and their asscociated concept sequence set that are checked on a whole of document basis
documentConceptSets = []	# The list of higher concepts and their associated concept set that are checked on a whole of document basis
inDocumentConceptSets = {}	# The dictionary of concepts that exist in one or more of the document concept sets and the list of document concept sets this concept exits in

# Precompiled regular expressions for complete
noColon = re.compile(r'([:])\s+$')
addPeriod = re.compile(r'([^.])\s*$')
