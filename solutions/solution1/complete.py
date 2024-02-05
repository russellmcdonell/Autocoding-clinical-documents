# pylint: disable=line-too-long, broad-exception-caught
'''
This is the NCSR histopathology autocoding coding completion module
This code share data/configuration with the analyze module via the shared data structure solData
'''

import os
import sys
import logging
from openpyxl import load_workbook
from openpyxl import utils
import re



def configure(wb):
    '''
    Read in any histopathology specific worksheets from workbook wb
    '''

    configConcepts = set()        # The set of additional known concepts

    # Return the additional known concepts
    return configConcepts


# ToDO - check the remainder of this code

def requireConcept(this, thisConcept, isNegated, partOfSpeech, isHistory, sentenceNo, start, length, theText):
    '''
Check if the solution requires this concept
For histopathology, the '?' character is used to indicate that the following may be present.
But this is a state that is neither postive, nor negative or ambiguous.
It is a suggestion of a direction for further testing, as in "? stomach ulcer"
As such, then concept following the '?' can be discarded
    '''

    if partOfSpeech in ['NN', 'NNP', 'NNS', 'NNPS', 'JJ', 'JJR', 'JJS', 'RB', 'RBR', 'RBS'] :
        # this.logger.debug('noun, adjective or adverb at %d[%s]', start, str(theText))
        # Check if this is just a question, not an answer - the ? will always be the last character on the previous line
        if sentenceNo > 0 :        # Start by looking for ' ? xxxx'
            if re.search(r'\s\?\s*$', this.sentences[sentenceNo - 1][4], flags=re.IGNORECASE) != None :
                # this.logger.debug('requiredConcept:ignored as query term')
                return False
    return True


def checkHistory(this, inHistory, text):
    '''
Check for any solution specific markers that indicate the start or end of a section of history
in the current sentence or an preceeding sentence (when combined with information from this sentence).
Return the number of sentences ago that history changed (or -1 if no change detected)
and the number of characters to move on in this sentence
Here text is the current sentence.

End of History
no known triggers

Start of History
Histopathologies sometimes use hanging paragraphs. Sometimes the section heading 'CLINICAL INFORMATION',
[which is a history marker] gets split over two lines.
    '''

    if inHistory:        # We are in history - check to see if we came have fallen out of this history section
        return (-1, None)
    else:                # We are not in history - check to see if that we have fallen into a new history section
        # Checking if this sentence contains 'INFORMATION:' and any of the three previous sentences starts with 'CLINICAL'
        clinicalFound = -1
        search = re.search(r'\b' + 'INFORMATION\s*:', text)
        if search != None :
            clinicalFound = -1
            if (len(this.sentences) == 0) and (re.search(r'^\s*CLINICAL', text) != None) :
                clinicalFound = 0
            if (len(this.sentences) > 0) and (re.search(r'^\s*CLINICAL', this.sentences[-1][4]) != None) :
                clinicalFound = 1
            elif (len(this.sentences) > 1) and (re.search(r'^\s*CLINICAL', this.sentences[-2][4]) != None) :
                clinicalFound = 2
            elif (len(this.sentences) > 2) and (re.search(r'^\s*CLINICAL', this.sentences[-3][4]) != None) :
                clinicalFound = 3
            elif (len(this.sentences) > 3) and (re.search(r'^\s*CLINICAL', this.sentences[-4][4]) != None) :
                clinicalFound = 4
        if clinicalFound == -1:
            return (-1, None)
        else:
            return (clinicalFound, len(search.group()))


