'''
The common functions for the Clinical Costing system associated with processing Excel workbooks.
'''

# pylint: disable=invalid-name, line-too-long, broad-exception-caught, unused-variable, superfluous-parens, too-many-lines

import sys
import logging
import re
import pandas as pd
import data as d


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
    Check a regular expression pattern from an Excel worksheet and bound it with \b if appropriate
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


def loadSimpleSheet(wb, workbook, sheet, columns):
    '''
    Load worksheet as a list of lists
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
    Returns
        target          - list
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    target = []
    for i, record in enumerate(thisData):
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
        if record[0] is None:
            break
        if len(record) < len(columns):
            logging.critical('Insufficient column data in row %d in sheet(%s) in workbook(%s)', i + 1, sheet, workbook)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        target.append(record)
    return target


def loadSimpleDictionarySheet(wb, workbook, sheet, columns, skip):
    '''
    Load worksheet as a dictionary
        {key: column 1 value,
         value: If there are only two columns, then the value in the second column}
                If more than two columns, then list of values from remaining columns}
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        skip            - int, the number of columns to skip after the first
    Returns
        target          - dict
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    target = {}
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
        if (1 + skip) == (len(columns) - 1):
            target[record[0]] = record[1 + skip]
        else:
            target[record[0]] = record[1 + skip:]
    return target


def loadDictionaryDictionarySheet(wb, workbook, sheet, columns):
    '''
    Load worksheet as a dictionary
        {key:   column 1 value,
         value: If there are only two columns, then the value in the second column}
                If more than two columns, then dictionary
                {key:   the remaining cleaned column names,
                 value: the row data from the matching columns}}
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
    Returns
        target          - dict
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    target = {}
    newColumns = cleanColumnHeadings(columns)
    for row in this_df.itertuples(index=False):
        # logging.debug("workbook(%s) sheet(%s), columns(%s), row(%s)", workbook, sheet, columns, row)
        thisKey = row[0]
        target[thisKey] = {}
        if len(columns) == 2:
            target[thisKey] = row[1]
        else:
            for col in range(1, len(columns)):
                target[thisKey][newColumns[col]] = row[col]
    return target


def loadDictionarySetSheet(wb, workbook, sheet, columns):
    '''
    Load worksheet as a dictionary
        {key:   column 1 value,
         value: set of values from the remaining columns}
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
    Returns
        target          - dict
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, False)
    thisData = this_df.values.tolist()
    target = {}
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
        concepts = set()
        j = 1
        while (j < len(record)) and (record[j] is not None):
            concepts.add(record[j])
            d.knownConcepts.add(record[j])
            j += 1
        target[record[0]] = concepts
    return target


def loadSimpleCompileSheet(wb, workbook, sheet, columns, pretext, posttext, ignorecase, dotall):
    '''
    Load worksheet as a list of tuples
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
    Returns
        target          - list of tuples
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    target = []
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
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
    return target


def loadBoolCompileWorksheet(wb, workbook, sheet, columns, pretext, posttext, dotall):
    '''
    Load worksheet as a list of tuples where the first tuple item is a compiled regular expression.
    isCase must be a column heading and data in this column must be a boolean - False compiles the expression with re.IGNORECASE
    if isStart is a column heading then data in this column must be a boolean
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to the data in the first column before it is compiled
        posttext        - str or None, any text to be appended to the data in the first column before it is compiled
        dotall          - boolean, True if the compiled expression should be flagged with re.DOTALL
    Returns
        target          - list of tuples
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    target = []
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
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
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
                compText = re.compile(reText, flags=re.DOTALL)
            else:
                compText = re.compile(reText)
        elif dotall is not None:
            compText = re.compile(reText, flags=re.IGNORECASE|re.DOTALL)
        else:
            compText = re.compile(reText, flags=re.IGNORECASE)
        if len(columns) == 1:
            target.append(compText)
        elif isCase < (len(columns) - 1):
            target.append(tuple([compText] + record[1:isCase] + record[isCase + 1:]))
        else:
            target.append(tuple([compText] + record[1:isCase]))
    return target


def loadCompileConceptsWorksheet(wb, workbook, sheet, columns, pretext, posttext):
    '''
    Load a worksheet as a list of lists
    where the first value in each list is a compiled regular expression
    and the remaining list items are conceptIDs (variable length lists)
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to the data in the first column before it is compiled
        posttext        - str or None, any text to be appended to the data in the first column before it is compiled
    Returns
        target          - list of variable length lists
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, False)
    thisData = this_df.values.tolist()
    target = []
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
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
            target.append([compText])
        else:
            target.append([compText] + concepts)
    return target


def loadCompileCompileWorksheet(wb, workbook, sheet, columns, pretext):
    '''
    Load a worksheet into as a list of tuples
    where the first tuple value is a compiled regular expression
    and the second tuple value is either a compiled regular expression or None
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to the data before it is compiled
    Returns
        target          - list of tuples
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    thisData = this_df.values.tolist()
    target = []
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
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
    return target


