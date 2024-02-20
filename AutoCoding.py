# pylint: disable=line-too-long, broad-exception-caught, too-many-lines. too-many-nested-blocks
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
    The URL for the AutoCoding service on the MetaMapLite Server (default="/AutoCoding/MetaMapLite")

    -v loggingLevel|--verbose=loggingLevel
    Set the level of logging that you want.

    -L logDir|--logDir=logDir
    The directory where the log file will be created (default=".").

    -l logfile|--logfile=logfile
    The name of a log file where you want all messages captured.


    This script processes a clinical document, which may contain headings, lists, wrapped text etc.
    This script uses MetaMapLite to identify the clinical concepts within the clinical document and
    also split the clinical document into sentences (full stops are good!).

    However, before this the clinical document may need cleaning (preparing) so that MetaMapLite will be able
    to find all the clinical terms. For instance, abbrevations and acronyms will have to be replaced with their
    full, correct medical terms.

    And after coding, all we will have it a collection of clinical codes. Some processing will be required in order
    to create a collection of interpretable/analyzable clinical concepts. Firstly, it may be necessary to
    interpret the codes "in context" so we create a new "document" being a blend of sentences and
    clinical codes embedded within those sentences at the point within each sentence where MetaMapLite
    identified as piece of text that mapped to a clinical code. Whilst doing this we identify which
    sentences or parts of sentences contain historical information ('past history of ...'). Usually, any analysis
    will want to focus on current conditions/problems and ignore any historical observations.

    Ths other "in context" issue that will need addressing is 'negation'. MetaMapLite will identify negated concepts
    such as "no signs of X" but only negated concepts. MetaMapLite does not propate negation to subsequent concepts.
    The AutoCoding Clinical Documents project has to be able to handle sentences like "no signs of X or Y,
    but clear evidence of Z". The negation of "X" must be extended to "Y", but negation extension must cease
    whenever the word "but" or "however" or any other, similar negation termination word or phrase is encountered.

    The final step in creating a set of interpretable/analyzable clinical concepts it to recognize that MetaMapLite
    returns codes with varing degrees of specificity; sometimes it returns a sequence of small concepts which,
    when taken as a whole, imply a more complex concept that is relevant to any subsequent analysis.

    The AutoCoding Clinical Documents project handles all of this at an abtract level, which means that it can
    be used in many, varied situations, to automatically code many, varied types of clinical documents. However
    the details will vary greatly between Use Cases; the acronyms found in nursing notes will be different to
    those found in discharge sumarries which, in turn, will be different to those found in pathology reports.
    To cater for these different Use Cases, the AutoCoding Clinical Documents project read solution specific
    configuration data and imports solution specific Python modules, for each Use Case. The name of the "solution"
    (name of the folder containing the solution specific Excel workbooks and Python scripts) must be specified
    on the command line when you run "AutoCoding.py".    