def addAdditionalConcept(this, solData, concept, sentenceNo, start, j, history, description, reason) :
    '''
Add an additional concept to the mini-document for this sentence because an implied concept has been found.
The additional concept will be added at position 'start', by copying most of the details from the jth concept at start
If the concept is a Finding and it is an unsatisfactory finding, then we save it as the unsatFinding so we can report it as the finding,
rather than 'normal' or 'no abnormality' when, after all other processing, we've found nothing and the grid is empty.
If the concept is a Site then we update 'cervixFound' or 'endomFound' as appropriate so we can report 'xxx - normal'
rather 'no abnormality' when, after all other processing, we've found nothing and the grid is empty.
    '''

    this.logger.info('Adding additional concept (%s) to sentence[%d] at %d [%s]', str(concept), sentenceNo, start, reason)
    document = this.sentences[sentenceNo][6]    # Sentences hold mini-documents
    # Check that this concept doesn't already exist in the document at this point
    for k in range(len(document[start])):
        if concept == document[start][k]['concept']:
            break
    else:
        document[start].append({})
        document[start][-1]['concept'] = concept
        document[start][-1]['negation'] = '0'
        document[start][-1]['text'] = document[start][j]['text']
        document[start][-1]['length'] = document[start][j]['length']
        document[start][-1]['history'] = history
        document[start][-1]['partOfSpeech'] = 'NN'
        document[start][-1]['used'] = False
        document[start][-1]['description'] = description

    # Check if this concept has an implied procedure
    if concept in solData.ProcedureImplied :
        thisProcedure = solData.ProcedureImplied[concept]
        description = solData.Procedure[thisProcedure]['desc']
        history = document[start][j]['history']
        addAdditionalConcept(this, solData, thisProcedure, sentenceNo, start, j, history, description, 'procedureImplied by concept %s' % (concept))

    # Check if this concept has an implied diagnosis
    if concept in solData.DiagnosisImplied :
        # this.logger.debug('%s is in diagnosisImplied', str(concept))
        for thisSite, thisFinding in solData.DiagnosisImplied[concept]:
            # There is an implied Site so we add it to the document
            description = solData.Site[thisSite]['desc']
            addAdditionalConcept(this, solData, thisSite, sentenceNo, start, j, history, description, 'diagnosis(Site) implied by %s' % (concept))
            # There is an implied Finding so we add it to the document
            description = solData.Finding[thisFinding]['desc']
            addAdditionalConcept(this, solData, Finding, sentenceNo, start, j, history, description, 'diagnosis(Finding) implied by %s' % (concept))
        # Mark this diagnosis implied concept as 'used'; we don't want it to participant in any other Site/Finding pair.
        # this.logger.debug('[implies diagnosis] concept (%s) at %d/%d is used', str(concept), start, j)
        document[start][j]['used'] = True

    # Check if this concept has any implied site(s) (concept can be a Finding or a Procedure, but the implied concept must be a Site)
    if concept in solData.SiteImplied :
        # There is one or more implied Sites so we add them to the mini-document
        for thisSite in solData.SiteImplied[concept]:
            description = solData.Site[thisSite]['desc']
            addAdditionalConcept(this, solData, thisSite, sentenceNo, start, j, history, description, 'siteImplied by concept %s' % (concept))

    # Check if this concept has any implied finding(s) (concept can be a Site or a Procedure, but the implied concept must be a Finding)
    if concept in solData.FindingImplied :
        # There is one or more implied Findings so we add them to the mini-document
        for thisFinding in solData.FindingImplied[concept]:
            description = solData.Finding[thisFinding]['desc']
            addAdditionalConcept(this, solData, thisFinding, sentenceNo, start, j, history, description, 'findingImplied by concept %s' % (concept))

    return


def addRawConcepts(this, solData):
    '''
Add any solution specific concepts to the document before negation.
These concepts may get negated, but are candiates for inclusion in concept sets.
Note: must be knownConcepts as we cannot change the configuration at this point
    '''

    return


def initalizeNegation(this):
    '''
Initialize any local variables required for extending negation.
this.solution is a dictionary reservered for solution variables
    '''

    this.solution['lastNegation'] = None        # Last Site/Finding negation
    return


def extendNegation(this, solData, sentenceNo, start, lastNegation, thisNegation):
    '''
Extend negation or ambiguity for any Findings at this point in this sentence
    '''

    # Don't extend negation at the start of a sentence or if we have just crossed a but boundary
    if lastNegation is None:
        this.solution['lastNegation'] = None

    # Look for Findings, Sites and Procedures at this point in the sentence
    document = this.sentences[sentenceNo][6]    # Sentences hold mini-documents
    for i in range(len(document[start])) :            # Step through the list of alternate concepts at this point in this sentence
        # Extend negation or ambiguity for non-adjacent, but sequential Findings, Sites and Procedures
        # (Skip things that are not a Finding, Site or Procedure)
        concept = document[start][i]['concept']
        if (concept not in solData.Site) and (concept not in solData.Finding) and (concept not in solData.Procedure) :
            continue

        # Check if the solution is extending negation or ambiguous (but not immediately ambiguous) concepts
        # If we are extending solution negation or ambiguity, then we do so to all Findings
        # but we use a non-negated/not ambigous Site or Procedure to terminate solution negation/ambiguity extension
        # If we are not extending solution negation or ambiguity, then we use a negated Finding to trigger solution negation/ambiguity extension
        if this.solution['lastNegation'] is not None:    # Extending negation/ambiguity
            if concept in solData.Finding:            # All Findings become negated or ambiguous
                this.logger.info('Extending negation or amgiguity to %s - %s [%d/%d]', concept, str(document[start][i]['description']), start, i)
                document[start][i]['negation'] = this.solution['lastNegation']        # Negate this Finding or make it ambiguous
            else:        # Not a Finding - must be a Site or Procedure
                # A Site or Procedure that isn't negated or ambiguous terminates solution negation/ambiguity extension
                if (document[start][i]['negation'] == '0') :
                    this.solution['thisNegation'] = None            # Turn off negations or ambiguity
        elif concept in solData.Finding:            # Not extending negation/ambiguity - see if we should start
            # Negated or ambiguous Findings trigger solution negation/ambituity extension.
            # Check if this is a negated or ambiguous (but not immediately ambiguous) Finding
            if (document[start][i]['negation'] in ['1','2']) :
                this.solution['thisNegation'] = document[start][i]['negation']        # Turn on solution negations or ambiguity
    return


