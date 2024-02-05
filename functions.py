'''
The common functions for the Clinical Costing system.
'''

# pylint: disable=invalid-name, line-too-long, broad-exception-caught, unused-variable, superfluous-parens

import os
import sys
import argparse
import logging
import re
import pandas as pd
import data as d


def setArguments(isFlask):
    '''
    Add the common command line arguments and parse the commond line
    '''

    d.progName = sys.argv[0]
    d.progName = d.progName[0:-3]        # Strip off the .py ending

    parser = argparse.ArgumentParser(description='AutoCode Clinical Documents')
    if not isFlask:
        parser.add_argument('-I', '--inputDir', dest='inputDir',
                            help='The folder containing the clinical document text files (default="testData")')
        parser.add_argument('-i', '--inputFile', dest='inputFile',
                            help='The name of the clinical document file (default exmaple1.txt)')
        parser.add_argument('-O', '--outputDir', dest='outputDir',
                            help='The folder where the AutoCoding output(s) will be created (default="testOutput")')
    parser.add_argument('-H', '--MetaMapLiteHost', dest='MetaMapLiteHost', default='localhost',
                        help='The name of the MetaMapLite Server (default="localhost")')
    parser.add_argument('-P', '--MetaMapLitePort', dest='MetaMapLitePort', default='8080',
                        help='The port for the AutoCoding service on the MetaMapLite Server (default="8080")')
    parser.add_argument('-U', '--MetaMapLiteURL', dest='MetaMapLiteURL', default='/AutoCoding/MetaMapLite',
                        help='The URL for the AutoCoding service on the MetaMapLite Server (default="localhost"")')
    if isFlask:
        parser.add_argument('-p', '--port', dest='FlaskPort', default='8000',
                            help='The port for the AutoCoding service on this server (default="8000")')
    parser.add_argument('-S', '--Solution', dest='solution', required=True,
                        help='The folder containing the solution configuration files')
    parser.add_argument ('-v', '--verbose', dest='verbose', type=int, choices=range(0,5),
                         help='The level of logging\n\t0=CRITICAL,1=ERROR,2=WARNING,3=INFO,4=DEBUG')
    parser.add_argument ('-L', '--logDir', dest='logDir', default='.', metavar='logDir',
                         help='The name of the directory where the logging file will be created')
    parser.add_argument ('-l', '--logFile', dest='logFile', metavar='logfile', help='The name of a logging file')
    return parser


