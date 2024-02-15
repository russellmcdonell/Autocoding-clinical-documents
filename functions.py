'''
The common functions for the Clinical Costing system.
'''

# pylint: disable=invalid-name, line-too-long, broad-exception-caught, unused-variable, superfluous-parens, too-many-lines

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
    Parameters
        isFlask - Boolean, True if the calling application is a Flask application
    Returns
        parser  - an argparse.ArgumentParser
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
    Parameters
        parser  - an argparse.ArgumentParser
        isFlask - Boolean, True if the calling application is a Flask application
    Returns
        Nothing
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

def cleanColumnHeadings(columns):
    '''
    Clean column headings and convert them to valid Python names so that
    Pandas dataframe will play nice when you do itertuples() [requires valid Python names for columns]
    Parameters
        columns         - list, the worksheet column headings
    Returns
        cleanColumns    - list, worksheet columns converted into valid python names
    '''
    cleanColumns = list(columns)
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
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        exact           - boolean, True of only the required columns are to be loaded
    Returns
        sheet_df        - pandas dataframe, the loaded data
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
    headings = cleanColumnHeadings(next(data))
    sheet_df = pd.DataFrame(list(data), columns=tuple(headings))
    if exact:
        newColumns = cleanColumnHeadings(columns)
        sheet_df = sheet_df[sheet_df.columns.intersection(newColumns)]
    return sheet_df


def checkPattern(pattern):
    '''
    Check a regular expression pattern and bound it with \b if appropriate
    Parameters
        pattern         - str, the pattern to be checked/fixed
    Returns
        returnPattern   - The modified (if necessary) pattern
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


def checkConfigConcept(concept):
    '''
    Check if a configuration concept is negated or ambigous
    We check the first character (which is normally the letter 'C' as all MetaThesaurus concepts start with the letter 'C')
    If the first character is '-' then we strip it off and declare the remaining characters a negated concept
    If the first character is '?' then we strip it off and declare the remaining characters an ambiguous concept
    NOTE: we assume concepts all start with either 'C' or '-C' or '?C', but we do not check.
    Parameters
        concept     - str, the concept to be checked
    Returns
        newConcept  - str, the concept stripped of any negation or ambiguity character
        isNeg       - str, one character indicating the negation or ambiguity of the concept
    '''

    newConcept = concept
    isNeg = '0'
    if concept[0] == '-':
        newConcept = concept[1:]
        isNeg = '1'
    elif concept[0] == '?':
        newConcept = concept[1:]
        isNeg = '2'
    return newConcept, isNeg


def loadSimpleSheet(wb, workbook, sheet, columns, target):
    '''
    Load a simple worksheet into the target as a list of lists
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        target          - data structure where the data is to be loaded
    Returns
        Nothing
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        target.append(record)
    return


def loadSimpleDictionarySheet(wb, workbook, sheet, columns, skip, target):
    '''
    Load a simple worksheet of keys and (list of) values into the target as a dictionary
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        skip            - int, the number of columns to skip after the first
        target          - data structure where the data is to be loaded
    Returns
        Nothing
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        target[record[0]] = record[1 + skip:]
    return


def loadSimpleCompileSheet(wb, workbook, sheet, columns, pretext, posttext, ignorecase, dotall, target):
    '''
    Load a simple worksheet into the target as a list of tuples
    where the first value in each tuple is a compiled regular expression
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to the data in the first column before it is compiled
        posttext        - str or None, any text to be appended to the data in the first column before it is compiled
        ignorecase      - boolean, True if the compiled expression should be flagged with re.IGNORECASE
        dotall          - boolean, True if the compiled expression should be flagged with re.DOTALL
        target          - data structure where the data is to be loaded
    Returns
        Nothing
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
    return


def loadBoolComileWorksheet(wb, workbook, sheet, columns, pretext, posttext, dotall, target):
    '''
    Load a worksheet which has isCase and/or isStart into the target as a list of tuples
    where the first value in each tuple is a compiled regular expression
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to the data in the first column before it is compiled
        posttext        - str or None, any text to be appended to the data in the first column before it is compiled
        dotall          - boolean, True if the compiled expression should be flagged with re.DOTALL
        target          - data structure where the data is to be loaded
    Returns
        Nothing
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
        if isStart != -1:       # If  isStart is a heading then we check that the data is also boolean
            if not isinstance(record[isStart], bool):
                logging.critical('Invalid value for isStart (%s) in worksheet(%s) in workbook(%s) in solution folder "%s"', record[isStart], sheet, workbook, d.solution)
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
    return


def loadCompileConceptsWorksheet(wb, workbook, sheet, columns, pretext, posttext, target):
    '''
    Load a worksheet into the target as a list of lists
    where the first value in each list is a compiled regular expression
    and the remaining list items are conceptIDs (variable length lists)
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to the data in the first column before it is compiled
        posttext        - str or None, any text to be appended to the data in the first column before it is compiled
        target          - data structure where the data is to be loaded
    Returns
        Nothing
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
    Load a worksheet into the target as a list of tuples
    where the first tuple value is a compiled regular expression
    and the second tuple value is either a compiled regular expression or None
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to the data before it is compiled
        target          - data structure where the data is to be loaded
    Returns
        Nothing
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
            target.append((compText, exCompText))
        else:
            target.append((compText, None))
    return


