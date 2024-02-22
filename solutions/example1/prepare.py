# pylint: disable=line-too-long, broad-exception-caught, unused-argument
'''
This is the example solution 1 - histopathology autocoding
'''

# pylint: disable=invalid-name, line-too-long

import sys
import logging
import re
import excelFunctions as excel
import data as d


def configure(wb):
    '''
    Read in any histopathology specific worksheets from workbook wb
    Parameters
        wb              - an openpyxl workbook containing prepare configuration data
    Returns
        configConcepts  - set(), all concepts detected when processing the workbook
    '''

    configConcepts = set()        # The set of additional known concepts

    # Read in the List Markers which are at the start of lines
    requiredColumns = ['List markers', 'isCase']
    this_df = excel.checkWorksheet(wb, 'prepare', 'List markers', requiredColumns, True)
    for row in this_df.itertuples():
        if row.List_markers is None:
            break
        # logging.debug("sheet(List markers)), columns(%s), row(%s)", requiredColumns, row)
        if not isinstance(row.isCase, bool):
            logging.critical('Invalid value for isCase (%s) in worksheet "List markers" in workbook "prepare.xlsx" in solution folder "%s"', row.isCase, d.solution)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if row.isCase:      # marker is case sensitive
            marker = re.compile(excel.checkPattern(r'^' + row.List_markers), flags=re.DOTALL)
        else:
            marker = re.compile(excel.checkPattern(r'^' + row.List_markers), flags=re.IGNORECASE|re.DOTALL)
        d.sd.listMarkers.append(marker)
    requiredColumns = ['Hyphenated words']
    this_df = excel.checkWorksheet(wb, 'prepare', 'Hyphenated words', requiredColumns, True)
    for row in this_df.itertuples():
        if row.Hyphenated_words is None:
            break
        # logging.debug("sheet(Hypenated words)), columns(%s), row(%s)", requiredColumns, row)
        d.sd.hyphenatedWords.add(str(row.Hyphenated_words).lower())

    # Return the additional known concepts
    return configConcepts


def checkHyphenated(cleanLine):
    '''
    Change hyphens/dashes to spaces, except for hyphenated words that must be preserved
    Paramenters
        cleanLine       - str, line to be cleansed
    Returns
        newCleanLine    - str, line after it has been cleansed
    '''

    newCleanLine = cleanLine
    for match in d.sd.tisHyphen.finditer(cleanLine):
        # logging.debug('dash(%s) found in :%s', match.group(0), cleanLine)
        hyphenatedWord = (match.group(1) + '-' + match.group(2)).encode('ascii', errors='ignore')
        if str(hyphenatedWord).lower() in d.sd.hyphenatedWords:
            # logging.debug('is hyphenated word (%s)', match.group(1) + '-' + match.group(2))
            continue
        newCleanLine = re.sub(match.group(0), match.group(1) + '    ' + match.group(2), newCleanLine, re.IGNORECASE)

    # Deal with dangling dashes
    newCleanLine = d.sd.preHyphen.sub(r'    \1', newCleanLine)
    newCleanLine = d.sd.postHyphen.sub(r'\1    ', newCleanLine)
    return newCleanLine


