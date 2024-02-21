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
import functions as f
import data as d


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
            changeAt = d.sp.solutionCheckNotPreamble(text)
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
            changeAt = d.sp.solutionCheckPreamble(text)
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

    logging.debug('checkHistory() - checking for history in text(%s)', text)
    # Check if we are in history and ran into something useful, or in useful text, but ran in to history
    if inHistory:        # We are in history - check to see if we've come to the end of this history section
        logging.debug('checkHistory() - checking for leaving history in text(%s)', text)
        # Check for the configured end of history markers (regular expression, ignore case)
        historyEndFound = False
        newStart = None
        matchLen = None
        # Search for the first occurence of an 'end of history marker' in this text
        for marker, isStart in d.historyMarkers:
            if isStart:    # This is a start of history marker, but we are in history, so skip this marker
                continue
            logging.debug('checkHistory() - checking endOfHistory marker:%s[%s]', marker.pattern, marker.flags)
            match = marker.search(text)
            if match is not None:        # End of history found
                historyEndFound = True        # Some document 'end of history' text found
                # Remember where we ended history
                if (newStart is None) or (match.start() < newStart):
                    newStart = match.start()
                    matchLen = len(match.group())
        if historyEndFound:        # We did bounced out of history
            logging.debug('checkHistory() - end of history found at %d with "%s"', newStart, text[newStart:newStart + matchLen])
            return (newStart, matchLen)
        # We are still in history, or at least we think we are - the specific solution may have a different answer
        historyEnds, scChangeAt, scLen = d.sc.solutionCheckHistory(inHistory, text)
        # The solution can indicate that history ended at a previous sentence
        # All sentences between this new end of history and the current sentence are not history
        if historyEnds == 0:        # History ends with this sentence
            logging.debug('checkHistory() - solution say history ended at the start of this sentence')
            return (scChangeAt, scLen)
        elif historyEnds > 0:        # History ended with a previous sentence
            # History ended several sentences ago - update those sentences to not history
            # We need to reprocess these sentence as they were processed as though they were in history.
            # However this is recursive, so check that we haven't fallen into a recursive loop
            logging.debug('checkHistory() - solution says history ended %d sentences ago', historyEnds)
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
        logging.debug('Checking for entering history in text(%s)', text)
        # Check for the configured start of history markers (regular expression, ignore case)
        historyFound = False
        newStart = None
        matchLen = None
        # Search for the first occurance of a 'start of history marker' in this text
        for marker, isStart in d.historyMarkers:
            if not isStart:    # This is an end of history marker, but we are not in history, so skip this marker
                continue
            logging.debug('Checking inHistory marker:%s[%s]', marker.pattern, marker.flags)
            match = marker.search(text)
            if match is not None:    # Start of history found
                historyFound = True        # Start of history marker found
                # Remember where we started history
                if (newStart is None) or (match.start() < newStart):
                    newStart = match.start()
                    matchLen = len(match.group())
        if historyFound:        # We did bounce into history
            logging.debug('checkHistory() - history found at %d with text "%s"', newStart, text[newStart:newStart + matchLen])
            return (newStart, matchLen)
        # We aren't in history, or at least we don't think we are - the specific solution may have a different answer
        historyAt, scChangeAt, scLen = d.sc.solutionCheckHistory(inHistory, text)
        # The solution can indicate that history started at a previous sentence
        # All sentences between this new start of history and the current sentence are history
        if historyAt == 0:            # History starts with this sentence
            logging.debug('checkHistory() - solution say history started at the start of this sentence')
            return (scChangeAt, scLen)
        elif historyAt > 0:            # History starts at a previous sentence
            # History started several sentences ago - update those sentences to history
            # We need to reprocess these sentence as they were processed as though they were not in history.
            # However this is recursive, so check that we haven't fallen into a recursive loop
            if depth > 2:
                logging.critical('Too many levels of recursion when checking history')
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            logging.debug('checkHistory() - solution says history started %d sentences ago', historyEnds)
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
                logging.debug('checkHistory() - found a pre-history tag at %d', startHistory)
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
                    logging.debug('found preNegation(%s) at %d', reason, changeAt)
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
                    logging.debug('found immediatePreNegation (%s) at %d', reason, changeAt)
    for immedPreAmbig in d.immediatePreAmbiguous:
        if (len(immedPreAmbig) > 1) and (concept not in immedPreAmbig[1:]):        # Check if this ambiguity is limited to a list of concepts
            continue
        logging.debug('looking for immediate preAmbiguous of (%s) in (%s)', immedPreAmbig[0].pattern, thisText[:thisStart + len(text)])
        for match in immedPreAmbig[0].finditer(thisText[:thisStart]):
            if match.start() > changeAt:
                changeAt = match.start()
                changeIt = '2'
                reason = immedPreAmbig[0].pattern
                prePost = 'immediatePreAmbiguous'
                logging.debug('found immediatePreAmbiguous(%s) at %d', reason, changeAt)
    for preAmbig in d.preAmbiguous:
        if (len(preAmbig) > 1) and (concept not in preAmbig[1:]):        # Check if this ambiguity is limited to a list of concepts
            continue
        logging.debug('looking for preAmbiguous of (%s) in (%s)', preAmbig[0].pattern, thisText[:thisStart + len(text)])
        for match in preAmbig[0].finditer(thisText[:thisStart]):
            if match.start() > changeAt:
                changeAt = match.start()
                changeIt = '2'
                reason = preAmbig[0].pattern
                prePost = 'preAmbiguous'
                logging.debug('found preAmbiguous(%s) at %d', reason, changeAt)
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
    if concept in d.preModifiers:
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
            if newConcept in d.solutionMetaThesaurus:
                document[start][miniDoc]['description'] = d.solutionMetaThesaurus[newConcept]['description'] + '(was:' + concept + ')'
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
            if newConcept in d.solutionMetaThesaurus:
                document[start][miniDoc]['description'] = d.solutionMetaThesaurus[newConcept]['description'] + '(was:' + concept + ')'
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

    # Check if any of the sentences contains any of the the Sentence (Strict) Sequence Concept Sets
    # We test sentence sequence sets first because they are a stricter test.
    # Sentence sequence sets are checked in the order in which they are appended to the sentenceConceptSequenceSets array
    # which is 'sent_strict_seq_concepts_set', 'sentence_sequence_concept_sets', 'multi_sent_strict_seq_conc_sets' then 'multi_sentence_seq_concept_sets'
    # [solutionID, [[concept, negation]], isStrict, sentenceRange, isNeg, asserted]

    # check each sentence concept sequence set
    for setNo, (higherConcept, thisSet, isStrict, sentenceRange, higherConceptNegated, asserted) in enumerate(d.sentenceConceptSequenceSets):
        logging.debug('Checking sentence Concept Sequence set (%s) [%s]', d.sentenceConceptSequenceSets[setNo], history)
        if len(thisSet) == 0:       # Empty concept list
            continue
        conceptNo = 0           # The index of the next concept in the sequence set
        conceptList = []        # The concepts in this set that have been found
        concept, isNeg = thisSet[conceptNo]     # The next concept that we are looking for
        firstConcept, firstIsNeg = thisSet[0]
        for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
            logging.debug('checkSets - sentence Concept (Strict) (Sequence) Sets - processing sentence[%d]', sentenceNo)
            document = sentence[6]        # Sentences hold mini-documents
            if len(conceptList) == 0:        # Compute a new 'valid range' if still looking for the first concept
                # Compute the last sentence for this range
                lastSentence = sentenceNo + sentenceRange - 1
                if lastSentence >= len(d.sentences):
                    lastSentence = len(d.sentences) - 1
                # Compute the character position of the end of the last sentence in this range
                sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
            for thisStart in sorted(document, key=int):        # We step through all concepts in each sentence
                conceptFound = False                    # Concept in theSet at 'conceptNo' not yet found at thisStart
                for jj, miniDoc in enumerate(document[thisStart]):    # Step through the list of alternate concepts at this point in this sentence
                    # Only check history if we are looking for history, and non-history if we are looking for non-history
                    if miniDoc['history'] != history:
                        break
                    if miniDoc['used']:        # Skip used concepts
                        continue
                    # Ignore any concept who's text extends beyond this sentence range
                    if thisStart + miniDoc['length'] > sentenceEnd:
                        continue
                    thisConcept = miniDoc['concept']        # This concept
                    thisIsNeg = miniDoc['negation']        # And it's negation
                    # Only check concepts that we know something about - the appeared in one of our configuration files
                    if thisConcept not in d.knownConcepts:
                        continue
                    # Check if this alternate concept, at 'start', is in the next concept in this sentence concept sequence set
                    found = False
                    if concept == thisConcept:
                        if isNeg == thisIsNeg:
                            found = True
                            break
                        elif (isNeg in ['2', '3']) and (thisIsNeg in ['2', '3']):
                            found = True
                            break
                    if not found:
                        # Check for a restart of the sequence,
                        # We special case of a repetition of the first concept in the set
                        # We don't handle repetitions within a set - just a repetition of the first concept
                        # i.e.looking for concept 'n' - found concept 0 [this set, array of concepts in dict, first entry, concept]
                        if (thisConcept == firstConcept) and ((firstIsNeg == thisIsNeg) or (firstIsNeg in ['2', '3']) and (thisIsNeg in ['2', '3'])):
                            # Found the first concept - restart the multi-sentence counter
                            # Compute the last sentence for this range
                            lastSentence = sentenceNo + sentenceRange - 1
                            if lastSentence >= len(d.sentences):
                                lastSentence = len(d.sentences) - 1
                            # Compute the character position of the end of the last sentence in this range
                            sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
                            conceptList = []
                            conceptList.append((sentenceNo, thisStart, jj))        # Add to the list of things we may need to mark as 'used'
                            conceptNo = 1
                            conceptFound = True
                            logging.debug('concept(%s[%s]) is not the next concept (%s[%s]) in set[%d], but is the first - restarting',
                                            thisConcept, thisIsNeg, concept, isNeg, setNo)
                            break   # Proceed to next 'start' in this sentence
                        continue
                    # We have the next concept from this set
                    conceptFound = True
                    conceptList.append((sentenceNo, thisStart, jj))        # Add to the list of things we may need to mark as 'used'
                    logging.debug('Concept (%s) [for sentence Concept (Strict) (Sequence) set:%d] found', thisConcept, setNo)
                    conceptNo += 1
                    if len(conceptList) == len(thisSet):
                        # We have a full concept (strict) (sequence) set - so save the higher concept - append the higher concept to the list of alternates
                        logging.info('Sentence concept sequence set (%s:%s) found', higherConcept, thisSet)
                        addAdditionalConcept(higherConcept, sentenceNo, thisStart, jj, None, higherConceptNegated,
                                            f'sentenceConceptSequenceSet:{repr(thisSet)}', 0)

                        # Check if we should mark all/some of the concepts in the concept list as used
                        if asserted or (d.sc.higherConceptFound(higherConcept)):
                            for sno, strt, k in conceptList:
                                foundConcept = d.sentences[sno][6][strt][k]['concept']
                                # Check if we should mark this concepts in the concept list as used
                                if asserted or (d.sc.setConcept(higherConcept, foundConcept)):
                                    d.sentences[sno][6][strt][k]['used'] = True
                                    logging.debug('Marking sentence concept sequence set item at %d/%d as used', strt, k)

                        conceptNo = 0        # Restart in case the same concept sequence set exists later in the sentences
                        conceptList = []
                        # Compute the last sentence for this range
                        lastSentence = sentenceNo + sentenceRange - 1
                        if lastSentence >= len(d.sentences):
                            lastSentence = len(d.sentences) - 1
                        # Compute the character position of the end of the last sentence in this range
                        sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
                        break   # Proceed to next 'start' in this sentence
                    else:
                        conceptNo += 1
                # end of all the alternate concepts at this point in the sentence
                # If this is a strict list - and we are part way through matching the concepts, then start again
                if isStrict and (conceptNo > 0) and not conceptFound:    # Tried all alternatives and the next concept in the strict list was not found
                    logging.info('Strict sequence started[%d] abandoned due to mismatch', setNo)
                    conceptNo = 0        # Restart in case the set exists later in the sentences
                    conceptList = []
                    # Compute the last sentence for this range
                    lastSentence = sentenceNo + sentenceRange - 1
                    if lastSentence >= len(d.sentences):
                        lastSentence = len(d.sentences) - 1
                    sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
            # end of all the concepts in this sentence
            # If we are part way through matching the concepts, but this is the last sentence in the current range then start again
            if (conceptNo > 0) and (sentenceNo == lastSentence):
                conceptNo = 0
                conceptList = []
        # end of the sentences
    # end of sentence concept sequence set


    # Next check the Sentence Concept Sets
    # We test these next because Sentence Concept Sets may create concepts that become part of a document sequence or document concept set
    # Sentence Concept Sets can be valid over a number of sentences, but we may have to expire things found if we go beyond that range
    # (SolutionID, [(concept, isNeg)], sentences, isNeg, asserted)
    for setNo, (higherConcept, thisSet, sentenceRange, higherConceptNegated, asserted) in enumerate(d.sentenceConceptSets):
        logging.debug('Checking sentence Concept set (%s) [%s]', d.sentenceConceptSets[setNo], history)
        if len(thisSet) == 0:       # Empty concept list
            continue
        toFindCount = {}        # The count of the number of times each concept/negation occurs in this set
        for concept, isNeg in thisSet:
            if (concept, isNeg) not in toFindCount:
                toFindCount[(concept, isNeg)] = 1
            else:
                toFindCount[(concept, isNeg)] += 1
        conceptList = []        # The concepts in this set that have been found
        for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
            logging.debug('checkSets - sentence Concept Sets - processing sentence[%d]', sentenceNo)
            document = sentence[6]        # Sentences hold mini-documents
            if len(conceptList) == 0:        # Compute a new 'valid range' if still looking for the first concept
                # Compute the last sentence for this range
                lastSentence = sentenceNo + sentenceRange - 1
                if lastSentence >= len(d.sentences):
                    lastSentence = len(d.sentences) - 1
                # Compute the character position of the end of the last sentence in this range
                sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]

            for thisStart in sorted(document, key=int):        # We step through all concepts in each sentence
                for jj, miniDoc in enumerate(document[thisStart]):    # Step through the list of alternate concepts at this point in this sentence
                    # Only check history if we are looking for history, and non-history if we are looking for non-history
                    if miniDoc['history'] != history:
                        break
                    if miniDoc['used']:        # Skip used concepts
                        continue
                    # Ignore any concept who's text extends beyond this sentence range
                    if thisStart + miniDoc['length'] > sentenceEnd:
                        continue
                    thisConcept = miniDoc['concept']        # This concept
                    thisIsNeg = miniDoc['negation']        # And it's negation
                    # Only check concepts that we know something about - the appeared in one of our configuration files
                    if thisConcept not in d.knownConcepts:
                        continue
                    # Check if this alternate concept, at 'start', is in this sentence concept set
                    if (thisConcept, thisIsNeg) not in toFindCount:
                        continue
                    if toFindCount[(thisConcept, thisIsNeg)] == 0:      # All required instances already found
                        continue
                    toFindCount[(thisConcept, thisIsNeg)] -= 1
                    conceptList.append((sentenceNo, thisStart, jj))        # Add to the list of things we may need to mark as 'used'
                    logging.debug('Concept (%s) [for sentence Concept set:%d] found', thisConcept, setNo)
                    if len(conceptList) == len(thisSet):
                        # We have a full concept set - so save the higher concept - append the higher concept to the list of alternates
                        logging.info('Sentence concept set (%s:%s) found', higherConcept, thisSet)
                        f.addAdditionalConcept(higherConcept, sentenceNo, thisStart, jj, None, higherConceptNegated,
                                            f'sentenceConceptSequenceSet:{repr(thisSet)}', 0)

                        # Check if we should mark all/some of the concepts in the concept list as used
                        if (asserted) or (d.sc.higherConceptFound(higherConcept)):
                            for sno, strt, k in conceptList:
                                foundConcept = d.sentences[sno][6][strt][k]['concept']
                                # Check if we should mark this concepts in the concept list as used
                                if asserted or (d.sc.setConcept(higherConcept, foundConcept)):
                                    d.sentences[sno][6][strt][k]['used'] = True
                                    logging.debug('Marking sentence concept sequence set item at %d/%d as used', strt, k)

                        # Restart in case the same concept sequence set exists later in the sentences
                        toFindCount = {}        # The count of the number of times each concept/negation occurs in this set
                        for concept, isNeg in thisSet:
                            if (concept, isNeg) not in toFindCount:
                                toFindCount[(concept, isNeg)] = 1
                            else:
                                toFindCount[(concept, isNeg)] += 1
                        conceptList = []        # The concepts in this set that have been found
                        # Compute the last sentence for this range
                        lastSentence = sentenceNo + sentenceRange - 1
                        if lastSentence >= len(d.sentences):
                            lastSentence = len(d.sentences) - 1
                        # Compute the character position of the end of the last sentence in this range
                        sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
                        break   # Proceed to next 'start' in this sentence
                # end of all the alternate concepts at this point in the sentence
            # end of all the concepts in this sentence
        # end of the sentences
    # end of sentence concept sequence set

    # Next check for any document Concept Sequence Sets - checking across all sentences
    # We test sequence sets first because they are a stricter test
    # and because Document Sequence Sets may create concepts that become part of a document concept set
    # [solutionID, [[concept, isNeg]], isNeg, asserted])

    # check each document concept sequence set
    for setNo, (higherConcept, thisSet, sentenceRange, higherConceptNegated, asserted) in enumerate(d.documentConceptSequenceSets):
        # sentenceRange will be '1' and should be ignored, as this is a whole of document check
        logging.debug('Checking document concept sequence set (%s)', d.documentConceptSequenceSets[setNo])
        conceptNo = 0                # Check each concept in the set in sequence
        conceptList = []            # And remember which one's we've found so we can mark them as used if we get a full set
        concept, isNeg = thisSet[conceptNo]     # The next concept that we are looking for
        firstConcept, firstIsNeg = thisSet[0]
        for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
            logging.debug('checkSets - document Concept Sequence Sets - processing sentence[%d]', sentenceNo)
            document = sentence[6]    # Sentences hold mini-documents
            for thisStart in sorted(document, key=int):
                conceptFound = False                    # Concept in theSet at 'conceptNo' not yet found at thisStart
                for jj, miniDoc in enumerate(document[thisStart]):
                    # Only check history if we are looking for history, and non-history if we are looking for non-history
                    if miniDoc['history'] != history:
                        break
                    thisConcept =  miniDoc['concept']
                    thisIsNeg =  miniDoc['negation']        # Check negation matches
                    if miniDoc['used']:        # Skip used concepts [only Findings get 'used']
                        continue
                    # Only check concepts that we know something about - the appeared in one of our configuration files
                    if thisConcept not in d.knownConcepts:
                        continue
                    # Check if this is the next one in the sequence
                    found = False
                    thisNeg = thisSet[conceptNo][1]
                    if thisConcept == thisSet[conceptNo][0]:
                        if thisIsNeg == thisNeg:
                            found = True
                        elif (thisIsNeg in ['2', '3']) and (thisNeg in ['2', '3']):
                            found = True
                    if not found:
                        # Check for a restart of the sequence,
                        # We special case of a repetition of the first concept in the set
                        # We don't handle repetitions within a set - just a repetition of the first concept
                        # i.e.looking for concept 'n' - found concept 0 [this set, array of concepts in dict, first entry, concept]
                        if (thisConcept == firstConcept) and ((firstIsNeg == thisIsNeg) or (firstIsNeg in ['2', '3']) and (thisIsNeg in ['2', '3'])):
                            # Found the first concept - restart the multi-sentence counter
                            # Compute the last sentence for this range
                            lastSentence = sentenceNo + sentenceRange - 1
                            if lastSentence >= len(d.sentences):
                                lastSentence = len(d.sentences) - 1
                            # Compute the character position of the end of the last sentence in this range
                            sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
                            conceptList = []
                            conceptList.append((sentenceNo, thisStart, jj))        # Add to the list of things we may need to mark as 'used'
                            conceptNo = 1
                            conceptFound = True
                            logging.debug('concept(%s[%s]) is not the next concept (%s[%s]) in set[%d], but is the first - restarting',
                                            thisConcept, thisIsNeg, concept, isNeg, setNo)
                            break   # Proceed to next 'start' in this sentence
                        continue
                    # We have the next concept from this set
                    conceptFound = True
                    conceptList.append((sentenceNo, thisStart, jj))        # Add to the list of things we may need to mark as 'used'
                    logging.debug('Concept (%s) [for document Concept Sequence set:%d] found', thisConcept, setNo)
                    if conceptNo == len(thisSet):
                        # We have a full set - so save the higher concept
                        logging.info('Document concept Sequence set (%s:%s) found', higherConcept, thisSet)
                        addAdditionalConcept(higherConcept, sentenceNo, thisStart, jj, None, higherConceptNegated,
                                             f'documentConceptSequenceSet:{repr(thisSet)}', 0)

                        # Check if we should mark all/some of the concepts in the concept list as used
                        if asserted or (d.sc.higherConceptFound(higherConcept)):
                            for item, thisList in enumerate(conceptList):
                                sno = thisList[0]
                                strt = thisList[1]
                                k = thisList[2]
                                foundConcept = d.sentences[sno][6][strt][k]['concept']
                                # Check if we should mark this concepts in the concept list as used
                                if asserted or (d.sc.setConcept(higherConcept, foundConcept)):
                                    d.sentences[sno][6][strt][k]['used'] = True
                                logging.debug('Marking document concept Sequence set item at %d/%d as used', strt, k)
                        conceptNo = 0        # Restart in case the same concept sequence set exists later in the sentences
                        conceptList = []
                        # Compute the last sentence for this range
                        lastSentence = sentenceNo + sentenceRange - 1
                        if lastSentence >= len(d.sentences):
                            lastSentence = len(d.sentences) - 1
                        # Compute the character position of the end of the last sentence in this range
                        sentenceEnd = d.sentences[lastSentence][2] + d.sentences[lastSentence][3]
                        break   # Proceed to next 'start' in this sentence
                    # end of list of things to check
                # end of all the alternate concepts at this point in the sentence
            # end of all the concepts in this sentence
        # end of all this sentences
    # end of the document concept sequence set


    # Now check for any Document Concept Sets - checking across all sentences
    for setNo, (higherConcept, thisSet, sentenceRange, higherConceptNegated, asserted) in enumerate(d.documentConceptSets):
        # sentenceRange will be '1' and should be ignored, as this is a whole of document check
        logging.debug('Checking document Concept set (%s) [%s]', d.documentConceptSets[setNo], history)
        if len(thisSet) == 0:       # Empty concept list
            continue
        toFindCount = {}        # The count of the number of times each concept/negation occurs in this set
        for concept, isNeg in thisSet:
            if (concept, isNeg) not in toFindCount:
                toFindCount[(concept, isNeg)] = 1
            else:
                toFindCount[(concept, isNeg)] += 1
        conceptList = []        # The concepts in this set that have been found
        for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
            logging.debug('checkSets - document Concept Sets - processing sentence[%d]', sentenceNo)
            document = sentence[6]        # Sentences hold mini-documents
            for thisStart in sorted(document, key=int):        # We step through all concepts in each sentence
                for jj, miniDoc in enumerate(document[thisStart]):    # Step through the list of alternate concepts at this point in this sentence
                    # Only check history if we are looking for history, and non-history if we are looking for non-history
                    if miniDoc['history'] != history:
                        break
                    if miniDoc['used']:        # Skip used concepts
                        continue
                    # Ignore any concept who's text extends beyond this sentence range
                    if thisStart + miniDoc['length'] > sentenceEnd:
                        continue
                    thisConcept = miniDoc['concept']        # This concept
                    thisIsNeg = miniDoc['negation']        # And it's negation
                    # Only check concepts that we know something about - the appeared in one of our configuration files
                    if thisConcept not in d.knownConcepts:
                        continue
                    # Check if this alternate concept, at 'start', is in this sentence concept set
                    if (thisConcept, thisIsNeg) not in toFindCount:
                        continue
                    if toFindCount[(thisConcept, thisIsNeg)] == 0:      # All required instances already found
                        continue
                    toFindCount[(thisConcept, thisIsNeg)] -= 1
                    conceptList.append((sentenceNo, thisStart, jj))        # Add to the list of things we may need to mark as 'used'
                    logging.debug('Concept (%s) [for document Concept set:%d] found', thisConcept, setNo)
                    if len(conceptList) == len(thisSet):
                        # We have a full concept set - so save the higher concept - append the higher concept to the list of alternates
                        logging.info('Sentence concept set (%s:%s) found', higherConcept, thisSet)
                        f.addAdditionalConcept(higherConcept, sentenceNo, thisStart, jj, None, higherConceptNegated,
                                            f'sentenceConceptSequenceSet:{repr(thisSet)}', 0)

                        # Check if we should mark all/some of the concepts in the concept list as used
                        if (asserted) or (d.sc.higherConceptFound(higherConcept)):
                            for sno, strt, k in conceptList:
                                foundConcept = d.sentences[sno][6][strt][k]['concept']
                                # Check if we should mark this concepts in the concept list as used
                                if asserted or (d.sc.setConcept(higherConcept, foundConcept)):
                                    d.sentences[sno][6][strt][k]['used'] = True
                                    logging.debug('Marking sentence concept sequence set item at %d/%d as used', strt, k)

                        # Restart in case the same concept sequence set exists later in the sentences
                        toFindCount = {}        # The count of the number of times each concept/negation occurs in this set
                        for concept, isNeg in thisSet:
                            if (concept, isNeg) not in toFindCount:
                                toFindCount[(concept, isNeg)] = 1
                            else:
                                toFindCount[(concept, isNeg)] += 1
                        conceptList = []        # The concepts in this set that have been found
                        break   # Proceed to next 'start' in this sentence
                # end of all the alternate concepts at this point in the sentence
            # end of all the concepts in this sentence
        # end of the sentences
    # end of sentence concept sequence set
    return