def doArguments(parser, isFlask):
    '''
    Parse the commond line
    '''

    args = parser.parse_args()
    if not isFlask:
        d.inputDir = args.inputDir
        d.inputFile = args.inputFile
        d.outputDir = args.outputDir
    d.MetaMapLiteHost = args.MetaMapLiteHost
    d.MetaMapLitePort = args.MetaMapLitePort
    d.MetaMapLiteURL = args.MetaMapLiteURL
    if isFlask:
        d.FlaskPort = args.FlaskPort
    d.solution = args.solution
    logDir = args.logDir
    logFile = args.logFile
    loggingLevel = args.verbose

    # Set up logging
    logging_levels = {0:logging.CRITICAL, 1:logging.ERROR, 2:logging.WARNING, 3:logging.INFO, 4:logging.DEBUG}
    logfmt = d.progName + ' [%(asctime)s]: %(message)s'
    if loggingLevel is not None:    # Change the logging level from "WARN" if the -v vebose option is specified
        if logFile is not None:        # and send it to a file if the -o logfile option is specified
            with open(os.path.join(logDir, logFile), 'wt', encoding='utf-8', newline='') as logOutput:
                pass
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel], filename=os.path.join(logDir, logFile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', level=logging_levels[loggingLevel])
    else:
        if logFile is not None:        # send the default (WARN) logging to a file if the -o logfile option is specified
            with open(os.path.join(logDir, logFile), 'wt', encoding='utf-8', newline='') as logOutput:
                pass
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p', filename=os.path.join(logDir, logFile))
        else:
            logging.basicConfig(format=logfmt, datefmt='%d/%m/%y %H:%M:%S %p')
    logging.debug('Logging set up')
    return

def cleanColumnHeadings(theseColumns):
    '''
    Clean column headings and convert them to valid Python names so that
    Pandas dataframe will play nice when you do itertuples() [requires valid Python names for columns]
    '''
    cleanColumns = list(theseColumns)
    lastHeading = ''
    for i, col in enumerate(cleanColumns):
        if col is None:
            cleanColumns[i] = lastHeading + '_' + str(i)
        else:
            cleanColumns[i] = d.cleanPython.sub('_', col)
            lastHeading = cleanColumns[i]
    return cleanColumns


def checkWorksheet(wb, workbookName, sheet, columns, exact):
    '''
    Check that a worksheet exist in the workbook and that the sheet has the required column headings.
    '''
    # Check that this worksheet exits
    if sheet not in wb.sheetnames:
        logging.critical('No sheet named "%s" in workbook "%s"', sheet, workbookName)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Check this worksheet
    ws = wb[sheet]
    row0 = list(ws.rows)[0]
    headings = []
    for heading in row0:
        headings.append(heading.value)

    # Make sure the required columns in the this worksheet are present
    for col in columns:
        if col not in headings:
            logging.critical('Missing heading "%s" in worksheet "%s" in workbook "%s"', col, sheet, workbookName)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # Check any codes that need to be in a code table
    data = ws.values
    cols = tuple(cleanColumnHeadings(next(data)))
    sheet_df = pd.DataFrame(list(data), columns=cols)
    if exact:
        newCols = columns.copy()
        lastHeading = ''
        for i, col in enumerate(newCols):
            if col is None:
                newCols[i] = lastHeading + '_' + str(i)
            else:
                newCols[i] = d.cleanPython.sub('_', col)
                lastHeading = newCols[i]
        sheet_df = sheet_df[sheet_df.columns.intersection(newCols)]
    return sheet_df


def checkPattern(pattern):
    '''
    Check a regular expression pattern and bound it with \b if appropriate
    '''
    if pattern == '':
        return ''
    returnPattern = ''
    if pattern[0].isalnum():
        returnPattern = r'\b'
    returnPattern += pattern
    if pattern[-1].isalnum():
        returnPattern += r'\b'
    return returnPattern

def checkConfigConcept(thisConcept):
    '''
    Check if a configuration concept is negated or ambigous
    We check the first character (which is normally the letter 'C' as all MetaThesaurus concepts start with the letter 'C')
    If the first character is '-' then we strip it off and declare the remaining characters a negated concept
    If the first character is '?' then we strip it off and declare the remaining characters an ambiguous concept
    NOTE: we assume concepts all start with either 'C' or '-C' or '?C', but we do not check.
    '''

    newConcept = thisConcept
    isNeg = '0'
    if thisConcept[0] == '-':
        newConcept = thisConcept[1:]
        isNeg = '1'
    elif thisConcept[0] == '?':
        newConcept = thisConcept[1:]
        isNeg = '2'
    return newConcept, isNeg

def loadSimpleSheet(wb, workbook, sheet, columns, target):
    '''
    Load a simple worksheet into the target as a list of lists
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        target.append(record)


def loadSimpleDictionarySheet(wb, workbook, sheet, columns, target):
    '''
    Load a simple worksheet of keys and (list of) values into the target as a dictionary
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        target[record[0]] = record[1:]


def loadSkipDictionarySheet(wb, workbook, sheet, columns, target):
    '''
    Load a simple worksheet of keys and (list of) values into the target as a dictionary
    where the second column is a description of the first column and is skipped in the list of values
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        target[record[0]] = record[2:]


def loadSimpleCompileSheet(wb, workbook, sheet, columns, pretext, posttext, ignorecase, dotall, target):
    '''
    Load a simple worksheet into the target as a list of tuples
    where the first value in each tuple is a compiled regular expression
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        reText = checkPattern(record[0])
        if pretext is not None:
            reText = pretext + reText
        if posttext is not None:
            reText = reText + posttext
        if ignorecase is not None:
            if dotall is not None:
                compText = re.compile(reText, flags=re.IGNORECASE|re.DOTALL)
            else:
                compText = re.compile(reText, flags=re.IGNORECASE)
        elif dotall is not None:
            compText = re.compile(reText, flags=re.DOTALL)
        else:
            compText = re.compile(reText)
        if len(columns) == 1:
            target.append(compText)
        else:
            target.append(tuple([compText] + record[1:]))


def loadBoolComileWorksheet(wb, workbook, sheet, columns, pretext, posttext, dotall, target):
    '''
    Load a worksheet which has isCase and/or isStart into the target as a list of tuples
    where the first value in each tuple is a compiled regular expression
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    try:
        isCase = columns.index('isCase')
    except ValueError:
        logging.fatal('Missing "isCase" column in worksheet(%s) in workbook(%s) in solution folder "%s"', sheet, workbook, d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    try:
        isStart = columns.index('isStart')
    except ValueError:
        isStart = -1
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        reText = checkPattern(record[0])
        if pretext is not None:
            reText = pretext + reText
        if posttext is not None:
            reText = reText + posttext
        if not isinstance(record[isCase], bool):
            logging.critical('Invalid value for isCase (%s) in worksheet(%s) in workbook(%s) in solution folder "%s"', record[isCase], sheet, workbook, d.solution)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if record[isCase]:
            if dotall is not None:
                compText = re.compile(reText, flags=re.IGNORECASE|re.DOTALL)
            else:
                compText = re.compile(reText, flags=re.IGNORECASE)
        elif dotall is not None:
            compText = re.compile(reText, flags=re.DOTALL)
        else:
            compText = re.compile(reText)
        if len(columns) == 1:
            target.append(compText)
        elif isCase < (len(columns) - 1):
            target.append(tuple([compText] + record[1:isCase] + record[isCase + 1:]))
        else:
            target.append(tuple([compText] + record[1:isCase]))


def loadCompileConceptsWorksheet(wb, workbook, sheet, columns, pretext, posttext, target):
    '''
    Load a worksheet into the target as a list of lists
    where the first value in each list is a compiled regular expression
    and the remaining list items are conceptIDs (variable length lists)
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, False)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        reText = checkPattern(record[0])
        if pretext is not None:
            reText = pretext + reText
        if posttext is not None:
            reText = reText + posttext
        compText = re.compile(reText, flags=re.IGNORECASE|re.DOTALL)
        concepts = []
        j = 1
        while (j < len(record)) and (record[j] is not None):
            concepts.append(record[j])
            d.knownConcepts.add(record[j])
            j += 1
        if len(columns) == 1:
            target.append(compText)
        else:
            target.append([compText] + concepts)