def solutionCleanDocument():
    '''
    Perform any histopathology specific document cleaning
    Parameters
        None
    Returns
        Nothing
    '''

    # Histopathology document contain 'lists'
    # A list start with a line the starts with a capital letter, contains only words and space, before a training ':'
    # List items are lines that start with optional white space, then a '-'
    newDocument = []
    # logging.debug('Text document before lists removed:')
    # logging.debug('%s', d.rawClinicalDocument)
    for line in d.rawClinicalDocument.split('\n'):
        # logging.debug('Next line is:(%s)', line)
        cleanLine = line.strip()

        if cleanLine == '' :
            # End of a list, which means what was before was the end of a sentence, unless it's an empty line or another list heading
            # logging.debug('empty line == end of list')
            if len(newDocument) > 0:
                # Change a colon at the end of the previous line, if present, to a full stop
                newDocument[-1] = d.sd.noColon.sub(r'.', newDocument[-1])
                # Append a full stop to the end of the previous sentence if necessary
                newDocument[-1] = d.sd.addPeriod.sub(r'\1.', newDocument[-1], count=1)
        else:
            for marker in d.sd.listMarkers:
                # logging.debug('Checking list marker:%s', marker[0].pattern)
                match = marker.search(cleanLine)
                if match is not None :        # list marker found
                    # logging.debug('List marker(%s) found', marker.pattern)
                    cleanLine = checkHyphenated(cleanLine)            # Change hyphens in heading to "    "
                    if d.sd.hasColon.search(match.group()) is not None:
                        parts = cleanLine.split(':')                # Replace additional ':' with '.'
                        cleanLine = parts[0] + ':'
                        for i in range(1, len(parts) - 1):
                            cleanLine += parts[i] + '. '
                        if len(parts) > 1:
                            cleanLine += parts[-1]
                    if len(newDocument) > 0:
                        # Change a colon at the end of the previous line, if present, to a full stop
                        newDocument[-1] = d.sd.noColon.sub(r'.', newDocument[-1])
                        # Append a full stop to the end of the previous sentence if necessary
                        # logging.debug('Adding period to(%s)', newDocument[-1])
                        newDocument[-1] = d.sd.addPeriod.sub(r'\1.', newDocument[-1], count=1)
                        # this.logger.debug('With period (%s)', newDocument[-1])
            newDocument.append(cleanLine)

            # Histopathology document have 'headings' which will be cleaned up as 'Labels' by the normal cleanup code.
            # But it would be nice if the preceding sentence ended with a full stop!
            if d.sd.allCAPS.match(cleanLine) is not None:
                if len(newDocument) > 0:
                    # Change a colon at the end of the previous line, if present, to a full stop
                    newDocument[-1] = d.sd.noColon.sub(r'.', newDocument[-1])
                    # Append a full stop to the end of the previous sentence if necessary
                    newDocument[-1] = d.sd.addPeriod.sub(r'\1.', newDocument[-1], count=1)

    d.preparedDocument = '\n'.join(newDocument) + '\n'
    # logging.debug('Text document after lists removed:')
    # logging.debug('%s', d.preparedDocument)
    return


def solutionCheckPreamble(text):
    '''
    Check for any solution specific markers that indicate the start of a preamble section (not the body of the text document)
    Here text is whole document.
    Histopathologies sometimes use hanging paragraphs.
    Sometimes the section heading 'CLINICAL INFORMATION', [a preamble marker] gets split over two lines.
    Parameters
        text    - str, the text to be checked for preamble markers
    Returns
        at      - int, location within text where preamble located, or -1 if no preamble located
    '''

    # logging.debug('Checking for preabmle in "%s"', text)

    # Start by spliting the document into lines
    lines = text.split('\n')

    # Now look for 'CLINICAL'
    for i, line in enumerate(lines):
        if d.sd.tisCLINICAL.search(line) is not None:
            # Check if 'INFORMATION' is in this line or one of the following three lines (if there are three more lines)
            for j in range(i, min(i + 4, len(lines))):        # Check this line and up to 3 more lines
                if d.sd.tisINFORMATION.search(lines[j]) is not None :
                    # Preamble marker found. Work out how far into the document this occured
                    beforePreamble = '\r'.join(lines[:i])
                    return len(beforePreamble)
    return -1


def solutionCheckNotPreamble(text):
    '''
    Check for any solution specific markers that indicate the end of a preamble section (not the body of the text document)
    Here text is whole document.
    Parameters
        text    - str, the text to be checked for end of preamble markers
    Returns
        at      - int, location within text where end of preamble located, or -1 if no end of preamble located
    '''

    # logging.debug('Checking for not preabmle in "%s"', text)

    return -1
