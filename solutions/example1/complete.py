# pylint: disable=line-too-long, broad-exception-caught, invalid-name, unused-argument
'''
This is the histopathology autocoding coding completion module
This code share data/configuration with the analyze module via the shared data structure solData
'''

import sys
import logging
import re
import functions as f
import data as d


def configure(wb):
    '''
    Read in any histopathology specific worksheets from workbook wb
    Parameters
        wb              - an openpyxl workbook containing complete configuration data
    Returns
        configConcepts  - set(), all concepts detected when processing the workbook
    '''

    configConcepts = set()        # The set of additional known concepts

    # Return the additional known concepts
    return configConcepts


def requireConcept(concept, isNegated, partOfSpeech, isHistory, sentenceNo, start, length, text):
    '''
    Check if the solution requires this concept
    For histopathology, the '?' character is used to indicate that the following may be present.
    But this is a state that is neither postive, nor negative or ambiguous.
    It is a suggestion of a direction for further testing, as in "? stomach ulcer"
    As such, then concept following the '?' can be discarded
    Parameters
        concept         - str, the concept that may be required
        isNegated       - str, one character indicating whether the concept is negated or ambiguous
        partOfSpeech    - str, the MetaMapLite determined part of speech for this concept
        isHistory       - boolean, True means that this is a historical concept
        sentenceNo      - int, the sentence in d.sentences where this concept was found
        start           - int, the location within this sentence where this concept was found
        length          - int, the length of the matching text that was coded to this concept
        text            - str, the text that was coded to this concept
    Returns
        isRequired      - boolean, True means that this concept is required
    '''

    # logging.debug('requireConcept:%s, %s, %s, %s, %d, %d, %d, %s', concept, isNegated, partOfSpeech, isHistory, sentenceNo, start, length, text)

    if partOfSpeech in ['NN', 'NNP', 'NNS', 'NNPS', 'JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS']:
        # logging.debug('noun, adjective or adverb at %d[%s]', start, text)
        # Check if this is just a question, not an answer - the ? will always be the last character on the previous line
        if sentenceNo > 0:        # Start by looking for ' ? xxxx'
            if re.search(r'\s\?\s*$', d.sentences[sentenceNo - 1][4], flags=re.IGNORECASE) is not None:
                # logging.debug('requiredConcept:ignored as query term')
                return False
    return True


def solutionCheckHistory(inHistory, text):
    '''
    Check for any solution specific markers that indicate the start or end of a section of history
    in the current sentence or an preceeding sentence (when combined with information from this sentence).
    Return the number of sentences ago that history changed (or -1 if no change detected)
    and the number of characters to move on in this sentence
    Here text is the current sentence.

    Histopathologies sometimes use hanging paragraphs.
    Sometimes the section heading 'CLINICAL INFORMATION',
    [which is a history marker] gets split over two lines.
    Parameters
        inHistory       - boolean, True indicates that the text preceeding 'text' is historical information
        text            - str, the text to be scanned
    Returns
        sentenceFound   - How many sentence back from the current end d.sentences the match was found
        changeAt        - Where the change occured in the last/current sentence (only valid if sentenceFound == 0)
        matchLen        - The length of the matching text in the last/current sentence (only valid if sentenceFound == 0)
    '''

    if inHistory:        # We are in history - check to see if we came have fallen out of this history section
        return (-1, None, None)
    else:                # We are not in history - check to see if that we have fallen into a new history section
        # Checking if this sentence contains 'INFORMATION:' and any of the three previous sentences starts with 'CLINICAL'
        # logging.debug('solutionCheckHistory() - searching through sentences %s', d.sentences)
        clinicalFound = -1
        search = re.search(r'\b' + r'INFORMATION\s*:', text)
        if search is not None:      # We have 'INFORMATION' in the current sentence in d.sentences
            clinicalFound = -1      # Now search previous sentence for 'CLINICAL'
            if (len(d.sentences) == 0) and (re.search(r'^\s*CLINICAL', text) is not None):
                clinicalFound = 0
            if (len(d.sentences) > 0) and (re.search(r'^\s*CLINICAL', d.sentences[-1][4]) is not None):
                clinicalFound = 1
            if (len(d.sentences) > 1) and (re.search(r'^\s*CLINICAL', d.sentences[-2][4]) is not None):
                clinicalFound = 2
            if (len(d.sentences) > 2) and (re.search(r'^\s*CLINICAL', d.sentences[-3][4]) is not None):
                clinicalFound = 3
            if (len(d.sentences) > 3) and (re.search(r'^\s*CLINICAL', d.sentences[-4][4]) is not None):
                clinicalFound = 4
        if clinicalFound == -1:
            return (-1, None, None)
        elif clinicalFound == 0:
            return (clinicalFound, search.start(), len(search.group()))
        else:
            return (clinicalFound, None, None)


