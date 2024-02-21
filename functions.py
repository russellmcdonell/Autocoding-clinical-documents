'''
The common functions for the Clinical Costing system.
'''

# pylint: disable=invalid-name, line-too-long, broad-exception-caught, unused-variable, superfluous-parens, too-many-lines

import os
import sys
import argparse
import logging
import json
from urllib.parse import urlencode
from http import client
import checkFunctions as ch
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
                            docu = thisSntnc[6]    # Sentences hold mini-documents
                            for strt in sorted(docu, key=int):        # We step through all concepts in this sentence
                                for k in range(len(docu[strt])):            # Step through the list of alternate concepts at this point in this sentence
                                    thisDocConcept = docu[strt][k]['concept']
                                    if thisDocConcept in d.documentNegationLists[thisConcept][thisSection][negation]:
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
        elif concept in d.solutionMetaThesaurus:
            thisConcept['description'] = d.solutionMetaThesaurus[concept]['description']
        else:
            thisConcept['description'] = 'unknown'
        document[start].append(thisConcept)

        # Now see if this has implications for the solution
        d.sc.solutionAddAdditionalConcept(concept, sentenceNo, start, j, negated, depth + 1)
    return


def cleanDocument():
    '''
    Clean d.rawClinicalDocument, saving the cleaned document in d.preparedDocument
    '''

    # Start by doing any solution specific document cleaning
    d.sp.solutionCleanDocument()

    # Clean the text document
    newDocument = []
    for line in d.preparedDocument.split('\n'):
        # logging.debug('Next line is (%s)', line)
        cleanLine = line.rstrip()

        # Now deal with any labels
        for label, newLabel in d.labels:
            # logging.debug('Checking for label (%s) and replacing with label(%s)', label.pattern, newLabel)
            if label.match(cleanLine) is not None:
                logging.debug('Label(%s) found', label.match(cleanLine).match())
                cleanLine = label.sub(newLabel, cleanLine)
                if len(newDocument) > 0:
                    # Change a colon at the end of the previous line, if present, to a full stop
                    newDocument[-1] = d.noColon.sub(r'.', newDocument[-1])
                    # Append a full stop to the end of the previous line if necessary
                    newDocument[-1] = d.addPeriod.sub(r'\1.', newDocument[-1], count=1)

        # Then change any commonly used terms into their technical equivalents
        # logging.debug('line before replacements:%s', cleanLine)
        for common, technical in d.terms:
            # logging.debug('Replacing (%s) with (%s)', common.pattern, technical)
            cleanLine = common.sub(technical, cleanLine)
        # logging.debug('line with replacements:%s', cleanLine)

        # And skip blank lines
        # logging.debug(cleanLine)
        if cleanLine == '':
            # logging.debug('empty line - continuing')
            # Append a full stop to the end of the previous line to make it a sentence
            if len(newDocument) > 0:
                newDocument[-1] = d.addPeriod.sub(r'\1.', newDocument[-1], count=1)
            continue

        newDocument.append(cleanLine)

    d.preparedDocument = '\n'.join(newDocument) + '\n'

    # Now change any commonly used preamble terms into their non-technical equivalents
    # We do that by treating the whole of the document as a single sentence and go looking for history.
    # Preamble is everything from the start of the document up to the end of the first slab of history

    # logging.debug('looking for preamble')
    # Looking for the start of history in the document
    thisText = d.preparedDocument

    # logging.debug('Text document before preamble Terms changed')
    # logging.debug(d.preparedDocument)
    (changeFound, changeAt) = ch.checkPreamble(False, thisText)
    if changeFound:            # We have history at the start or somewhere in, the document
        if changeAt != 0:
            document1 = thisText[:changeAt]        # Everything before the start of the first slab of history
            document2 = thisText[changeAt:]        # The first slab of history and everything after that
            someText = document2
            # logging.debug('some preamble found (%s)', document1)
            # Look for the end of history in the remainder of the document
            (changeFound, changeAt) = ch.checkPreamble(True, someText)
            if not changeFound:            # We have end of history at the start, or somewhere in the document
                if changeAt != 0:
                    document1 += someText[:changeAt]        # Preamble includes everything up to the end of the last slab of history
                    document2 = someText[changeAt:]        # Everything that must remain unchanged
            # logging.debug('preamble found (%s)', document1)
            # Now change any commonly used preamble terms into their non-technical equivalents
            for common, nonTechnical in d.preambleTerms:
                # logging.debug('Replacing preamble (%s) with (%s) if found in preamble', common.pattern, nonTechnical)
                document1 = common.sub(nonTechnical, document1)
            d.preparedDocument = document1 + document2
    # logging.debug('Text document after preamble Terms changed')
    # logging.debug(d.preparedDocument)
    return