def loadCompileCompileWorksheet(wb, workbook, sheet, columns, pretext, target):
    '''
    Load a worksheet into the target as a list of lists
    where the first value in each list is a compiled regular expression
    where the second value in each list is either a compiled regular expression or None
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        reText = checkPattern(record[0])
        if pretext is not None:
            reText = pretext + reText
        compText = re.compile(reText, flags=re.IGNORECASE|re.DOTALL)
        if record[1] is not None:
            rexText = checkPattern(record[1])
            if pretext is not None:
                rexText = pretext + rexText
            exCompText = re.compile(rexText, flags=re.IGNORECASE|re.DOTALL)
            target.append([compText, exCompText])
        else:
            target.append([compText, None])


def loadModifierWorksheet(wb, workbook, sheet, columns, pretext, posttext, target):
    '''
    Load a worksheet into the target as a list of lists
    where the first value in each list is a compiled regular expression
    where the second value in each list is either a compiled regular expression or None
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        # logging.debug("sheet(%s), columns(%s), row(%s)", sheet, columns, row)
        concept, oldNeg = checkConfigConcept(row.MetaThesaurusID)
        d.knownConcepts.add(concept)
        newConcept, newNeg = checkConfigConcept(row.SolutionID)
        d.knownConcepts.add(newConcept)
        Modifier = checkPattern(row.Modifier)
        if pretext is not None:
            Modifier = pretext + Modifier
        if posttext is not None:
            Modifier = Modifier + posttext
        compText = re.compile(Modifier, flags=re.IGNORECASE|re.DOTALL)
        target.append([concept, oldNeg, newConcept, newNeg, compText])