def solutionAddAdditionalConcept(concept, sentenceNo, start, j, negated, depth):
    '''
    An additional concept has been added to the mini-document.
    If the concept is a Finding and it is an unsatisfactory finding, then we save it as the unsatFinding so we can report it as the finding,
    rather than 'normal' or 'no abnormality' when, after all other processing, we've no other findings.
    If the concept is a Site then we update 'cervixFound' or 'endomFound' as appropriate so we can report 'xxx - normal'
    rather 'no abnormality' when, after all other processing, we've no site/finding pairs.
    Parameters
        concept     - str, the additional concept  added to the mini-document
        sentenceNo  - int, the sentence in d.sentences where the mini-document was found
        start       - int, where, within the sentence the mini-document was found and the additional concept added
        j           - int, the location of another concept in this mini-document from which attributes can be copied
        negated     - str, the negation/ambiguity status of the additional concept
        reason      - str, the reason the additional code was added - for logging only
        depth       - the level of recursion
    Returns
        Nothing
    '''

    # This is recursive, so check that we haven't fallen into a recursive loop
    if depth > 5:
        logging.critical('Too many levels of recursion when adding additional solution concepts')
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Sentence hold mini-documents of concepts
    document = d.sentences[sentenceNo][6]

    # Check if this concept has an implied procedure
    if concept in d.sd.ProcedureImplied:
        thisProcedure = d.sd.ProcedureImplied[concept]
        description = d.sd.Procedure[thisProcedure]['desc']
        f.addAdditionalConcept(thisProcedure, sentenceNo, start, j, description, negated, f'procedureImplied by concept "{concept}"', depth + 1)

    # Check if this concept has an implied diagnosis
    if concept in d.sd.DiagnosisImplied:
        # logging.debug('%s is in diagnosisImplied', concept)
        for thisSite, thisFinding in d.sd.DiagnosisImplied[concept]:
            # There is an implied Site so we add it to the document
            description = d.sd.Site[thisSite]['desc']
            f.addAdditionalConcept(thisSite, sentenceNo, start, j, description, negated, f'diagnosis(Site) implied by "{concept}"', depth + 1)
            # There is an implied Finding so we add it to the document
            description = d.sd.Finding[thisFinding]['desc']
            f.addAdditionalConcept(thisFinding, sentenceNo, start, j, description, negated, f'diagnosis(Finding) implied by "{concept}"', depth + 1)

        # Mark this diagnosis implied concept as 'used'; we don't want it to participant in any other Site/Finding pair.
        # this.logger.debug('[implies diagnosis] concept (%s) at %d/%d is used', str(concept), start, j)
        document[start][j]['used'] = True

    # Check if this concept has any implied site(s) (concept can be a Finding or a Procedure, but the implied concept must be a Site)
    if concept in d.sd.SiteImplied:
        # There is one or more implied Sites so we add them to the mini-document
        for thisSite in d.sd.SiteImplied[concept]:
            description = d.sd.Site[thisSite]['desc']
            f.addAdditionalConcept(thisSite, sentenceNo, start, j, description, negated, f'siteImplied by concept "{concept}"', depth + 1)

    # Check if this concept has any implied finding(s) (concept can be a Site or a Procedure, but the implied concept must be a Finding)
    if concept in d.sd.FindingImplied:
        # There is one or more implied Findings so we add them to the mini-document
        for thisFinding in d.sd.FindingImplied[concept]:
            description = d.sd.Finding[thisFinding]['desc']
            f.addAdditionalConcept(thisFinding, sentenceNo, start, j, description, negated, f'findingImplied by concept "{concept}"', depth + 1)
    return


