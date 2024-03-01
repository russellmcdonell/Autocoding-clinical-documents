# pylint: disable=line-too-long, broad-exception-caught, invalid-name, too-many-lines, too-many-nested-blocks
# pylint: disable=too-many-locals, too-many-branches, too-many-statements, unused-import, unnecessary-pass

'''
This is the histopathology autocoding analysis module
'''

import sys
import os
import logging
import functions as f
import excelFunctions as excel
import data as d


def configure(wb):
    '''
    Configure the analysis
    Read in any histopathology specific worksheets from workbook wb
    Parameters
        wb              - an openpyxl workbook containing analyze configuration data
    Returns
        configConcepts  - set(), all concepts detected when processing the workbook
    '''

    configConcepts = set()        # The set of additional known concepts

    # Read in the AIHW Procedure and Finding codes and descriptions
    requiredColumns = ['AIHW', 'Description']
    d.sd.AIHWprocedure = excel.loadSimpleDictionarySheet(wb, 'analyze', 'AIHW Procedure', requiredColumns, 0)
    d.sd.AIHWfinding = excel.loadSimpleDictionarySheet(wb, 'analyze', 'AIHW Finding', requiredColumns, 0)

    # Read in and check the SNOMED CT Sites
    requiredColumns = ['MetaThesaurusID', 'Site', 'SubSite']
    d.sd.Site = excel.loadDictionaryDictionarySheet(wb, 'analyze', 'Site', requiredColumns)
    for concept, row in d.sd.Site.items():
        if concept in configConcepts:
            logging.critical('Attempt to redefine site(%s)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        # Check that this Site is a defined SNOMED_CT code
        if concept not in d.solutionMetaThesaurus:
            logging.critical('Site(%s) in worksheet(Site) in workbook(analyze) not in the SolutionMetaThesaurus workbook', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if d.solutionMetaThesaurus[concept]['Source'] != "SNOMEDCT_US":
            logging.critical('Site(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        configConcepts.add(concept)
        d.sd.Site[concept]['snomed_ct'] = d.solutionMetaThesaurus[concept]['Source_code']
        d.sd.Site[concept]['desc'] = d.solutionMetaThesaurus[concept]['description']
        # Next validate site and subsite
        if row['Site'] not in ['Cervix', 'Vagina', 'Other', 'Not_Stated']:
            logging.critical('Site(%s) in worksheet(Site) in workbook(analyze) not in "cervix", "vagina", "other" or "notStated"', row['Site'])
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if row['SubSite'] not in ['Cervix', 'Vagina', 'endom', 'Other', 'Not_Stated']:
            logging.critical('SubSite(%s) in worksheet(Site) in workbook(analyze) not in "Cervix", "Vagina", "endom", "Other" or "Not_Stated"',
                             row['SubSite'])
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # Now check that we have configurations for a few, fixed MetaThesaurus Site codes
    if d.sd.cervixUteri not in d.sd.Site:
        logging.critical('Missing definition for concept "%s" in worksheet(Site) in workbook(analyze)', d.sd.cervixUteri)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if d.sd.endomStructure not in d.sd.Site:
        logging.critical('Missing definition for concept "%s" in worksheet(Site) in workbook(analyze)', d.sd.endomStructure)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Read in and check the Findings
    requiredColumns = ['MetaThesaurusID', 'Cervix', 'Vagina', 'Other', 'Not Stated']
    d.sd.Finding = excel.loadDictionaryDictionarySheet(wb, 'analyze', 'Finding', requiredColumns)
    concepts = set()
    for concept, row in d.sd.Finding.items():
        if concept in configConcepts:
            logging.critical('Attempt to redefine finding(%s)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        # Check that this Finding is a defined SNOMED_CT code
        if concept not in d.solutionMetaThesaurus:
            logging.critical('Finding in worksheet(Site) in workbook(analyze) not in the SolutionMetaThesaurus workbook')
            logging.shutdown()
            sys.stdout.flush()
            sys.exit(d.EX_CONFIG)
        if d.solutionMetaThesaurus[concept]['Source'] != "SNOMEDCT_US":
            logging.critical('Finding(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        configConcepts.add(concept)
        d.sd.Finding[concept]['snomed_ct'] = d.solutionMetaThesaurus[concept]['Source_code']
        d.sd.Finding[concept]['desc'] = d.solutionMetaThesaurus[concept]['description']

        # Next validate Cervix, Vagina, Other and Not Stated
        # We have to map MetaThesaurus codes to AIHW S/E/O codes, based upon 'site'
        if row['Cervix'] not in d.sd.AIHWfinding:
            logging.critical('Cervix code(%s) in worksheet(Finding) in workbook(analyze) is not a valid AIHW Finding code', row['Cervix'])
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if row['Vagina'] not in d.sd.AIHWfinding:
            logging.critical('Vagina code(%s) in worksheet(Finding) in workbook(analyze) is not a valid AIHW Finding code', row['Vagina'])
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if row['Other'] not in d.sd.AIHWfinding:
            logging.critical('Other code(%s) in worksheet(Finding) in workbook(analyze) is not a valid AIHW Finding code', row['Other'])
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if row['Not_Stated'] not in d.sd.AIHWfinding:
            logging.critical('Not Stated code(%s) in worksheet(Finding) in workbook(analyze) is not a valid AIHW Finding code', row.Not_Stated)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # Now check that we have configurations for a few, fixed MetaThesaurus Finding codes
    if d.sd.normalCervixCode not in d.sd.Finding:
        logging.critical('Missing definition for concept "%s" in worksheet(Finding) in workbook(analyze)', d.sd.normalCervixCode)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if d.sd.normalEndomCode not in d.sd.Finding:
        logging.critical('Missing definition for concept "%s" in worksheet(Finding) in workbook(analyze)', d.sd.normalEndomCode)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if d.sd.noAbnormality not in d.sd.Finding:
        logging.critical('Missing definition for concept "%s" in worksheet(Finding) in workbook(analyze)', d.sd.noAbnormality)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Read in and check the Procedures
    requiredColumns = ['MetaThesaurusID', 'Cervix', 'Vagina', 'Other', 'Not Stated', 'Cervix Rank', 'Vagina Rank', 'Other Rank', 'Not Stated Rank']
    d.sd.Procedure = excel.loadDictionaryDictionarySheet(wb, 'analyze', 'Procedure', requiredColumns)
    for concept, row in d.sd.Procedure.items():
        if concept in configConcepts:
            logging.critical('Attempt to redefine procedure(%s)', str(concept))
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        # Check that this Procedure is a defined SNOMED_CT code
        if concept not in d.solutionMetaThesaurus:
            logging.critical('Procedure(%s) in worksheet(Site) in workbook(analyze) not in sheet SolutionMetaThesaurus', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if d.solutionMetaThesaurus[concept]['Source'] != "SNOMEDCT_US":
            logging.critical('Procedure(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        configConcepts.add(concept)
        d.sd.Procedure[concept]['snomed_ct'] = d.solutionMetaThesaurus[concept]['Source_code']
        d.sd.Procedure[concept]['desc'] = d.solutionMetaThesaurus[concept]['description']

        # Next validate Cervix, Vagina, Other, Not Stated, Cervix Rank, Vagina Rank, Other Rank, Not Stated Rank
        # We have to map SNOMED_CT procedure codes to AIHW procedure codes,
        # but then only report the one most significant procedure (highest rank)
        if (row['Cervix'] not in d.sd.AIHWprocedure) and (row['Cervix'] != '99'):
            logging.critical('Cervix code(%s) in worksheet(Procedure) in workbook(analyze) is not a valid AIHW Procedure code', row['Cervix'])
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if (row['Vagina'] not in d.sd.AIHWprocedure) and (row['Vagina'] != '99'):
            logging.critical('Vagina code(%s) in worksheet(Procedure) in workbook(analyze) is not a valid AIHW Procedure code', row['Vagina'])
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if (row['Other'] not in d.sd.AIHWprocedure) and (row['Other'] != '99'):
            logging.critical('Other code(%s) in worksheet(Procedure) in workbook(analyze) is not a valid AIHW Procedure code', row.Other)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if (row['Not_Stated'] not in d.sd.AIHWprocedure) and (row['Not_Stated'] != '99'):
            logging.critical('Not Stated code(%s) in worksheet(Procedure) in workbook(anallyze) is not a valid AIHW Procedure code', row['Not_Stated'])
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

    # THE FOLLOWING ARE 'complete' DATA STRUCTURES - data structures required by the 'complete' module,
    # but the validity of the 'complete' configuration data depends upon 'analysis' data.
    # Hence they cannot be loaded until after the preceeding 'analyze' worksheets.

    # Read in and chedk the Site implied concept sets
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID']
    d.sd.SiteImplied = excel.loadDictionarySetSheet(wb, 'analyze', 'site implied', requiredColumns)
    isDefined = set()
    for concept, row in d.sd.SiteImplied.items():
        if concept in isDefined:
            logging.critical('Attempt to redefine list of implied sites for concept(%s) in worksheet(site impllied) in workbook(analyze)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        isDefined.add(concept)
        for implied in row:
            if implied not in d.sd.Site:
                logging.critical('Attempt to define an implied Site(%s) for concept(%s) in worksheet(site implied) in workbook(analyze), but (%s) is not defined as a Site',
                                 implied, concept, implied)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)

    # Read in and chedk the Finding implied concept sets
    requiredColumns = ['MetaThesaurusID', 'HistopathologyFindingID']
    d.sd.FindingImplied = excel.loadDictionarySetSheet(wb, 'analyze', 'finding implied', requiredColumns)
    isDefined = set()
    for concept, row in d.sd.FindingImplied.items():
        if concept in isDefined:
            logging.critical('Attempt to redefine list of implied sites for concept(%s) in worksheet(site impllied) in workbook(analyze)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        isDefined.add(concept)
        for implied in row:
            if implied not in d.sd.Finding:
                logging.critical('Attempt to define an implied Finding(%s) for concept(%s) in worksheet(site implied) in workbook(analyze), but (%s) is not defined as a Finding',
                                 implied, concept, implied)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)

    # Read in and check the Site restricted Finding concepts
    # These Findings can only be paired with one of these sites
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteIDs']
    d.sd.SiteRestrictions = excel.loadDictionarySetSheet(wb, 'analyze', 'site restricted', requiredColumns)
    # logging.debug('analyze() - SiteRestrictions (%s)', d.sd.SiteRestrictions)
    isDefined = set()
    for concept, row in d.sd.SiteRestrictions.items():
        if concept in isDefined:
            logging.critical('Attempt to redefine site restrictions list for finding(%s) in worksheet(site restricted) in workbook(analyze)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if concept not in d.sd.Finding:
            logging.critical('Attempt to define an restriction on Finding(%s) in worksheet(site restricted) in workbook(analyze), but (%s) is not defined as a Finding',
                             concept, concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        isDefined.add(concept)
        for restriction in row:
            if restriction not in d.sd.Site:
                logging.critical('Attempt to define a restriction of Site(%s) for Finding(%s) in worksheet(site restricted) in workbook(analyze), but (%s) is not defined as a Site',
                                 restriction, concept, restriction)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)

    # Read in and check the Site impossible Finding concepts
    # These Findings can never be paired with one of these Sites
    d.sd.SiteImpossible = excel.loadDictionarySetSheet(wb, 'analyze', 'site impossible', requiredColumns)
    isDefined = set()
    for concept, row in d.sd.SiteImpossible:
        if concept in d.sd.SiteImpossible:
            logging.critical('Attempt to redefine site impossible list for finding(%s) in worksheet(site impossible) in workbook(analyze)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if concept not in d.sd.Finding:
            logging.critical('Attempt to define an impossible Site for Finding(%s) in worksheet(site impossible) in workbook(analyze), but (%s) is not defined as a Finding',
                             concept, concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        isDefined.add(concept)
        for restriction in row:
            if restriction not in d.sd.Site:
                logging.critical('Attempt to define an impossible Site(%s) for Finding(%s) in worksheet(site impossible) in workbook(analyze), but (%s) is not defined as a Site',
                                 restriction, concept, restriction)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)

    # Read in and check the Site likelyhood Finding concepts
    # These Findings can be paired with anyone of these sites, but if they are, only one pairing
    # should be included in the analysis, and it should be the pairing with the highest rank
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID|rank']
    d.sd.tempDict = excel.loadDictionarySetSheet(wb, 'analyze', 'site likely', requiredColumns)
    d.sd.SiteRank = {}
    for concept, row in d.sd.tempDict.items():
        if concept not in d.sd.Finding:
            logging.critical('Attempt to define an likelyhood ranking for Finding(%s) in worksheet(site likely) in workbook(analyze), but (%s) is not defined as a Finding',
                             concept, concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if concept in d.sd.SiteRank:
            logging.critical('Attempt to redefine site likelyhood value(s) for finding(%s) in worksheet(site likely) in workbook(analyze)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.SiteRank[concept] = {}
        for likelyhood in row:
            bits = likelyhood.split('|')
            if len(bits) != 2:
                logging.critical('Site|likelyhood (%s) for concept(%s) in worksheet(site likely) in workbook(analyze) is incorrectly formatted',
                                     likelyhood, concept)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            if bits[0] not in d.sd.Site:
                logging.critical('Attempt to define an likelyhood for Site(%s) for Finding(%s) in worksheet(site likely) in workbook(analyze), but (%s) is not defined as a Site',
                                 bits[0], concept, bits[0])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            try:
                rank = int(bits[1])
            except ValueError:
                logging.critical('Attempt to define an likelyhood for Site(%s) for Finding(%s) in worksheet(site likely) in workbook(analyze), but likelyhodd(%s) is not defined as a valid value',
                                 bits[0], concept, bits[1])
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            if bits[0] in d.sd.SiteRank[concept]:
                logging.critical('Attempt to redefine likelyhood value for Site(%s) for Finding(%s) in worksheet(site likely) in workbook(analyze) from(%d) to (%d)',
                                 bits[0], concept, d.sd.SiteRank[concept][bits[0]], rank)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            d.sd.SiteRank[concept][bits[0]] = rank

    # Read in and check the Site default Finding concepts
    # These are the Sites to be paired with these Finding concepts if they remain unpaired.
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID']
    d.sd.SiteDefault = excel.loadDictionaryDictionarySheet(wb, 'analyze', 'site default', requiredColumns)
    isDefined = set()
    for concept in d.sd.SiteDefault:
        default = d.sd.SiteDefault[concept]
        if concept in isDefined:
            logging.critical('Attempt to redefine default site for finding(%s) in worksheet(site default) in workbook(analyze) from (%s) to (%s)',
                             concept, d.sd.SiteDefault[concept], default)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if concept not in d.sd.Finding:
            logging.critical('Attempt to define a default Site for Finding(%s) in worksheet(site default) in workbook(analyze), but (%s) is not defined as a Finding',
                             concept, concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if default not in d.sd.Site:
            logging.critical('Attempt to define a default Site(%s) for Fining(%s), but (%s) is not defined as a Site',
                                 str(default), str(concept), str(default))
            logging.shutdown()
            sys.stdout.flush()
        isDefined.add(concept)

    # Read in the concepts which imply a Diagnosis (Site/Finding pairs)
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID', 'HistopathologyFindingID']
    d.sd.tempDict = excel.loadDictionaryDictionarySheet(wb, 'analyze', 'diagnosis implied', requiredColumns)
    for diagnosis in d.sd.tempDict:
        site = d.sd.tempDict[diagnosis]['HistopathologySiteID']
        finding = d.sd.tempDict[diagnosis]['HistopathologyFindingID']
        if site not in d.sd.Site:
            logging.critical('Attempt to define an implied diagnosis with Site(%s) for concept(%s) in worksheet(diagnosis implied) in workbook(analyze), but (%s) is not defined as a Site',
                             site, concept, site)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if finding not in d.sd.Finding:
            logging.critical('Attempt to define an implied diagnosis with Finding(%s) for concept(%s) in worksheet(diagnosis implied) in workbook(analyze), but (%s) is not defined as a Finding',
                             finding, concept, finding)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if diagnosis not in d.sd.DiagnosisImplied:
            d.sd.DiagnosisImplied[diagnosis] = []
        d.sd.DiagnosisImplied[diagnosis].append((site, finding))
        configConcepts.add(diagnosis)

    # Read in and check the concepts that imply a procedure the implied procedure
    requiredColumns = ['MetaThesaurusID', 'HistopathologyProcedureID']
    d.sd.ProcedureImplied = excel.loadDictionaryDictionarySheet(wb, 'analyze', 'procedure implied', requiredColumns)
    isDefined = set()
    for concept in d.sd.ProcedureImplied:
        procedure = d.sd.ProcedureImplied[concept]
        if concept in isDefined:
            logging.critical('Attempt to redefine implied procedure for concept(%s) in worksheet(procedure implied) in workbook(analyze) from (%s) to (%s)',
                             concept, d.sd.ProcedureImplied[concept], procedure)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if procedure not in d.sd.Procedure:
            logging.critical('Attempt to define an implied procedure(%s) for concept(%s) in worksheet(procedure implied) in workbook(analyze), but (%s) is not defined as a Procedure',
                             procedure, concept, procedure)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        isDefined.add(concept)
        configConcepts.add(concept)

    # Read in and check the Site/Finding concept pairs that define a procedure concept and that procedure concept
    requiredColumns = ['HistopathologyProcedureID', 'HistopathologySiteID', 'HistopathologyFindingID']
    d.sd.tempList = excel.loadSimpleSheet(wb, 'analyze', 'procedure defined', requiredColumns)
    for row in d.sd.tempList:
        procedure = row[0]
        site = row[1]
        finding = row[2]
        if (site, finding) in d.sd.ProcedureDefined:
            logging.critical('Attempt to redefine procedureDefined diagnosis(%s,%s) in worksheet(procedure defined) in workbook(analyze) from (%s) to (%s)',
                             site, finding, d.sd.ProcedureDefined[(site, finding)], procedure)
            logging.shutdown()
            sys.exit(d.EX_IOERR)
        if site not in d.sd.Site:
            logging.critical('Attempt to define a procedure defined diagnosis(%s) with Site(%s) in worksheet(procedure defined) in workbook(analyze) but (%s) is not defined as a Site',
                             procedure, site, site)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if finding not in d.sd.Finding:
            logging.critical('Attempt to define a procedure defined diagnosis(%s) with Finding(%s) in worksheet(procedure defined) in workbook(analyze) but (%s) is not defined as a Finding',
                             concept, finding, finding)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.ProcedureDefined[(site, finding)] = procedure
        configConcepts.add(procedure)

    # Read in and check the report Site sequence concept sets - sets of MetaThesaurus ConceptIDs which, when found in sequence,
    # imply a higher MetaThesaurus ConceptID Site for the purposes of reporting.
    requiredColumns = ['SolutionID', 'MetaThesaurus or Solution IDs']
    d.sd.tempList = excel.loadSimpleSheet(wb, 'analyze', 'report site seq concept sets', requiredColumns)
    for row in d.sd.tempList:
        site = row[0]
        if site not in d.sd.Site:
            logging.critical('Attempt to define a report site sequence concept set with Site(%s) in worksheet(report site seq concept sets) in workbook(analyze) but (%s) is not defined as a Site',
                             site, site)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        configConcepts.add(site)
        concepts = []
        for eachConcept in row[1:]:
            if eachConcept is None:
                break
            concept, isNeg = excel.checkConfigConcept(eachConcept)
            concepts.append([concept, isNeg])
            configConcepts.add(concept)
        d.sd.ReportSites.append([site, concepts])       # The site and the associated list of concept/isNeg pairs

    # Return the additional known concepts
    return configConcepts


def gridAppend (sentenceNo, start, thisSite, isHistory, thisFinding, AIHWcode, subSiteCode):
    '''
    Append this Site and Finding to the grid (unless it's historical).
    The grid is a list of all the Site/Finding pairs, with matching AIHW S/E/O code.
    The grid is normally quite short, so the optimization of creating it, then sorting it
    is offset by the readability of the code and the ease of using it in reporting.
    The grid is maintained 'in order' based upon a ranking for AIHW S/E/O codes.
    Parameters
        sentenceNo      - int, the sentence in d.sentences where the diagnosis was detected
        start           - int, the position within the clinical document where this diagnosis was detected
        thisSite        - str, the SNOMED_CT Site Code
        isHistory       - boolean, True if this is historical diagnosis (Site/Finding pair)
        thisFinding     - str, the SNOMED_CT Finding code
        AIHWcode        - str, the AIHW S/E/O code for the diagnosis (used to rank diagnoses)
        subSiteCode     - str, the classification of Site into cervix, enometrial, etc.
    '''

    if not isHistory and ((thisSite, thisFinding) not in d.sd.gridFound):
        if thisSite in d.sd.Site:
            logging.debug('gridAppend() - saving Site[%s](%s - %s)/Finding[%s](%s - %s)',
                        thisSite, d.sd.Site[thisSite]['snomed_ct'], d.sd.Site[thisSite]['desc'],
                        thisFinding, d.sd.Finding[thisFinding]['snomed_ct'], d.sd.Finding[thisFinding]['desc'])
        else:
            logging.debug('gridAppend() - saving Site[%s]/Finding[%s](%s - %s)',
                        thisSite, thisFinding, d.sd.Finding[thisFinding]['snomed_ct'], d.sd.Finding[thisFinding]['desc'])
        if AIHWcode[0] == 'S':
            try:
                AIHWrank = ['S4.2', 'S4.1', 'S3.3', 'S3.2', 'S3.1', 'S2', 'S1', 'SU', 'SN'].index(AIHWcode)
            except ValueError:
                AIHWrank = 9
        elif AIHWcode[0] == 'E':
            try:
                AIHWrank = ['E4.4', 'E4.3', 'E4.2', 'E4.1', 'E3.2', 'E3.1', 'E2', 'E1', 'EU', 'EN'].index(AIHWcode) + 10
            except ValueError:
                AIHWrank = 20
        else:
            try:
                AIHWrank = ['O4.2', 'O4.1', 'O3.2', 'O3.1', 'O2', 'O1', 'ON', 'OU'].index(AIHWcode) + 21
            except ValueError:
                AIHWrank = 29
        for i, grid in enumerate(d.sd.grid):
            if grid[3] > AIHWrank:      # Insert before here
                logging.debug('gridAppend() - inserting code(%s), rank %d before %d at %d', AIHWcode, AIHWrank, grid[3], i)
                d.sd.grid.insert(i, [thisSite, thisFinding, AIHWcode, AIHWrank])
                break
        else:
            logging.debug('gridAppend() - appending code(%s), rank %d', AIHWcode, AIHWrank)
            d.sd.grid.append([thisSite, thisFinding, AIHWcode, AIHWrank])
        d.sd.gridFound.add((thisSite, thisFinding))

        # Check if we've found a cervix or endometrial code
        if subSiteCode == 'Cervix':
            d.sd.solution['cervixDone'] = True
        elif subSiteCode == 'endom':
            d.sd.solution['endomDone'] = True

    # Check if this Site/Finding pair defines a Procedure
    if (thisSite, thisFinding) not in d.sd.ProcedureDefined:
        return

    # Save the defined Procedure
    thisProcedure = d.sd.ProcedureDefined[(thisSite, thisFinding)]
    if isHistory:
        logging.info('saving defined history procedure:%s - %s', thisProcedure, d.sd.Procedure[thisProcedure]['desc'])
        # We save the sentence number for reporting purposes
        d.sd.historyProcedure[start] = thisProcedure
    else:
        logging.info('saving defined procedure:%s - %s', thisProcedure, d.sd.Procedure[thisProcedure]['desc'])
        # We save the sentence number for reporting purposes
        # If the AIHW code for this procedure is '7', then this is a hysterectomy procedure.
        # We only need to check the 'Cervix' site because, for hysterectomies, the AIHW code is '7' for all sites.
        if d.sd.Procedure[thisProcedure]['Cervix'] == '7':
            d.sd.hysterectomy.add((thisProcedure, sentenceNo))
        else:
            d.sd.otherProcedure.add((thisProcedure, sentenceNo))
    return


def analyze():
    '''
    Analyze the sentences and concepts and build up the results which are stored in the this.solution dictionary
    '''

    # Find all the sentence Sites and Finding, plus track Procedures.
    # This is preparitory work that is needed by the juxtoposition analysis below.
    d.sd.historyProcedure = {}
    d.sd.hysterectomy = set()
    d.sd.otherProcedure = set()
    d.sd.solution['unsatFinding'] = None
    d.sd.solution['cervixFound'] = False
    d.sd.solution['endomFound'] = False
    SentenceSites = {}                   # The Sites found in each sentence
    SentenceFindings = {}                # The Findings found in each sentence
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence looking for implied Sites preceed any SentenceSites
        # logging.debug('analyze() finding Sites and Findings - processing sentence[%d]', sentenceNo)
        sentence = d.sentences[sentenceNo]
        SentenceSites[sentenceNo] = {}
        SentenceFindings[sentenceNo] = {}
        document = sentence[6]    # Sentences hold mini-documents
        for start in sorted(document, key=int):        # We step through all concepts in this sentence
            for j in range(len(document[start])):            # Step through the list of alternate concepts at this point in this sentence
                concept = document[start][j]['concept']
                if document[start][j]['used']:        # Skip used concepts [only Findings get 'used']
                    continue
                # We only report positive procedures, sites and findings
                if document[start][j]['negation'] != '0':    # Skip negated and ambiguous concepts
                    continue
                isHistory = document[start][j]['history']    # A history concept - information about things that predate this analysis.
                # Check if this concept is a Procedure
                if concept in d.sd.Procedure:
                    # Check if it's a history procedure
                    if isHistory:    # Save the last history procedure
                        logging.info('saving history procedure (sentence %d):%s - %s', sentenceNo, str(concept), str(d.sd.Procedure[concept]['desc']))
                        d.sd.historyProcedure[start] = concept
                    else:
                        logging.info('saving procedure (sentence %d):%s - %s', sentenceNo, str(concept), str(d.sd.Procedure[concept]['desc']))
                        # Check if this is a hysterectomy
                        # If the AIHW code for this procedure is '7', then this is a hysterectomy procedure.
                        # We only need to check the 'Cervix' site because, for hysterectomies, the AIHW code is '7' for all sites.
                        if d.sd.Procedure[concept]['Cervix'] == '7':
                            d.sd.hysterectomy.add((concept, sentenceNo))
                            logging.info('saving hysterectomy procedure(sentence %d):%s - %s', sentenceNo, str(concept), str(d.sd.Procedure[concept]['desc']))
                        else:
                            d.sd.otherProcedure.add((concept, sentenceNo))
                            logging.info('saving other procedure(sentence %d):%s - %s', sentenceNo, str(concept), str(d.sd.Procedure[concept]['desc']))
                    continue

                # Check if this concept is a Finding
                if concept in d.sd.Finding:
                    # Save the last Site Finding, at this point, in this sentence
                    # logging.debug('found finding concept (%s) in sentence(%d)', concept, sentenceNo)
                    if start not in SentenceFindings[sentenceNo]:
                        SentenceFindings[sentenceNo][start] = []
                    SentenceFindings[sentenceNo][start].append((concept, isHistory))        # The Sentence Finding(s)
                    logging.info('saving Finding(sentence %d):%s - %s', sentenceNo, str(concept), str(d.sd.Finding[concept]['desc']))
                    # Check if this concept is an unsatifactory Finding
                    if d.sd.Finding[concept]['Cervix'] == 'SU':
                        d.sd.solution['unsatFinding'] = concept
                    continue

                # Check if this concept is a Site
                if concept in d.sd.Site:
                    # Save the last Site concept, at this point, in this sentence
                    # logging.debug('found site concept (%s) in sentence(%d)', concept, sentenceNo)
                    if start not in SentenceSites[sentenceNo]:
                        SentenceSites[sentenceNo][start] = []
                    SentenceSites[sentenceNo][start].append((concept, isHistory, False))        # The Sentence Site - not used
                    logging.info('saving Site(sentence %d):%s - %s', sentenceNo, str(concept), str(d.sd.Site[concept]['desc']))

                    # Mark cervixFound or endomFound if appropriate
                    # By "found" we mean that these site were noted
                    subsite = d.sd.Site[concept]['SubSite']
                    if subsite == 'Cervix':
                        if not d.sd.solution['cervixFound']:
                            d.sd.solution['cervixFound'] = True
                            logging.info('cervixFound')
                    elif subsite == 'endom':
                        if not d.sd.solution['endomFound']:
                            d.sd.solution['endomFound'] = True
                            logging.info('endomFound')
                    continue
            # end of all the alternate concepts
        # end of all the concepts in this sentence
    # end of sentence
    # logging.debug('analyze() Sentence Sites [%s]', repr(SentenceSites))
    # logging.debug('analyze() Sentence Findings [%s]', repr(SentenceFindings))

    # Juxtoposition Analysis
    # Start by looking through each sentence for Site/Finding pairs, in the same history phase, and add them to the grid.
    # [Only non-history things are actually added to the grid, but the gridAppend() function does procedure analysis as well
    #  for implied procedures, which can be historical.]
    d.sd.grid = []
    d.sd.gridFound = set()
    d.sd.solution['cervixDone'] = False
    d.sd.solution['endomDone'] = False
    for sentenceNo in range(len(d.sentences)):            # Step through each sentence
        # Check if at least one Site was found in this sentence
        if len(SentenceSites[sentenceNo]) == 0:
            continue
        # Check if at least one Finding was found in this sentence
        if len(SentenceFindings[sentenceNo]) == 0:
            continue
        # logging.debug('analyze() Sites and Findings in sentence[%d]', sentenceNo)

        # We have both Sites and Findings in this sentence.
        # For each Finding, work through every Site and calculate a "best fit".
        # Where "best fit" is a combination of 'likelyhood' and 'distance'.
        # 'likelyhood' is a ranking between 1 and 7, which can be set in configuration (4 is the default)
        # 'distance' is then number of other Sites between this Finding and this Site.
        # We subtract the 'distance' from the 'likelyhood' in order to score each Site for this Finding.
        # Highest score wins.

        # Build up the Site index so we can compute 'nearest' Site to a Finding and number of other Sites in beteween
        SiteAt = {}
        for SiteIndex, SiteStart in enumerate(sorted(SentenceSites[sentenceNo])):
            SiteAt[SiteStart] = SiteIndex
        logging.debug('analyze() Sites at (%s) in sentence %d', SiteAt, sentenceNo)

        # Work through the findings in this sentence
        for FindingStart in SentenceFindings[sentenceNo]:
            # Find the nearest Site for all the Findings at this FindingStart
            nearestStart = None
            smallestDif = None
            for SiteStart in SiteAt:
                if (smallestDif is None) or abs(FindingStart - SiteStart) < smallestDif:
                    smallestDif = abs(FindingStart - SiteStart)
                    nearestStart = SiteStart
            # Now work through all the Findings at this FindingStart - looking for the best Site
            for thisFindingIndex, (thisFinding, thisFindingHistory) in enumerate(SentenceFindings[sentenceNo][FindingStart]):
                logging.debug('analyze() - looking for nearest/best Site(near %d) for Finding(%s) at %d', nearestStart, thisFinding, FindingStart)
                # Now test every site
                bestRank = None
                bestSiteStart = None
                bestSiteIndex = None
                bestSite = None
                bestSiteHistory = None
                for SiteStart in SentenceSites[sentenceNo]:
                    for thisSiteIndex, (thisSite, thisSiteHistory, thisSiteUsed) in enumerate(SentenceSites[sentenceNo][SiteStart]):
                        # logging.debug('analyze() - checking Site %s at %d', thisSite, SiteStart)
                        # If they are from different histories then they are not a match
                        if thisFindingHistory != thisSiteHistory:
                            # logging.debug('analyze() - discarding %s because of history mismatch[%s:%s]', thisSite, thisFindingHistory, thisSiteHistory)
                            continue
                        # Skip if not in restricted list
                        if (thisFinding in d.sd.SiteRestrictions) and len(d.sd.SiteRestrictions[thisFinding]) > 0:
                            if thisSite not in d.sd.SiteRestrictions[thisFinding]:
                                # logging.debug('analyze() - discarding %s because of Site Restrictions for %s', thisSite, thisFinding)
                                continue
                        # Skip if in impossible list
                        if (thisFinding in d.sd.SiteImpossible) and len(d.sd.SiteImpossible[thisFinding]) > 0:
                            if thisSite in d.sd.SiteImpossible[thisFinding]:
                                # logging.debug('analyze() - discarding %s - impossible Site for %s', thisSite, thisFinding)
                                continue
                        # Compute the ranking
                        if (thisFinding in d.sd.SiteRank) and (thisSite in d.sd.SiteRank[thisFinding]):
                            rank = d.sd.SiteRank[thisFinding][thisSite]
                        else:
                            rank = 4
                        rank -= abs(SiteAt[nearestStart] - SiteAt[SiteStart])
                        # logging.debug('analyze() - Site %s has rank %d', thisSite, rank)
                        if (bestRank is None) or (rank < bestRank):
                            bestRank = rank
                            bestSiteStart = SiteStart
                            bestSiteIndex = thisSiteIndex
                            bestSite = thisSite
                            bestSiteHistory = thisSiteHistory
                # logging.debug('analyse() - best Site(%s) at %d has ranking %d and history (%s)', bestSite, bestSiteStart, bestRank, bestSiteHistory)

                # If we found a Site add it to the grid, mark the Site as used and delete this Finding from SentenceFindings
                if bestRank is not None:
                    siteCode = d.sd.Site[bestSite]['Site']
                    subSiteCode = d.sd.Site[bestSite]['SubSite']
                    findingCode = d.sd.Finding[thisFinding][siteCode]
                    gridAppend(sentenceNo, FindingStart, bestSite, bestSiteHistory, thisFinding, findingCode, subSiteCode)
                    # Delete this finding and move onto the next one
                    # logging.debug('analyze() - deleting Finding (%s) at %d from sentence %d', thisFinding, FindingStart, sentenceNo)
                    # logging.debug('analyze() - Findings at %d in sentence no %d - %s',
                    #               FindingStart, sentenceNo, SentenceFindings[sentenceNo][FindingStart])
                    del SentenceFindings[sentenceNo][FindingStart][thisFindingIndex]
                    # logging.debug('analyze() - remaining Findings at %d in sentence no %d - %s',
                    #               FindingStart, sentenceNo, SentenceFindings[sentenceNo][FindingStart])
                    # Mark the site as used
                    SentenceSites[sentenceNo][bestSiteStart][bestSiteIndex] = (bestSite, bestSiteHistory, True)
        # Clean up any empty Sentence Findings
        for findingStart in list(SentenceFindings[sentenceNo].keys()):
            if len(SentenceFindings[sentenceNo][findingStart]) == 0:
                del SentenceFindings[sentenceNo][findingStart]
        # end of this sentence
    # end of sentences

    # Now re-work the sentences looking for Sites for any remaining Findings.
    # These can occur when the site is in a subheading, with all the finding in following sentence below that subheading
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
        # Check if there is a remaining found Finding in this sentence
        if len(SentenceFindings[sentenceNo]) == 0:
            # logging.debug('No unmatched findings in sentence(%d)', sentenceNo)
            continue

        # Check a number of the sentences around this Finding
        maxGap = 2            # Sites are really only valid for two sentences (unless the grid is empty)
        if len(d.sd.grid) == 0:
            maxGap = 3        # in which case they are valid for 3
        # Find the Sites across these sentences
        logging.debug('analyze() - checking sentence %d with findings (%s) for Sites within %d sentences',
                      sentenceNo, SentenceFindings[sentenceNo], maxGap)
        localSites = []
        bestSiteIndex = None
        for sno in range(max(0, sentenceNo - maxGap), min(sentenceNo + maxGap, len(d.sentences))):
            # logging.debug('analyze() - checking sentence %d which has Sites(%s)', sno, SentenceSites[sno])
            if sno == sentenceNo:        # No Sites in the current sentence - that was handled above
                localSites.append((sno, 0))     # A fake marker being "this sentence"
                bestSiteIndex = len(localSites)     # The index of "this sentence"
                continue
            elif (sno > sentenceNo) and (d.sd.sentenceCAPS.match(d.sentences[sno][4]) is not None):    # Stop searching forward if we hit a label
                break
            if len(SentenceSites[sno]) == 0:        # No Sites in this sentence
                continue
            for SiteStart in sorted(SentenceSites[sno]):        # Add all the sites in this sentence
                localSites.append((sno, SiteStart))
        # If there are no Sites around this sentence, just the fake marker for "this sentence" - go to the next sentence
        if len(localSites) == 1:
            logging.debug('analyze() - no sites found')
            continue        # Check the next sentence as any findings must remain unmatched
        else:
            # logging.debug('analyze() - Sites found (%s)', localSites)
            pass

        # Walk through the findings in this sentence
        for FindingStart in SentenceFindings[sentenceNo]:
            # Then wak though all the Findings at this start - looking for the best Site
            for thisFindingIndex, (thisFinding, thisFindingHistory) in enumerate(SentenceFindings[sentenceNo][FindingStart]):
                # Find the best site from the local sites - which is an orderd list
                bestRank = None
                bestSno = None
                bestSiteStart = None
                bestSiteIndex = None
                bestSite = None
                bestSiteHistory = None
                for localIndex, (sno, SiteStart) in enumerate(localSites):
                    if sno == sentenceNo:       # Skip fake marker for "this sentence"
                        continue
                    for thisSiteIndex, (thisSite, thisSiteHistory, thisSiteUsed) in enumerate(SentenceSites[sno][SiteStart]):
                        # If they are from different histories then they are not a match
                        if thisFindingHistory != thisSiteHistory:
                            logging.debug('analyze() - Site(%s) and Finding(%s) have different histories', thisSite, thisFinding)
                            continue
                        # Skip if not in restricted list
                        if (thisFinding in d.sd.SiteRestrictions) and len(d.sd.SiteRestrictions[thisFinding]) > 0:
                            if thisSite not in d.sd.SiteRestrictions[thisFinding]:
                                logging.debug('analyze() - Site(%s) not in restricted list (%s) for Finding(%s)',
                                              thisSite, d.sd.SiteRestrictions[thisFinding], thisFinding)
                                continue
                        # Skip if in impossible list
                        if (thisFinding in d.sd.SiteImpossible) and len(d.sd.SiteImpossible[thisFinding]) > 0:
                            if thisSite in d.sd.SiteImpossible[thisFinding]:
                                logging.debug('analyze() - Site(%s) is impossible Site (%s) for Finding(%s)',
                                              thisSite, d.sd.SiteImpossible[thisFinding], thisFinding)
                                continue
                        # logging.debug('analyze() - possible Site (%s) in sentence %d at %d', thisSite, sno, SiteStart)
                        # Compute the ranking
                        if (thisFinding in d.sd.SiteRank) and (thisSite in d.sd.SiteRank[thisFinding]):
                            rank = d.sd.SiteRank[thisFinding][thisSite]
                        else:
                            rank = 4
                        if bestSiteIndex is not None:
                            rank -= abs(bestSiteIndex - localIndex)
                        if (bestRank is None) or (rank < bestRank):
                            bestRank = rank
                            bestSno = sno
                            bestSiteStart = SiteStart
                            bestSiteIndex = thisSiteIndex
                            bestSite = thisSite
                            bestSiteHistory = thisSiteHistory
                # If we found a Site add it to the grid, mark the Site as used and delete this Finding from SentenceFindings
                if bestRank is not None:
                    logging.debug('analyze() - best Site (%s)', bestSite)
                    siteCode = d.sd.Site[bestSite]['Site']
                    subSiteCode = d.sd.Site[bestSite]['SubSite']
                    findingCode = d.sd.Finding[thisFinding][siteCode]
                    gridAppend(sentenceNo, FindingStart, bestSite, bestSiteHistory, thisFinding, findingCode, subSiteCode)
                    # Delete this finding and move onto the next one
                    del SentenceFindings[sentenceNo][FindingStart][thisFindingIndex]
                    # Mark the site as used
                    SentenceSites[bestSno][bestSiteStart][bestSiteIndex] = (thisSite, thisSiteHistory, True)
                else:
                    logging.debug('analyze() - no suitable Site')
                    pass
        # Clean up any empty Sentence Findings
        for findingStart in list(SentenceFindings[sentenceNo].keys()):
            if len(SentenceFindings[sentenceNo][findingStart]) == 0:
                del SentenceFindings[sentenceNo][findingStart]

    # Report unused Sites
    for sentenceNo, Sites in SentenceSites.items():
        for SiteStart in Sites:
            for thisSite, thisSiteHistory, thisSiteUsed in SentenceSites[sentenceNo][SiteStart]:
                if thisSiteUsed:
                    continue
                logging.info('Unused Site in sentence(%s):%s - %s', sentenceNo, thisSite, d.sd.Site[thisSite]['desc'])

    # Report unused Findings
    for sentenceNo, Findings in SentenceFindings.items():
        for FindingStart in Findings:
            for thisFinding, thisFindingHistory in SentenceFindings[sentenceNo][FindingStart]:
                if thisFinding in d.sd.SiteDefault:    # Check if we have a default site
                    thisSite = d.sd.SiteDefault
                    siteCode = d.sd.Site[thisSite]['Site']
                    subSiteCode = d.sd.Site[thisSite]['SubSite']
                    findingCode = d.sd.Finding[thisFinding][siteCode]
                    gridAppend(sentenceNo, FindingStart, thisSite, thisSiteHistory, thisFinding, findingCode, subSiteCode)
                else:
                    logging.info('Unused Finding in sentence(%s):%s - %s', sentenceNo, thisFinding, d.sd.Finding[thisFinding]['desc'])

    # Make sure there is something in the grid
    if len(d.sd.grid) == 0:    # We have no Site/Finding pairs (which means no usable Findings or they would have been handled above)
        logging.info('Empty grid')
        # We may have usable sites (Report Sites) in the document, which we can pair with 'nothing found' - check each in order
        # However, they are only report sites if all the associated concepts are found in the coded histopathology report
        foundSites = []
        for siteInfo in d.sd.ReportSites:     # The Report Sites and their concept lists
            # siteInfo[0] is the Report Site, siteInfo[1] is a list of pairs for this set
            thisReportSite = siteInfo[0]
            thisReportSet = siteInfo[1]
            conceptNo = 0           # Step through the concepts for this Report Site in thisReportSet
            # logging.debug('analyze() - checking Report Site set %d - %s', setNo, thisReportSet)
            for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
                document = sentence[6]      # Sentences hold mini-documents
                for start in sorted(document, key=int):        # We step through all concepts in this sentence
                    for j in range(len(document[start])):            # Step through the list of alternate concepts at this point in this sentence
                        if document[start][j]['used']:        # Skip used concepts [only Findings get 'used']
                            continue
                        if document[start][j]['history']:            # Skip historical concepts
                            continue
                        concept = document[start][j]['concept']
                        isNeg =  document[start][j]['negation']        # Check that the negation matches

                        # Check if this alternate concept at 'start' is the next one in this Report Site sequence of concept in this set
                        found = False
                        thisNeg =  thisReportSet[conceptNo][1]        # The desired negation
                        if concept == thisReportSet[conceptNo][0]:    # A matching concept
                            if thisNeg == isNeg:
                                found = True        # With a mathing negation
                            elif (isNeg in ['2', '3']) and (thisNeg in ['2', '3']):
                                found = True        # Or a near enough negation (both ambiguous)
                        if not found:    # Check the special case of a repetition of the first concept in the set
                            # We don't handle repetitions within a set - just a repetition of the first concept
                            # i.e.looking for concept 'n' - found concept 0 [this set, array of concepts in dict, first entry, concept]
                            if concept == thisReportSet[0][0]:
                                # Found the first concept - restart the multi-sentence counter
                                conceptNo = 0
                            continue
                        # logging.debug('Concept (%s) (for sentence Report Site Sequence concept set[%d]) found', concept, setNo)
                        conceptNo += 1      # Found so proceed to the next concept in this Report Site concept set
                        if conceptNo == len(thisReportSet):
                            # We have a full concept sequence set - so save this Report Site
                            foundSites.append(thisReportSite)
                            conceptNo = 0       # Reset in case this set occurs more than once

        # Now check the foundSites to see if we can use any of them
        for thisSite in foundSites:
            subsite = d.sd.Site[thisSite]['SubSite']
            if subsite == 'Cervix':         # A 'Cervix' type Site
                if d.sd.solution['cervixDone']:
                    continue
                if d.sd.solution['unsatFinding'] is not None:
                    thisFinding = d.sd.solution['unsatFinding']
                    findingCode = 'SU'      # Unsatisfactory
                elif d.sd.solution['cervixFound']:
                    thisFinding = d.sd.normalCervixCode
                    findingCode = 'S1'      # Normal
                else:
                    thisFinding = d.sd.noAbnormality
                    findingCode = 'S1'      # Normal
                # logging.debug('cervical ReportSite:%s', str(thisSite))
                gridAppend(0, 0, thisSite, False, thisFinding, findingCode, subsite)
            elif subsite == 'endom':        # An 'endom' type Site
                if d.sd.solution['endomDone']:
                    continue
                if d.sd.solution['unsatFinding'] is not None:
                    Finding = d.sd.solution['unsatFinding']
                    findingCode = 'ON'      # Not applicable
                elif d.sd.solution['endomFound']:
                    Finding = d.sd.normalEndomCode
                    findingCode = 'O1'      # Negative/no abnormalities reported or benign changes only
                else:
                    Finding = d.sd.noAbnormality
                    findingCode = 'E1'      # Negative
                gridAppend(0, 0, thisSite, False, Finding, findingCode, subsite)
                # logging.debug('endometrial ReportSite:%s', thisSite)
            else:
                # logging.info('other ReportSite:%s', thisSite)
                if d.sd.solution['unsatFinding'] is not None:
                    gridAppend(0, 0, thisSite, False, d.sd.solution['unsatFinding'], 'ON', '')
                else:
                    gridAppend(0, 0, thisSite, False, d.sd.noAbnormality, 'ON', '')
                break

    # Now add any 'normal' finding for any missing things - there may have been no Report Sites
    logging.info('cervixFound:%s, cervixDone:%s', d.sd.solution['cervixFound'], d.sd.solution['cervixDone'])
    if d.sd.solution['cervixFound'] and not d.sd.solution['cervixDone']:
        gridAppend(0, 0, d.sd.cervixUteri, False, d.sd.normalCervixCode, 'S1', 'Cervix')
    logging.info('endomFound:%s, endomDone:%d', d.sd.solution['endomFound'], d.sd.solution['endomDone'])
    if d.sd.solution['endomFound'] and not d.sd.solution['endomDone']:
        gridAppend(0, 0, d.sd.endomStructure, False, d.sd.normalEndomCode, 'O1', 'endom')

    if len(d.sd.grid) == 0:        # We still have nothing - So report No Topopgraphy/No abnormality
        gridAppend(0, 0, '', False, d.sd.noAbnormality, 'ON', '')

    # Find the first S, E and O codes in the grid
    foundRows = set()       # Filter out duplicates of Site/Finding pairs
    d.sd.reportS = None
    d.sd.reportE = None
    d.sd.reportO = None
    for row in d.sd.grid:
        thisSite = row[0]
        thisFinding = row[1]
        thisAIHW = row[2]
        thisRow = thisSite + '|' + thisFinding      # This Site/Finding pair
        if thisRow not in foundRows:
            foundRows.add(thisRow)
            if thisAIHW[:1] == 'S':
                if d.sd.reportS is None:
                    d.sd.reportS = thisAIHW
            elif thisAIHW[:1] == 'E':
                if d.sd.reportE is None:
                    d.sd.reportE = thisAIHW
            else:
                if d.sd.reportO is None:
                    d.sd.reportO = thisAIHW
    if d.sd.reportS is None:
        d.sd.reportS = 'SN'
    if d.sd.reportE is None:
        d.sd.reportE = 'EN'
    if d.sd.reportO is None:
        d.sd.reportO = 'ON'

    # If we have no procedures, but we have a history procedure, then that's as good as it gets
    # Promote the last history procedure found to procedures and remove from the set of history procedures
    # History procedures are stored as a dictionary, where the key is the position within the document
    reportedProcs = set()       # The set of procedures included in the report/analysis
    if (len(d.sd.hysterectomy) == 0) and (len(d.sd.otherProcedure) == 0):
        if len(d.sd.historyProcedure) > 0:
            histStart = sorted(d.sd.historyProcedure)[-1]       # The last historical procedure in the histopathology report
            histProc = d.sd.historyProcedure[histStart]
            # Check if this is a hysterectomy
            # If the AIHW code for this procedure is '7', then this is a hysterectomy procedure.
            # We only need to check the 'Cervix' site because, for hysterectomies, the AIHW code is '7' for all sites.
            if d.sd.Procedure[histProc]['Cervix'] == '7':
                d.sd.hysterectomy.add((histProc, sentenceNo))
            else:
                d.sd.otherProcedure.add((histProc, sentenceNo))
            reportedProcs.add(histProc)
            del d.sd.historyProcedure[histStart]        # Remove as we have moved this to hyterectomy or otherProcedure

    # Now lets work out those Procedures - start by finding the top site
    # We have some defaults in case the grid only has 'Topography not assigned'
    topSite = d.sd.grid[0][0]
    if topSite != '':
        TopSite = d.sd.Site[topSite]['Site']
        TopSubSite = d.sd.Site[topSite]['SubSite']
        if TopSubSite == 'Not_Stated':
            TopSubSite = 'Other'
    else:
        TopSite = 'Cervix'
        TopSubSite = 'Cervix'
    # logging.debug('topSite:%s', str(TopSite))

    # Compute the SNOMED_CT procedure and AIHW procedure
    d.sd.reportSN_CTprocedure = {}
    d.sd.reportAIHWprocedure = {}
    if len(d.sd.hysterectomy) > 0:      # Use any hysterectomy
        thisProcedure, thisSno = list(d.sd.hysterectomy)[0]
        logging.info('Hysterectomy procedure(%s):%s - %s',
                          thisProcedure, d.sd.Procedure[thisProcedure]['snomed_ct'], d.sd.Procedure[thisProcedure]['desc'])
        d.sd.reportSN_CTprocedure['code'] = d.sd.Procedure[thisProcedure]['snomed_ct']
        d.sd.reportSN_CTprocedure['desc'] = d.sd.Procedure[thisProcedure]['desc']
        d.sd.reportAIHWprocedure['code'] = '7'
        d.sd.reportAIHWprocedure['desc'] = d.sd.AIHWprocedure['7']
        reportedProcs.add(thisProcedure)
        d.sd.hysterectomy.remove((thisProcedure, thisSno))
    elif len(d.sd.otherProcedure) > 0:        # Multiple other procedures - find the highest ranked procedure for the top site
        rank = -1
        rankProc = None
        rankSno = None
        # We need to print the highest ranked procedure
        for thisProc, thisSno in d.sd.otherProcedure:
            if TopSite == 'Cervix':
                thisRank = int(d.sd.Procedure[thisProc]['Cervix_Rank'])
            elif TopSite == 'Vagina':
                thisRank = int(d.sd.Procedure[thisProc]['Vagina_Rank'])
            elif TopSite == 'Other':
                thisRank = int(d.sd.Procedure[thisProc]['Other_Rank'])
            else:
                thisRank = int(d.sd.Procedure[thisProc]['Not_Stated_Rank'])
            if (thisRank > rank) and (thisRank != 99):        # Filter out invalid procedures
                logging.debug('analyze() - selecting Other Procedure (TopSite (%s), rank %d) %s from sentence %s', TopSite, thisRank, thisProc, thisSno)
                rank = thisRank
                rankProc = thisProc
                rankSno = thisSno
        if rankProc is None:        # None of the procedures were valid
            logging.info('No valid procedure')
            d.sd.reportSN_CTprocedure['code'] = 'WARNING'
            d.sd.reportSN_CTprocedure['desc'] = 'No Procedure specified'
            d.sd.reportAIHWprocedure['code'] = 'WARNING'
            d.sd.reportAIHWprocedure['desc'] = 'No Procedure specified'
        else:
            logging.info('Other procedure(%s):%s - %s',
                              rankProc, d.sd.Procedure[rankProc]['snomed_ct'], d.sd.Procedure[rankProc]['desc'])
            d.sd.reportSN_CTprocedure['code'] = d.sd.Procedure[rankProc]['snomed_ct']
            d.sd.reportSN_CTprocedure['desc'] = d.sd.Procedure[rankProc]['desc']
            AIHWProc = d.sd.Procedure[rankProc][TopSite]
            if AIHWProc == '99':
                d.sd.reportAIHWprocedure['code'] = 'WARNING'
                d.sd.reportAIHWprocedure['desc'] = 'No Applicable Procedure specified'
            else:
                d.sd.reportAIHWprocedure['code'] = AIHWProc
                d.sd.reportAIHWprocedure['desc'] = d.sd.AIHWprocedure[AIHWProc]
            reportedProcs.add(rankProc)
            d.sd.otherProcedure.remove((rankProc, rankSno))
    else:
        logging.info('No procedure')
        d.sd.reportSN_CTprocedure['code'] = 'WARNING'
        d.sd.reportSN_CTprocedure['desc'] = 'No Procedure specified'
        d.sd.reportAIHWprocedure['code'] = 'WARNING'
        d.sd.reportAIHWprocedure['desc'] = 'No Procedure specified'

    # Report any unused hysterectomies
    d.sd.solution['otherHysterectomies'] = []
    for proc, sno in d.sd.hysterectomy:
        if proc in reportedProcs:
            continue
        logging.info('Unused Hysterectomy procedure in sentence(%s):%s - %s', sno, proc, d.sd.Procedure[proc]['desc'])
        d.sd.solution['otherHysterectomies'].append([d.sd.Prodecure[proc]['snomed_ct'], d.sd.Procedure[proc]['desc'], '7', d.sd.AIHWprocedure['7']])
        reportedProcs.add(proc)

    # Report any unused procedures
    d.sd.solution['otherProcedures'] = []
    for proc, sno in d.sd.otherProcedure:
        if proc in reportedProcs:
            continue
        logging.info('Unused Procedure in sentence(%d):%s - %s', sno, proc, d.sd.Procedure[proc]['desc'])
        AIHWProc = d.sd.Procedure[proc][TopSite]
        if AIHWProc == '99':
            d.sd.solution['otherProcedures'].append([d.sd.Procedure[proc]['snomed_ct'], d.sd.Procedure[proc]['desc'], 'WARNING', 'No Applicable Procedure specified'])
        else:
            d.sd.solution['otherProcedures'].append([d.sd.Procedure[proc]['snomed_ct'], d.sd.Procedure[proc]['desc'], AIHWProc, d.sd.AIHWprocedure[AIHWProc]])
        reportedProcs.add(proc)
    return


def reportJSON(asSuccess):
    '''
    Assemble the response as a dictionary.
    reportHTML converts this into HTML.
    The Flask routine turns this into JSON which will be returned to the HTTP service requester.
    '''

    response = {}
    if not asSuccess:       # Return and empty dictionary upon failure
        response['SCTprocedure'] = ''
        response['grid'] = []
        response['AIHWprocedure'] = ''
        response['S'] = {}
        response['S']['code'] = ''
        response['S']['desc'] = ''
        response['E'] = {}
        response['E']['code'] = ''
        response['E']['desc'] = ''
        response['O'] = {}
        response['O']['code'] = ''
        response['O']['desc'] = ''
        response['otherHysterectomies'] = []
        response['otherProcedures'] = []
        return response

    # Build the dictionary of response values
    response['SCTprocedure'] = d.sd.reportSN_CTprocedure
    response['grid'] = []
    for row in d.sd.grid:
        thisRow = {}
        thisSite = row[0]
        thisFinding = row[1]
        AIHW = row[2]
        if thisSite == '':                # no Topography
            thisRow['site'] = '21229009'
            thisRow['site description'] = 'Topography not assigned (body structure)'
        else:
            thisRow['site'] = d.sd.Site[thisSite]['snomed_ct']
            thisRow['site description'] = d.sd.Site[thisSite]['desc']
        thisRow['finding'] = d.sd.Finding[thisFinding]['snomed_ct']
        thisRow['finding description'] = d.sd.Finding[thisFinding]['desc']
        thisRow['AIHW'] = AIHW
        response['grid'].append(thisRow)
    response['AIHWprocedure'] = d.sd.reportAIHWprocedure
    response['S'] = {}
    response['S']['code'] = d.sd.reportS
    response['S']['desc'] = d.sd.AIHWfinding[d.sd.reportS]
    response['E'] = {}
    response['E']['code'] = d.sd.reportE
    response['E']['desc'] = d.sd.AIHWfinding[d.sd.reportE]
    response['O'] = {}
    response['O']['code'] = d.sd.reportO
    response['O']['desc'] = d.sd.AIHWfinding[d.sd.reportO]
    response['otherHysterectomies'] = []
    for i in range(len(d.sd.solution['otherHysterectomies'])):
        response['otherHysterectomies'].append(d.sd.solution['otherHysterectomies'][i])
    response['otherProcedures'] = []
    for i in range(len(d.sd.solution['otherProcedures'])):
        response['otherProcedures'].append(d.sd.solution['otherProcedures'][i])
    return response


def reportFile(folder, filename):
    '''
    Print the results
    '''

    if filename is None:
        fpOut = sys.stdout
    else:
        try:
            fpOut = open(os.path.join(folder, filename + '.txt'), 'wt', newline='', encoding='utf-8')
        except Exception as e:
            logging.critical('Cannot create file %s, error:%s', os.path.join(folder, filename + '.txt'), e.args)
            logging.shutdown()
            sys.exit(d.EX_CANTCREAT)

    # Workout how wide the grid is for formatting purposes
    siteCodeLen = 0
    siteDescLen = 0
    findingCodeLen = 0
    findingDescLen = 0
    AIHWlen = 0
    for row in d.sd.grid:
        thisSite = row[0]
        thisFinding = row[1]
        if thisSite != '':
            thisSiteCodeLen = len(d.sd.Site[thisSite]['snomed_ct'])
            thisSiteDescLen = len(d.sd.Site[thisSite]['desc'])
        else:
            thisSiteCodeLen = len('21229009')
            thisSiteDescLen = len('Topography not assigned (body structure)')
        thisFindingCodeLen = len(d.sd.Finding[thisFinding]['snomed_ct'])
        thisFindingDescLen = len(d.sd.Finding[thisFinding]['desc'])
        thisAIHWlen = len(row[2])
        if thisSiteCodeLen > siteCodeLen:
            siteCodeLen = thisSiteCodeLen
        if thisSiteDescLen > siteDescLen:
            siteDescLen = thisSiteDescLen
        if thisFindingCodeLen > findingCodeLen:
            findingCodeLen = thisFindingCodeLen
        if thisFindingDescLen > findingDescLen:
            findingDescLen = thisFindingDescLen
        if thisAIHWlen > AIHWlen:
            AIHWlen = thisAIHWlen

    col1Len = siteCodeLen + 4 + siteDescLen     # Allow for ' - ' between code and description, plus a trailing space
    col2Len = findingCodeLen + 4 + findingDescLen     # Allow for ' - ' between code and description, plus a trailing space
    if AIHWlen < 4:
        AIHWlen = 5
    else:
        AIHWlen = AIHWlen + 1       # Allow for a trailing space
    headerLen = col1Len + col2Len + AIHWlen + 7     # four '+' characters and three leading spaces
    headerLine = '-' * (headerLen)
    boxLine = '+-' + '-' * col1Len + '+-' + '-' * col2Len + '+-' + '-' * AIHWlen + '+'
    print(headerLine, file=fpOut)
    print(file=fpOut)
    print(f"Procedure: {d.sd.reportSN_CTprocedure['code']} - {d.sd.reportSN_CTprocedure['desc']}", file=fpOut)
    print(file=fpOut)
    print(headerLine, file=fpOut)

    print(file=fpOut)
    print(boxLine, file=fpOut)
    print(f"| {'Site':{col1Len}}| {'Finding':{col2Len}}| {'AIHW':{AIHWlen}}|", file=fpOut)
    print(boxLine, file=fpOut)

    # Next print the Grid (it is already in descending S, then descending E, then descending O order)
    for row in d.sd.grid:
        thisSite = row[0]
        thisFinding = row[1]
        thisAIHW = row[2]
        thisFindingCode = d.sd.Finding[thisFinding]['snomed_ct']
        thisFindingDesc = d.sd.Finding[thisFinding]['desc']
        if thisSite != '':
            thisSiteCode = d.sd.Site[thisSite]['snomed_ct']
            thisSiteDesc = d.sd.Site[thisSite]['desc']
        else:
            thisSiteCode = '21229009'
            thisSiteDesc = 'Topography not assigned (body structure)'
        line = f"| {thisSiteCode + ' - ' + thisSiteDesc:{col1Len}}"
        line += f"| {thisFindingCode+ ' - ' + thisFindingDesc:{col2Len}}"
        line += f'| {thisAIHW:{AIHWlen}}|'
        print(line, file=fpOut)
    print(boxLine, file=fpOut)

    # Now output the AIHW results
    print(file=fpOut)
    print('AIHW', file=fpOut)
    print(f"Procedure: {d.sd.reportAIHWprocedure['code']} - {d.sd.reportAIHWprocedure['desc']}", file=fpOut)
    print(f'S: {d.sd.reportS} - {d.sd.AIHWfinding[d.sd.reportS]}', file=fpOut)
    print(f'E: {d.sd.reportE} - {d.sd.AIHWfinding[d.sd.reportE]}', file=fpOut)
    print(f'O: {d.sd.reportO} - {d.sd.AIHWfinding[d.sd.reportO]}', file=fpOut)

    # Now output any other Hysterectomies
    if len(d.sd.solution['otherHysterectomies']) > 0:
        SCTcodeWidth = len('SCT code')
        SCTdescWidth = len('SCT hysterectomy description')
        AIHWcodeWidth = len('AIHW code')
        AIHWdescWidth = len('AIHW hysterectomy description')
        for row in d.sd.solution['otherHysterectomies']:
            if len(row[0]) > SCTcodeWidth:
                SCTcodeWidth = len(row[0])
            if len(row[1]) > SCTdescWidth:
                SCTdescWidth = len(row[1])
            if len(row[2]) > AIHWcodeWidth:
                AIHWcodeWidth = len(row[2])
            if len(row[3]) > AIHWdescWidth:
                AIHWdescWidth = len(row[3])
        col1Len = SCTcodeWidth + 4 + SCTdescWidth     # Allow for ' - ' between code and description, plus a trailing space
        col2Len = AIHWcodeWidth + 4 + AIHWdescWidth     # Allow for ' - ' between code and description, plus a trailing space
        headerLen = col1Len + col2Len + 5     # three '+' characters and two leading spaces
        headerLine = '-' * (headerLen)
        boxLine = '+-' + '-' * col1Len + '+-' + '-' * col2Len + '+'
        print(file=fpOut)
        print(headerLine, file=fpOut)
        print(file=fpOut)
        print('Other Hysterectomies', file=fpOut)
        print(boxLine, file=fpOut)
        print(f"| {'SNOMED CT':{col1Len}}| {'AIHW':{col2Len}}|", file=fpOut)
        print(boxLine, file=fpOut)
        for row in d.sd.solution['otherHysterectomies']:
            line = f"| {row[0] + ' - ' + row[1]:{col1Len}}"
            line += f"| {row[2] + ' - ' + row[3]:{col2Len}}|"
            print(line, file=fpOut)
        print(boxLine, file=fpOut)

    # Now output any other Procedures
    if len(d.sd.solution['otherProcedures']) > 0:
        SCTcodeWidth = len('SCT code')
        SCTdescWidth = len('SCT procedure description')
        AIHWcodeWidth = len('AIHW code')
        AIHWdescWidth = len('AIHW procedure description')
        for row in d.sd.solution['otherProcedures']:
            if len(row[0]) > SCTcodeWidth:
                SCTcodeWidth = len(row[0])
            if len(row[1]) > SCTdescWidth:
                SCTdescWidth = len(row[1])
            if len(row[2]) > AIHWcodeWidth:
                AIHWcodeWidth = len(row[2])
            if len(row[3]) > AIHWdescWidth:
                AIHWdescWidth = len(row[3])
        col1Len = SCTcodeWidth + 4 + SCTdescWidth    # Allow for ' - ' between code and description, plus a trailing space
        col2Len = AIHWcodeWidth + 4 + AIHWdescWidth    # Allow for ' - ' between code and description, plus a trailing space
        headerLen = col1Len + col2Len + 5     # three '+' characters and two leading spaces
        headerLine = '-' * (headerLen)
        boxLine = '+-' + '-' * col1Len + '+-' + '-' * col2Len + '+'
        print(file=fpOut)
        print(headerLine, file=fpOut)
        print(file=fpOut)
        print('Other Procedures', file=fpOut)
        print(boxLine, file=fpOut)
        print(f"| {'SNOMED CT':{col1Len }}| {'AIHW':{col2Len}}|", file=fpOut)
        print(boxLine, file=fpOut)
        for row in d.sd.solution['otherProcedures']:
            line = f"| {row[0] + ' - ' + row[1]:{col1Len }}"
            line += f"| {row[2] + ' - ' + row[3]:{col2Len}}|"
            print(line, file=fpOut)
        print(boxLine, file=fpOut)
    return


def reportHTML():
    '''
    Create the HTML version of the report
    '''

    # logging.debug('reportHTML()')

    message = '<h2>AutoCoding of a Histopathology Report</h2>'
    response = reportJSON(True)
    siteLen = 5
    findLen = 8
    aihwLen = 5
    for row in response['grid']:
        SiteLen = len(row['site']) + len(row['site description']) + 4    # Allow for a trailing space
        FindingLen = len(row['finding']) + len(row['finding description']) + 4    # Allow for a trailing space
        AIHWlen = len(row['AIHW']) + 1      # Allow for a trailing space
        if SiteLen > siteLen:
            siteLen = SiteLen
        if FindingLen > findLen:
            findLen = FindingLen
        if AIHWlen > aihwLen:
            aihwLen = AIHWlen
    message += '<pre>' + '-' * (siteLen + findLen + aihwLen + 7) + '\n'

    if response['SCTprocedure']['code'] != '':
        message += f"Procedure: {response['SCTprocedure']['code']} - {response['SCTprocedure']['desc']}\n"
    else:
        message += 'Procedure: WARNING - No Procedure specified\n'

    message += f"+-{'-' * siteLen}+-{'-'* findLen}+-{'-' * aihwLen}+\n"
    message += f"| {'Site':{siteLen}}| {'Finding':{findLen}}| {'AIHW':{aihwLen}}|\n"
    message += f"+-{'-' * siteLen}+-{'-'* findLen}+-{'-' * aihwLen}+\n"

    # Next print the Grid (it is already in descending S, then descending E, then descending O order)
    for row in response['grid']:
        message += f"| {row['site'] + ' - ' + row['site description']:{siteLen}}"
        message += f"| {row['finding'] + ' - ' + row['finding description']:{findLen}}"
        message += f"| {row['AIHW']:{aihwLen}}|\n"
    message += f"+-{'-' * siteLen}+-{'-'* findLen}+-{'-' * aihwLen}+\n"

    # Now output the AIHW results
    message += 'AIHW\n'
    if response['AIHWprocedure']['code'] != '':
        message += f"Procedure: { response['O']['code']} - {response['AIHWprocedure']['desc']}\n"
    else:
        message += 'Procedure: WARNING - No Procedure specified\n'
    message += f"S: {response['S']['code']} - {response['S']['desc']}\n"
    message += f"E: {response['E']['code']} - {response['E']['desc']}\n"
    message += f"O: {response['O']['code']} - { response['O']['desc']}\n"
    message += '</pre><br>'
    if len(response['otherHysterectomies']) > 0:
        SCTcodeWidth = len('SCT code') + 1
        SCTdescWidth = len('SCT hysterectomy description') +1
        AIHWcodeWidth = len('AIHW code') + 1
        AIHWdescWidth = len('AIHW hysterectomy description') + 1
        for row in response['otherHysterectomies']:
            if len(row[0]) >= SCTcodeWidth:
                SCTcodeWidth = len(row[0]) + 1      # Allow for a trailing space
            if len(row[1]) >= SCTdescWidth:
                SCTdescWidth = len(row[1]) + 1      # Allow for a trailing space
            if len(row[2]) >= AIHWcodeWidth:
                AIHWcodeWidth = len(row[2]) + 1      # Allow for a trailing space
            if len(row[3]) >= AIHWdescWidth:
                AIHWdescWidth = len(row[3]) + 1      # Allow for a trailing space
        message += '<pre>Other Hysterectomies\n'
        message += f"+-{'-' * SCTcodeWidth}+-{'-' * SCTdescWidth}+-{'-' * AIHWcodeWidth}+-{'-' * AIHWdescWidth}+\n"
        message += f"| {'SCT code':{SCTcodeWidth}}| {'SCT hysterectomy description':{SCTdescWidth}}"
        message += f"| {'AIHW code':{AIHWcodeWidth}}| {'AIHW hysterectomy description':{AIHWdescWidth}}|\n"
        message += f"+-{'-' * SCTcodeWidth}+-{'-' * SCTdescWidth}+-{'-' * AIHWcodeWidth}+-{'-' * AIHWdescWidth}+\n"
        for row in response['otherHysterectomies']:
            message += f'| {row[0]:{SCTcodeWidth}}| {row[1]:{SCTdescWidth }}'
            message += f'| {row[2]:{AIHWcodeWidth}}| {row[3]:{AIHWdescWidth}}|\n'
        message += f"+-{'-' * SCTcodeWidth}+-{'-' * SCTdescWidth}+-{'-' * AIHWcodeWidth}+-{'-' * AIHWdescWidth}+\n"
        message += '</pre><br>'

    if len(response['otherProcedures']) > 0:
        SCTcodeWidth = len('SCT code') + 1
        SCTdescWidth = len('SCT hysterectomy description') + 1
        AIHWcodeWidth = len('AIHW code') + 1
        AIHWdescWidth = len('AIHW hysterectomy description') +1
        for row in response['otherProcedures']:
            if len(row[0]) >= SCTcodeWidth:
                SCTcodeWidth = len(row[0]) + 1      # Allow for a trailing space
            if len(row[1]) >= SCTdescWidth:
                SCTdescWidth = len(row[1]) + 1      # Allow for a trailing space
            if len(row[2]) >= AIHWcodeWidth:
                AIHWcodeWidth = len(row[2]) + 1      # Allow for a trailing space
            if len(row[3]) >= AIHWdescWidth:
                AIHWdescWidth = len(row[3]) + 1      # Allow for a trailing space
        message += '<pre>Other Procedures\n'
        message += f"+-{'-' * SCTcodeWidth}+-{'-' * SCTdescWidth}+-{'-' * AIHWcodeWidth}+-{'-' * AIHWdescWidth}+\n"
        message += f"| {'SCT code':{SCTcodeWidth}}| {'SCT hysterectomy description':{SCTdescWidth}}"
        message += f"| {'AIHW code':{AIHWcodeWidth}}| {'AIHW hysterectomy description':{AIHWdescWidth}}|\n"
        message += f"+-{'-' * SCTcodeWidth}+-{'-' * SCTdescWidth}+-{'-' * AIHWcodeWidth}+-{'-' * AIHWdescWidth}+\n"
        for row in response['otherProcedures']:
            message += f'| {row[0]:{SCTcodeWidth}}| {row[1]:{SCTdescWidth}}'
            message += f'| {row[2]:{AIHWcodeWidth}}| {row[3]:{AIHWdescWidth}}|\n'
        message += f"+-{'-' * SCTcodeWidth}+-{'-' * SCTdescWidth}+-{'-' * AIHWcodeWidth}+-{'-' * AIHWdescWidth}+\n"
        message += '</pre><br>'
    return message
