'''
The common data for AutoCoding Clinical Documents
'''

# pylint: disable=invalid-name, line-too-long

import re
from flask import Flask

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
MetaMapLiteHeaders = None   # The HTTP Headers for calls to the MetaMapLite Service
MetaMapLiteServiceLock = None   # A Threading Lock used to avoid threadding issues in the MetaMapLite Service
MetaMapLiteResponse = None  # The data returned by the MetaMapLite Service
FlaskPort = None            # The port for the AutoCoding service on this server
solution = None             # The name of the solution for AutoCoding clinical documents
cleanPython = re.compile(r'\W+|^(?=\d)')  # Convert column names to valid Pandas variables
solutionMetaThesaurus = {}  # The Solution Specific MetaThesaurus codes, descriptions, source and source code
knownConcepts = set()       # The set of concepts known to be relevant to AutoCoding (from the configuration values)
otherConcepts = set()       # The set of concepts found in clinical documents of this type, but known to be irrelevant to this solution
sd = None                   # The Solution data model
sp = None                   # The Solution prepare module
sc = None                   # The Solution complete module
sa = None                   # The Solution analysis module
rawClinicalDocument = None  # The Clinical Document "as read"
preparedDocument = None     # The Prepared Clinical Document
codedSentences = None       # The MetaMapLite coded version of the Clinical Document
completedSentences = None   # The Coding Completed version of the Clinical Document
sentences = []              # The list of sentences/sentence parts of the MetaMapLite response (to which we attach mini documents of concepts)
'''
This is the main data structure - a list of the sentences in the clinical document.
Each sentence in the list has the following attributes
    [0] - a boolean that indicates that this sentence contains changes - parts of this sentence are not the same history as the start
    [1] - a boolean that indicates the initial history state of this sentence (True => isHistory)
    [2] - an integer - the character position of the start of this sentence within the document
    [3] - an integer - the length of this sentence
    [4] - a string - the text of this sentence
    [5] - a list of all the places in this sentence where history flips (into/out of history)
    [6] - a dictionary of the concepts within this sentence (a mini-document)
    [7] - the section containg this sentence

    Each mini-document (d.sentences[sentenceNo][6]) is a dictionary with an integer as the key (the start of this concept in the main document).
    The value for each key ('start') is a list of alternate concepts, all of which start at the same character position in the main document.
    Each alternate concept in the list is a dictionary of concept attributes.
    The keys for each alternate concept dictionary in the list are
        'length' - an integer - the number of characters in the sentence required to identifying this concept
        'history' - a boolean that indicates that this concept is historical information - in a history sentence or after this sentence flipped into history
        'concept' - a string - the MetaThesaurus concept.
        'used' - a boolean that is set to True when a concept has been used to identify a higher concept
        'text' - a string - the text at start, for 'length', which MetaMapLite found to be 'concept'.
        'partOfSpeech' - a sting - the part of speech tag (code) that indicates how this concept was used in the sentence (noun, adverb, adjective etc)
        'negation' - a string that indicates that this is a positive ('0'), negative ('1') or ambiguous ('2') concept
        'description' - a string - the description of this concept (which may differ from the text matched to this concept).
'''

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
preModifiers = {}			# The dictionary of MetaThesaurus concepts that get modified to another concept when preceded by specific words or phrases
postModifiers = {}			# The dictionary of MetaThesaurus concepts that get modified to another concept when followed by specific words or phrases
sentenceConcepts = []		# The list of concept and the regular expressions that represent those concepts, that are check on a sentence by sentence basis
grossNegation = []			# A list of pairs of things that negate all concept between these two markers
sentenceNegationLists = {}	# The lists of lower concepts in a sentence that need to be made ambiguous because of a negated instance of the higher concept
documentNegationLists = {}	# The lists of lower concepts anywhere in the document that need to be made ambiguous because of a negated instance of the higher concept
sentenceConceptSequenceSets = []	# The list of higher concepts and their asscociated concept sequence set that are checked on a sentence by sentence basis
sentenceConceptSets = []	# The list of higher concepts and their associated concept set that are checked on a sentence by sentence basis
documentConceptSequenceSets = []	# The list of higher concepts and their asscociated concept sequence set that are checked on a whole of document basis
documentConceptSets = []	# The list of higher concepts and their associated concept set that are checked on a whole of document basis
sentenceConceptFound = []   # The list of sentence concepts found
documentConceptFound = []   # The list of documents concepts found

# Precompiled regular expressions for complete
noColon = re.compile(r'([:])\s+$')
addPeriod = re.compile(r'([^.])\s*$')

# Analysis
grid = []                   # The list of lists of Diagnoses (Site/Finding pairs) and the associate S/E/O code [and rank]
historyProcedure = {}       # The dictionary of historical procedures (key:position in document, value: tuple of procedure code and sentenceNo)
hysterectomy = set()        # The set of tuples of hysterectomy procedures (tuple:(concept, sentenceNo))
otherProcedure = set()      # The set of tuples of other (non-hysterectomy) procedures (tuple:(concept, sentenceNo))

# Flask
app = Flask(__name__)