def addRawConcepts():
    '''
    Add any solution specific concepts to the document before negation.
    These concepts may get negated, but are candiates for inclusion in concept sets.
    Note: must be knownConcepts as we cannot change the configuration at this point
    Parameters
        None
    Returns
        Nothing
    '''

    return


def initalizeNegation():
    '''
    Initialize any local variables required for extending negation.
    this.solution is a dictionary reservered for solution variables
    Parameters
        None
    Returns
        Nothing
    '''

    d.sd.solution['lastNegation'] = None        # Last Site/Finding negation
    return


def extendNegation(sentenceNo, start, lastNegation, thisNegation):
    '''
    Extend negation or ambiguity for any Findings at this point in this sentence
    Parameters
        sentenceNo      - int, the sentence in d.sentences
        start           - int, where we are in this sentence
        lastNegation    - str, the last negation or None
        thisNegation    - str, the current negation
    Returns
        Nothing
    '''

    # logging.debug('extendNegation:%d, %d, %s, %s', sentenceNo, start, lastNegation, thisNegation)

    # Don't extend negation at the start of a sentence or if we have just crossed a but boundary
    if lastNegation is None:
        d.sd.solution['lastNegation'] = None

    # Look for Findings, Sites and Procedures at this point in the sentence
    document = d.sentences[sentenceNo][6]    # Sentences hold mini-documents
    for i, miniDoc in enumerate(document[start]):            # Step through the list of alternate concepts at this point in this sentence
        # Extend negation or ambiguity for non-adjacent, but sequential Findings, Sites and Procedures
        # (Skip things that are not a Finding, Site or Procedure)
        thisConcept = miniDoc['concept']
        if (thisConcept not in d.sd.Site) and (thisConcept not in d.sd.Finding) and (thisConcept not in d.sd.Procedure):
            continue

        # Check if the solution is extending negation or ambiguous (but not immediately ambiguous) concepts
        # If we are extending solution negation or ambiguity, then we do so to all Findings
        # but we use a non-negated/not ambigous Site or Procedure to terminate solution negation/ambiguity extension
        # If we are not extending solution negation or ambiguity, then we use a negated Finding to trigger solution negation/ambiguity extension
        if d.sd.solution['lastNegation'] is not None:    # Extending negation/ambiguity
            if thisConcept in d.sd.Finding:            # All Findings become negated or ambiguous
                logging.info('Extending negation or amgiguity to %s - %s [%d/%d]', thisConcept, miniDoc['description'], start, i)
                miniDoc['negation'] = d.sd.solution['lastNegation']        # Negate this Finding or make it ambiguous
            else:        # Not a Finding - must be a Site or Procedure
                # A Site or Procedure that isn't negated or ambiguous terminates solution negation/ambiguity extension
                if miniDoc['negation'] == '0':
                    d.sd.solution['thisNegation'] = None            # Turn off negations or ambiguity
        elif thisConcept in d.sd.Finding:            # Not extending negation/ambiguity - see if we should start
            # Negated or ambiguous Findings trigger solution negation/ambituity extension.
            # Check if this is a negated or ambiguous (but not immediately ambiguous) Finding
            if (miniDoc['negation'] in ['1','2']):
                d.sd.solution['thisNegation'] = miniDoc['negation']        # Turn on solution negations or ambiguity
    return


def higherConceptFound(higherConcept):
    '''
    Check if this higher concept, which has just been found, implies that any of the concepts in the set should be marked as 'used'
    Parameters
        higherConcept   - str, the higher concept being check for implications
    Returns
        markUsed        - boolean, True means higher concept implies related concepts should be marked as used
    '''

    if (higherConcept in d.sd.DiagnosisImplied) or (higherConcept in d.sd.Finding):
        return True
    else:
        return False


def setConcept(thisHigherConcept, thisConcept):
    '''
    Check if this concept, which has just been found in this higher concept set, set should be marked as 'used'
    Parameters
        higherConcept   - str, the higher concept being check for implications
    Returns
        markUsed        - boolean, True means higher concept implies related concepts should be marked as used
    '''

    if (thisHigherConcept in d.sd.DiagnosisImplied) or (thisHigherConcept in d.sd.Finding):
        if (thisConcept in d.sd.Site) or (thisConcept in d.sd.Finding):
            return True
        else:
            return False
    else:
        return False