def AutoCode():
    '''
    AutoCode d.rawClinicalDocument
    Call MetaMapLite to process this document
    Then complete the coding by calling the solution specific complete() function
    '''

    # Prepare the clinical document
    cleanDocument()
    logging.debug('raw document:\n%s\n', d.rawClinicalDocument)
    logging.debug('prepared document:\n%s\n', d.preparedDocument)

    # logging.info('Text document after labels, terms preamble, terms and lists changed')
    # logging.info(d.preparedDocument)

    # Get the sentences and concepts using MetaMapLite and compute the start and end of each sentence
    # (sentence are output in sentence order - we ignore some in order to skip 'history')

    # Acquire the MetaMapLite lock - MetaMapLite may not be thread safe
    d.MetaMapLiteServiceLock.acquire()

    # Set up the parameter (the document) and call the MetaMapLite service
    params = urlencode({'document':d.preparedDocument})
    try:
        thisMetaMapLiteConnection = client.HTTPConnection(d.MetaMapLiteHost, d.MetaMapLitePort)
        thisMetaMapLiteConnection.request('POST', d.MetaMapLiteURL, params, d.MetaMapLiteHeaders)
        response = thisMetaMapLiteConnection.getresponse()
        if response.status != 200:
            logging.critical('Invalid response from MetaMapLite Service:error %s', response.status)
            return (d.EX_SOFTWARE, f'Invalid response from MetaMapLite Service:({repr(response.status)})')
        responseData = response.read()
        thisMetaMapLiteConnection.close()
    except (client.NotConnected, client.InvalidURL, client.UnknownProtocol,client.UnknownTransferEncoding,client.UnimplementedFileMode,   client.IncompleteRead, client.ImproperConnectionState, client.CannotSendRequest, client.CannotSendHeader, client.ResponseNotReady, client.BadStatusLine) as thisE:
        logging.critical('MetaMapLite Service request error:(%s)', repr(thisE))
        d.MetaMapLiteServiceLock.release()
        return (d.EX_SOFTWARE, f'MetaMapLite Service request error:({repr(thisE)})')

    # Release the MetaMapLite lock
    d.MetaMapLiteServiceLock.release()

    logging.debug('MetaMapLite returned:%s', responseData)

    # Parse the response into into a dictionary of sentences and concepts
    try:
        d.MetaMapLiteResponse = json.loads(responseData)
    except ValueError as thisE:
        logging.critical('Invalid JSON response (%s) from MetaMapLite Service - error(%s)', repr(responseData), repr(thisE))
        return (d.EX_SOFTWARE, f'Invalid JSON response ({repr(response.status)}) from MetaMapLite Service:({repr(thisE)})')
    logging.debug('MetaMapLite response:%s', json.dumps(d.MetaMapLiteResponse, indent=2))
    # The MetaMapLite response is a dictionary with two keys - "concepts" and "sentences", each of which is an array of dictionaries
    # for "concepts" each dictionary has only one key - being a MetaMapLite Concept ID. The value is a dictionary with five keys
    #        "start" - where the text mapped to this concept starts in the text document
    #        "length" - the length of the text mapped to this concept
    #        "partOfSpeach" - coded representation of the part of speach (noun, verb, adverb etc)
    #        "text" - the actual text mapped to this concept
    #        "isNegated" - a boolean indicating whether or not this text/concept was preceded by a negation word (i.e. not)
    # for "sentences" each dictionary has two keys
    #        "start" - where the sentence started in the text document
    #        "text" - the text of the sentence
    # "sentences" are ordered.
    # That is, the order of the sentences in the array matches the order of the text in the original text document.
    # (each "start" value is larger than the preceeding "start" [by at least len("text")]

    # Now complete the coding of this document
    codingSuccess, reason = complete()
    if codingSuccess != d.EX_OK:
        logging.critical('AutoCoding failed: error(%s) with reason (%s)', codingSuccess, reason)
        return codingSuccess

    # Now analyze the results
    d.sa.analyze()
    return d.EX_OK


