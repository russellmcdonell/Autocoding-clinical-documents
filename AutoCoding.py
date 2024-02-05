# pylint: disable=line-too-long, broad-exception-caught
'''
Script AutoCoding.py
A script to find clinical concepts (MetaThesaurus codes) in text document and map them to other coding systems.

This script import modules for the relevant text document type; a module for preparing the document text for autocoding,
a module for completing any coding not completed by MetaMapLite (extending negation etc),
and a module for analysing the required codes.

This script reads a text document from <stdin> or reads a text documents from a file(s),
or reads text documents from a folder and autocodes it/them and prints the extracted codes.

Labels and lists are processed before Terms.
History section and history markers are found before concepts are extracted.
Modifiers are done


    SYNOPSIS
    $ python AutoCode.py [-I inputDir|--inputDir=inputDir]
        [-i inputFile|--inputFile=inputFile]
        [-O outputDir|--outputDir=outputDir]
        [-C configDir|--configDir=configDir]
        [-c configFile|--configFile=configFile]
        [-v loggingLevel|--verbose=logingLevel]
        [-L logDir|--logDir=logDir]
        [-l logfile|--logfile=logfile]
        [-|filename]...


    REQUIRED


    OPTIONS
    -I inputDir|--inputDir=inputDir
    The folder containing the text document(s).

    -I inputFile|--inputFile=inputFile
    The name of the clinical document to be AutoCoded.

    -O outputDir|--outputDir=outputDir
    The foleder where the output file(s) will be created.

    -H hostname|--MetaMapLiteHost=hostname
    The name of the MetaMapLite Server (default="localhost")

    -P port|--MetaMapLitePort=port
    The port for the AutoCoding service on the MetaMapLite Server (default="8080")

    -U URL|--MetaMapLiteURL=URL
    The URL for the AutoCoding service on the MetaMapLite Server (default="localhost"")

    -v loggingLevel|--verbose=loggingLevel
    Set the level of logging that you want.

    -L logDir|--logDir=logDir
    The directory where the log file will be created (default=".").

    -l logfile|--logfile=logfile
    The name of a log file where you want all messages captured.


    THE MAIN CODE
    Parse the command line arguments and set up error logging.
    Then import the solution files and read in the configuration data.
    Then process each file name in the command line - read the text document,
    autocode it, analyze the sentences and codes before printing the results.
'''

# pylint: disable=invalid-name, bare-except, pointless-string-statement, unspecified-encoding

import os
import sys
import logging
import importlib
import threading
import re
from http import client
from openpyxl import load_workbook
import functions as f
import data as d