def loadNegationListWorksheet(wb, workbook, sheet, columns, target):
    '''
    Load a worksheet into the target as a dictionary.
    The key is the SolutionID which, if negated, triggers document modification.
    The value is child dictionary where the key is the section to which this negation is applicable.
    The value of the child dictionary is another dictiony.
    The key of this grandchild dictionary is a boolean which indicates whether the matching concepts
    in the following list should be negated or made ambiguous.
    The value of this grandchild dictionary is the list of matching concepts. 
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, False)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        solutionID = record[0]
        section = record[1]
        negate = record[2]
        concepts = []
        j = 3
        while (j < len(record)) and (record[j] is not None):
            concepts.append(record[j])
            d.knownConcepts.add(record[j])
            j += 1
        d.knownConcepts.add(solutionID)
        target[solutionID] = {}
        target[solutionID][section] = {}
        target[solutionID][section][negate] = concepts


def loadConceptSetsWorksheeet(wb, workbook, sheet, columns, isStrict, target):
    '''
    Load a worksheet into the target as a list of tuples
    where the first tuple element is a Solution ID.
    The second tuple element is a list of tuples, being pairs of MetaThesaurusIDs and a ternary value indicating
    whether the MetaThesaurusI is asserted, negated or ambiguous.
    This is the set of concepts being searched for in the clincial document.
    The third tuple element is a boolean indicating whether this is a strict sequence set.
    The fourth tuple element is the maximum number of sentence within which this sequence must occur.
    The fifth tuple element is a ternary value indicating whether the Solution ID is asserted, negated or ambiguous.
    The sixth tuple element indicates that the matched MetaThesaurusIDs should be deemed 'Used'
    so that they cannot participate in any further set matching operations.
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, False)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        solutionID, isNegated = checkConfigConcept(record[0])
        asserted = record[1]
        if not isinstance(asserted, bool):
            logging.critical('Invalid value for Asserted (%s) in worksheet(%s) in workbook(%s) in solution folder "%s"', asserted, sheet, workbook, d.solution)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.knownConcepts.add(solutionID)
        concepts = []
        j = 2
        while (j < len(record)) and (record[j] is not None):
            conceptID, thisNeg = checkConfigConcept(record[j])
            concepts.append((conceptID, thisNeg))
            d.knownConcepts.add(conceptID)
            j += 1
        target.append((solutionID, concepts, isStrict, 1, isNegated, asserted))


def loadMultiConceptSetsWorksheeet(wb, workbook, sheet, columns, isStrict, target):
    '''
    Load a worksheet into the target as a list of tuples
    where the first tuple element is a Solution ID.
    The second tuple element is a list of tuples, being pairs of MetaThesaurusIDs and a ternary value indicating
    whether the MetaThesaurusI is asserted, negated or ambiguous.
    This is the set of concepts being searched for in the clincial document.
    The third tuple element is a boolean indicating whether this is a strict sequence set.
    The fourth tuple element is the maximum number of sentence within which this sequence must occur.
    The fifth tuple element is a ternary value indicating whether the Solution ID is asserted, negated or ambiguous.
    The sixth tuple element indicates that the matched MetaThesaurusIDs should be deemed 'Used'
    so that they cannot participate in any further set matching operations.
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, False)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        solutionID, isNegated = checkConfigConcept(record[0])
        sentences = int(record[1])
        asserted = record[2]
        if not isinstance(asserted, bool):
            logging.critical('Invalid value for Asserted (%s) in worksheet(%s) in workbook(%s) in solution folder "%s"', asserted, sheet, workbook, d.solution)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.knownConcepts.add(solutionID)
        concepts = []
        j = 3
        while (j < len(record)) and (record[j] is not None):
            conceptID, thisNeg = checkConfigConcept(record[j])
            concepts.append((conceptID, thisNeg))
            d.knownConcepts.add(conceptID)
            j += 1
        target.append((solutionID, concepts, isStrict, sentences, isNegated, asserted))