def addSolutionConcepts():
    '''
    Add any solution specific concepts to the document after negation extension, but before sentence or document list negation.
    These concepts may get negated, if they are in sentence_negation_lists or document_negation_lists, but are candidates for concept sets
    Note: sentence_negation_lists and document_negation_lists are intended for negating findings, so you can add sites at this point
        if you add findings, then sentence_negation_lists and document_negation_list become negation of things both actual, and implied.
    Note: must be knownConcepts as we cannot change the configuration at this point
    '''

    return


def addFinalConcepts():
    '''
    Add any solution specific concepts to the document. We have done all negation and all concept set checking.
    So these concepts are not candidates for inclusion in concept sets.
    Note: must be knownConcepts as we cannot change the configuration at this point
    Note: for sites we must check that the concept to be added doesn't already exist in this document at this point
    Note: for diagnosies the concept will have been marked as 'used' when the site and finding were added
    '''

    # Walk throught the document and add any sites or findings implied by MetaThesaurus concepts in the document
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
        document = sentence[6]    # Sentences hold mini-documents
        for start in sorted(document, key=int):        # We step through all concepts, in sequence across this sentence
            for j in range(len(document[start])):            # Step through the list of alternate concepts at this point in this sentence
                concept = document[start][j]['concept']        # This concept

                if document[start][j]['used']:        # Skip used concepts [only Findings get 'used']
                    continue

                if document[start][j]['negation'] != '0':    # Skip negated and ambiguous concepts
                    continue

                negated =  document[start][j]['negation']

                # Check if this concept has an implied procedure
                if concept in d.sd.ProcedureImplied:
                    thisProcedure = d.sd.ProcedureImplied[concept]
                    description = d.sd.Procedure[thisProcedure]['desc']
                    f.addAdditionalConcept(thisProcedure, sentenceNo, start, j, description, negated, f'procedureImplied by concept "{concept}"', 0)

                # Check if this concept has an implied diagnosis
                if concept in d.sd.DiagnosisImplied:
                    # logging.debug('%s is in diagnosisImplied', concept)
                    for thisSite, thisFinding in d.sd.DiagnosisImplied[concept]:
                        # There is an implied Site so we add it to the document
                        description = d.sd.Site[thisSite]['desc']
                        f.addAdditionalConcept(thisSite, sentenceNo, start, j, description, negated, f'diagnosis(Site) implied by "{concept}"', 0)
                        # There is an implied Finding so we add it to the document
                        description = d.sd.Finding[thisFinding]['desc']
                        f.addAdditionalConcept(thisFinding, sentenceNo, start, j, description, negated, f'diagnosis(Finding) implied by "{concept}"', 0)
                    # Mark this diagnosis implied concept as 'used'; we don't want it to participant in any other Site/Finding pair.
                    # this.logger.debug('[implies diagnosis] concept (%s) at %d/%d is used', str(concept), start, j)
                    document[start][j]['used'] = True

                # Check if this concept has any implied site(s) (concept can be a Finding or a Procedure, but the implied concept must be a Site)
                if concept in d.sd.SiteImplied:
                    # There is one or more implied Sites so we add them to the mini-document
                    for thisSite in d.sd.SiteImplied[concept]:
                        description = d.sd.Site[thisSite]['desc']
                        f.addAdditionalConcept(thisSite, sentenceNo, start, j, description, negated, f'siteImplied by concept "{concept}"', 0)

                # Check if this concept has any implied finding(s) (concept can be a Site or a Procedure, but the implied concept must be a Finding)
                if concept in d.sd.FindingImplied:
                    # There is one or more implied Findings so we add them to the mini-document
                    for thisFinding in d.sd.FindingImplied[concept]:
                        description = d.sd.Finding[thisFinding]['desc']
                        f.addAdditionalConcept(thisFinding, sentenceNo, start, j, description, negated, f'findingImplied by concept "{concept}"', 0)
    return


def complete():
    '''
    Complete any histopathology specific coding
    '''

    # Perform any additional tasks after additional concepts (addSolutionConcepts())
    # and final concepts(addFInalConcepts()) have been added bu before analysis begins

    return