def higherConceptFound(this, solData, higherConcept):
    '''
Check if this higher concept, which has just been found, implies that any of the concepts in the set should be marked as 'used'
    '''
 
    if (higherConcept in solData.DiagnosisImplied) or (higherConcept in solData.Finding):
        return True
    else:
        return False


def setConcept(this, solData, higherConcept, thisConcept):
    '''
Check if this concept, which has just been found in this higher concept set, set should be marked as 'used'
    '''
 
    if (higherConcept in solData.DiagnosisImplied) or (higherConcept in solData.Finding):
        if (thisConcept in solData.Site) or (thisConcept in solData.Finding):
            return True
        else:
            return False
    else:
        return False


def foundConcept(this, solData):
    '''
Check if this concept in the found set should be marked as 'used'
    '''
 
    if concept in solData.Finding:
        return True
    else:
        return False


def addSolutionConcepts(this, solData):
    '''
Add any solution specific concepts to the document after negation extension, but before sentence or document list negation.
These concepts may get negated, if they are in sentence_negation_lists or document_negation_lists, but are candidates for concept sets
Note: sentence_negation_lists and document_negation_lists are intended for negating findings, so you can add sites at this point
      if you add findings, then sentence_negation_lists and document_negation_list become negation of things both actual, and implied.
Note: must be knownConcepts as we cannot change the configuration at this point
    '''

    return


def addFinalConcepts(this, solData):
    '''
Add any solution specific concepts to the document. We have done all negation and all concept set checking.
So these concepts are not candidates for inclusion in concept sets.
Note: must be knownConcepts as we cannot change the configuration at this point
Note: for sites we must check that the concept to be added doesn't already exist in this document at this point
Note: for diagnosies the concept will have been marked as 'used' when the site and finding were added
    '''

    # Walk throught the document and add any sites or findings implied by MetaThesaurus concepts in the document
    for sentenceNo in range(len(this.sentences)) :            # Step through each sentence
        sentence = this.sentences[sentenceNo]
        sentenceStart = sentence[2]
        sentenceLength = sentence[3]
        document = this.sentences[sentenceNo][6]    # Sentences hold mini-documents
        for start in sorted(document, key=int) :        # We step through all concepts, in sequence across this sentence
            for j in range(len(document[start])) :            # Step through the list of alternate concepts at this point in this sentence
                concept = document[start][j]['concept']        # This concept

                if document[start][j]['used'] == True :        # Skip used concepts [only Findings get 'used']
                    continue

                if document[start][j]['negation'] != '0' :    # Skip negated and ambiguous concepts
                    continue

                history =  document[start][j]['history']

                # Check if this concept has an implied procedure
                if concept in solData.ProcedureImplied :
                    thisProcedure = solData.ProcedureImplied[concept]
                    description = solData.Procedure[thisProcedure]['desc']
                    history = document[start][j]['history']
                    addAdditionalConcept(this, solData, thisProcedure, sentenceNo, start, j, history, description, 'procedureImplied by concept %s' % (concept))

                # Check if this concept has an implied diagnosis
                if concept in solData.DiagnosisImplied :
                    # this.logger.debug('%s is in diagnosisImplied', str(concept))
                    for thisSite, thisFinding in solData.DiagnosisImplied[concept]:
                        # There is an implied Site so we add it to the document
                        description = solData.Site[thisSite]['desc']
                        addAdditionalConcept(this, solData, thisSite, sentenceNo, start, j, history, description, 'diagnosis(Site) implied by %s' % (concept))
                        # There is an implied Finding so we add it to the document
                        description = solData.Finding[thisFinding]['desc']
                        addAdditionalConcept(this, solData, thisFinding, sentenceNo, start, j, history, description, 'diagnosis(Finding) implied by %s' % (concept))
                    # Mark this diagnosis implied concept as 'used'; we don't want it to participant in any other Site/Finding pair.
                    # this.logger.debug('[implies diagnosis] concept (%s) at %d/%d is used', str(concept), start, j)
                    document[start][j]['used'] = True

                # Check if this concept has any implied site(s) (concept can be a Finding or a Procedure, but the implied concept must be a Site)
                if concept in solData.SiteImplied :
                    # There is one or more implied Sites so we add them to the mini-document
                    for thisSite in solData.SiteImplied[concept]:
                        description = solData.Site[thisSite]['desc']
                        addAdditionalConcept(this, solData, thisSite, sentenceNo, start, j, history, description, 'siteImplied by concept %s' % (concept))

                # Check if this concept has any implied finding(s) (concept can be a Site or a Procedure, but the implied concept must be a Finding)
                if concept in solData.FindingImplied :
                    # There is one or more implied Findings so we add them to the mini-document
                    for thisFinding in solData.FindingImplied[concept]:
                        description = solData.Finding[thisFinding]['desc']
                        addAdditionalConcept(this, solData, thisFinding, sentenceNo, start, j, history, description, 'findingImplied by concept %s' % (concept))
    return


def complete(this, solData):
    '''
Complete any histopathology specific coding
    '''

    # Perform any additional tasks after additional concepts (addSolutionConcepts())
    # and final concepts(addFInalConcepts()) have been added bu before analysis begins

    return


