# pylint: disable=line-too-long, broad-exception-caught, invalid-name
'''
This is the histopathology autocoding analysis module
'''

import os
import sys
import logging
import json
from collections import OrderedDict
import functions as f
import data as d


def configure(wb):
    '''
    Configure the analysis
    Read in any histopathology specific worksheets from workbook wb
    '''

    configConcepts = set()        # The set of additional known concepts

    # Read in the Solution MetaThesaurus
    requiredColumns = ['MetaThesaurus code', 'MetaThesaurus description', 'Source', 'SourceCode']
    f.loadSimpleDictionarySheet(wb, 'analyze', 'Solution MetaThesaurus', requiredColumns, d.sd.SolutionMetaThesaurus)

    # Read in the AIHW Procedure and Finding codes and descriptions
    requiredColumns = ['AIHW', 'Description']
    f.loadSimpleDictionarySheet(wb, 'analyze', 'AIHW Procedure', requiredColumns, d.sd.AIHWprocedure)
    f.loadSimpleDictionarySheet(wb, 'analyze', 'AIHW Finding', requiredColumns, d.sd.AIHWfinding)

    # Read in the SNOMED CT Sites
    requiredColumns = ['MetaThesaurusID', 'SNOMED_CT Description', 'Site', 'SubSite']
    this_df = f.checkWorksheet(wb, 'analyze', 'Site', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        # logging.debug("sheet(Site), columns(%s), row(%s)", requiredColumns, row)
        concept = row.MetaThesaurusID
        if concept in d.sd.Site:
            logging.critical('Attempt to redefine site(%s)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if concept not in d.sd.SolutionMetaThesaurus:
            logging.critical('Site(%s) in worksheet(Site) in workbook(analyze) not in sheet SolutionMetaThesaurus', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if d.sd.SolutionMetaThesaurus[concept][1] != "SNOMEDCT_US":
            logging.critical('Site(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Site[concept] = {}
        configConcepts.add(concept)
        d.sd.Site[concept]['sct'] = d.sd.SolutionMetaThesaurus[concept][2]
        d.sd.Site[concept]['desc'] = d.sd.SolutionMetaThesaurus[concept][0]
        site = row.Site
        if site not in ['cervix', 'vagina', 'other', 'notStated']:
            logging.critical('Site(%s) in worksheet(Site) in workbook(analyze) not in "cervix", "vagina", "other" or "notStated"', site)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Site[concept]['site'] = site
        subsite = row.SubSite
        if subsite not in ['cervix', 'vagina', 'endom', 'other', 'notStated']:
            logging.critical('SubSite(%s) in worksheet(Site) in workbook(analyze) not in "cervix", "vagina", "endom", "other" or "notStated"', subsite)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Site[concept]['subsite'] = subsite

    # Now check that we have configurations for a few, fixed MetaThesaurus Site codes
    if d.sd.cervixUteri not in d.sd.Site:
        logging.critical('Missing definition for concept "%s" in worksheet(Site) in workbook(analyze)', d.sd.cervixUteri)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if d.sd.endomStructure not in d.sd.Site:
        logging.critical('Missing definition for concept "%s" in worksheet(Site) in workbook(analyze)', d.sd.endomStructure)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Read in the Findings
    requiredColumns = ['MetaThesaurusID', 'SNOMED_CT Description', 'Cervix', 'Vagina', 'Other', 'Not Stated']
    this_df = f.checkWorksheet(wb, 'analyze', 'Finding', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        # logging.debug("sheet(Finding), columns(%s), row(%s)", requiredColumns, row)
        concept = row.MetaThesaurusID
        if concept in d.sd.Finding:
            logging.critical('Attempt to redefine finding(%s)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Finding[concept] = {}
        configConcepts.add(concept)
        if concept not in d.sd.SolutionMetaThesaurus:
            logging.critical('Finding in worksheet(Site) in workbook(analyze) not in sheet SolutionMetaThesaurus')
            logging.shutdown()
            sys.stdout.flush()
            sys.exit(d.EX_CONFIG)
        if d.sd.SolutionMetaThesaurus[concept][1] != "SNOMEDCT_US":
            logging.critical('Finding(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Finding[concept]['sct'] = d.sd.SolutionMetaThesaurus[concept][2]
        d.sd.Finding[concept]['desc'] = d.sd.SolutionMetaThesaurus[concept][0]
        cervix = row.Cervix
        if cervix not in d.sd.AIHWfinding:
            logging.critical('Cervix code(%s) in worksheet(Finding) in workbook(analyze) is not a valid AIHW Finding code', cervix)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Finding[concept]['cervix'] = cervix
        vagina = row.Vagina
        if vagina not in d.sd.AIHWfinding:
            logging.critical('Vagina code(%s) in worksheet(Finding) in workbook(analyze) is not a valid AIHW Finding code', vagina)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Finding[concept]['vagina'] = vagina
        other = row.Other
        if other not in d.sd.AIHWfinding:
            logging.critical('Other code(%s) in worksheet(Finding) in workbook(analyze) is not a valid AIHW Finding code', other)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Finding[concept]['other'] = other
        notStated = row.Not_Stated
        if notStated not in d.sd.AIHWfinding:
            logging.critical('Not Stated code(%s) in worksheet(Finding) in workbook(analyze) is not a valid AIHW Finding code', notStated)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Finding[concept]['notStated'] = notStated

    # Now check that we have configurations for a few, fixed MetaThesaurus Finding codes
    if d.sd.normalCervixCode not in d.sd.Finding:
        logging.critical('Missing definition for concept "%s" in worksheet(Finding) in workbook(analyze)', d.normalCervixCode)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if d.sd.normalEndomCode not in d.sd.Finding:
        logging.critical('Missing definition for concept "%s" in worksheet(Finding) in workbook(analyze)', d.normalEndomCode)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)
    if d.sd.noAbnormality not in d.sd.Finding:
        logging.critical('Missing definition for concept "%s" in worksheet(Finding) in workbook(analyze)', d.noAbnormality)
        logging.shutdown()
        sys.exit(d.EX_CONFIG)

    # Read in the Procedures
    requiredColumns = ['MetaThesaurusID', 'SNOMED_CT Description', 'Cervix', 'Vagina', 'Other', 'Not Stated', 'Cervix Rank', 'Vagina Rank', 'Other Rank', 'Not Stated Rank']
    this_df = f.checkWorksheet(wb, 'analyze', 'Procedure', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        # logging.debug("sheet(Procedure), columns(%s), row(%s)", requiredColumns, row)
        concept = row.MetaThesaurusID
        if concept in d.sd.Procedure:
            logging.critical('Attempt to redefine procedure(%s)', str(concept))
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Procedure[concept] = {}
        configConcepts.add(concept)
        if concept not in d.sd.SolutionMetaThesaurus:
            logging.critical('Procedure(%s) in worksheet(Site) in workbook(analyze) not in sheet SolutionMetaThesaurus', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if d.sd.SolutionMetaThesaurus[concept][1] != "SNOMEDCT_US":
            logging.critical('Procedure(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Procedure[concept]['sct'] = d.sd.SolutionMetaThesaurus[concept][2]
        d.sd.Procedure[concept]['desc'] = d.sd.SolutionMetaThesaurus[concept][0]
        d.sd.Procedure[concept]['site'] = {}
        cervix = row.Cervix
        d.sd.Procedure[concept]['site']['cervix'] = cervix
        if (cervix not in d.sd.AIHWprocedure) and (cervix != '99'):
            logging.critical('Cervix code(%s) in worksheet(Procedure) in workbook(analyze) is not a valid AIHW Procedure code', cervix)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        vagina = row.Vagina
        if (vagina not in d.sd.AIHWprocedure) and (vagina != '99'):
            logging.critical('Vagina code(%s) in worksheet(Procedure) in workbook(analyze) is not a valid AIHW Procedure code', vagina)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Procedure[concept]['site']['vagina'] = vagina
        other = row.Other
        if (other not in d.sd.AIHWprocedure) and (other != '99'):
            logging.critical('Other code(%s) in worksheet(Procedure) in workbook(analyze) is not a valid AIHW Procedure code', other)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Procedure[concept]['site']['other'] = other
        notStated = row.Not_Stated
        if (notStated not in d.sd.AIHWprocedure) and (notStated != '99'):
            logging.critical('Not Stated code(%s) in worksheet(Procedure) in workbook(anallyze) is not a valid AIHW Procedure code', notStated)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Procedure[concept]['site']['notStated'] = notStated
        d.sd.Procedure[concept]['rank'] = {}
        cervixRank = row.Cervix_Rank
        d.sd.Procedure[concept]['rank']['cervix'] = cervixRank
        vaginaRank = row.Vagina_Rank
        d.sd.Procedure[concept]['rank']['vagina'] = vaginaRank
        otherRank = row.Other_Rank
        d.sd.Procedure[concept]['rank']['other'] = otherRank
        notStatedRank = row.Not_Stated_Rank
        d.sd.Procedure[concept]['rank']['notStated'] = notStatedRank

    # Read in the site implied concepts
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID']
    this_df = f.checkWorksheet(wb, 'analyze', 'site implied', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(site implied), columns(%s), record(%s)", requiredColumns, record)
        concept = record[0]
        if concept in d.sd.SiteImplied:
            logging.critical('Attempt to redefine list of implied sites for concept(%s) in worksheet(site impllied) in workbook(analyze)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.SiteImplied[concept] = set()
        j = 1
        while (j < len(record)) and (record[j] is not None):
            implied = record[j]
            if implied not in d.sd.Site:
                logging.critical('Attempt to define an implied Site(%s) for concept(%s) in worksheet(site implied) in workbook(analyze), but (%s) is not defined as a Site',
                                 implied, concept, implied)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            d.sd.SiteImplied[concept].add(implied)
            j += 1
        configConcepts.add(concept)

    # Read in the finding implied concepts
    requiredColumns = ['MetaThesaurusID', 'HistopathologyFindingID']
    this_df = f.checkWorksheet(wb, 'analyze', 'finding implied', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(finding implied), columns(%s), record(%s)", requiredColumns, record)
        concept = record[0]
        if concept in d.sd.FindingImplied:
            logging.critical('Attempt to redefine list of implied findings for concept(%s)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.FindingImplied[concept] = set()
        j = 1
        while (j < len(record)) and (record[j] is not None):
            implied = record[j]
            if implied not in d.sd.Finding:
                logging.critical('Attempt to define an implied Finding(%s) for concept(%s) in worksheet(finding implied) in workbook(analyze), but (%s) is not defined as a Finding',
                                 implied, concept, implied)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            d.sd.FindingImplied[concept].add(implied)
            j += 1
        configConcepts.add(concept)

    # Read in the site restricted concepts
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteIDs']
    this_df = f.checkWorksheet(wb, 'analyze', 'site restricted', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(site restricted), columns(%s), record(%s)", requiredColumns, record)
        concept = record[0]
        if concept in d.sd.SiteRestrictions:
            logging.critical('Attempt to redefine site restrictions list for finding(%s) in worksheet(site restricted) in workbook(analyze)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.SiteRestrictions[concept] = set()
        if concept not in d.sd.Finding:
            logging.critical('Attempt to define an restriction on Finding(%s) in worksheet(site restricted) in workbook(analyze), but (%s) is not defined as a Finding',
                             concept, concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        j = 1
        while (j < len(record)) and (record[j] is not None):
            restriction = record[j]
            if restriction not in d.sd.Site:
                logging.critical('Attempt to define a restriction of Site(%s) for Finding(%s) in worksheet(site restricted) in workbook(analyze), but (%s) is not defined as a Site',
                                 restriction, concept, restriction)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            d.sd.SiteRestrictions[concept].add(restriction)
            j += 1

    # Read in the site impossible concepts
    this_df = f.checkWorksheet(wb, 'analyze', 'site impossible', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(site impossible), columns(%s), record(%s)", requiredColumns, record)
        concept = record[0]
        if concept in d.sd.SiteImpossible:
            logging.critical('Attempt to redefine site impossible list for finding(%s) in worksheet(site impossible) in workbook(analyze)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.SiteImpossible[concept] = set()
        if concept not in d.sd.Finding:
            logging.critical('Attempt to define an impossible Site for Finding(%s) in worksheet(site impossible) in workbook(analyze), but (%s) is not defined as a Finding',
                             concept, concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        j = 1
        while (j < len(record)) and (record[j] is not None):
            restriction = record[j]
            if restriction not in d.sd.Site:
                logging.critical('Attempt to define an impossible Site(%s) for Finding(%s) in worksheet(site impossible) in workbook(analyze), but (%s) is not defined as a Site',
                                 restriction, concept, restriction)
                logging.shutdown()
                sys.exit(d.EX_CONFIG)
            d.sd.SiteImpossible[concept].add(restriction)
            j += 1

    # Read in the site likelyhood concepts
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID|rank']
    this_df = f.checkWorksheet(wb, 'analyze', 'site likely', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(site likely), columns(%s), record(%s)", requiredColumns, record)
        concept = record[0]
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
        j = 1
        while (j < len(record)) and (record[j] is not None):
            likelyhood = record[j]
            bits = likelyhood.split('|')
            if len(bits) != 2:
                logging.critical('likelyhood (%s) for concept(%s) in worksheet(site likely) in workbook(analyze) is incorrectly formatted',
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
            j += 1

    # Read in the site default concepts
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID']
    this_df = f.checkWorksheet(wb, 'analyze', 'site default', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        # logging.debug("sheet(site default), columns(%s), row(%s)", requiredColumns, row)
        concept = row.MetaThesaurusID
        default = row.HistopathologySiteID
        if concept in d.sd.SiteDefault:
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
        d.sd.SiteDefault[concept] = default

    # Read in the diagnosis implied site/finding pairs
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID', 'HistopathologyFindingID']
    this_df = f.checkWorksheet(wb, 'analyze', 'diagnosis implied', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        # logging.debug("sheet(diagnosis implied), columns(%s), row(%s)", requiredColumns, row)
        diagnosis = row.MetaThesaurusID
        site = row.HistopathologySiteID
        finding = row.HistopathologyFindingID
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

    # Read in the implied procedure concept and the concept that implies that procedure concept
    requiredColumns = ['MetaThesaurusID', 'HistopathologyProcedureID']
    this_df = f.checkWorksheet(wb, 'analyze', 'procedure implied', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        # logging.debug("sheet(procedure implied), columns(%s), row(%s)", requiredColumns, row)
        concept = row.MetaThesaurusID
        procedure = row.HistopathologyProcedureID
        if concept in d.sd.ProcedureImplied:
            logging.critical('Attempt to redefine implied procedure for concept(%s) in worksheet(procedure implied) in workbook(analyze) from (%s) to (%s)',
                             concept, d.sd.ProcedureImplied[concept], procedure)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if procedure not in d.sd.Procedure:
            logging.critical('Attempt to define an implied procedure(%s) for concept(%s) in worksheet(procedure implied) in workbook(analyze), but (%s) is not defined as a Procedure',
                             procedure, concept, procedure)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.ProcedureImplied[concept] = procedure
        configConcepts.add(concept)

    # Read in the defined procedure concept and the concepts pairs that define that procedure concept
    requiredColumns = ['HistopathologyProcedureID', 'HistopathologySiteID', 'HistopathologyFindingID']
    this_df = f.checkWorksheet(wb, 'analyze', 'procedure defined', requiredColumns, True)
    for row in this_df.itertuples():
        if row.HistopathologyProcedureID is None:
            break
        # logging.debug("sheet(procedure defined), columns(%s), row(%s)", requiredColumns, row)
        procedure = row.HistopathologyProcedureID
        site = row.HistopathologySiteID
        finding = row.HistopathologyFindingID
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

    # Read in the report site sequence concept sets - sets of MetaThesaurus ConceptIDs which, when found in sequence, imply a higher MetaThesaurus ConceptID Site.
    requiredColumns = ['SolutionID', 'MetaThesaurus or Solution IDs']
    this_df = f.checkWorksheet(wb, 'analyze', 'report site seq concept sets', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        # logging.debug("sheet(report site seq concept sets), columns(%s), record(%s)", requiredColumns, record)
        site = record[0]
        if site not in d.sd.Site:
            logging.critical('Attempt to define a report site sequence concept set with Site(%s) in worksheet(report site seq concept sets) in workbook(analyze) but (%s) is not defined as a Site',
                             site, site)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        configConcepts.add(site)
        j = 1
        concepts = []
        while (j < len(record)) and (record[j] is not None):
            eachConcept = record[j]
            concept, isNeg = f.checkConfigConcept(eachConcept)
            concepts.append([concept, isNeg])
            configConcepts.add(concept)
            j += 1
        d.sd.ReportSites.append([site, concepts])

    # Return the additional known concepts
    return (configConcepts)


def gridAppend (sentenceNo, start, thisSite, thisSiteHistory, thisFinding, findingCode, subSiteCode):
    # Append this Site and Finding to the grid (unless it's historical)
    if not thisSiteHistory:
        solution['grid'].append((thisSite, thisFinding, findingCode))
        if subSiteCode == 'cervix' :
            solution['cervixDone'] = True
        elif subSiteCode == 'endom' :
            solution['endomDone'] = True
    # Check if this Site/Finding pair defines a Procedure
    if (thisSite, thisFinding) not in d.sd.ProcedureDefined:
        return
    thisProcedure = d.sd.ProcedureDefined[(thisSite, thisFinding)]
    # Record this procedure
    if thisSiteHistory:
        logging.info('saving defined history procedure:%s - %s', str(concept), str(d.sd.Procedure[concept]['desc']))
        solution['historyProcedure'][start] = (thisProcedure, sentenceNo)
    else:
        logging.info('saving defined procedure:%s - %s', str(concept), str(d.sd.Procedure[concept]['desc']))
        if d.sd.Procedure[procedure]['site']['cervix'] == '7' :
            solution['hysterectomy'].add((procedure, sentenceNo))
        else:
            solution['procedure'].add((procedure, sentenceNo))
    return


def analyze():
    '''
Analyze the sentences and concepts and build up the results which are stored in the this.solution dictionary
    '''

    # Find all the sentence Sites and Finding, plus track Procedures
    solution['historyProcedure'] = {}
    solution['hysterectomy'] = set()
    solution['procedure'] = set()
    solution['unsatFinding'] = None
    solution['cervixFound'] = False
    solution['endomFound'] = False
    SentenceSites = {}                    # The Sites found in each sentence
    SentenceFindings = {}                # The Findings found in each sentence
    for sentenceNo in range(len(this.sentences)) :            # Step through each sentence looking for implied Sites preceed any SentenceSites
        sentence = this.sentences[sentenceNo]
        sentenceStart = sentence[2]
        sentenceLength = sentence[3]
        SentenceSites[sentenceNo] = OrderedDict()
        SentenceFindings[sentenceNo] = OrderedDict()
        document = this.sentences[sentenceNo][6]    # Sentences hold mini-documents
        for start in sorted(document, key=int) :        # We step through all concepts in this sentence
            for j in range(len(document[start])) :            # Step through the list of alternate concepts at this point in this sentence
                concept = document[start][j]['concept']

                if document[start][j]['used'] == True :        # Skip used concepts [only Findings get 'used']
                    continue

                # We only report positive procedures, sites and findings
                if document[start][j]['negation'] != '0' :    # Skip negated and ambiguous concepts
                    continue

                isHistory = document[start][j]['history']    # A history concept - information about things that predate this analysis.

                # Check if this concept is a Procedure
                if concept in d.sd.Procedure:
                    # Check if it's a history procedure
                    if isHistory :    # Save the last history procedure
                        logging.info('saving history procedure:%s - %s', str(concept), str(d.sd.Procedure[concept]['desc']))
                        this.solution['historyProcedure'][start] = (concept, sentenceNo)
                    else:
                        logging.info('saving procedure:%s - %s', str(concept), str(d.sd.Procedure[concept]['desc']))
                        # Check if this is a hysterectomy - hysterectomy is hysterectomy at all sites, so only checking 'cervix' will be fine
                        if d.sd.Procedure[concept]['site']['cervix'] == '7' :
                            this.solution['hysterectomy'].add((concept, sentenceNo))
                        else:
                            this.solution['procedure'].add((concept, sentenceNo))
                    continue

                # Check if this concept is a Finding
                if concept in d.sd.Finding:
                    # Save the last Site Finding, at this point, in this sentence
                    # logging.debug('found finding concept (%s) in sentence(%d)', concept, sentenceNo)
                    if start not in SentenceFindings[sentenceNo]:
                        SentenceFindings[sentenceNo][start] = []
                    SentenceFindings[sentenceNo][start].append((concept, isHistory))        # The Sentence Finding(s)

                    # Check if this is an unsatifactory Finding
                    if d.sd.Finding[concept]['cervix'] == 'SU':
                        this.solution['unsatFinding'] = concept
                    continue

                # Check if this concept is a Site
                if concept in d.sd.Site:
                    # Save the last Site concept, at this point, in this sentence
                    # logging.debug('found site concept (%s) in sentence(%d)', concept, sentenceNo)
                    if start not in SentenceSites[sentenceNo]:
                        SentenceSites[sentenceNo][start] = []
                    SentenceSites[sentenceNo][start].append((concept, isHistory, False))        # The Sentence Site - not used

                    # Mark cervixFound or endomFound if appropriate
                    subsite = d.sd.Site[concept]['subsite']
                    if (subsite == 'cervix') :
                        if not this.solution['cervixFound']:
                            this.solution['cervixFound'] = True
                            logging.info('cervixFound')
                    elif (subsite == 'endom') :
                        if not this.solution['endomFound']:
                            this.solution['endomFound'] = True
                            logging.info('endomFound')
                    continue
            # end of all the alternate concepts
        # end of all the concepts in this sentence
    # end of sentence

    # Now look through each sentence for Site/Finding pairs
    this.solution['grid'] = []
    this.solution['cervixDone'] = False
    this.solution['endomDone'] = False
    for sentenceNo in range(len(this.sentences)) :            # Step through each sentence
        # Check if at least one Site was found in this sentence
        if len(SentenceSites[sentenceNo]) == 0 :
            continue
        # Check if at least one Finding was found in this sentence
        if len(SentenceFindings[sentenceNo]) == 0 :
            continue

        # We have both Sites and Findings in this sentence.
        # For each Finding, work through every Site and calculate a "best fit".
        # Where "best fit" is a combination of 'likelyhood' and 'distance'.
        # 'likelyhood' is a ranking between 1 and 7, which can be set in configuration (4 is the default)
        # 'distance' is then number of other Sites between this Finding and this Site.
        # We subtract the 'distance' from the 'likelyhood' in order to score each Site for this Finding.
        # Highest score wins.

        # Walk through the findings one at a time
        for FSindex in range(len(SentenceFindings[sentenceNo]) - 1, -1, -1):
            FindingStart = list(SentenceFindings[sentenceNo])[FSindex]

            # Find the nearest Site
            best = None
            bestIndex = None
            SSindex = -1
            for SiteStart in SentenceSites[sentenceNo]:
                SSindex += 1
                if (best is None) or abs(FindingStart - SiteStart) < best:
                    best = abs(FindingStart - SiteStart)
                    bestIndex = SSindex

            # Then wak though all the Findings at this start - looking for the best Site
            for FSsubIndex in range(len(SentenceFindings[sentenceNo][FindingStart]) - 1, -1, -1):
                thisFinding, thisFindingHistory = SentenceFindings[sentenceNo][FindingStart][FSsubIndex]

                # Now test every site
                bestSiteStart = None
                bestSiteSubIndex = None
                bestRank = None
                SSindex = -1
                for SiteStart in SentenceSites[sentenceNo]:
                    SSindex += 1
                    for SSsubIndex in range(len(SentenceSites[sentenceNo][SiteStart])):
                        thisSite, thisSiteHistory, thisSiteUsed = SentenceSites[sentenceNo][SiteStart][SSsubIndex]
                        # If they are from different histories then they are not a match
                        if thisFindingHistory != thisSiteHistory:
                            continue
                        # Skip if not in restricted list
                        if (thisFinding in d.sd.SiteRestrictions) and len(d.sd.SiteRestrictions[thisFinding]) > 0:
                            if thisSite not in d.sd.SiteRestrictions[thisFinding]:
                                continue
                        # Skip if in impossible list
                        if (thisFinding in d.sd.SiteImpossible) and len(d.sd.SiteImpossible[thisFinding]) > 0:
                            if thisSite in d.sd.SiteImpossible[thisFinding]:
                                continue
                        # Compute the ranking
                        if (thisFinding in d.sd.SiteRank) and (thisSite in d.sd.SiteRank[thisFinding]):
                            rank = d.sd.SiteRank[thisFinding][thisSite]
                        else:
                            rank = 4
                        rank -= abs(SSindex - bestIndex)
                        if (bestRank is None) or (rank < bestRank):
                            bestRank = rank
                            bestSiteStart = SiteStart
                            bestSiteSubIndex = SSsubIndex

                # If we found a Site add it to the grid, mark the Site as used and delete this Finding from SentenceFindings
                if bestRank is not None:
                    thisSite, thisSiteHistory, thisSiteUsed = SentenceSites[sentenceNo][bestSiteStart][bestSiteSubIndex]
                    siteCode = d.sd.Site[thisSite]['site']
                    subSiteCode = d.sd.Site[thisSite]['subsite']
                    findingCode = d.sd.Finding[thisFinding][siteCode]
                    gridAppend(this, d.sd, sentenceNo, FindingStart, thisSite, thisSiteHistory, thisFinding, findingCode, subSiteCode)
                    # Delete this finding and move onto the next one
                    del SentenceFindings[sentenceNo][FindingStart][FSsubIndex]
                    if len(SentenceFindings[sentenceNo][FindingStart]) == 0:
                        del SentenceFindings[sentenceNo][FindingStart]
                    # Mark the site as used
                    SentenceSites[sentenceNo][bestSiteStart][bestSiteSubIndex] = (thisSite, thisSiteHistory, True)
        # end of this sentence
    # end of sentences

    # Now re-work the sentences looking for remaining Findings.
    # These can occur when the site is in a subheading, with all the finding in following sentence below that subheading
    for sentenceNo in range(len(this.sentences) - 1) :            # Step through each sentence - except that last one - no where to look forward from there
        # Check if there is a remaining found Finding in this sentence
        if len(SentenceFindings[sentenceNo]) == 0 :
            logging.debug('No unmatched findings in sentence(%d)', sentenceNo)
            continue

        # Check a number of the sentences around this Finding
        maxGap = 2            # Sites are really only valid for two sentences (unless the grid is empty)
        if len(this.solution['grid']) == 0 :
            maxGap = 4        # in which case they are valid for 4
        # Find the Sites across these sentences
        localSites = []
        for sno in range(max(0, sentenceNo - maxGap), min(sentenceNo + maxGap, len(this.sentences))):
            if sno == sentenceNo:        # No sites in this sentence matched
                localSites.append((sno, 0))        # Add a marker for the "sentence containing this Finding"
                findingIndex = len(localSites)
                continue
            if len(SentenceSites[sno]) == 0 :
                continue
            for SiteStart in SentenceSites[sno]:
                localSites.append((sno, SiteStart))
        # If there are no sites around this sentence - go to the next sentence
        if len(localSites) == 1:        # Just the "this sentence" marker
            break

        # Walk through the findings in this sentence
        for FSindex in range(len(SentenceFindings[sentenceNo]) - 1, -1, -1):
            FindingStart = list(SentenceFindings[sentenceNo])[FSindex]
            # Then wak though all the Findings at this start - looking for the best Site
            for FSsubIndex in range(len(SentenceFindings[sentenceNo][FindingStart]) - 1, -1, -1):
                thisFinding, thisFindingHistory = SentenceFindings[sentenceNo][FindingStart][FSsubIndex]

                # Find the best site from the local sites
                bestSno = None
                bestSiteStart = None
                bestSiteSubIndex = None
                bestRank = None
                SSindex = -1
                for SSindex in range(len(localSites)):
                    sno, SiteStart = localSites[SSindex]
                    if sno == sentenceNo:    # The "sentence containing this Finding" marker
                        continue
                    for SSsubIndex in range(len(SentenceSites[sno][SiteStart])):
                        thisSite, thisSiteHistory, thisSiteUsed = SentenceSites[sno][SiteStart][SSsubIndex]
                        # If they are from different histories then they are not a match
                        if thisFindingHistory != thisSiteHistory:
                            continue
                        # Skip if not in restricted list
                        if (thisFinding in d.sd.SiteRestrictions) and len(d.sd.SiteRestrictions[thisFinding]) > 0:
                            if thisSite not in d.sd.SiteRestrictions[thisFinding]:
                                continue
                        # Skip if in impossible list
                        if (thisFinding in d.sd.SiteImpossible) and len(d.sd.SiteImpossible[thisFinding]) > 0:
                            if thisSite in d.sd.SiteImpossible[thisFinding]:
                                continue
                        # Compute the ranking
                        if (thisFinding in d.sd.SiteRank) and (thisSite in d.sd.SiteRank[thisFinding]):
                            rank = d.sd.SiteRank[thisFinding][thisSite]
                        else:
                            rank = 4
                        rank -= abs(SSindex - findingIndex)
                        if (bestRank is None) or (rank < bestRank):
                            bestRank = rank
                            bestSno = sno
                            bestSiteStart = SiteStart
                            bestSiteSubIndex = SSsubIndex
                # If we found a Site add it to the grid, mark the Site as used and delete this Finding from SentenceFindings
                if bestRank is not None:
                    thisSite, thisSiteHistory, thisSiteUsed = SentenceSites[bestSno][bestSiteStart][bestSiteSubIndex]
                    siteCode = d.sd.Site[thisSite]['site']
                    subSiteCode = d.sd.Site[thisSite]['subsite']
                    findingCode = d.sd.Finding[thisFinding][siteCode]
                    gridAppend(this, d.sd, sentenceNo, FindingStart, thisSite, thisSiteHistory, thisFinding, findingCode, subSiteCode)
                    # Delete this finding and move onto the next one
                    del SentenceFindings[sentenceNo][FindingStart][FSsubIndex]
                    if len(SentenceFindings[sentenceNo][FindingStart]) == 0:
                        del SentenceFindings[sentenceNo][FindingStart]
                    # Mark the site as used
                    SentenceSites[bestSno][bestSiteStart][bestSiteSubIndex] = (thisSite, thisSiteHistory, True)

    # Report unused Sites
    for sentenceNo in SentenceSites:
        for SiteStart in SentenceSites[sentenceNo]:
            for SSsubIndex in range(len(SentenceSites[sentenceNo][SiteStart])):
                thisSite, thisSiteHistory, thisSiteUsed = SentenceSites[sentenceNo][SiteStart][SSsubIndex]
                if thisSiteUsed:
                    continue
                logging.info('Unused Site in sentence(%s):%s - %s', sentenceNo, thisSite, d.sd.Site[thisSite]['desc'])

    # Report unused Findings
    for sentenceNo in SentenceFindings:
        for FindingStart in SentenceFindings[sentenceNo]:
            for FSsubIndex in range(len(SentenceFindings[sentenceNo][FindingStart])):
                thisFinding, thisFindingHistory = SentenceFindings[sentenceNo][FindingStart][FSsubIndex]
                if thisFinding in d.sd.SiteDefault:    # Check if we have a default site
                    thisSite = d.sd.SiteDefault
                    siteCode = d.sd.Site[thisSite]['site']
                    subSiteCode = d.sd.Site[thisSite]['subsite']
                    findingCode = d.sd.Finding[thisFinding][siteCode]
                    gridAppend(this, d.sd, sentenceNo, FindingStart, thisSite, thisSiteHistory, thisFinding, findingCode, subSiteCode)
                else:
                    logging.warning('Unused Finding in sentence(%s):%s - %s', sentenceNo, thisFinding, d.sd.Finding[thisFinding]['desc'])

    # Make sure there is something in the grid
    if len(this.solution['grid']) == 0 :    # We have no Site/Finding pairs (which means no usable Findings or they would have been handled above)
        logging.info('Empty grid')
        # But we may have usable sites (Report Sites) in the document, which we can pair with 'nothing found' - check each in order
        ReportSites = []
        for setNo in range(len(d.sd.ReportSites)):
            conceptNo = 0
            for sentenceNo in range(len(this.sentences)) :            # Step through each sentence
                document = this.sentences[sentenceNo][6]    # Sentences hold mini-documents
                for start in sorted(document, key=int) :        # We step through all concepts in this sentence
                    for j in range(len(document[start])) :            # Step through the list of alternate concepts at this point in this sentence
                        concept = document[start][j]['concept']

                        if document[start][j]['used'] == True :        # Skip used concepts [only Findings get 'used']
                            continue

                        if document[start][j]['history'] :            # Skip historical concepts
                            continue

                        concept = document[start][j]['concept']
                        isNeg =  document[start][j]['negation']        # Check negation matches

                        # Check if this alternate concept at 'start' is the next one in this Report Site Sequence concept sequence set
                        found = False
                        thisNeg =  d.sd.ReportSites[setNo][conceptNo][1]        # The desired negation
                        if concept == d.sd.ReportSites[setNo][conceptNo][0]:    # A matching concept
                            if thisNeg == isNeg :
                                found = True        # With a mathing negation
                            elif (isNeg in ['2', '3']) and (thisNeg in ['2', '3']) :
                                found = True        # Or a near enough negation (both ambiguous)
                        if not found:    # Check the special case of a repetition of the first concept in the set
                            # We don't handle repetitions within a set - just a repetition of the first concept
                            # i.e.looking for concept 'n' - found concept 0 [this set, array of concepts in dict, first entry, concept]
                            if concept == d.sd.ReportSites[setNo][0][0]:
                                # Found the first concept - restart the multi-sentence counter
                                conceptNo = 0
                            continue
                        # logging.debug('Concept (%s) (for sentence Report Site Sequence concept set[%d]) found', concept, setNo)
                        conceptNo += 1
                        if conceptNo == len(d.sd.ReportSites[setNo]) :
                            # We have a full concept sequence set - so save the report site
                            ReportSites.append(d.sd.ReportSites[setNo][0])

        # Now check the ReportSites
        for thisSite in ReportSites :
            subsite = d.sd.Site[thisSite]['subsite']
            if subsite == 'cervix' :
                if this.solution['cervixDone']:
                    continue
                if this.solution['unsatFinding'] is not None :
                    thisFinding = this.solution['unsatFinding']
                    findingCode = 'SU'
                elif this.solution['cervixFound']:
                    thisFinding = normalCervixCode
                    findingCode = 'S1'
                else :
                    thisFinding = noAbnormality
                    findingCode = 'S1'
                # logging.debug('cervical ReportSite:%s', str(thisSite))
                gridAppend(this, d.sd, 0, 0, thisSite, False, thisFinding, findingCode, subSite)
            elif subsite == 'endom' :
                if this.solution['endomDone']:
                    continue
                if this.solution['unsatFinding'] is not None :
                    Finding = this.solution['unsatFinding']
                    findingCode = 'ON'
                elif this.solution['endomFound']:
                    Finding = normalEndomCode
                    findingCode = 'ON'
                else :
                    Finding = noAbnormality
                    findingCode = 'E1'
                gridAppend(this, d.sd, 0, 0, thisSite, False, thisFinding, findingCode, subSite)
                # logging.debug('endometrial ReportSite:%s', str(Site))
            else :
                logging.info('other ReportSite:%s', str(Site))
                if this.solution['unsatFinding'] is not None :
                    gridAppend(this, d.sd, 0, 0, thisSite, False, this.solution['unsatFinding'], 'ON', '')
                else :
                    gridAppend(this, d.sd, 0, 0, thisSite, False, noAbnormality, 'ON', '')
                break
    
    # Now add any 'normal' finding
    logging.info('cervixFound:%s, cervixDone:%s', this.solution['cervixFound'], this.solution['cervixDone'])
    if this.solution['cervixFound'] and not this.solution['cervixDone']:
        gridAppend(this, d.sd, 0, 0, cervixUteri, False, normalCervixCode, 'S1', 'cervix')
    logging.info('endomFound:%s, endomDone:%d', this.solution['endomFound'], this.solution['endomDone'])
    if this.solution['endomFound'] and not this.solution['endomDone']:
        gridAppend(this, d.sd, 0, 0, endomStructure, False, normalEndomCode, 'O1', 'endom')

    if len(this.solution['grid']) == 0 :        # We still have nothing - So report No Topopgraphy/No abnormality
        gridAppend(this, d.sd, 0, 0, '', False, noAbnormality, 'ON', '')

    # We need to sort the grid - we'll put the AIHW finding codes (modified) into the sorting hat
    this.solution['sortingHat'] = []
    for i in range(len(this.solution['grid'])):
        findingCode = this.solution['grid'][i][2]
        if findingCode[:1] == 'S':
            if findingCode[1:2] == 'U':
                findingCode = 'C' + findingCode
            elif findingCode[1:2] == 'N':
                findingCode = 'B' + findingCode
            else:
                findingCode = 'A' + findingCode
        elif findingCode[:1] == 'E':
            if findingCode[1:2] == 'U':
                findingCode = 'G' + findingCode
            elif findingCode[1:2] == 'N':
                findingCode = 'F' + findingCode
            else:
                findingCode = 'E' + findingCode
        else:
            if findingCode[1:2] == 'U':
                findingCode = 'W' + findingCode
            elif findingCode[1:2] == 'N':
                findingCode = 'V' + findingCode
            else:
                findingCode = 'U' + findingCode
        this.solution['sortingHat'].append([findingCode, i])

    # Create a sorted grid, weed out duplicates and find the highest S, E and O codes
    foundRows = set()
    this.solution['sortedGrid'] = []
    this.solution['S'] = None
    this.solution['E'] = None
    this.solution['O'] = None
    for row in sorted(this.solution['sortingHat']):
        index = row[1]
        thisSite = this.solution['grid'][index][0]
        thisFinding = this.solution['grid'][index][1]
        thisAIHW = this.solution['grid'][index][2]
        thisRow = thisSite + '|' + thisFinding
        if thisRow not in foundRows:
            foundRows.add(thisRow)
            if thisAIHW[:1] == 'S':
                if this.solution['S'] is None:
                    this.solution['S'] = thisAIHW
            elif thisAIHW[:1] == 'E':
                if this.solution['E'] is None:
                    this.solution['E'] = thisAIHW
            else:
                if this.solution['O'] is None:
                    this.solution['O'] = thisAIHW
            this.solution['sortedGrid'].append([thisSite, thisFinding, thisAIHW])
    if this.solution['S'] is None:
        this.solution['S'] = 'SN'
    if this.solution['E'] is None:
        this.solution['E'] = 'EN'
    if this.solution['O'] is None:
        this.solution['O'] = 'ON'

    # If we have no procedures, but we have a history procedure, then that's as good as it gets
    # Promote the last history procedure found to procedures and remove from the set of history procedures
    reportedProcs = set()
    if (len(this.solution['hysterectomy']) == 0) and (len(this.solution['procedure']) == 0):
        if len(this.solution['historyProcedure']) > 0:
            histStart = sorted(this.solution['historyProcedure'])[-1]
            histProc, histProcSno = this.solution['historyProcedure'][histStart]
            this.solution['procedure'].add((histProc, histProcSno))
            reportedProcs.add(histProc)
            del this.solution['historyProcedure'][histStart]

    # Now lets work out those Procedures - start by finding the top site
    # We have some defaults in case the grid only has 'Topography not assigned'
    topSite = this.solution['sortedGrid'][0][0]
    if topSite != '' :
        TopSite = d.sd.Site[topSite]['site']
        TopSubSite = d.sd.Site[topSite]['subsite']
        if TopSubSite == 'notStated':
            TopSubSite = 'other'
    else :
        TopSite = 'cervix'
        TopSubSite = 'cervix'
    # logging.debug('topSite:%s', str(TopSite))

    # Compute the SCTprocedure and AIHWprocedure
    this.solution['SCTprocedure'] = {}
    this.solution['AIHWprocedure'] = {}
    if len(this.solution['hysterectomy']) > 0 :
        thisProcedure, thisSno = list(this.solution['hysterectomy'])[0]
        logging.info('Hysterectomy procedure(%s):%s - %s',
                          thisProcedure, d.sd.Procedure[thisProcedure]['sct'], d.sd.Procedure[thisProcedure]['desc'])
        this.solution['SCTprocedure']['code'] = d.sd.Procedure[thisProcedure]['sct']
        this.solution['SCTprocedure']['desc'] = d.sd.Procedure[thisProcedure]['desc']
        this.solution['AIHWprocedure']['code'] = '7'
        this.solution['AIHWprocedure']['desc'] = d.sd.AIHWprocedure['7']
        reportedProcs.add(thisProcedure)
        this.solution['hysterectomy'].remove((thisProcedure, thisSno))
    elif len(this.solution['procedure']) > 0 :        # Multiple procedures - find the highest ranked procedure for the top site
        rank = -1
        rankProc = None
        randSno = None
        # We need to print the highest ranked procedure
        for thisProc, thisSno in this.solution['procedure'] :
            if TopSubSite not in d.sd.Procedure[thisProc]['rank']:
                thisRank = int(d.sd.Procedure[thisProc]['rank']['cervix'])
            else:
                thisRank = int(d.sd.Procedure[thisProc]['rank'][TopSubSite])
            if (thisRank > rank) and (thisRank != 99):        # Filter out invalid procedures
                rank = thisRank
                rankProc = thisProc
                rankSno = thisSno
        if rankProc is None:        # None of the procedures were valid
            logging.info('No valid procedure')
            this.solution['SCTprocedure']['code'] = 'WARNING'
            this.solution['SCTprocedure']['desc'] = 'No Procedure specified'
            this.solution['AIHWprocedure']['code'] = 'WARNING'
            this.solution['AIHWprocedure']['desc'] = 'No Procedure specified'
        else:
            logging.info('Other procedure(%s):%s - %s',
                              rankProc, d.sd.Procedure[rankProc]['sct'], d.sd.Procedure[rankProc]['desc'])
            this.solution['SCTprocedure']['code'] = d.sd.Procedure[rankProc]['sct']
            this.solution['SCTprocedure']['desc'] = d.sd.Procedure[rankProc]['desc']
            AIHWProc = d.sd.Procedure[rankProc]['site'][TopSite]
            if AIHWProc == '99':
                this.solution['AIHWprocedure']['code'] = 'WARNING'
                this.solution['AIHWprocedure']['desc'] = 'No Applicable Procedure specified'
            else:
                this.solution['AIHWprocedure']['code'] = AIHWProc
                this.solution['AIHWprocedure']['desc'] = d.sd.AIHWprocedure[AIHWProc]
            reportedProcs.add(rankProc)
            this.solution['procedure'].remove((thisProc, thisSno))
    else :
        logging.info('No procedure')
        this.solution['SCTprocedure']['code'] = 'WARNING'
        this.solution['SCTprocedure']['desc'] = 'No Procedure specified'
        this.solution['AIHWprocedure']['code'] = 'WARNING'
        this.solution['AIHWprocedure']['desc'] = 'No Procedure specified'

    # Report any unused hysterectomies
    this.solution['otherHysterectomies'] = []
    for proc, sno in this.solution['hysterectomy']:
        if proc in reportedProcs:
            continue
        logging.warning('Unused Hysterectomy procedure in sentence(%s):%s - %s', sno, proc, d.sd.Procedure[proc]['desc'])
        this.solution['otherHysterectomies'].append([d.sd.Prodecure[proc]['sct'], d.sd.Procedure[proc]['desc'], '7', d.sd.AIHWprocedure['7']])
        reportedProcs.add(proc)

    # Report any unused procedures
    this.solution['otherProcedures'] = []
    for proc, sno in this.solution['procedure']:
        if proc in reportedProcs:
            continue
        logging.warning('Unused Procedure in sentence(%d):%s - %s', sno, proc, d.sd.Procedure[proc]['desc'])
        if TopSubSite not in d.sd.Procedure[proc]['rank']:
            thisRank = int(d.sd.Procedure[proc]['rank']['cervix'])
        else:
            thisRank = int(d.sd.Procedure[proc]['rank'][TopSubSite])
        AIHWProc = d.sd.Procedure[proc]['site'][TopSite]
        if AIHWProc == '99':
            this.solution['otherProcedures'].append([d.sd.Procedure[proc]['sct'], d.sd.Procedure[proc]['desc'], 'WARNING', 'No Applicable Procedure specified'])
        else:
            this.solution['otherProcedures'].append([d.sd.Procedure[proc]['sct'], d.sd.Procedure[proc]['desc'], AIHWProc, d.sd.AIHWprocedure[AIHWProc]])
        reportedProcs.add(proc)
    return


def Welcome(this):
    this.message = '<html><head><title>AutoCode a Clinical Text Document</title><link rel="icon" href="data:,"></head><body>'
    this.message += '<h1>AutoCode a Clinical Text Document</h1><h2>Paste your Clinical Text Document below - then click the AutoCode button</h2>'
    this.message += '<form method="post" action ="' + this.path + '">'
    this.message += '<textarea type="text" name="document" style="height:70%; width:70%; word-wrap:break-word; word-break:break-word"></textarea>'
    this.message += '<p><input type="submit" value="AutoCode this please"/></p>'
    this.message += '</form></body></html>'
    return


def Result():
    '''
Assemble the response dictionary which will be returned to the HTTP service requester
    '''

    response = {}
    response['SCTprocedure'] = this.solution['SCTprocedure']
    response['grid'] = []
    for i in range(len(this.solution['sortedGrid'])):
            thisRow = {}
            thisSite = this.solution['sortedGrid'][i][0]
            thisFinding = this.solution['sortedGrid'][i][1]
            AIHW = this.solution['sortedGrid'][i][2]
            if thisSite == '' :                # no Topography
                thisRow['site'] = '21229009'
                thisRow['site description'] = 'Topography not assigned (body structure)'
            else :
                thisRow['site'] = d.sd.Site[thisSite]['sct']
                thisRow['site description'] = d.sd.Site[thisSite]['desc']
            thisRow['finding'] = d.sd.Finding[thisFinding]['sct']
            thisRow['finding description'] = d.sd.Finding[thisFinding]['desc']
            thisRow['AIHW'] = AIHW
            response['grid'].append(thisRow)
    response['AIHWprocedure'] = this.solution['AIHWprocedure']
    response['S'] = {}
    response['S']['code'] = this.solution['S']
    response['S']['desc'] = d.sd.AIHWfinding[this.solution['S']]
    response['E'] = {}
    response['E']['code'] = this.solution['E']
    response['E']['desc'] = d.sd.AIHWfinding[this.solution['E']]
    response['O'] = {}
    response['O']['code'] = this.solution['O']
    response['O']['desc'] = d.sd.AIHWfinding[this.solution['O']]
    response['otherHysterectomies'] = []
    for i in range(len(this.solution['otherHysterectomies'])):
        response['otherHysterectomies'].append(this.solution['otherHysterectomies'][i])
    response['otherProcedures'] = []
    for i in range(len(this.solution['otherProcedures'])):
        response['otherProcedures'].append(this.solution['otherProcedures'][i])

    return response


def Display(fpOut):
    '''
Print the results
    '''

    # Don't print if we are running a service
    if fpOut == None :
        return


    # Workout how wide the grid is for formatting purposes
    siteCodeLen = 0
    siteDescLen = 0
    findingCodeLen = 0
    findingDescLen = 0
    AIHWlen = 0
    for row in this.solution['sortedGrid']:
        thisSite = row[0]
        thisFinding = row[1]
        thisAIHW = row[2]
        if thisSite != '' :
            thisSiteCodeLen = len(d.sd.Site[thisSite]['sct'])
            thisSiteDescLen = len(d.sd.Site[thisSite]['desc'])
        else:
            thisSiteCodeLen = 0
            thisSiteDescLen = len('Topography not assigned (body structure)')
        thisFindingCodeLen = len(d.sd.Finding[thisFinding]['sct'])
        thisFindingDescLen = len(d.sd.Finding[thisFinding]['desc'])
        thisAIHWlen = len(thisAIHW)
        if thisSiteCodeLen > siteCodeLen :
            siteCodeLen = thisSiteCodeLen
        if thisSiteDescLen > siteDescLen :
            siteDescLen = thisSiteDescLen
        if thisFindingCodeLen > findingCodeLen :
            findingCodeLen = thisFindingCodeLen
        if thisFindingDescLen > findingDescLen :
            findingDescLen = thisFindingDescLen
        if thisAIHWlen > AIHWlen:
            AIHWlen = thisAIHWlen

    col1Len = siteCodeLen + 5 + siteDescLen
    col2Len = findingCodeLen + 5 + findingDescLen
    col3Len = AIHWlen + 2
    headerLen = col1Len + col2Len + col3Len + 4
    headerLine = '-' * (headerLen)
    boxLine = '+' + '-' * col1Len + '+' + '-' * col2Len + '+' + '-' * col3Len + '+'
    print(file=fpOut)
    print(headerLine, file=fpOut)

    print(file=fpOut)
    print('Procedure: %s - %s' % (this.solution['SCTprocedure']['code'], this.solution['SCTprocedure']['desc']), file=fpOut)
    print(file=fpOut)

    print(headerLine, file=fpOut)
    print(boxLine, file=fpOut)
    print('| ' + 'Site' + ' ' * (col1Len - 5) + '| ' + 'Finding' + ' ' * (col2Len - 8) + '| AIHW' + ' ' * (AIHWlen - 4) + ' |', file=fpOut)
    print(boxLine, file=fpOut)

    # Next print the Grid (it is already in descending S, then descending E, then descending O order)
    for row in this.solution['sortedGrid']:
        thisSite = row[0]
        thisFinding = row[1]
        thisAIHW = row[2]
        thisFindingCode = d.sd.Finding[thisFinding]['sct']
        thisFindingDesc = d.sd.Finding[thisFinding]['desc']
        if thisSite != '' :
            thisSiteCode = d.sd.Site[thisSite]['sct']
            thisSiteDesc = d.sd.Site[thisSite]['desc']
        else :
            thisSiteCode = '21229009'
            thisSiteDesc = 'Topography not assigned (body structure)'
        line = '| ' + thisSiteCode + ' ' * (siteCodeLen - len(thisSiteCode)) + ' - ' + thisSiteDesc + ' ' * (siteDescLen - len(thisSiteDesc))
        line += ' | ' + thisFindingCode + ' ' * (findingCodeLen - len(thisFindingCode)) + ' - ' + thisFindingDesc + ' ' * (findingDescLen - len(thisFindingDesc))
        line += ' | ' + thisAIHW + ' ' * (AIHWlen - len(thisAIHW)) + ' |'
        print(line, file=fpOut)
    print(boxLine, file=fpOut)

    # Now output the AIHW results
    print(file=fpOut)
    print('AIHW', file=fpOut)
    print('Procedure: %s - %s' % (this.solution['AIHWprocedure']['code'], this.solution['AIHWprocedure']['desc']), file=fpOut)
    print('S: %s - %s' % (this.solution['S'], d.sd.AIHWfinding[this.solution['S']]), file=fpOut)
    print('E: %s - %s' % (this.solution['E'], d.sd.AIHWfinding[this.solution['E']]), file=fpOut)
    print('O: %s - %s' % (this.solution['O'], d.sd.AIHWfinding[this.solution['O']]), file=fpOut)

    # Now output any other Hysterectomies
    if len(this.solution['otherHysterectomies']) > 0:
        SCTcodeWidth = len('SCT code')
        SCTdescWidth = len('SCT hysterectomy description')
        AIHWcodeWidth = len('AIHW code')
        AIHWdescWidth = len('AIHW hysterectomy description')
        for row in this.solution['otherHysterectomies']:
            if len(row[0]) > SCTcodeWidth:
                SCTcodeWidth = len(row[0])
            if len(row[1]) > SCTdescWidth:
                SCTdescWidth = len(row[1])
            if len(row[2]) > AIHWcodeWidth:
                AIHWcodeWidth = len(row[2])
            if len(row[3]) > AIHWdescWidth:
                AIHWdescWidth = len(row[3])
        col1Len = SCTcodeWidth + 5 + SCTdescWidth
        col2Len = AIHWcodeWidth + 5 + AIHWdescWidth
        headerLen = col1Len + col2Len + 3
        headerLine = '-' * (headerLen)
        boxLine = '+' + '-' * col1Len + '+' + '-' * col2Len + '+'
        print(file=fpOut)
        print('Other Hysterectomies', file=fpOut)
        print(boxLine, file=fpOut)
        print('| ' + 'SNOMED CT' + ' ' * (col1Len - 10) + '| ' + 'AIHW' + ' ' * (col2Len - 6) + ' |', file=fpOut)
        print(boxLine, file=fpOut)
        for row in this.solution['otherHysterectomies']:
            line = '| ' + row[0] + ' - ' + row[1] + ' ' * (col1Len - len(row[0]) - len(row[1]) - 5) + ' |'
            line += ' ' + row[2] + ' - ' + row[3] + ' ' * (col2Len - len(row[2]) - len(row[3]) - 5) + ' |'
            print(line, file=fpOut)
        print(boxLine, file=fpOut)

    # Now output any other Procedures
    if len(this.solution['otherProcedures']) > 0:
        SCTcodeWidth = len('SCT code')
        SCTdescWidth = len('SCT procedure description')
        AIHWcodeWidth = len('AIHW code')
        AIHWdescWidth = len('AIHW procedure description')
        for row in this.solution['otherProcedures']:
            if len(row[0]) > SCTcodeWidth:
                SCTcodeWidth = len(row[0])
            if len(row[1]) > SCTdescWidth:
                SCTdescWidth = len(row[1])
            if len(row[2]) > AIHWcodeWidth:
                AIHWcodeWidth = len(row[2])
            if len(row[3]) > AIHWdescWidth:
                AIHWdescWidth = len(row[3])
        col1Len = SCTcodeWidth + 5 + SCTdescWidth
        col2Len = AIHWcodeWidth + 5 + AIHWdescWidth
        headerLen = col1Len + col2Len + 3
        headerLine = '-' * (headerLen)
        boxLine = '+' + '-' * col1Len + '+' + '-' * col2Len + '+'
        print(file=fpOut)
        print('Other Procedures', file=fpOut)
        print(boxLine, file=fpOut)
        print('| ' + 'SNOMED CT' + ' ' * (col1Len - 10) + '| ' + 'AIHW' + ' ' * (col2Len - 6) + ' |', file=fpOut)
        print(boxLine, file=fpOut)
        for row in this.solution['otherProcedures']:
            line = '| ' + row[0] + ' - ' + row[1] + ' ' * (col1Len - len(row[0]) - len(row[1]) - 5) + ' |'
            line += ' ' + row[2] + ' - ' + row[3] + ' ' * (col2Len - len(row[2]) - len(row[3]) - 5) + ' |'
            print(line, file=fpOut)
        print(boxLine, file=fpOut)
    return

def MakeHTML(this, response, logs):

    # this.data.logger.critical('MakeHTML')

    this.message = '<html><head>\n'
    this.message += '<link rel="icon" href="data:,">\n'
    this.message += '<title>AutoCoding of a Clinical Text Document</title>\n'
    this.message += '<script type="text/javascript">\n'
    this.message += 'var toggleVisibility = function(element) {\n'
    this.message += "    if(element.style.display=='block'){\n"
    this.message += "        element.style.display='none';\n"
    this.message += '    } else {\n'
    this.message += "        element.style.display='block';\n"
    this.message += '    }\n'
    this.message += '};\n'
    this.message += '</script>\n'
    this.message += '</head><body>\n'
    this.message += '<h1>AutoCoding of a Clinical Text Document</h1>'
    siteLen = 0
    findLen = 0
    for row in response['grid']:
        SiteLen = len(row['site']) + len(row['site description']) + 3
        FindingLen = len(row['finding']) + len(row['finding description']) + 3
        if SiteLen > siteLen:
            siteLen = SiteLen
        if FindingLen > findLen:
            findLen = FindingLen

    this.message += '<pre>' + '-' * (siteLen + findLen + 14) + '\n'

    if response['SCTprocedure']['code'] != '':
        this.message += 'Procedure: %s - %s\n' % (response['SCTprocedure']['code'], response['SCTprocedure']['desc'])
    else:
        this.message += 'Procedure: WARNING - No Procedure specified\n'

    this.message += '-' * (siteLen + findLen + 14) + '\n'
    this.message += '| Site' + ' ' * (siteLen - 4) + ' | Finding' + ' ' * (findLen - 7) + ' | AIHW |\n'
    this.message += '-' * (siteLen + findLen + 14) + '\n'

    # Next print the Grid (it is already in descending S, then descending E, then descending O order)
    for row in response['grid']:
        sitePad = siteLen - len(row['site']) - len(row['site description']) - 3
        findPad = findLen - len(row['finding']) - len(row['finding description']) - 3
        AIHWpad = 4 - len(row['AIHW'])
        this.message += '| ' + row['site'] + ' - ' + row['site description'] + ' ' * sitePad + ' | ' + row['finding'] + ' - ' +row['finding description'] + ' ' * findPad + ' | ' + row['AIHW'] + ' ' * AIHWpad + ' |\n'
    this.message += '-' * (siteLen + findLen + 14) + '\n\n'

    # Now output the AIHW results
    this.message += 'AIHW\n'
    if response['AIHWprocedure']['code'] != '':
        this.message += 'Procedure: %s - %s\n' % (response['AIHWprocedure']['code'], response['AIHWprocedure']['desc'])
    else:
        this.message += 'Procedure: WARNING - No Procedure specified\n'
    this.message += 'S: %s - %s\n' % (response['S']['code'], response['S']['desc'])
    this.message += 'E: %s - %s\n' % (response['E']['code'], response['E']['desc'])
    this.message += 'O: %s - %s\n' % (response['O']['code'], response['O']['desc'])
    this.message += '</pre><br>'
    if len(response['otherHysterectomies']) > 0:
        SCTcodeWidth = len('SCT code')
        SCTdescWidth = len('SCT hysterectomy description')
        AIHWcodeWidth = len('AIHW code')
        AIHWdescWidth = len('AIHW hysterectomy description')
        for row in response['otherHysterectomies']:
            if len(row[0]) > SCTcodeWidth:
                SCTcodeWidth = len(row[0])
            if len(row[1]) > SCTdescWidth:
                SCTdescWidth = len(row[1])
            if len(row[2]) > AIHWcodeWidth:
                AIHWcodeWidth = len(row[2])
            if len(row[3]) > AIHWdescWidth:
                AIHWdescWidth = len(row[3])
        this.message += '<pre>Other Hysterectomies\n'
        this.message += '-' * (SCTcodeWidth + SCTdescWidth + AIHWcodeWidth + AIHWdescWidth + 13) + '\n'
        this.message += '| SCT code' + ' ' * (SCTcodeWidth - 8) + ' | SCT hysterectomy description' + ' ' * (SCTdescWidth - 25)
        this.message += ' | AIHW code' + ' ' * (AIHWcodeWidth - 9) + ' | AIHW hysterectomy description' + ' ' * (AIHWdescWidth - 26) + ' |\n'
        this.message += '-' * (SCTcodeWidth + SCTdescWidth + AIHWcodeWidth + AIHWdescWidth + 13) + '\n'
        for row in response['otherHysterectomies']:
            this.message += '| ' + row[0] + ' ' * (SCTcodeWidth - len(row[0])) + ' | ' + row[1] + ' ' * (SCTdescWidth - len(row[1]))
            this.message += ' | ' + row[2] + ' ' * (AIHWcodeWidth - len(row[2])) + ' | ' + row[3] + ' ' * (AIHWdescWidth - len(row[3])) + ' |\n'
        this.message += '-' * (SCTcodeWidth + SCTdescWidth + AIHWcodeWidth + AIHWdescWidth + 13) + '\n'
        this.message += '</pre><br>'

    if len(response['otherProcedures']) > 0:
        SCTcodeWidth = len('SCT code')
        SCTdescWidth = len('SCT procedure description')
        AIHWcodeWidth = len('AIHW code')
        AIHWdescWidth = len('AIHW procedure description')
        for row in response['otherProcedures']:
            if len(row[0]) > SCTcodeWidth:
                SCTcodeWidth = len(row[0])
            if len(row[1]) > SCTdescWidth:
                SCTdescWidth = len(row[1])
            if len(row[2]) > AIHWcodeWidth:
                AIHWcodeWidth = len(row[2])
            if len(row[3]) > AIHWdescWidth:
                AIHWdescWidth = len(row[3])
        this.message += '<pre>Other Procedures\n'
        this.message += '-' * (SCTcodeWidth + SCTdescWidth + AIHWcodeWidth + AIHWdescWidth + 13) + '\n'
        this.message += '| SCT code' + ' ' * (SCTcodeWidth - 8) + ' | SCT procedure description' + ' ' * (SCTdescWidth - 25)
        this.message += ' | AIHW code' + ' ' * (AIHWcodeWidth - 9) + ' | AIHW procedure description' + ' ' * (AIHWdescWidth - 26) + ' |\n'
        this.message += '-' * (SCTcodeWidth + SCTdescWidth + AIHWcodeWidth + AIHWdescWidth + 13) + '\n'
        for row in response['otherProcedures']:
            this.message += '| ' + row[0] + ' ' * (SCTcodeWidth - len(row[0])) + ' | ' + row[1] + ' ' * (SCTdescWidth - len(row[1]))
            this.message += ' | ' + row[2] + ' ' * (AIHWcodeWidth - len(row[2])) + ' | ' + row[3] + ' ' * (AIHWdescWidth - len(row[3])) + ' |\n'
        this.message += '-' * (SCTcodeWidth + SCTdescWidth + AIHWcodeWidth + AIHWdescWidth + 13) + '\n'
        this.message += '</pre><br>'

    this.message += '<a href="' + this.path + '">Click here to AutoCode another document</a><br>'

    if (logs != '') or this.data.Tracking:
        if this.data.Tracking:
            raw = this.data.rawHTML
            prepared = this.data.preparedHTML
            NLP = this.data.NLPHTML
            complete = this.data.completeHTML
        this.message += '\n'
        this.message += '<div>\n'
        this.message += '   <ul>\n'
        if this.data.Tracking:
            this.message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'raw'" + '))">Initial Document</li></u>\n'
            this.message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'prepared'" + '))">Prepared Document</li></u>\n'
            this.message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'NLP'" + '))">NLP processed Document</li></u>\n'
            this.message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'complete'" + '))">Coded Document</li></u>\n'
        if logs != '':
            this.message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'logs'" + '))">Coding Log Records</li></u>\n'
        this.message += '   </ul>\n'
        this.message += '</div>\n'

        if this.data.Tracking:
            this.message += '<div id="raw" style="display:none"><h1>Raw Input</h1><pre>\n'
            this.message += raw
            this.message += '</pre></div>\n'
            this.message += '<div id="prepared" style="display:none"><h1>Prepared Input</h1><pre>\n'
            this.message += prepared
            this.message += '</pre></div>\n'
            this.message += '<div id="NLP" style="display:none"><h1>NLP Sentences</h1><pre>\n'
            this.message += NLP
            this.message += '</pre></div>\n'
            this.message += '<div id="complete" style="display:none"><h1>Completed Sentences</h1><pre>\n'
            this.message += complete
            this.message += '</pre></div>\n'
        if logs != '':
            this.message += '<div id="logs" style="display:none"><h1>Coding Log Records</h1><pre>\n'
            this.message += logs
            this.message += '</pre></div>\n'
    this.message += '</body></html>'
    return