def complete():
    '''
    Complete the coding of this document
    '''

    # The text document has been reassembled into sentences (full stops in the text helps).
    # And the clinical terms have identified by MetaMapLite. All of this stored in the MetaMapLit respone (d.MetaMapLiteResponse).
    # Next we create the "sentences" structure (d.sentences) where we associate the MetaThesaurus Concept IDs
    # with their specific location with their specific 'sentence'.
    # However, we also need to know which concepts are historical concepts and which concepts are current concepts.
    # The main data structure here is 'sentences' - a list of the sentences in the clinical document.
    # Each sentence in the list has the following attributes
    #     [0] - a boolean that indicates that this sentence contains changes - parts of this sentence are not the same history as the start
    #     [1] - a boolean that indicates the initial history state of this sentence (True => isHistory)
    #     [2] - an integer - the character position of the start of this sentence within the document
    #     [3] - an integer - the length of this sentence
    #     [4] - a string - the text of this sentence
    #     [5] - a list of all the places in this sentence where history flips (into/out of history)
    #     [6] - a dictionary of the concepts within this sentence (a mini-document)
    #     [7] - the section containg this sentence
    #
    #     Each mini-document (d.sentences[sentenceNo][6]) is a dictionary with an integer as the key (the start of this concept in the main document).
    #     The value for each key ('start') is a list of alternate concepts, all of which start at the same character position in the main document.
    #     Each alternate concept in the list is a dictionary of concept attributes.
    #     The keys for each alternate concept dictionary in the list are
    #         'length' - an integer - the number of characters in the sentence required to identifying this concept
    #         'history' - a boolean that indicates that this concept is historical information - in a history sentence or after this sentence flipped into history
    #         'concept' - a string - the MetaThesaurus concept.
    #         'used' - a boolean that is set to True when a concept has been used to identify a higher concept
    #         'text' - a string - the text at start, for 'length', which MetaMapLite found to be 'concept'.
    #         'partOfSpeech' - a sting - the part of speech tag (code) that indicates how this concept was used in the sentence (noun, adverb, adjective etc)
    #         'negation' - a string that indicates that this is a positive ('0'), negative ('1') or ambiguous ('2') concept
    #         'description' - a string - the description of this concept (which may differ from the text matched to this concept).

    # Process the returned sentences
    d.sentences=[]    # The sentence/sentence part, to which we will attach mini documents of MetaThesaurus Concepts
    inHistory = False    # We assume the text document starts by referencing the present
    currentSection = 'None'
    DOSeol = False          # Check for DOS/Windows end of line characters
    lastSentence = d.MetaMapLiteResponse['sentences'][-1]
    if (lastSentence['start'] + len(lastSentence['text']) + 1) < len(d.preparedDocument):
        DOSeol = True
    for sentenceNo, sentence in enumerate(d.MetaMapLiteResponse['sentences']):        # process each sentence
        if DOSeol:
            thisStart = sentence['start'] + sentenceNo        # The start of the current sentence is DOS/Windows land
        else:
            thisStart = sentence['start']        # The start of the current sentence
        thisText = sentence['text']            # The text of the current sentence
        thisText = thisText.replace('\n', ' ')            # Replace any embedded newlines with spaces
        thisText = thisText.rstrip()
        section = getSection(currentSection, thisText)        # Get the section for this sentence
        currentSection = section
        d.sentences.append([False, inHistory, thisStart, len(thisText), thisText, [], {}, section])
        # We need to know if this sentence is in a history section, or just contains the word(s) implying 'history' somewhere in the sentence
        firstChange = True
        lastChange = 0
        depth = 0
        changesAt, matchLen = ch.checkHistory(inHistory, thisText, depth)
        while changesAt is not None:        # Bounced in or out of history mid sentence
            if firstChange and (changesAt == 0):            # Changed at the start of the text which is the start of the sentence
                d.sentences[-1][1] = not inHistory
            else:
                d.sentences[-1][0] = True    # Does contain history changes somewhere
                if len(d.sentences[-1][5]) == 0:
                    d.sentences[-1][5].append(changesAt)
                else:
                    changesAt += d.sentences[-1][5][-1] + lastChange
                    d.sentences[-1][5].append(changesAt)
            firstChange = False
            lastChange = matchLen
            inHistory = not inHistory
            thisText = thisText[changesAt + lastChange:]
            changesAt, matchLen = ch.checkHistory(inHistory, thisText, depth)

    # Now get the MetaThesaurus concepts (MetaMapLite returned them as a dictionary)
    # And add them to the appropriate sentences as mini documents.
    # Concepts are returned as a list of dictionaries. Each dictionary has a single key - the MetaThesaurus Concept ID
    # The 'value' associated with each Concept ID is a dictionary of the attributes of that Concept ID
    # this.logger.debug('Concepts')
    for thisConcept in d.MetaMapLiteResponse['concepts']:
        conceptID = list(thisConcept.keys())[0]
        logging.debug('Concept:%s', repr(thisConcept))
        thisStart = int(thisConcept[conceptID]['start'])
        length = int(thisConcept[conceptID]['length'])
        partOfSpeech = str(thisConcept[conceptID]['partOfSpeech'])
        thisText = str(thisConcept[conceptID]['text'])
        thisText = thisText.replace('\n', ' ')            # Replace any embedded newlines with spaces
        thisConcept[conceptID]['text'] = thisText
        isNegated = thisConcept[conceptID]['isNegated']
        if isNegated:
            isNegated = '1'
        else:
            isNegated = '0'

        # Find the relevant sentence for this concept
        # The sentences array is ordered so
        sentenceNo = None
        lastJJ = None
        for jj, sentence in enumerate(d.sentences):
            lastJJ = jj
            if sentence[2] + sentence[3] < thisStart:    # This sentence ends before this concept starts
                continue
            if sentence[2] > thisStart:                # This sentence starts after this concept starts - which is an error
                break
            # We have found the right sentence
            if sentence[2] + sentence[3] == thisStart:    # Can't start a concept with the last character of this sentence - must be next sentence
                sentenceNo = jj + 1
            else:
                sentenceNo = jj
            break

        # Check that we did find a sentence for this concept
        if sentenceNo is None:
            logging.critical('Concept not in any sentence')
            logging.critical('Concept at %d', thisStart)
            if len(d.sentences) == 0:
                logging.critical('THERE ARE NO SENTENCES!!!!')
            else:
                logging.critical('Last sentence starts at %d and ends at %d', d.sentences[-1][2], d.sentences[-1][2] + d.sentences[-1][3] - 1)
            return (d.EX_SOFTWARE, f'Concept ({repr(thisConcept)}) at {thisStart} is not in a sentence')

        # Check that this is a knownConcept
        if conceptID not in d.knownConcepts:
            if conceptID not in d.otherConcepts:
                logging.warning('New Concept(%s) in sentence(%d), text(%s)', conceptID, sentenceNo, thisText)
            continue
        logging.info('Concept[%d:%d]:%s', thisStart, sentenceNo, repr(thisConcept))

        # Check if this is a historical concept
        isHistory = d.sentences[sentenceNo][1]
        if d.sentences[sentenceNo][0]:            # This sentence contains history changes
            # Check the history list for this concept
            for changeAt in d.sentences[sentenceNo][5]:
                if changeAt > thisStart - d.sentences[sentenceNo][2]:    # Next change is after this concept
                    break
                isHistory = not isHistory

        # Replace this MetaThesaurusID with the SolutionID if there is a Solution equivalent for this MetaThesaurusID
        if conceptID in d.equivalents:        # For equivalents we need to know both the original concept and the new equivalent concept
            thisConcept = d.equivalents[conceptID]
        else:
            thisConcept = conceptID

        # Check if we need to negate - nouns and adjective only
        if partOfSpeech in ['NN', 'NNP', 'NNS', 'NNPS', 'JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS']:
            # Here we assume some that some phrases are demonstrative enough to apply to everything before or after them in the sentence
            changeIt, reason, prePost =  ch.checkNegation(thisConcept, thisText, thisStart, sentenceNo, isNegated)
            if changeIt != '0':
                if changeIt == '1':
                    logging.info('Concept %s (%d/%d) got negated - %s:%s', thisConcept, thisStart, lastJJ, prePost, reason)
                else:
                    logging.info('Concept %s (%d/%d) became ambigous - %s:%s', thisConcept, thisStart, lastJJ, prePost, reason)
                isNegated = changeIt

        # Check if the Solution requires this concept
        if not d.sc.requireConcept(thisConcept, isNegated, partOfSpeech, isHistory, sentenceNo, thisStart, length, thisText):
            continue

        # Add this concept to the mini-document in this sentence. The min-document can have multiple concepts starting at the same spot.
        document = d.sentences[sentenceNo][6]    # Sentences hold mini-documents
        if thisStart not in document:
            document[thisStart] = []
        miniDoc = len(document[thisStart])
        # Check if this concept already exists in this document at this point
        found = False
        for k in range(miniDoc):
            if document[thisStart][k]['concept'] == thisConcept:
                found = True
                break
        if found:
            continue
        document[thisStart].append({})
        document[thisStart][miniDoc]['concept'] = thisConcept            # This concept ID (MetaThesaurus or SolutionID)
        document[thisStart][miniDoc]['negation'] = isNegated                # This concept is negated
        document[thisStart][miniDoc]['text'] = thisText                        # The text that matches this concept
        document[thisStart][miniDoc]['length'] = length                    # The length of the text that matches this concept
        document[thisStart][miniDoc]['history'] = isHistory                # Whether or not this concept exists in historical text
        document[thisStart][miniDoc]['partOfSpeech'] = partOfSpeech        # The part of speech assigned by MetaMapLite
        document[thisStart][miniDoc]['used'] = False                    # This concept has not yet been used

        # Add a description if we have one
        if thisConcept in d.solutionMetaThesaurus:
            document[thisStart][miniDoc]['description'] = d.solutionMetaThesaurus[thisConcept]['description']
        else:
            logging.debug(thisConcept)
            document[thisStart][miniDoc]['description'] = 'unknown'
        if thisConcept != conceptID:
            if conceptID in d.solutionMetaThesaurus:
                document[thisStart][miniDoc]['description'] += '(was:' + d.solutionMetaThesaurus[conceptID]['description'] + ')'
            else:
                document[thisStart][miniDoc]['description'] += '(was:unknown)'

        # Check if we need to modify this concept
        ch.checkModified(thisConcept, document[thisStart][miniDoc]['negation'], sentenceNo, thisStart, miniDoc)
        logging.debug('added %s to sentence[%d]', repr(document[thisStart][miniDoc]), sentenceNo)

    # We have all the basic clinical concepts attached to sentences.
    # Now we need to add the higher concepts - or compound concepts - or solution specific concepts
    # Add to the mini-documents in each sentence any sentence implied concepts - word/pattern matching
    # Known compound phrases, or known acronyms that have a specific clinical concept.
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through all the sentence in order
        # Look for sentenceConcepts in this sentence.
        # Scan the original text looking for any words and/or phrases that are commonly used within documents, which have implied MetaThesaurus Concept.
        for (thisConcept, pattern, thisIsNeg, commonText) in d.sentenceConcepts:        # Check each sentence against all of the sentence concepts
            # this.logger.debug('looking for %s in sentence[%d] (%s)', str(common), sentenceNo, str(this.sentences[sentenceNo][4]))
            for match in pattern.finditer(sentence[4]):    # Process each match and add to the higherConcept to the document
                thisStart = sentence[2] + match.start()
                logging.debug('pattern(%s) found at %d', pattern.pattern, thisStart)
                # Check if this is a historical concept
                isHistory = sentence[1]
                if sentence[0]:            # This sentence contains history
                    # Check the history list for this concept
                    for changeAt in sentence[5]:
                        if changeAt > thisStart - sentence[2]:    # Next change is after this concept
                            break
                        isHistory = not isHistory

                # Check if the sentence concept (text) has been negated
                # We pass 'isNegated' as 0 so that checkNegation() will check for both negation and ambiguity
                thisText = match.group()
                changeIt, reason, prePost =  ch.checkNegation(thisConcept, thisText, thisStart, sentenceNo, 0)

                # Need to XOR(isNeg, changeIt) as negating a negative is a positive
                # If the 'concept' has a negated semantic meaning, but those word(s) have been negated
                # then we have a sentence with a double negative - which must result in a positive concept
                if thisIsNeg in ['0', '1']:        # An intended concept is unambiguous
                    if changeIt in ['0', '1']:        # The matching text is unambigous
                        if changeIt != thisIsNeg:    # Check if the negation has changed
                            thisIsNeg = '1'        # negative concept that is unchanged, or a postive concept that got negated
                        elif thisIsNeg == '1':
                            thisIsNeg = '0'        # a postivie concept that is unchanged, or a negative concept that got negated
                    else:                    # a positive or negative concept that became ambiguous
                        thisIsNeg = changeIt
                elif changeIt == '1':            # an ambiguous concept that was negated - becomes a negated concept
                    thisIsNeg = '1'                    # 'possible flu' versus 'not possible flu' -> not flu

                # Add to min-document
                document = sentence[6]    # Sentences hold mini-documents
                if thisStart not in document:
                    document[thisStart] = []
                miniDoc = len(document[thisStart])
                document[thisStart].append({})
                document[thisStart][miniDoc]['length'] = match.end() - match.start()
                document[thisStart][miniDoc]['history'] = isHistory
                document[thisStart][miniDoc]['concept'] = thisConcept
                document[thisStart][miniDoc]['used'] = False
                document[thisStart][miniDoc]['text'] = thisText
                document[thisStart][miniDoc]['partOfSpeech'] = 'NN'
                document[thisStart][miniDoc]['negation'] = thisIsNeg

                # With a description if we have one
                if thisConcept in d.solutionMetaThesaurus:
                    document[thisStart][miniDoc]['description'] = d.solutionMetaThesaurus[thisConcept]['description']
                else:
                    document[thisStart][miniDoc]['description'] = commonText

                # Check if we need to modify this concept
                ch.checkModified(thisConcept, thisIsNeg, sentenceNo, thisStart, miniDoc)
                logging.info('SentenceConcept(%s) found - adding %s to sentence[%d]', thisConcept, document[thisStart][miniDoc], sentenceNo)

    # Now add any solution specific raw concepts to the document
    # Note: We have not yet done negation, so these concepts may get negated, but are candidates for concept sets
    # Note: Must be knownConcepts as we cannot change the configuration at this point
    d.sc.addRawConcepts()

    # At this point all the word based concepts have been added to the mini-documents. Two things remain to complete the process.
    # 1. Do some extension of negation.
    # 2. Look for sets of concepts and, when found, add in the higher concept at the point where the last thing in the set was found.
    # We to do the negation extension first. Sets can contain positive and negative concepts.
    # So we extend negation and then look for concept sets.

    # Work through each of the sentences - extending negation
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
        logging.debug('Extending negation - processing sentence[%d]', sentenceNo)
        sentenceStart = sentence[2]
        sentenceLength = sentence[3]
        document = sentence[6]    # Sentences hold mini-documents

        # Do some gross negation - look for negations patterns within the text in the sentence
        # Gross negatation patters are a start regular expression and and end regular expression
        for grossStart, grossEnd, grossRange in d.grossNegation:
            if sentenceNo + grossRange > len(d.sentences):
                grossRange = len(d.sentences) - sentenceNo
            theText = ''
            for grossSentence in range(sentenceNo, sentenceNo + grossRange):
                if theText != '':
                    theText += ' '
                theText += d.sentences[grossSentence][4]
            logging.debug('Looking for gross negation pattern (%s.*%s) in (%s)', grossStart.pattern, grossEnd.pattern, theText)
            matchStart = grossStart.search(theText)
            if matchStart is not None:                # Start of gross negation found
                startNegation = matchStart.end()        # Check after the end of the start of gross negation
                matchEnd = grossEnd.search(theText[startNegation:])
                if matchEnd is not None:                # End of gross negation found
                    logging.info('Gross negation found - (%s..%s)', grossStart.pattern, grossEnd.pattern)
                    startNegation += sentenceStart                        # Start after the start of gross negation marker
                    endNegation = sentenceStart + matchEnd.start()        # And end at the end of gross negation marker
                    logging.debug('negating from %d to %d', sentenceStart + startNegation, sentenceStart + endNegation)
                    for grossSentence in range(sentenceNo, sentenceNo + grossRange):
                        thisDocument = d.sentences[grossSentence][6]    # Sentences hold mini-documents
                        for thisStart in sorted(thisDocument, key=int):        # Negate each concept between start and end of gross negation markers
                            if thisStart < startNegation:
                                continue
                            if thisStart > endNegation:
                                break
                            for jj, miniDoc in enumerate(thisDocument[thisStart]):
                                thisConcept = miniDoc['concept']
                                thisDocument[thisStart][jj]['negation'] = 1        # Negate this concept
                                logging.info('Negating concept(%s.*%s) [gross negation(%s)] in sentence[%d]',
                                                 thisConcept, grossStart.pattern, grossEnd.pattern, sentenceNo)

        # Extend negation and ambiguity for mini-document concepts in this sentence up to 'but' or from 'but'
        butAt = []
        buts = []
        thisBut = None
        # Find all the but boundaries in this sentence
        for butBoundary in d.butBoundaries:
            logging.debug('looking for butBoundary (%s)', butBoundary.pattern)
            match = butBoundary.search(d.sentences[sentenceNo][4])
            if match is not None:
                butAt.append(match.start() + d.sentences[sentenceNo][2])
                logging.debug('butBoundary found at %d', butAt[-1])
        if len(butAt) > 0:        # At least one found
            buts = sorted(butAt)
            thisBut = 0

        # Let the solution initialze it's own negate code
        d.sc.initalizeNegation()

        lastNegation = None        # Last concept was not negated - because there wasn't one
        for thisStart in sorted(document, key=int):        # We step through all concepts, in sequence across this sentence
            # Stop extending negation if we are crossing a but boundary
            while (thisBut is not None) and (buts[thisBut] <= thisStart):
                logging.debug('Crossing a butBoundary at %d in sentence %d', thisStart, sentenceNo)
                lastNegation = None        # Last concept was not negated - because there wasn't one - we just crossed a but boundary
                thisBut += 1
                # Check if we've crossed the last but boundary
                if thisBut == len(buts):
                    thisBut = None

            thisNegation = None            # Remember the negation of any noun or adjective at this point in the sentence
            for jj, minDoc in enumerate(document[thisStart]):            # Step through the list of alternate concepts at this point in this sentence
                if thisStart + minDoc['length'] > sentenceStart + sentenceLength:     # Skip concepts that extend beyond the end of this sentence
                    break

                # If this is a noun or adjective, then it is a concept of interest
                if minDoc['partOfSpeech'] in ['NN', 'NNP', 'NNS', 'NNPS', 'JJ', 'JJR', 'JJT']:
                    # Check if this is a concept is a knownConcept
                    # We do not extend negation to concepts we do not understand
                    thisConcept = minDoc['concept']
                    if thisConcept not in d.knownConcepts:
                        continue

                    # If this noun or adjective has been negated or is ambiguous
                    # then this will trigger negation/ambiguity extension for following concepts
                    if minDoc['negation'] in [1, 2, 3]:
                        thisNegation = minDoc['negation']

                    # If the last noun or adjective was negated or was ambigous, then extend negation/ambiguity
                    if lastNegation is not None:
                        logging.info('Extending negation or ambiguity to %s - %s [%d/%d]', thisConcept, document[thisStart][jj]['description'], thisStart, jj)
                        minDoc['negation'] = lastNegation
                        thisNegation = lastNegation        # Continue extending negation

            # Check if the solution wants to negate anything at this point in the document, before we update lastNegation
            d.sc.extendNegation(sentenceNo, thisStart, lastNegation, thisNegation)

            # If we had a negated noun or adjective, then we better extend negation from this point forward
            if thisNegation is not None:
                lastNegation = thisNegation


    # Output the mini-documents to the log if required
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
        document = sentence[6]    # Sentences hold mini-documents
        for thisStart in sorted(document, key=int):
            for jj, miniDoc in enumerate(document[thisStart]):
                logging.debug('[%d:%d:%d]%s', sentenceNo, thisStart, jj, miniDoc)


    # Now add any solution specific concepts to the document
    # Note: We have done negation extension, but not sentence or document list negation.
    # So these concepts may get negated, if they are in sentence_negation_lists or document_negation_lists, but are candidates for concept sets
    # Note: Must be knownConcepts as we cannot change the configuration at this point
    d.sc.addSolutionConcepts()

    # Now check the mini-documents for Document and Sentence Concept sets

    # Do any negation lists
    doNegationLists()

    # Check for document and sentence sets in the history
    ch.checkSets(True)

    # Check for document and sentence sets in the non-history
    ch.checkSets(False)

    # Do any negation lists again - in case a sentence set created a negated higher concept which is in a Negation List
    doNegationLists()

    # Now add any final solution specific concepts to the document
    # Note: We have done all negation and concept set checking, so these concepts are not candidates for concept sets
    # Note: Must be knownConcepts as we cannot change the configuration at this point
    d.sc.addFinalConcepts()

    # Do any solution completion tasks
    d.sc.complete()

    return (d.EX_OK, 'success')