if __name__ == '__main__':
    '''
    The main code
    Start by parsing the command line arguements and setting up logging.
    Then import the solution files and read in the configuration data.
    Validate the solution - all files exist, all worksheets in workbooks.
    Then process each file name in the command line - read the text document,
    autocode it, analyze the sentences and codes before printing the results.
    '''

    # Set the command line options
    parser = f.setArguments(False)

    # Parse the command line
    f.doArguments(parser, False)

	# Make sure we can connect to the MetaMapLite Service
    '''
    MetaMapLiteConnection = None				# The MetaMapLite http connection
    MetaMapLiteServiceLock = threading.Lock()	# A Threading Lock used to avoid threading issues in the MetaMapLiteService
    MetaMapLiteHeaders = {'Content-type':'application/x-www-form-urlencoded', 'Accept':'application/json'}
    try:
        MetaMapLiteConnection = client.HTTPConnection(d.MetaMapLiteHost, d.MetaMapLitePort)
        MetaMapLiteConnection.close()
    except (client.NotConnected, client.InvalidURL, client.UnknownProtocol,client.UnknownTransferEncoding,client.UnimplementedFileMode,   client.IncompleteRead, client.ImproperConnectionState, client.CannotSendRequest, client.CannotSendHeader, client.ResponseNotReady, client.BadStatusLine) as e:
        logging.critical('Cannot connect to the MetaMapLite Service on host (%s) and port (%s) [error:(%s)]', d.MetaMapLiteHost, d.MetaMapLitePort, repr(e))
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(d.EX_UNAVAILABLE)
    '''

    # Check that the solution files all exist and appear correct.
    if not os.path.isdir(os.path.join('solutions', d.solution)):
        logging.critical('No solution folder named "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'data.py')):
        logging.critical('No solution file "data.py" in solution folder "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'prepare.py')):
        logging.critical('No solution file "prepare.py" in solution folder "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'prepare.xlsx')):
        logging.critical('No solution file "prepare.xlsx" in solution folder "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'complete.py')):
        logging.critical('No solution file "complete.py" in solution folder "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'complete.xlsx')):
        logging.critical('No solution file "complete.xlsx" in solution folder "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'analyze.py')):
        logging.critical('No solution file "analyze.py" in solution folder "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'analyze.xlsx')):
        logging.critical('No solution file "analyze.xlsx" in solution folder "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'Solution MetaThesaurus.xlsx')):
        logging.critical('No solution file "Solution MetaThesaurus.xlsx" in solution folder "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Check the solution MetaThesaurus Excel workbook
    wb = load_workbook(os.path.join('solutions', d.solution, 'Solution MetaThesaurus.xlsx'))
    requiredColumns = ['MetaThesaurus code', 'MetaThesaurus description']
    this_df = f.checkWorksheet(wb, 'Solution MetaThesaurus', 'Solution MetaThesaurus', requiredColumns, True)
    this_df = this_df.set_index(this_df.iloc[:,0].name)     # The code is really the index/dictionary keys()
    this_df = this_df.rename(columns={'MetaThesaurus_description': 'description'})
    d.SolutionMetaThesaurus = this_df.to_dict(orient='index')

    # Import the solution specific data module
    try:
        d.sd = importlib.import_module('solutions.' + d.solution + '.data')
    except Exception as e:
        logging.fatal('Cannot import "data.py" for solution "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Check the solution 'prepare' Excel workbook
    wb = load_workbook(os.path.join('solutions', d.solution, 'prepare.xlsx'))
    requiredColumns = ['Label', 'Replacement']
    f.loadSimpleCompileSheet(wb, 'prepare', 'labels', requiredColumns, r'^', None, False, False, d.labels)
    requiredColumns = ['Common', 'Technical']
    f.loadSimpleCompileSheet(wb, 'prepare', 'terms', requiredColumns, None, None, True, True, d.terms)
    requiredColumns = ['Preamble markers', 'isCase', 'isStart']
    f.loadBoolComileWorksheet(wb, 'prepare', 'preamble markers', requiredColumns, None, None, True, d.preambleMarkers)
    requiredColumns = ['Preamble terms', 'Technical']
    f.loadSimpleCompileSheet(wb, 'prepare', 'preamble terms', requiredColumns, None, None, True, True, d.preambleTerms)

    # Import the solution specific prepare module and check that it has all the required functions
    try:
        d.sp = importlib.import_module('solutions.' + d.solution + '.prepare')
    except Exception as e:
        logging.fatal('Cannot import "prepare.py" for solution "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    for requiredFunction in ['configure']:
        if not hasattr(d.sp, requiredFunction):
            logging.fatal('"prepare" module in solution "%s" is missing the "%s" function', d.solution, requiredFunction)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # Now do any solution specific configuration and initialzation
    configConcepts = d.sp.configure(wb)
    d.knownConcepts.update(configConcepts)

    # Check the solution 'complete' Excel workbook
    wb = load_workbook(os.path.join('solutions', d.solution, 'complete.xlsx'))
    requiredColumns = ['History markers', 'isCase', 'isStart']
    f.loadBoolComileWorksheet(wb, 'complete', 'history markers', requiredColumns, None, None, True, d.historyMarkers)
    requiredColumns = ['Pre history']
    f.loadSimpleCompileSheet(wb, 'complete', 'pre history', requiredColumns, None, None, True, True, d.preHistory)
    requiredColumns = ['Section markers', 'Section', 'isCase']
    f.loadSimpleCompileSheet(wb, 'complete', 'section markers', requiredColumns, None, None, True, True, d.sectionMarkers)
    requiredColumns = ['SolutionID', 'MetaThesaurusID(s)']
    this_df = f.checkWorksheet(wb, 'complete', 'equivalents', requiredColumns, False)
    for index, row in this_df.iterrows():
        equivalent = row[0]
        d.knownConcepts.add(row[0])
        j = 1
        while (j < len(row)) and (row[j] is not None):
            d.equivalents[row[j]] = equivalent
            d.knownConcepts.add(row[j])
            j += 1
    requiredColumns = ['But boundaries']
    f.loadSimpleCompileSheet(wb, 'complete', 'but boundaries', requiredColumns, None, None, True, True, d.butBoundaries)
    requiredColumns = ['Pre negations']
    f.loadCompileConceptsWorksheet(wb, 'complete', 'pre negations', requiredColumns, None, r'.*', d.preNegation)
    requiredColumns = ['Immediate pre negations']
    f.loadCompileConceptsWorksheet(wb, 'complete', 'immediate pre negations', requiredColumns, None, r'\s+', d.immediatePreNegation)
    requiredColumns = ['Post negations', 'Exceptions']
    f.loadCompileCompileWorksheet(wb, 'complete', 'post negations', requiredColumns, r'.*', d.postNegation)
    requiredColumns = ['Immediate post negations', 'Exceptions']
    f.loadCompileCompileWorksheet(wb, 'complete', 'immediate post negations', requiredColumns, r'\s*', d.immediatePostNegation)
    requiredColumns = ['Pre ambiguous']
    f.loadCompileConceptsWorksheet(wb, 'complete', 'pre ambiguous', requiredColumns, None, r'.*', d.preAmbiguous)
    requiredColumns = ['Immediate pre ambiguous']
    f.loadCompileConceptsWorksheet(wb, 'complete', 'immediate pre ambiguous', requiredColumns, None, r'\s+', d.immediatePreAmbiguous)
    requiredColumns = ['Post ambiguous', 'Exceptions']
    f.loadCompileCompileWorksheet(wb, 'complete', 'post ambiguous', requiredColumns, r'\s*', d.postAmbiguous)
    requiredColumns = ['Immediate post ambiguous', 'Exceptions']
    f.loadCompileCompileWorksheet(wb, 'complete', 'immediate post ambiguous', requiredColumns, r'\s*', d.immediatePostAmbiguous)
    requiredColumns = ['MetaThesaurusID', 'SolutionID', 'Modifier']
    this_df = f.checkWorksheet(wb, 'complete', 'pre modifiers', requiredColumns, True)
    f.loadModifierWorksheet(wb, 'complete', 'pre modifiers', requiredColumns, None, r'\s.*$', d.preModifiers)
    f.loadModifierWorksheet(wb, 'complete', 'post modifiers', requiredColumns, r'^\s*', None, d.postModifiers)
    requiredColumns = ['SolutionID', 'Concept']
    this_df = f.checkWorksheet(wb, 'complete', 'sentence concepts', requiredColumns, True)
    for row in this_df.itertuples():
        concept, isNeg = f.checkConfigConcept(row.SolutionID)
        reText = re.compile(f.checkPattern(row.Concept), flags=re.IGNORECASE|re.DOTALL)
        text = row.Concept
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\b', '', text)
        text = re.sub(r'\(', '(', text)
        text = re.sub(r'\)', ')', text)
        d.sentenceConcepts.append((concept, reText, isNeg, text))
        d.knownConcepts.add(concept)
    requiredColumns = ['Start Negation', 'End Negation', 'Sentences']
    this_df = f.checkWorksheet(wb, 'complete', 'gross negations', requiredColumns, True)
    for row in this_df.itertuples():
        start = re.compile(f.checkPattern(row.Start_Negation), flags=re.IGNORECASE|re.DOTALL)
        end = re.compile(f.checkPattern(row.End_Negation), flags=re.IGNORECASE|re.DOTALL)
        sentences = int(row.Sentences)
        d.grossNegation.append((start, end, sentences))
    requiredColumns = ['SolutionID', 'Section', 'Negate', 'MetaThesaurusIDs']
    f.loadNegationListWorksheet(wb, 'complete', 'sentence negation lists', requiredColumns, d.sentenceNegationLists)
    f.loadNegationListWorksheet(wb, 'complete', 'document negation lists', requiredColumns, d.documentNegationLists)
    requiredColumns = ['SolutionID', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadConceptSetsWorksheeet(wb, 'complete', 'sent strict seq concept sets', requiredColumns, True, d.sentenceConceptSequenceSets)
    f.loadConceptSetsWorksheeet(wb, 'complete', 'sentence sequence concept sets', requiredColumns, False, d.sentenceConceptSequenceSets)
    requiredColumns = ['SolutionID', 'Sentences', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadMultiConceptSetsWorksheeet(wb, 'complete', 'multi sent strict seq conc sets', requiredColumns, True, d.sentenceConceptSequenceSets)
    f.loadMultiConceptSetsWorksheeet(wb, 'complete', 'multi sentence seq concept sets', requiredColumns, False, d.sentenceConceptSequenceSets)
    requiredColumns = ['SolutionID', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadConceptSetsWorksheeet(wb, 'complete', 'sentence concept sets', requiredColumns, True, d.sentenceConceptSets)
    requiredColumns = ['SolutionID', 'Sentences', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadMultiConceptSetsWorksheeet(wb, 'complete', 'multi sentence concept sets', requiredColumns, True, d.sentenceConceptSets)
    requiredColumns = ['SolutionID', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadConceptSetsWorksheeet(wb, 'complete', 'document sequence concept sets', requiredColumns, True, d.documentConceptSequenceSets)
    f.loadConceptSetsWorksheeet(wb, 'complete', 'document concept sets', requiredColumns, True, d.documentConceptSets)