def loadModifierWorksheet(wb, workbook, sheet, columns, pretext, posttext):
    '''
    Load a worksheet as a dictionary
        {key:   column 1 value (SolutionID) after negation removed,
         value: tuple}
    The first tuple value is whether not the column 1 value was negated,
    the second tuple value is the new SolutionID, the third tuple value is whether or not the new SolutionID is negated
    and the fourth tuple value is the regular expression that triggers modifying the first SolutionID into the second SolutionID
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        pretext         - str or None, any text to be prepended to Modifier before it is compiled
        posttext        - str or None, any text to be appended to the Modifier before it is compiled
    Returns
        target          - dict
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, True)
    target = {}
    for row in this_df.itertuples(index=False):
        if row.MetaThesaurusID is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), row(%s)", workbook, sheet, columns, row)
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
    return target


def loadNegationListWorksheet(wb, workbook, sheet, columns):
    '''
    Load a worksheet as a dictionary 
        {key: column 1 value (SolutionID),
         value: dictionary
            {key:   section name,
             value: dictionary
                key:    negation (bool),
                value:  set of concepts}}}
    The key is the SolutionID which, if negated, triggers document modification.
    The value is child dictionary where the key is the section to which this negation is applicable.
    The value of the child dictionary is another dictionary.
    The key of this grandchild dictionary is a boolean which indicates whether the matching concepts
    in the following list should be negated or made ambiguous.
    The value of this grandchild dictionary is the list of matching concepts. 
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
    Returns
        target          - dict
    '''
    this_df = checkWorksheet(wb, workbook, sheet, columns, False)
    thisData = this_df.values.tolist()
    target = {}
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
        solutionID = record[0]
        section = record[1]
        if not isinstance(record[2], bool):
            logging.critical('Invalid value for Negate (%s) in worksheet(%s) in workbook(%s) in solution folder "%s"', record[2], sheet, workbook, d.solution)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
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
    return target


def loadSequenceConceptSetsWorksheet(wb, workbook, sheet, columns, isStrict):
    '''
    Load a worksheet as a list of tuples
    where the first tuple element is a Solution ID.
    The second tuple element is a list of tuples, being pairs of MetaThesaurusIDs and a ternary value indicating
    whether the MetaThesaurusID is asserted, negated or ambiguous.
    This is the set of concepts being searched for in the clincial document.
    The third tuple element is a boolean indicating these concepts occur in a strict sequence (no intervening concepts).
    The fourth tuple element is the maximum number of sentence within which this sequence must occur.
    The fifth tuple element is a ternary value indicating whether the Solution ID is asserted, negated or ambiguous.
    The sixth tuple element indicates wherter or not all the matched MetaThesaurusIDs should be deemed 'Used'
    when the set if found and the Solution ID added to the document. That is, concepts found to match the set
    are deemed 'Used' and cannot participate in any further set or matching operations.
    e.g. (SolutionID, [(concept, isNeg)], isStrict, sentences, isNeg, asserted)
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        isStrict        - boolean, True means concepts must be sequential (loaded as part of the data)
    Returns
        target          - list of tuples
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
    target = []
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
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
    return target


def loadConceptSetsWorksheet(wb, workbook, sheet, columns):
    '''
    Load a worksheet as a list of tuples
    where the first tuple element is a Solution ID.
    The second tuple element is a list of tuples, being pairs of MetaThesaurusIDs and a ternary value indicating
    whether the MetaThesaurusID is asserted, negated or ambiguous.
    This is the set of concepts being searched for in the clincial document.
    The third tuple element is the maximum number of sentence within which this sequence must occur.
    The fourth tuple element is a ternary value indicating whether the Solution ID is asserted, negated or ambiguous.
    The fifth tuple element indicates wherter or not all the matched MetaThesaurusIDs should be deemed 'Used'
    when the set if found and the Solution ID added to the document. That is, concepts found to match the set
    are deemed 'Used' and cannot participate in any further set or matching operations.
    e.g. (SolutionID, [(concept, isNeg)], sentences, isNeg, asserted)
    Parameters
        wb              - an openpyxl workbook containing configuration data
        workbookName    - str, the name of the workbook/part of the solution
        sheet           - str, the name of the sheet to be loaded
        columns         - list(str), the list of columns required/to be loaded
        isStrict        - boolean, True means concepts must be sequential (loaded as part of the data)
    Returns
        target          - list of tuples
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
    target = []
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("workbook(%s), sheet(%s), columns(%s), record(%s)", workbook, sheet, columns, record)
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
            target.append((solutionID, concepts, sentences, isNegated, asserted))
        else:
            target.append((solutionID, concepts, 1, isNegated, asserted))
    return target