def loadModifierWorksheet(wb, workbook, sheet, columns, pretext, posttext, target):
    '''
    Load a worksheet into the target as a dictionary of tuples
    where the key is a SolutionID, the first tuple value is whether not the SolutionID is negated,
    the second tuple value is the new SolutionID, the third tuple value is whether or not the new SolutionID is negated
    and the fourth tuple value is the regular expression that triggers modifying the first SolutionID into the second SolutionID
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to Modifier before it is compiled
        posttext        - str or None, any text to be appended to the Modifier before it is compiled
        target          - data structure where the data is to be loaded
    Returns
        Nothing
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
        target[concept] = (oldNeg, newConcept, newNeg, compText)
    return


def loadNegationListWorksheet(wb, workbook, sheet, columns, target):
    '''
    Load a worksheet into the target as a dictionary.
    The key is the SolutionID which, if negated, triggers document modification.
    The value is child dictionary where the key is the section to which this negation is applicable.
    The value of the child dictionary is another dictiony.
    The key of this grandchild dictionary is a boolean which indicates whether the matching concepts
    in the following list should be negated or made ambiguous.
    The value of this grandchild dictionary is the list of matching concepts. 
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        target          - data structure where the data is to be loaded
    Returns
        Nothing
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
    return


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
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        isStrict        - boolean, True means concepts must be sequential (loaded as part of the data)
        target          - data structure where the data is to be loaded
    Returns
        Nothing
    '''

    # Check for multi-sentence worksheet - must be column[1]
    try:
        colAt = columns.index('Sentences')
        if colAt == 1:
            isMulti = True
        else:
            isMulti = False
    except ValueError:
        isMulti = False

    this_df = checkWorksheet(wb, workbook, sheet, columns, False)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(%s), columns(%s), record(%s)", sheet, columns, record)
        solutionID, isNegated = checkConfigConcept(record[0])
        if isMulti:
            sentences = int(record[1])
            asserted = record[2]
        else:
            asserted = record[1]
        if not isinstance(asserted, bool):
            logging.critical('Invalid value for Asserted (%s) in worksheet(%s) in workbook(%s) in solution folder "%s"', asserted, sheet, workbook, d.solution)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.knownConcepts.add(solutionID)
        concepts = []
        if isMulti:
            j = 3
        else:
            j = 2
        while (j < len(record)) and (record[j] is not None):
            conceptID, thisNeg = checkConfigConcept(record[j])
            concepts.append((conceptID, thisNeg))
            d.knownConcepts.add(conceptID)
            j += 1
        if isMulti:
            target.append((solutionID, concepts, isStrict, sentences, isNegated, asserted))
        else:
            target.append((solutionID, concepts, isStrict, 1, isNegated, asserted))
    return


def checkPreamble(inPreamble, text):
    '''
    Check for preamble markers in document as a whole.
    If we are already in preamble, then check for an end of preamble marker.
    If we are not in preamble, then check for a start of preamble marker.
    Parameters
        inPreamble - Boolean, True if the end of the last piece of text was preamble
        text - the text to be tested
    Returns 
        changeFound - Boolean, True if the text contains a preamble marker in the middle of the text
                      that indicates a change in preamble (inPreamble to not inPreamble or visa versa)
        changeAt    - int, the location in the text where the preamble state changed
    '''

    # logging.debug('checking for preamble in document(%s)', text)
    # Check if we are in preamble and ran into something useful, or in useful text, but ran in to preamble
    if inPreamble:        # We are in preamble
        # Check for the configured end of preamble markers (regular expression, ignore case)
        documentFound = False
        changeAt = None
        # Search for the end 'start of preamble marker'
        for marker, isStart in d.preambleMarkers:
            # logging.debug('Checking marker:%s', marker.pattern)
            if isStart:    # This is a start of preamble marker, but we are in preamble, so skip this marker
                continue
            match = marker.search(text)
            if match is not None:        # End of preamble found
                documentFound = True        # Some document text found
                # Remember where we ended preamble
                if (changeAt is None) or (match.start() < changeAt):
                    changeAt = match.start()
        if not documentFound:        # We are still in preamble, or at least we think we are - the specific solution may have a different answer
            changeAt = d.sp.checkNotPreamble(text)
            if changeAt >= 0:    # The specific solution found the end of preamble
                documentFound = True
        if documentFound:        # We did bounced out of preamble
            return (True, changeAt)        # Preamble change found, at
        else:        # We did not bounce out of preamble
            return (False, 0)        # The rest was preamble
    else:        # We are not in preamble
        # Check for the configured start of preamble markers (regular expression, ignore case)
        preambleFound = False
        changeAt = None
        # Search for the first occurance of a 'start of preamble marker' in this sentence
        for marker, isStart in d.preambleMarkers:
            # logging.debug('Checking marker:%s', marker[0].pattern)
            if not isStart:    # This is an end of preamble marker, but we are not in preamble, so skip this marker
                continue
            match = marker.search(text)
            if match is not None:    # Start of preamble marker found
                preambleFound = True        # Start of preamble marker found
                # Remember where we started preamble
                if (changeAt is None) or (match.start() > changeAt):
                    changeAt = match.start()
        if not preambleFound:        # We aren't in preamble, or at least we don't think we are - the specific solution may have a different answer
            changeAt = d.sp.checkPreamble(text)
            if changeAt >= 0:    # The specific solution found the end of preamble
                preambleFound = True
        if preambleFound:                # We bounced into preamble
            return (True, changeAt)        # Preamble change found, at
        else:        # We did not bounce out of preamble
            return (False, 0)        # No preamble in this document


def checkHistory(inHistory, text, depth):
    '''
    Check for history markers in this text.
    If we are already in history, then check for an end of history marker.
    If we are not in history, then check for a start of history marker.
    This function is called as d.sentences is being compiled/growing.
    So 'text' will be in the last line added to d.sentences
    Parameters
        inHistory   - Boolean, True if the end of the last piece of text was history
        text        - the text to be tested
        depth       - the level of recursion
    Returns 
        changeAt    - int, the location in the text at which the state of history changed
        matchLen    - int, the length of the matching text which triggered a  history change
    '''

    logging.debug('Checking for history in text(%s)', text)
    # Check if we are in history and ran into something useful, or in useful text, but ran in to history
    if inHistory:        # We are in history - check to see if we've come to the end of this history section
        # Check for the configured end of history markers (regular expression, ignore case)
        documentFound = False
        newStart = None
        matchLen = None
        # Search for the first occurence of an 'end of history marker' in this text
        for marker, isStart in d.historyMarkers:
            if isStart:    # This is a start of history marker, but we are in history, so skip this marker
                continue
            logging.debug('Checking inHistory marker:%s', marker[0].pattern)
            match = marker.search(text)
            if match is not None:        # End of history found
                documentFound = True        # Some document 'end of history' text found
                # Remember where we ended history
                if (newStart is None) or (match.start() < newStart):
                    newStart = match.start()
                    matchLen = len(match.group())
        if documentFound:        # We did bounced out of history
            return (newStart, matchLen)
        # We are still in history, or at least we think we are - the specific solution may have a different answer
        historyEnds, scChangeAt, scLen = d.sc.solutionCheckHistory(inHistory, text)
        # The solution can indicate that history ended at a previous sentence
        # All sentences between this new end of history and the current sentence are not history
        if historyEnds == 0:        # History ends with this sentence
            return (scChangeAt, scLen)
        elif historyEnds > 0:        # History ended with a previous sentence
            # History ended several sentences ago - update those sentences to not history
            # We need to reprocess these sentence as they were processed as though they were in history.
            # However this is recursive, so check that we haven't fallen into a recursive loop
            if depth > 2:
                logging.critical('Too many levels of recursion when checking history')
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            thisHistory = False
            for fixIt in range(0, historyEnds):
                d.sentences[-1 - fixIt][0] = False        # Has no history changes
                d.sentences[-1 - fixIt][1] = False        # Starts with not history
                d.sentences[-1 - fixIt][5] = []            # No history changes
                txt = str(d.sentences[-1 - fixIt][4])
                # We have to check if this sentence has a sentence history tag somewhere in the sentence
                firstChange = True
                lastChange = 0
                changesAt, matchLen = checkHistory(thisHistory, txt, depth + 1)
                while changesAt is not None:        # Bounced in or out of history mid sentence
                    if firstChange and (changesAt == 0):            # Changed at the start of the text which is the start of the sentence
                        d.sentences[-1 - fixIt][1] = not thisHistory
                    elif len(d.sentences[-1 - fixIt][5]) == 0:    # Check for previous changes
                        d.sentences[-1 - fixIt][5].append(changesAt)
                        d.sentences[-1 - fixIt][0] = True    # Does contain history changes
                    else:
                        changesAt += d.sentences[-1 - fixIt][5][-1] + lastChange
                        d.sentences[-1 - fixIt][5].append(changesAt)
                        d.sentences[-1 - fixIt][0] = True    # Does contain history changes
                    firstChange = False
                    lastChange = matchLen
                    thisHistory = not thisHistory
                    txt = txt[changesAt + matchLen:]
                    changesAt, matchLen = checkHistory(thisHistory, txt, depth + 1)
            return (0, scLen)
        else:
            return (None, None)
    else:        # We are not in history - check that we didn't fall into another history section
        # Check for the configured start of history markers (regular expression, ignore case)
        historyFound = False
        newStart = None
        matchLen = None
        # Search for the first occurance of a 'start of history marker' in this text
        for marker, isStart in d.historyMarkers:
            if not isStart:    # This is an end of history marker, but we are not in history, so skip this marker
                continue
            logging.debug('Checking not inHistory marker:%s', marker[0].pattern)
            match = marker.search(text)
            if match is not None:    # Start of history found
                historyFound = True        # Start of history marker found
                # Remember where we started history
                if (newStart is None) or (match.start() < newStart):
                    newStart = match.start()
                    matchLen = len(match.group())
        if historyFound:        # We did bounce into history
            return (newStart, matchLen)
        # We aren't in history, or at least we don't think we are - the specific solution may have a different answer
        historyAt, scChangeAt, scLen = d.sc.checkHistory(inHistory, text)
        # The solution can indicate that history started at a previous sentence
        # All sentences between this new start of history and the current sentence are history
        if historyAt == 0:            # History starts with this sentence
            return (scChangeAt, scLen)
        elif historyAt > 0:            # History starts at a previous sentence
            # History started several sentences ago - update those sentences to history
            # We need to reprocess these sentence as they were processed as though they were not in history.
            # However this is recursive, so check that we haven't fallen into a recursive loop
            if depth > 2:
                logging.critical('Too many levels of recursion when checking history')
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            thisHistory = True
            for fixIt in range(0, historyAt):
                d.sentences[-1 - fixIt][0] = False        # Has no history changes
                d.sentences[-1 - fixIt][1] = True        # Starts with history
                d.sentences[-1 - fixIt][5] = []            # No history changes
                txt = str(d.sentences[-1 - fixIt][4])
                # We have to check if this sentence has a sentence history tag somewhere in the sentence
                firstChange = True
                lastChange = 0
                changesAt, matchLen = checkHistory(thisHistory, txt, depth + 1)
                while changesAt is not None:        # Bounced in or out of history mid sentence
                    if firstChange and (changesAt == 0):            # Changed at the start of the text which is the start of the sentence
                        d.sentences[-1 - fixIt][1] = not thisHistory
                    elif len(d.sentences[-1 - fixIt][5]) == 0:    # Check for previous changes
                        d.sentences[-1 - fixIt][5].append(changesAt)
                        d.sentences[-1 - fixIt][0] = True    # Does contain history somewhere
                    else:
                        changesAt += d.sentences[-1 - fixIt][5][-1] + lastChange
                        d.sentences[-1 - fixIt][5].append(changesAt)
                        d.sentences[-1 - fixIt][0] = True    # Does contain history somewhere
                    firstChange = False
                    lastChange = matchLen
                    thisHistory = not thisHistory
                    txt = txt[changesAt + matchLen:]
                    changesAt, matchLen = checkHistory(thisHistory, txt, depth + 1)
            return (0, scLen)
        else:
            # We didn't run into history. Check if we have a pre-history sentence tag in the sentence
            startHistory = None
            matchLen = None
            for prehistory in d.preHistory:
                match = prehistory.search(text)
                if match is not None:
                    if (startHistory is None) or (match.start() < startHistory):
                        # Remember where we entered history
                        startHistory = match.start()
                        matchLen = len(match.group())
            if startHistory is not None:
                return (startHistory, matchLen)
        return (None, None)


def checkNegation(concept, text, start, sentenceNo, isNeg):
    '''
    Check if this concept needs to be negated
    concept (which was triggered by 'text'), is at (start) in the document,
    which is in sentence(sentenceNo). It may already be negated(isNeg)
    Parameters
        concept     - str, the SolutionID
        text        - str, the text that has been coded to this SolutionID
        start       - int, the start of this text in this document
        sentenceNo  - int, the sentence in d.sentences where this text/concept was found
        isNeg       - boolean, True if concept is a negated concept
    Returns
        changeIt    - str, single character indication whether the negation of concept needs to be changed
                        '0' == "don't change", '1' == 'negate', '2' == 'make ambiguous'
        reason      - str, the regular expression pattern that triggered the change
        prePost     - str, the name of the name of the data set of patterns containing reason
    '''

    logging.debug('looking for negation of %s[%s] in %s', text, isNeg, d.sentences[sentenceNo][4])
    changeIt = '0'
    changeAt = -1
    reason = ''
    prePost = ''

    # Find the start of this trigger in this sentence
    thisStart = start - d.sentences[sentenceNo][2]      # Start in document minus start of this sentence

    # Find the nearest, preceding and following but boundaries, if any
    butBefore = None
    butAfter = None
    for butBoundary in d.butBoundaries:
        logging.debug('looking for butBoundary (%s)', butBoundary.pattern)
        match = butBoundary.search(d.sentences[sentenceNo][4])
        if match is not None:
            if match.start() < thisStart:
                if (butBefore is None) or (butBefore < match.start()):
                    butBefore = match.start()
            elif match.start() > thisStart:
                if (butAfter is None) or (butAfter > match.start()):
                    butAfter = match.start()
                logging.debug('found butBoundary (%s) at %d', butBoundary, match.start())
    # Truncate the sentence text if there are any but boundaries
    if butBefore is None:
        if butAfter is None:
            thisText = d.sentences[sentenceNo][4]
        else:
            thisText = d.sentences[sentenceNo][4][:butAfter]
    else:
        thisStart -= butBefore
        if butAfter is None:
            thisText = d.sentences[sentenceNo][4][butBefore:]
        else:
            thisText = d.sentences[sentenceNo][4][butBefore:butAfter]

    # Find the start of the text for "post" things
    thisEnd = thisStart + len(text)

    # Find the nearest negation before this concept
    if isNeg != '1':        # Don't look for negation of already negated
        # Check for pre-negations
        for preNegate in d.preNegation:
            if (len(preNegate) > 1) and (concept not in preNegate[1:]):        # Check if this negation is limited to a list of concepts
                continue
            logging.debug('looking for preNegation of (%s) in (%s)', preNegate[0].pattern, thisText[:thisStart])
            for match in preNegate[0].finditer(thisText[:thisStart]):
                if match.start() > changeAt:
                    changeAt = match.start()
                    changeIt = '1'
                    reason = preNegate[0].pattern
                    prePost = 'preNegation'
                    logging.debug('found preNegation(%s) at %d', preNegate[0].pattern, changeAt)
        for immedPreNegate in d.immediatePreNegation:
            if (len(immedPreNegate) > 1) and (concept not in immedPreNegate[1:]):        # Check if this negation is limited to a list of concepts
                continue
            logging.debug('looking for immediatePreNegation of (%s) in (%s)', immedPreNegate[0].pattern, thisText[:thisStart])
            for match in immedPreNegate[0].finditer(thisText[:thisStart]):
                if match.start() > changeAt:
                    changeAt = match.start()
                    changeIt = '1'
                    reason = immedPreNegate[0].pattern
                    prePost = 'immediatePreNegation'
                    logging.debug('found immediatePreNegation (%s) at %d', immedPreNegate[0].pattern, changeAt)
    for immedPreAmbig in d.immediatePreAmbiguous:
        if (len(immedPreAmbig) > 1) and (concept not in immedPreAmbig[1:]):        # Check if this ambiguity is limited to a list of concepts
            continue
        logging.debug('looking for immediate preAmbiguous of (%s) in (%s)', immedPreAmbig[0].pattern, thisText[:thisStart + len(text)])
        for match in immedPreAmbig[0].finditer(thisText[:thisStart]):
            if match.start() > changeAt:
                changeAt = match.start()
                changeIt = '2'
                reason = immedPreAmbig.pattern
                prePost = 'immediatePreAmbiguous'
                logging.debug('found immediatePreAmbiguous(%s) at %d', immedPreAmbig[0].pattern, changeAt)
    for preAmbig in d.preAmbiguous:
        if (len(preAmbig) > 1) and (concept not in preAmbig[1:]):        # Check if this ambiguity is limited to a list of concepts
            continue
        logging.debug('looking for preAmbiguous of (%s) in (%s)', preAmbig[0].pattern, thisText[:thisStart + len(text)])
        for match in preAmbig[0].finditer(thisText[:thisStart]):
            if match.start() > changeAt:
                changeAt = match.start()
                changeIt = '2'
                reason = preAmbig.pattern
                prePost = 'preAmbiguous'
                logging.debug('found preAmbiguous(%s) at %d', preAmbig[0].pattern, changeAt)
    if changeIt == '0':
        # No preNegate or preAmbiguous, so try postNegate and postAmbiguous
        changeAt = len(d.sentences[sentenceNo][4]) + 1
        for postAmbig, exceptAmbig in d.postAmbiguous:
            logging.debug('looking for postAmbigous of (%s) in (%s)', postAmbig.pattern, thisText[thisStart:])
            for match in postAmbig.finditer(thisText[thisEnd:]):
                if exceptAmbig is not None:
                    exceptMatch = exceptAmbig.search(thisText[thisEnd:])
                    if exceptMatch is not None:
                        continue
                if match.start() < changeAt:
                    changeAt = match.start()
                    changeIt = '2'
                    reason = postAmbig.pattern
                    prePost = 'postAmbiguous'
                    logging.debug('found postAmbigous(%s) at %d', postAmbig[0].pattern, changeAt)
        for immedPostAmbig, exceptAmbig in d.immediatePostAmbiguous:
            logging.debug('looking for immediate postAmbigous of (%s) in (%s)', immedPostAmbig.pattern, thisText[thisStart:])
            for match in immedPostAmbig.finditer(thisText[thisEnd:]):
                if exceptAmbig is not None:
                    exceptMatch = immedPostAmbig[1].search(thisText[thisEnd:])
                    if exceptMatch is not None:
                        continue
                if match.start() < changeAt:
                    changeAt = match.start()
                    changeIt = '2'
                    reason = immedPostAmbig.pattern
                    prePost = 'immediatePostAmbiguous'
                    logging.debug('found immediatePostAmbigous(%s) at %d', immedPostAmbig[0].pattern, changeAt)
        if isNeg != '1':        # Don't look for negation of already negated
            for postNegate, exceptNegate in d.postNegation:
                logging.debug('looking for postNegation of (%s) in (%s)', postNegate.pattern, thisText[thisStart:])
                for match in postNegate.finditer(thisText[thisEnd:]):
                    if exceptNegate is not None:
                        exceptMatch = exceptNegate.search(thisText[thisEnd:])
                        if exceptMatch is not None:
                            continue
                    if match.start() < changeAt:
                        changeAt = match.start()
                        changeIt = '1'
                        reason = postNegate[0].pattern
                        prePost = 'postNegation'
                        logging.debug('found postNegation(%s) at %d', postNegate[0].pattern, changeAt)
            for immedPostNegate, exceptNegate in d.immediatePostNegation:
                logging.debug('looking for immediatePostNegation of (%s) in (%s)', immedPostNegate.pattern, thisText[thisStart:])
                for match in immedPostNegate.finditer(thisText[thisEnd:]):
                    if exceptNegate is not None:
                        exceptMatch = exceptNegate.search(thisText[thisEnd:])
                        if exceptMatch is not None:
                            continue
                    if match.start() < changeAt:
                        changeAt = match.start()
                        changeIt = '1'
                        reason = immedPostNegate[0].pattern
                        prePost = 'immediatePostNegation'
                        logging.debug('found immediatePostNegation (%s) at %d', immedPostNegate[0].pattern, changeAt)
    return (changeIt, reason, prePost)


def checkModified(concept, isNeg, sentenceNo, start, miniDoc):
    '''
    Check if this concept has a modified definition,
    either because of an immediately preceding preModifier or because of an immediately following postModifier
    and if it does, then modify it.
    Parameters
        concept     - str, SolutionID which may need modification
        isNeg       - str, one character indicating negation/ambiguity
        sentenceNo  - int, the sentence in d.sentences where this concept was found
        start       - int, the location of the text in this sentence which was coded to this concept
    Returns
        nothing
    '''

    document = d.sentences[sentenceNo][6]        # Sentences hold mini-documents
    # Check concept, oldNeg, newConcept, newNeg, pattern
    if concept not in d.preModifiers:
        thisNeg, newConcept, newNeg, modifier = d.preModifiers[concept]
        if isNeg != thisNeg:            # And matching negation (ignore ambiguity)
            if (isNeg not in [2, 3]) or (thisNeg not in [2, 3]):
                return
        # Phrases preceding this concept that change the semantic meaning of this concept
        # this.logger.debug('looking for preModifier of (%s) in (%s)', str(preModier[4].pattern), str(preText))
        preText = d.sentences[sentenceNo][4][:start]    # The text before this concept text in the sentence
        match = modifier.search(preText)
        if match is not None:
            logging.info('Changing concept from (%s[%s]) to (%s[%s])', concept, isNeg, newConcept, newNeg)
            if newConcept in d.sd.SolutionMetaThesaurus:
                document[start][miniDoc]['description'] = d.sd.SolutionMetaThesaurus[newConcept][0] + '(was:' + concept + ')'
            else:
                document[start][miniDoc]['description'] = 'unknown (was:' + concept + ' - ' + document[start][miniDoc]['description'] + ')'
            document[start][miniDoc]['concept'] = newConcept
            document[start][miniDoc]['negation'] = newNeg
    # Check concept, oldNeg, newConcept, newNeg, pattern
    if concept in d.postModifiers:
        thisNeg, newConcept, newNeg, modifier = d.postModifiers[concept]
        if isNeg != thisNeg:            # And matching negation (ignore ambiguity)
            if (isNeg not in ['2', '3']) or (thisNeg not in ['2', '3']):
                return
        # Phrases that follow this concept and change the semantic meaning of this concept
        # this.logger.debug('looking for postModifier of (%s) in (%s)', str(postModier[4].pattern), str(preText))
        conceptEnd = start + document[start][miniDoc]['length']            # The end of this concept text in the sentence
        postText = d.sentences[sentenceNo][4][conceptEnd:]    # The text after this concept text in the sentence
        match = modifier.search(postText)
        if match is not None:
            logging.info('Changing concept from (%s[%s]) to (%s[%s])', concept, isNeg, newConcept, newNeg)
            if newConcept in d.sd.SolutionMetaThesaurus:
                document[start][miniDoc]['description'] = d.sd.SolutionMetaThesaurus[newConcept][0] + '(was:' + concept + ')'
            else:
                document[start][miniDoc]['description'] = 'unknown (was:' + concept + ' - ' + document[start][miniDoc]['description'] + ')'
            document[start][miniDoc]['concept'] = newConcept
            document[start][miniDoc]['negation'] = newNeg
    return


def checkSets(history):
    '''
    Work through each of the 'sets' concepts and see if we can find matches for each 'set'
    We do sentence sets before document sets, and sequential sets before non-sequential sets.
    Parameters
        history - boolean, True if we are checking in historical text
    Returns
        Nothing
    '''

    # Check if any of the sentences contains any of the the Sentence Concept Sequence Sets
    # We test sentence sequence sets first because they are a stricter test
    # Sentence sequence sets are checked in the order in which they are appended to the sentenceConceptSequenceSets array
    # which is 'sent_strict_seq_concepts_set', 'sentence_sequence_concept_sets', 'multi_sent_strict_seq_conc_sets' then 'multi_sentence_seq_concept_sets'
    # [solutionID, [[concept, negation]], isStrict, sentenceRange, isNeg, asserted]

    # check each sentence concept sequence set
    for setNo, (higherConcept, thisSet, isStrict, sentenceRange, higherConceptNegated, asserted) in enumerate(d.sentenceConceptSequenceSets):
        logging.debug('Checking sentence Concept Sequence set (%s) [%s]', d.sentenceConceptSequenceSets[setNo], history)
        conceptNo = 0        # The index of the next concept in the set
        conceptList = []    # The concepts in this list that have been found
        for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
            logging.debug('checkSets - sentence Concept Sequence Sets - processing sentence[%d]', sentenceNo)
            sentenceStart = sentence[2]        # The character position start of this sentence
            document = sentence[6]        # Sentences hold mini-documents
            if conceptNo == 0:        # Compute a new 'valid range' if still looking for the first concept
                # Compute the last sentence for this range
                lastSentence = sentenceNo + sentenceRange - 1
                if lastSentence >= len(d.sentences):
                    lastSentence = len(d.sentences) - 1
                # Compute the character position of the end of the last sentence in this range
                sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]

            for thisStart in sorted(document, key=int):        # We step through all concepts in each sentence
                conceptFound = False                    # Concept in theSet at 'conceptNo' not yet found
                for jj in range(len(document[thisStart])):    # Step through the list of alternate concepts at this point in this sentence
                    # Only check history if we are looking for history, and non-history if we are looking for non-history
                    if document[thisStart][jj]['history'] != history:
                        break

                    if document[thisStart][jj]['used']:        # Skip used concepts
                        continue

                    # Ignore any concept who's text extends beyond this sentence range
                    if thisStart + document[thisStart][jj]['length'] > sentenceEnd:
                        continue

                    thisConcept = document[thisStart][jj]['concept']        # This concept
                    thisIsNeg = document[thisStart][jj]['negation']        # And it's negation

                    # Only check concepts that we know something about - the appeared in one of our configuration files
                    if thisConcept not in d.knownConcepts:
                        continue

                    # Check if this alternate concept at 'start' is the next one in this sentence concept sequence set
                    found = False
                    thisNeg =  thisSet[conceptNo][1]        # The desired negation
                    if thisConcept == thisSet[conceptNo][0]:    # A matching concept
                        if thisNeg == thisIsNeg:
                            found = True        # With a mathing negation
                        elif (thisIsNeg in ['2', '3']) and (thisNeg in ['2', '3']):
                            found = True        # Or a near enough negation (both ambiguous)
                    if not found:    # Check the special case of a repetition of the first concept in the set
                        # We don't handle repetitions within a set - just a repetition of the first concept
                        # i.e.looking for concept 'n' - found concept 0 [this set, array of concepts in dict, first entry, concept]
                        if thisConcept == thisSet[0][0]:
                            # Found the first concept - restart the multi-sentence counter
                            # Compute the last sentence for this range
                            lastSentence = sentenceNo + sentenceRange - 1
                            if lastSentence >= len(d.sentences):
                                lastSentence = len(d.sentences) - 1
                            # Compute the character position of the end of the last sentence in this range
                            sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
                            logging.debug('concept(%s[%s]) is not the next concept (%s[%s]) in set[%d]',
                                            thisConcept, thisIsNeg, thisSet[conceptNo][0], thisNeg, setNo)
                        continue
                    logging.debug('Concept (%s) [for sentence Concept Sequence set %d] found', thisConcept, setNo)
                    conceptList.append([sentenceNo, thisStart, jj])        # Add to the list of things we may need to mark as 'used'
                    conceptFound = True
                    conceptNo += 1
                    if conceptNo == len(thisSet):
                        # We have a full concept sequence set - so save the higher concept - append the higher concept to the list of alternates
                        logging.info('Sentence concept sequence set (%s:%s) found', higherConcept, thisSet)
                        addAdditionalConcept(higherConcept, sentenceNo, thisStart, jj, None, higherConceptNegated,
                                             f'sentenceConceptSequenceSet:{repr(thisSet)}', 0)

                        # Check if we should mark all/some of the concepts in the concept list as used
                        if (asserted) or (d.sc.higherConceptFound(higherConcept)):
                            for item in conceptList:
                                sno = item[0]
                                strt = item[1]
                                k = item[2]
                                foundConcept = d.sentences[sno][6][strt][k]['concept']
                                # Check if we should mark this concepts in the concept list as used
                                if asserted or (d.sc.setConcept(higherConcept, foundConcept)):
                                    d.sentences[sno][6][strt][k]['used'] = True
                                    logging.debug('Marking sentence concept sequence set item at %d/%d as used', strt, k)

                        conceptNo = 0        # Restart in case the same concept sequence set exists later in the sentences
                        conceptList = []
                        conceptFound = False
                        # Compute the last sentence for this range
                        lastSentence = sentenceNo + sentenceRange - 1
                        if lastSentence >= len(d.sentences):
                            lastSentence = len(d.sentences) - 1
                        # Compute the character position of the end of the last sentence in this range
                        sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
                    # end of list of things to check
                # end of all the alternate concepts at this point in the sentence
                # If this is a strict list - and we are part way through matching the concepts, then start again
                if isStrict and (conceptNo > 0) and not conceptFound:    # Tried all alternatives and the next concept in the strict list was not found
                    logging.info('Strict sequence started[%d] abandoned due to mismatch', setNo)
                    conceptNo = 0        # Restart in case the set exists later in the sentences
                    conceptList = []
                    conceptFound = False
                    # Compute the last sentence for this range
                    lastSentence = sentenceNo + sentenceRange - 1
                    if lastSentence >= len(d.sentences):
                        lastSentence = len(d.sentences) - 1
                    sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
            # end of all the concepts in this sentence
            # If we are part way through matching the concepts, but this is the last sentence in the current range then start again
            if (conceptNo > 0) and (sentenceNo == lastSentence):
                conceptNo = 0
        # end of the sentence
    # end of sentence concept sequence set


    # Next check if any of the sentences contains any of the the Sentence Concept Sets
    # We test these next because Sentence Concept Sets may create concepts that become part of a document sequence or document concept set
    # Sentence Concept Sets can be valid over a number of sentences, but we may have to expire things found if we go beyond that range
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
        logging.info('checkSets Sentence Concept Sets - processing sentence[%d]', sentenceNo)
        sentenceStart = sentence[2]
        sentenceLength = sentence[3]
        document = sentence[6]        # Sentences hold mini-documents

        # Clear the sentence concept sets at the start of every sentence
        sentenceConceptSetFound = {}        # The higher concepts found in this sentence - so we don't add them more than once
        for setNo, eachSet in enumerate(d.sentenceConceptSets):
            for thisConcept in eachSet[1]:
                # Clear any expired instance "where" this concept have been found
                if d.sentenceConceptFound[setNo][thisConcept]['found']:
                    expired = sentenceNo - eachSet[1][thisConcept]['range']
                    for i in range(len(d.sentenceConceptFound[setNo][thisConcept]['where']) -1, -1, -1):    # Iterate backwards so we can use del
                        if d.sentenceConceptFound[setNo][thisConcept]['where'][i][2] <= expired:
                            # this.logger.info('Expiring concept (%s) at sentence (%d)', str(concept), sentenceNo)
                            del d.sentenceConceptFound[setNo][thisConcept]['where'][i]        # We can delete this one [n-1 is next in interation]

                    # If everything has been deleted then this concept has not been found
                    if len(d.sentenceConceptFound[setNo][thisConcept]['where']) == 0:
                        logging.debug('Concept (%s) no longer found', thisConcept)
                        d.sentenceConceptFound[setNo][thisConcept]['found'] = False

        # Now look for concepts in this sentence that are in a sentence concept set
        # We step through all concepts in this sentence
        for thisStart in sorted(document, key=int):
            for jj in range(len(document[thisStart])):            # Step through the list of alternate concepts at this point in this sentence
                # Only check history if we are looking for history, and non-history if we are looking for non-history
                if document[thisStart][jj]['history'] != history:
                    break

                thisConcept = document[thisStart][jj]['concept']
                thisIsNeg = document[thisStart][jj]['negation']        # Check negation matches

                if document[thisStart][jj]['used']:        # Skip used concepts
                    continue

                if thisStart + document[thisStart][jj]['length'] > sentenceStart + sentenceLength:     # Skip concepts that extend beyond the end of this sentence
                    break

                # Only check concepts that we know something about - the appeared in one of our configuration files
                if thisConcept not in d.knownConcepts:
                    continue

                # Look for sentence concept sets - 'found' and 'where' are reset for every sentence
                if thisConcept in d.inSentenceConceptSets:                # this concept is in at least one sentence concept set
                    for setNo in d.inSentenceConceptSets[thisConcept]:            # check each sentence concept set that contains this concept
                        logging.debug('Checking if (%s:%s) is in sentence concept set %s', thisConcept, thisIsNeg, d.sentenceConceptSets[setNo])
                        higherConcept = d.sentenceConceptSets[setNo][0]
                        higherConceptNegated = d.sentenceConceptSets[setNo][2]
                        higherConceptAsserted = d.sentenceConceptSets[setNo][3]
                        if higherConcept in sentenceConceptSetFound:    # the higher concept  has already been been found
                            logging.debug('higherConcept(%s) for this set(%d) in sentence(%s) has already been found', higherConcept, setNo, sentenceNo)
                            continue
                        fullSet = True
                        for setConcept in d.sentenceConceptSets[setNo][1]:    # check each concept in the set
                            found = False
                            if setConcept == thisConcept:            # required item, so check if it has been found
                                thisNeg = d.sentenceConceptSets[setNo][1][thisConcept]['isNeg']
                                if thisIsNeg == thisNeg:
                                    found = True
                                elif (thisIsNeg in ['2', '3']) and (thisNeg in ['2', '3']):
                                    found = True
                            if found:
                                logging.debug('Concept (%s) [for sentence Concept set %d] found', thisConcept, setNo)
                                d.sentenceConceptFound[setNo][thisConcept]['found'] = True
                                d.sentenceConceptFound[setNo][thisConcept]['where'].append([sentenceNo, thisStart, jj])
                            elif not d.sentenceConceptFound[setNo][thisConcept]['found']:        # an item hasn't been found
                                fullSet = False                    # at least one item remains missing
                        if fullSet:            # the concept set is full - append the higher concept to the list of alternates
                            logging.info('Sentence concept set (%s:%s) found', higherConcept, d.sentenceConceptFound[setNo])
                            sentenceConceptSetFound[higherConcept] = True        # full concept set found so mark the higher concept as found and save it
                            addAdditionalConcept(higherConcept, sentenceNo, thisStart, jj, None, higherConceptNegated,
                                                 f'sentenceConceptSet:{repr(d.sentenceConceptSets[setNo][1])}', 0)

                            # Check if we should mark all/some of the concepts in the concept list as used
                            if higherConceptAsserted or (d.sc.higherConceptFound(higherConcept)):
                                for setConcept in d.sentenceConceptFound[setNo]:        # Mark the set concepts as 'used'
                                    for i in range(len(d.sentenceConceptFound[setNo][setConcept]['where'])):
                                        sno, strt, k = d.sentenceConceptFound[setNo][setConcept]['where'][i]
                                        # Check if we should mark this concepts in the concept list as used
                                        if higherConceptAsserted or (d.sc.setConcept(higherConcept, thisConcept)):
                                            d.sentences[sno][6][strt][k]['used'] = True
                                        # this.logger.debug('Marking sentence concept set item at %d/%d as used', strt, k)
                    # end of sentence concept sets
                # concept in sentence concept set processed
            # end of all the alternate concepts
        # end of all the concepts in this sentence
    # end of the sentence


    # Next check for any document Concept Sequence Sets - checking across all sentences
    # We test sequence sets first because they are a stricter test
    # and because Document Sequence Sets may create concepts that become part of a document concept set
    # [solutionID, [[concept, isNeg]], isNeg, asserted])

    # check each document concept sequence set
    for setNo, (higherConcept, thisSet, isStrict, sentenceRange, higherConceptNegated, higherConceptAsserted) in enumerate(d.documentConceptSequenceSets):
        logging.debug('Checking document concept sequence set (%s)', d.documentConceptSequenceSets[setNo])
        conceptNo = 0                # Check each concept in the set in sequence
        conceptList = []            # And remember which one's we've found so we can mark them as used if we get a full set
        for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
            document = sentence[6]    # Sentences hold mini-documents
            for thisStart in sorted(document, key=int):
                for jj in range(len(document[thisStart])):
                    # Only check history if we are looking for history, and non-history if we are looking for non-history
                    if document[thisStart][jj]['history'] != history:
                        break

                    thisConcept = document[thisStart][jj]['concept']
                    thisIsNeg =  document[thisStart][jj]['negation']        # Check negation matches

                    if document[thisStart][jj]['used']:        # Skip used concepts [only Findings get 'used']
                        continue

                    # Only check concepts that we know something about - the appeared in one of our configuration files
                    if thisConcept not in d.knownConcepts:
                        continue

                    # Check if this is the next one in the sequence
                    logging.debug('Checking if concept (%s) is the next concept in a document concept sequence set', thisConcept)
                    found = False
                    thisNeg = thisSet[conceptNo][1]
                    if thisConcept == thisSet[conceptNo][0]:
                        if thisIsNeg == thisNeg:
                            found = True
                        elif (thisIsNeg in ['2', '3']) and (thisNeg in ['2', '3']):
                            found = True
                    if not found:
                        logging.debug('concept(%s[%s]) is not the next concept (%s[%s]) in set[%d]', thisConcept, thisIsNeg, thisSet[conceptNo][0], thisNeg, setNo)
                        continue
                    logging.debug('Concept (%s) [for document Concept Sequence set %d] found', thisConcept, setNo)
                    conceptList.append([sentenceNo, thisStart, jj])            # Remember it in case we get a full set
                    conceptNo += 1
                    if conceptNo == len(thisSet):
                        # We have a full set - so save the higher concept
                        logging.info('Document concept Sequence set (%s:%s) found', higherConcept, thisSet)
                        addAdditionalConcept(higherConcept, sentenceNo, thisStart, jj, None, higherConceptNegated,
                                             f'documentConceptSequenceSet:{repr(thisSet)}', 0)

                        # Check if we should mark all/some of the concepts in the concept list as used
                        if higherConceptAsserted or (d.sc.higherConceptFound(higherConcept)):
                            for item, thisList in enumerate(conceptList):
                                sno = thisList[0]
                                strt = thisList[1]
                                k = thisList[2]
                                foundConcept = d.sentences[sno][6][strt][k]['concept']
                                # Check if we should mark this concepts in the concept list as used
                                if higherConceptAsserted or (d.sc.setConcept(higherConcept, foundConcept)):
                                    d.sentences[sno][6][strt][k]['used'] = True
                                logging.debug('Marking document concept Sequence set item at %d/%d as used', strt, k)
                        conceptNo = 0        # Reset in case there's more than one instance of this document condept Sequence set in the report
                        conceptList = []
                    # end of list of things to check
                # end of all the alternate concepts
            # end of all the concepts in this sentence
        # end of all this sentences
    # end of the document concept sequence set


    # Now check for any Document Concept Sets - checking across all sentences
    documentConceptSetFound = {}        # The higher concepts found in this document - so we don't add them more than once
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
        # this.logger.debug('checkSets Document concept sets - processing sentence[%d]', sentenceNo)
        sentenceStart = sentence[2]
        sentenceLength = sentence[3]
        document = sentence[6]    # Sentences hold mini-documents

        # Now look for concepts in this sentence that are in a sentence or document concept set
        # There is a philosophical bias here - implied diagnosis and implied sites trump what is actually stated.
        # We step through all concepts in this sentence
        for thisStart in sorted(document, key=int):
            for jj in range(len(document[thisStart])):            # Step through the list of alternate concepts at this point in this sentence
                # Only check history if we are looking for history, and non-history if we are looking for non-history
                if document[thisStart][jj]['history'] != history:
                    break

                thisConcept = document[thisStart][jj]['concept']
                thisIsNeg = document[thisStart][jj]['negation']        # Check negation matches

                if document[thisStart][jj]['used']:        # Skip used concepts [only Findings get 'used']
                    continue


                # Only check concepts that we know something about - the appeared in one of our configuration files
                if thisConcept not in d.knownConcepts:
                    continue

                # Check if any of the concepts in this sentence are in one of the document concept sets
                if thisConcept in d.inDocumentConceptSets:                    # this concept is in at least on concept set
                    for setNo in d.inDocumentConceptSets[thisConcept]:                # check each concept set that contains this concept
                        logging.debug('Checking if concept(%s[%d:%d/%d]) is in document concept set[%d](%s)', thisConcept, sentenceNo, thisStart, jj, setNo, d.documentConceptSets[setNo])
                        higherConcept = d.documentConceptSets[setNo][0]
                        thisSet = d.documentConceptSets[setNo][1]
                        higherConceptNegated = d.documentConceptSets[setNo][2]
                        higherConceptAsserted = d.documentConceptSets[setNo][3]
                        if higherConcept in documentConceptSetFound:    # the higher concept  has already been been found
                            continue
                        fullSet = True
                        for setConcept in thisSet:        # check each concept in the set
                            found = False
                            if setConcept == thisConcept:            # required item, so check if it has been found
                                thisNeg = thisSet[setConcept]['isNeg']
                                if thisIsNeg == thisNeg:
                                    found = True
                                elif (thisIsNeg in ['2', '3']) and (thisNeg in ['2', '3']):
                                    found = True
                            if found:
                                # this.logger.debug('Concept (%s) [for document Concept set %d] found', concept, setNo)
                                d.documentConceptFound[setNo][setConcept]['found'] = True
                                d.documentConceptFound[setNo][setConcept]['where'].append([sentenceNo, thisStart, jj])
                            elif not d.documentConceptFound[setNo][setConcept]['found']:        # an item hasn't been found
                                fullSet = False                    # at least one item remains missing
                        if fullSet:            # the concept set is full - append the higher concept to the list of alternates
                            logging.info('Document concept set (%s:%s) found', higherConcept, d.documentConceptFound[setNo])
                            documentConceptSetFound[higherConcept] = True        # full concept set found so mark the higher concept as found and save it
                            addAdditionalConcept(higherConcept, sentenceNo, thisStart, jj, None, higherConceptNegated,
                                                 f'documentConceptSet:{repr(thisSet)}', 0)

                            # Check if we should mark all/some of the concepts in the concept list as used
                            if higherConceptAsserted or (d.sc.higherConceptFound(higherConcept)):
                                for thisConcept in d.documentConceptFound[setNo]:        # Mark the set concepts as 'used'
                                    for i in range(len(d.documentConceptFound[setNo][thisConcept]['where'])):
                                        sno, strt, k = d.documentConceptFound[setNo][thisConcept]['where'][i]
                                        # Check if we should mark this concepts in the concept list as used
                                        if higherConceptAsserted or (d.sc.setConcept(higherConcept, thisConcept)):
                                            logging.debug('Marking document concept set item at %d/%d as used', strt, k)
                                            d.sentences[sno][6][strt][k]['used'] = True
                        # end of document concept sets
                    # concept processed
                # end of list of concepts to check
            # end of all the alternate concepts
        # end of all the concepts in this sentence
    # end of the sentence
    return


def getSection(currentSection, text):
    '''
    Return the section code for this sentence
    Parameters
        currentSection  - str, the section being processed
        text            - str, the text being searched for a section marker
    Returns
        section         - str, the new section name, or currentSection if no section marker found
    '''

    for marker in d.sectionMarkers:
        logging.debug('Checking section_marker:%s', marker[0].pattern)
        match = marker[0].search(text)
        if match is not None:        # Section found
            return marker[2]    # return section
    return currentSection        # return current section


def doNegationLists():
    '''
    Look for negated concepts that imply that a list of related concepts should also be negated or made ambiguous.
    When found, do negate/make ambiguous the related condepts.
    Parameters
        None
    Returns
        Nothing
    '''

    # Look for concepts within sentence that are negated,
    # and which imply other concepts in the same sentence should be set to negative or ambiguous
    logging.debug('doNegationLists - looking for sentence negatations')
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
        logging.debug('doNegationLists[sentences] - processing sentence[%d]', sentenceNo)
        document = sentence[6]    # Sentences hold mini-documents
        section = sentence[7]        # The section for this sentence    - can be 'None'
        for thisStart in sorted(document, key=int):        # We step through all the places where there are concepts in this sentence
            for jj in range(len(document[thisStart])):            # Step through the list of alternate concepts at this point in this sentence
                thisConcept = document[thisStart][jj]['concept']
                logging.debug('checking concept (%s): %s', thisConcept, document[thisStart][jj])
                # Check if this is a negated concept that is in sentenceNegationLists
                if (document[thisStart][jj]['negation'] == '1') and (thisConcept in d.sentenceNegationLists):        # Check negated concepts
                    # Check if this sentence is in an appropriate section
                    if 'All' in d.sentenceNegationLists[thisConcept]:
                        thisSection = 'All'
                    elif section in d.sentenceNegationLists[thisConcept]:
                        thisSection = section
                    else:
                        continue        # Doesn't apply to this section
                    # Do all the negations/ambiguities that are implied by this negative concept
                    for negation in d.sentenceNegationLists[thisConcept][thisSection]:        # Do both 'make negative' and ' make ambuguous'
                        # For every concept in this sentence that matches a concept in this sentence negation list
                        for strt in sorted(document, key=int):        # We step through all concepts in this sentence
                            for k in range(len(document[strt])):        # Step through the list of alternate concepts at this point in this sentence
                                thisConcept = document[strt][k]['concept']
                                if thisConcept in d.sentenceNegationLists[thisConcept][thisSection][negation]:
                                    if negation:
                                        document[strt][k]['negation'] = '1'
                                    else:
                                        document[strt][k]['negation'] = '2'

    # Look for concepts within the document that are negated, and which imply other concepts within the document should be negated or made ambiguous
    logging.debug('doNegationLists - looking for document negatations')
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
        logging.debug('doNegationLists[document] - processing sentence[%d]', sentenceNo)
        document = sentence[6]    # Sentences hold mini-documents
        section = sentence[7]        # The section for this sentence
        for thisStart in sorted(document, key=int):        # We step through all the places where there are concepts in this sentence
            for jj in range(len(document[thisStart])):            # Step through the list of alternate concepts at this point in this sentence
                thisConcept = document[thisStart][jj]['concept']
                logging.debug('checking concept (%s): %s', thisConcept, document[thisStart][jj])
                # Check if this is a negated concept that is in documentNegationLists
                if (document[thisStart][jj]['negation'] == '1') and (thisConcept in d.documentNegationLists):        # Check negated concepts
                    # Check if this sentence is in an appropriate section
                    if 'All' in d.documentNegationLists[thisConcept]:
                        thisSection = 'All'
                    elif section in d.documentNegationLists[thisConcept]:
                        thisSection = section
                    else:
                        continue        # Doesn't apply to this section
                    # Do all the negations/ambiguities that are implied by this negative concept
                    for negation in d.documentNegationLists[thisConcept][thisSection]:
                        # Negate/make ambiguous every thing that matches something in this list
                        for senNo, thisSntnc in enumerate(d.sentences):            # Step through each sentence
                            docu = thisSntnc[senNo][6]    # Sentences hold mini-documents
                            for strt in sorted(docu, key=int):        # We step through all concepts in this sentence
                                for k in range(len(docu[strt])):            # Step through the list of alternate concepts at this point in this sentence
                                    thisConcept = docu[strt][k]['concept']
                                    if thisConcept in d.documentNegationLists[thisConcept][thisSection][negation]:
                                        if negation:
                                            docu[strt][k]['negation'] = '1'
                                        else:
                                            docu[strt][k]['negation'] = '2'
    return


def addAdditionalConcept(concept, sentenceNo, start, j, description, negated, reason, depth):
    '''
    Add an additional concept to the mini-document for this sentence because a concept set has been found.
    The additional concept will be added at position 'start', by copying most of the details from the jth concept at start.
    Parameters
        concept     - str, the additional concept being added to the mini-document
        sentenceNo  - int, the sentence in d.sentences where the mini-document will be found
        start       - int, where, within the sentence the mini-document will be found and the additional concept added
        j           - int, the location of another concept in this mini-document from which attributes can be copied
        negated     - str, the negation/ambiguity status of the additional concept
        reason      - str, the reason the additional code is being added - for logging only
        depth       - the level of recursion
    Returns
        Nothing
    '''

    # This is recursive, so check that we haven't fallen into a recursive loop
    if depth > 5:
        logging.critical('Too many levels of recursion when adding additional concepts')
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Check that this concept doesn't already exist in the document at this point
    document = d.sentences[sentenceNo][6]    # Sentences hold mini-documents
    for k in range(len(document[start])):
        if concept == document[start][k]['concept']:
            break
    else:
        logging.info('Adding additional concept (%s:%s) to sentence[%d] at %d [%s]', concept, negated, sentenceNo, start, reason)
        thisConcept = {}
        thisConcept['concept'] = concept
        thisConcept['negation'] = negated
        thisConcept['text'] = document[start][j]['text']
        thisConcept['length'] = document[start][j]['length']
        thisConcept['history'] = document[start][j]['history']
        thisConcept['partOfSpeech'] = 'NN'
        thisConcept['used'] = False
        if description is not None:
            thisConcept['description'] = description
        elif concept in d.SolutionMetaThesaurus:
            thisConcept['description'] = d.SolutionMetaThesaurus[concept][0]
        else:
            thisConcept['description'] = 'unknown'
        document[start].append(thisConcept)

        # Now see if this has implications for the solution
        d.sc.solutionAddAdditionalConcept(concept, sentenceNo, start, j, negated, depth + 1)
    return