'''

# pylint: disable=invalid-name, bare-except, pointless-string-statement, unspecified-encoding

import os
import sys
import logging
import importlib
import threading
import json
import re
from urllib.parse import urlencode
from http import client
from openpyxl import load_workbook
import functions as f
import data as d


def getDocument(fileName):
    '''
    Get a clinical from a file or standard input
    '''
    d.rawClinicalDocument = ''
    if fileName == '-':     # Use standard input
        for line in sys.stdin:
            d.rawClinicalDocument += line.rstrip() + '\n'
        return
    with open(fileName, 'rt', newline='', encoding='utf-8') as fp:
        for line in fp:
            d.rawClinicalDocument += line.rstrip() + '\n'
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
    (changeFound, changeAt) = f.checkPreamble(False, thisText)
    if changeFound:            # We have history at the start or somewhere in, the document
        if changeAt != 0:
            document1 = thisText[:changeAt]        # Everything before the start of the first slab of history
            document2 = thisText[changeAt:]        # The first slab of history and everything after that
            someText = document2
            # logging.debug('some preamble found (%s)', document1)
            # Look for the end of history in the remainder of the document
            (changeFound, changeAt) = f.checkPreamble(True, someText)
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
        section = f.getSection(currentSection, thisText)        # Get the section for this sentence
        currentSection = section
        d.sentences.append([False, inHistory, thisStart, len(thisText), thisText, [], {}, section])
        # We need to know if this sentence is in a history section, or just contains the word(s) implying 'history' somewhere in the sentence
        firstChange = True
        lastChange = 0
        depth = 0
        changesAt, matchLen = f.checkHistory(inHistory, thisText, depth)
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
            changesAt, matchLen = f.checkHistory(inHistory, thisText, depth)

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
            changeIt, reason, prePost =  f.checkNegation(thisConcept, thisText, thisStart, sentenceNo, isNegated)
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
        f.checkModified(thisConcept, document[thisStart][miniDoc]['negation'], sentenceNo, thisStart, miniDoc)
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
                changeIt, reason, prePost =  f.checkNegation(thisConcept, thisText, thisStart, sentenceNo, 0)

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
                f.checkModified(thisConcept, thisIsNeg, sentenceNo, thisStart, miniDoc)
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
    f.doNegationLists()

    # Check for document and sentence sets in the history
    f.checkSets(True)

    # Check for document and sentence sets in the non-history
    f.checkSets(False)

    # Do any negation lists again - in case a sentence set created a negated higher concept which is in a Negation List
    f.doNegationLists()

    # Now add any final solution specific concepts to the document
    # Note: We have done all negation and concept set checking, so these concepts are not candidates for concept sets
    # Note: Must be knownConcepts as we cannot change the configuration at this point
    d.sc.addFinalConcepts()

    # Do any solution completion tasks
    d.sc.complete()

    return(d.EX_OK, 'success')



if __name__ == '__main__':
    '''
    The main code
    Start by parsing the command line arguements and setting up logging.
    Then import the solution files and read in the configuration data.
    Validate the solution - all files exist, all worksheets in workbooks.
    Then process each file name in the command line - read the text document,
    autocode it, analyze the sentences and codes before printing the results.
    '''

    # Quick scan of the command line options to see if '-F' or '--Flask' have been set
    isFlask = False
    for arg in sys.argv:
        if arg == '-F':
            isFlask = True
        elif arg == '--Flask':
            isFlask = True

    # Set the command line options
    parser = f.setArguments(isFlask)

    # Parse the command line
    f.doArguments(parser, isFlask)

    # Check for a valid combination of arguments
    if (d.inputFile is not None) and (d.inputDir is None):
        logging.critical('Must specify inputDir when specifying inputFile')
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Make sure we can connect to the MetaMapLite Service
    MetaMapLiteConnection = None                # The MetaMapLite http connection
    d.MetaMapLiteServiceLock = threading.Lock()    # A Threading Lock used to avoid threading issues in the MetaMapLiteService
    d.MetaMapLiteHeaders = {'Content-type':'application/x-www-form-urlencoded', 'Accept':'application/json'}
    try:
        MetaMapLiteConnection = client.HTTPConnection(d.MetaMapLiteHost, d.MetaMapLitePort)
        MetaMapLiteConnection.close()
    except (client.NotConnected, client.InvalidURL, client.UnknownProtocol,client.UnknownTransferEncoding,client.UnimplementedFileMode,
            client.IncompleteRead, client.ImproperConnectionState, client.CannotSendRequest, client.CannotSendHeader,
            client.ResponseNotReady, client.BadStatusLine) as e:
        logging.critical('Cannot connect to the MetaMapLite Service on host (%s) and port (%s) [error:(%s)]',
                         d.MetaMapLiteHost, d.MetaMapLitePort, repr(e))
        logging.shutdown()
        sys.stdout.flush()
        sys.exit(d.EX_UNAVAILABLE)
    logging.debug('Connection to MetaMapLite server tested')

    # Check that the solution files all exist and appear correct.
    if not os.path.isdir(os.path.join('solutions', d.solution)):
        logging.critical('No solution folder named "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if not os.path.isfile(os.path.join('solutions', d.solution, 'solutionData.py')):
        logging.critical('No solution file "solutionData.py" in solution folder "%s"', d.solution)
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

    # Check the solution specific MetaThesaurus Excel workbook
    wb = load_workbook(os.path.join('solutions', d.solution, 'Solution MetaThesaurus.xlsx'))
    requiredColumns = ['MetaThesaurus code', 'MetaThesaurus description','Source', 'Source code']
    this_df = f.checkWorksheet(wb, 'Solution MetaThesaurus', 'Solution MetaThesaurus', requiredColumns, True)
    this_df = this_df.set_index(this_df.iloc[:,0].name)     # The code is really the index/dictionary keys()
    this_df = this_df.rename(columns={'MetaThesaurus_description': 'description'})
    d.solutionMetaThesaurus = this_df.to_dict(orient='index')

    # Import the solution specific data module
    try:
        d.sd = importlib.import_module('solutions.' + d.solution + '.solutionData')
    except Exception as e:
        logging.fatal('Cannot import "solutionData.py" for solution "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    logging.debug('Solution specific data loaded')

    # Check the solution 'prepare' Excel workbook
    wb = load_workbook(os.path.join('solutions', d.solution, 'prepare.xlsx'))
    requiredColumns = ['Label', 'Replacement']
    f.loadSimpleCompileSheet(wb, 'prepare', 'labels', requiredColumns, r'^', None, False, False, d.labels)
    requiredColumns = ['Common', 'Technical']
    f.loadSimpleCompileSheet(wb, 'prepare', 'terms', requiredColumns, None, None, True, True, d.terms)
    requiredColumns = ['Preamble markers', 'isCase', 'isStart']
    f.loadBoolCompileWorksheet(wb, 'prepare', 'preamble markers', requiredColumns, None, None, True, d.preambleMarkers)
    requiredColumns = ['Preamble terms', 'Technical']
    f.loadSimpleCompileSheet(wb, 'prepare', 'preamble terms', requiredColumns, None, None, True, True, d.preambleTerms)

    # Import the solution specific prepare module and check that it has all the required functions
    try:
        d.sp = importlib.import_module('solutions.' + d.solution + '.prepare')
    except Exception as e:
        logging.fatal('Cannot import "prepare.py" for solution "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    for requiredFunction in ['configure', 'solutionCleanDocument', 'checkPreamble', 'checkNotPreamble']:
        if not hasattr(d.sp, requiredFunction):
            logging.fatal('"prepare" module in solution "%s" is missing the "%s" function', d.solution, requiredFunction)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # Now do any solution specific 'prepare' configuration and initialzation
    configConcepts = d.sp.configure(wb)
    d.knownConcepts.update(configConcepts)
    logging.debug('Prepare module loaded and configured')

    # Check the solution 'complete' Excel workbook
    wb = load_workbook(os.path.join('solutions', d.solution, 'complete.xlsx'))
    requiredColumns = ['History markers', 'isCase', 'isStart']
    f.loadBoolCompileWorksheet(wb, 'complete', 'history markers', requiredColumns, None, None, True, d.historyMarkers)
    requiredColumns = ['Pre history']
    f.loadSimpleCompileSheet(wb, 'complete', 'pre history', requiredColumns, None, None, True, True, d.preHistory)
    requiredColumns = ['Section markers', 'Section', 'isCase']
    f.loadSimpleCompileSheet(wb, 'complete', 'section markers', requiredColumns, None, None, True, True, d.sectionMarkers)
    requiredColumns = ['SolutionID', 'MetaThesaurusID(s)']
    this_df = f.checkWorksheet(wb, 'complete', 'equivalents', requiredColumns, False)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(site implied), columns(%s), record(%s)", requiredColumns, record)
        equivalent = record[0]
        d.knownConcepts.add(equivalent)
        j = 1
        while (j < len(record)) and (record[j] is not None):
            d.equivalents[record[j]] = equivalent
            d.knownConcepts.add(record[j])
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
        if row.SolutionID is None:
            break
        # logging.debug("sheet(sentence concepts)), columns(%s), row(%s)", requiredColumns, row)
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
        if row.Start_Negation is None:
            break
        # logging.debug("sheet(gross negations)), columns(%s), row(%s)", requiredColumns, row)
        startNeg = re.compile(f.checkPattern(row.Start_Negation), flags=re.IGNORECASE|re.DOTALL)
        endNeg = re.compile(f.checkPattern(row.End_Negation), flags=re.IGNORECASE|re.DOTALL)
        sentences = int(row.Sentences)
        d.grossNegation.append((startNeg, endNeg, sentences))
    requiredColumns = ['SolutionID', 'Section', 'Negate', 'MetaThesaurusIDs']
    f.loadNegationListWorksheet(wb, 'complete', 'sentence negation lists', requiredColumns, d.sentenceNegationLists)
    f.loadNegationListWorksheet(wb, 'complete', 'document negation lists', requiredColumns, d.documentNegationLists)
    requiredColumns = ['SolutionID', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadSequenceConceptSetsWorksheet(wb, 'complete', 'sent strict seq concept sets', requiredColumns, True, d.sentenceConceptSequenceSets)
    f.loadSequenceConceptSetsWorksheet(wb, 'complete', 'sentence sequence concept sets', requiredColumns, False, d.sentenceConceptSequenceSets)
    requiredColumns = ['SolutionID', 'Sentences', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadSequenceConceptSetsWorksheet(wb, 'complete', 'multi sent strict seq conc sets', requiredColumns, True, d.sentenceConceptSequenceSets)
    f.loadSequenceConceptSetsWorksheet(wb, 'complete', 'multi sentence seq concept sets', requiredColumns, False, d.sentenceConceptSequenceSets)
    requiredColumns = ['SolutionID', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadConceptSetsWorksheet(wb, 'complete', 'sentence concept sets', requiredColumns, d.sentenceConceptSets)
    requiredColumns = ['SolutionID', 'Sentences', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadConceptSetsWorksheet(wb, 'complete', 'multi sentence concept sets', requiredColumns, d.sentenceConceptSets)
    requiredColumns = ['SolutionID', 'Asserted', 'MetaThesaurus or Solution IDs']
    f.loadConceptSetsWorksheet(wb, 'complete', 'document sequence concept sets', requiredColumns, d.documentConceptSequenceSets)
    f.loadConceptSetsWorksheet(wb, 'complete', 'document concept sets', requiredColumns, d.documentConceptSets)
    requiredColumns = ['MetaThesaurus code']
    this_df = f.checkWorksheet(wb, 'complete', 'other concepts', requiredColumns, True)
    d.otherConcepts = set(this_df['MetaThesaurus_code'].unique())


    # Import the solution specific complete module and check that it has all the required functions
    try:
        d.sc = importlib.import_module('solutions.' + d.solution + '.complete')
    except Exception as e:
        logging.fatal('Cannot import "complete.py" for solution "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    for requiredFunction in ['configure', 'requireConcept', 'solutionCheckHistory', 'addRawConcepts', 'initalizeNegation',
                             'extendNegation', 'higherConceptFound', 'setConcept', 'solutionAddAdditionalConcept', 'addFinalConcepts', 'complete']:
        if not hasattr(d.sc, requiredFunction):
            logging.fatal('"complete" module in solution "%s" is missing the "%s" function', d.solution, requiredFunction)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # Now do any solution specific 'complete' configuration and initialzation
    configConcepts = d.sc.configure(wb)
    d.knownConcepts.update(configConcepts)
    logging.debug('Complete module loaded and configured')

    # Check the solution 'analyze' Excel workbook
    wb = load_workbook(os.path.join('solutions', d.solution, 'analyze.xlsx'))

    # There are no standard solution 'analyze' Excel worksheets

    # Import the solution specific analyze module and check that it has all the required functions
    try:
        d.sa = importlib.import_module('solutions.' + d.solution + '.analyze')
    except Exception as e:
        logging.fatal('Cannot import "analyze.py" for solution "%s"', d.solution)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    for requiredFunction in ['configure', 'analyze']:
        if not hasattr(d.sa, requiredFunction):
            logging.fatal('"analyzee" module in solution "%s" is missing the "%s" function', d.solution, requiredFunction)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
    if isFlask:
        for requiredFunction in ['reportHTML', 'reportJSON']:
            if not hasattr(d.sa, requiredFunction):
                logging.fatal('"analyzee" module in solution "%s" is missing the "%s" function', d.solution, requiredFunction)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
    else:
        if not hasattr(d.sa, 'reportFile'):
            logging.fatal('"analyzee" module in solution "%s" is missing the "reportFile" function', d.solution)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # Now do any solution specific 'analyze' configuration and initialzation
    configConcepts = d.sa.configure(wb)
    d.knownConcepts.update(configConcepts)
    logging.debug('Analyze module loaded and configured')

    # Now read in the file(s) and AutoCode them
    # If neither inputDir, nor inputFile is specified, then read one file from standard input
    # and print the results to standard output.
    # If only inputDir is specified and outputDir is specified then process all the files in inputDir
    # and print all the results to outputDir with the same filename.
    # Otherwise, process just the one file - inputDir/inputFile. If outputDir is specified
    # then print the result to outputDir/inputFile, otherwise print the result to inputDir/AutoCoded_inputFile
    files = []
    if d.inputDir is None:
        files.append('-')
    elif d.inputFile is not None:
        files.append(d.inputFile)
    else:
        files = os.listdir(d.inputDir)

    for file in files:
        if d.inputDir is None:
            getDocument(file)
        else:
            getDocument(os.path.join(d.inputDir, file))

        # AutoCode this clinical document
        success = AutoCode()
        if success != d.EX_OK:
            continue

        # Print this clinical document
        if file == '-':
            d.sa.reportFile(None, None)
            sys.exit(d.EX_OK)
        baseFile = os.path.basename(file)
        filePart, ext = os.path.splitext(baseFile)
        if d.outputDir is None:
            d.sa.reportFile(d.inputDir, 'AutoCoded_' + filePart)
        else:
            d.sa.reportFile(d.outputDir, filePart)
