# pylint: disable=line-too-long, broad-exception-caught, invalid-name, too-many-lines
'''
This is the histopathology autocoding analysis module
'''

import sys
import os
import logging
from collections import OrderedDict
import functions as f
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
    f.loadSimpleDictionarySheet(wb, 'analyze', 'AIHW Procedure', requiredColumns, 0, d.sd.AIHWprocedure)
    f.loadSimpleDictionarySheet(wb, 'analyze', 'AIHW Finding', requiredColumns, 0, d.sd.AIHWfinding)

    # Read in the SNOMED CT Sites
    requiredColumns = ['MetaThesaurusID', 'Site', 'SubSite']
    this_df = f.checkWorksheet(wb, 'analyze', 'Site', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        logging.debug("sheet(Site), columns(%s), row(%s)", requiredColumns, row)
        concept = row.MetaThesaurusID
        if concept in d.sd.Site:
            logging.critical('Attempt to redefine site(%s)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

        # Check that this Site is a defined SNOMED_CT code
        if concept not in d.sd.SolutionMetaThesaurus:
            logging.critical('Site(%s) in worksheet(Site) in workbook(analyze) not in the SolutionMetaThesaurus workbook', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if d.sd.SolutionMetaThesaurus[concept][1] != "SNOMEDCT_US":
            logging.critical('Site(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Site[concept] = {}
        configConcepts.add(concept)
        d.sd.Site[concept]['snomed_ct'] = d.sd.SolutionMetaThesaurus[concept][2]
        d.sd.Site[concept]['desc'] = d.sd.SolutionMetaThesaurus[concept][0]

        # Next validate site and subsite
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
    requiredColumns = ['MetaThesaurusID', 'Cervix', 'Vagina', 'Other', 'Not Stated']
    this_df = f.checkWorksheet(wb, 'analyze', 'Finding', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        logging.debug("sheet(Finding), columns(%s), row(%s)", requiredColumns, row)
        concept = row.MetaThesaurusID
        if concept in d.sd.Finding:
            logging.critical('Attempt to redefine finding(%s)', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

        # Check that this Finding is a defined SNOMED_CT code
        if concept not in d.sd.SolutionMetaThesaurus:
            logging.critical('Finding in worksheet(Site) in workbook(analyze) not in the SolutionMetaThesaurus workbook')
            logging.shutdown()
            sys.stdout.flush()
            sys.exit(d.EX_CONFIG)
        if d.sd.SolutionMetaThesaurus[concept][1] != "SNOMEDCT_US":
            logging.critical('Finding(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Finding[concept] = {}
        configConcepts.add(concept)
        d.sd.Finding[concept]['snomed_ct'] = d.sd.SolutionMetaThesaurus[concept][2]
        d.sd.Finding[concept]['desc'] = d.sd.SolutionMetaThesaurus[concept][0]

        # Next validate Cervix, Vagina, Other and Not Stated
        # We have to map MetaThesaurus codes to AIHW S/E/O codes, based upon 'site'
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

    # Read in the Procedures
    requiredColumns = ['MetaThesaurusID', 'Cervix', 'Vagina', 'Other', 'Not Stated', 'Cervix Rank', 'Vagina Rank', 'Other Rank', 'Not Stated Rank']
    this_df = f.checkWorksheet(wb, 'analyze', 'Procedure', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        logging.debug("sheet(Procedure), columns(%s), row(%s)", requiredColumns, row)
        concept = row.MetaThesaurusID
        if concept in d.sd.Procedure:
            logging.critical('Attempt to redefine procedure(%s)', str(concept))
            logging.shutdown()
            sys.exit(d.EX_CONFIG)

        # Check that this Procedure is a defined SNOMED_CT code
        if concept not in d.sd.SolutionMetaThesaurus:
            logging.critical('Procedure(%s) in worksheet(Site) in workbook(analyze) not in sheet SolutionMetaThesaurus', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        if d.sd.SolutionMetaThesaurus[concept][1] != "SNOMEDCT_US":
            logging.critical('Procedure(%s) in worksheet(Site) in workbook(analyze) is not SNOMED_CT', concept)
            logging.shutdown()
            sys.exit(d.EX_CONFIG)
        d.sd.Procedure[concept] = {}
        configConcepts.add(concept)
        d.sd.Procedure[concept]['snomed_ct'] = d.sd.SolutionMetaThesaurus[concept][2]
        d.sd.Procedure[concept]['desc'] = d.sd.SolutionMetaThesaurus[concept][0]

        # Next validate Cervix, Vagina, Other, Not Stated, Cervix Rank, Vagina Rank, Other Rank, Not Stated Rank
        # We have to map SNOMED_CT procedure codes to AIHW procedure codes,
        # but then only report the one most significant procedure (highest rank)
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

    # THE FOLLOWING ARE 'complete' DATA STRUCTURES - data structures required by the 'complete' module,
    # but the validity of the 'complete' configuration data depends upon 'analysis' data.
    # Hence they cannot be loaded until after the preceeding 'analyze' worksheets.

    # Read in the Site implied concepts
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID']
    this_df = f.checkWorksheet(wb, 'analyze', 'site implied', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        logging.debug("sheet(site implied), columns(%s), record(%s)", requiredColumns, record)
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

    # Read in the Finding implied concepts
    requiredColumns = ['MetaThesaurusID', 'HistopathologyFindingID']
    this_df = f.checkWorksheet(wb, 'analyze', 'finding implied', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        logging.debug("sheet(finding implied), columns(%s), record(%s)", requiredColumns, record)
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

    # Read in the Site restricted Finding concepts
    # These Findings can only be paired with one of these sites
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteIDs']
    this_df = f.checkWorksheet(wb, 'analyze', 'site restricted', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        logging.debug("sheet(site restricted), columns(%s), record(%s)", requiredColumns, record)
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

    # Read in the Site impossible Finding concepts
    # These Findings can never be paired with one of these Sites
    this_df = f.checkWorksheet(wb, 'analyze', 'site impossible', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        logging.debug("sheet(site impossible), columns(%s), record(%s)", requiredColumns, record)
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

    # Read in the Site likelyhood Finding concepts
    # These Findings can be paired with anyone of these sites, but if they are, only one pairing
    # should be included in the analysis, and it should be the pairing with the highest rank
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
            j += 1

    # Read in the Site default Finding concepts
    # These are the Sites to be paired with these Finding concepts if they remain unpaired.
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

    # Read in the concepts which imply a Diagnosis (Site/Finding pairs)
    requiredColumns = ['MetaThesaurusID', 'HistopathologySiteID', 'HistopathologyFindingID']
    this_df = f.checkWorksheet(wb, 'analyze', 'diagnosis implied', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        logging.debug("sheet(diagnosis implied), columns(%s), row(%s)", requiredColumns, row)
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

    # Read in the concepts that imply a procedure the impliedt procedure
    requiredColumns = ['MetaThesaurusID', 'HistopathologyProcedureID']
    this_df = f.checkWorksheet(wb, 'analyze', 'procedure implied', requiredColumns, True)
    for row in this_df.itertuples():
        if row.MetaThesaurusID is None:
            break
        logging.debug("sheet(procedure implied), columns(%s), row(%s)", requiredColumns, row)
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

    # Read in the Site/Finding concept pairs that define a procedure concept and that procedure concept
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

    # Read in the report Site sequence concept sets - sets of MetaThesaurus ConceptIDs which, when found in sequence,
    # imply a higher MetaThesaurus ConceptID Site for the purposes of reporting.
    requiredColumns = ['SolutionID', 'MetaThesaurus or Solution IDs']
    this_df = f.checkWorksheet(wb, 'analyze', 'report site seq concept sets', requiredColumns, True)
    thisData = this_df.values.tolist()
    for record in thisData:
        if record[0] is None:
            break
        logging.debug("sheet(report site seq concept sets), columns(%s), record(%s)", requiredColumns, record)
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
        d.sd.ReportSites.append([site, concepts])       # The site and the associated list of concepts

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

    if not isHistory:
        if AIHWcode[0] == 'S':
            if AIHWcode[1] not in ['NU']:
                AIHWrank = 1
            elif AIHWcode[1] == 'U':
                AIHWrank = 2
            else:
                AIHWrank = 3
        elif AIHWcode[0] == 'E':
            if AIHWcode[1] not in ['NU']:
                AIHWrank = 4
            elif AIHWcode[1] == 'U':
                AIHWrank = 5
            else:
                AIHWrank = 6
        else:
            if AIHWcode[1] not in ['NU']:
                AIHWrank = 7
            elif AIHWcode[1] == 'U':
                AIHWrank = 8
            else:
                AIHWrank = 9
        for i, grid in enumerate(d.sd.grid):
            if grid[3] > AIHWrank:      # Insert before here
                d.sd.grid.insert(i, [thisSite, thisFinding, AIHWcode, AIHWrank])
                break
        else:
            d.sd.grid.append([thisSite, thisFinding, AIHWcode, AIHWrank])

        # Check if we've found a cervix or endometrial code
        if subSiteCode == 'cervix':
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
        # We only need to check the 'cervix' site because, for hysterectomies, the AIHW code is '7' for all sites.
        if d.sd.Procedure[thisProcedure]['site']['cervix'] == '7':
            d.sd.hysterectomy.add((thisProcedure, sentenceNo))
        else:
            d.sd.otherProcedure.add((thisProcedure, sentenceNo))
    return


def analyze():
    '''
    Analyze the sentences and concepts and build up the results which are stored in the this.solution dictionary
    '''

    # Find all the sentence Sites and Finding, plus track Procedures
    d.sd.historyProcedure = {}
    d.sd.hysterectomy = set()
    d.sd.otherProcedure = set()
    d.sd.solution['unsatFinding'] = None
    d.sd.solution['cervixFound'] = False
    d.sd.solution['endomFound'] = False
    SentenceSites = {}                   # The Sites found in each sentence
    SentenceFindings = {}                # The Findings found in each sentence
    for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence looking for implied Sites preceed any SentenceSites
        sentence = d.sentences[sentenceNo]
        SentenceSites[sentenceNo] = OrderedDict()
        SentenceFindings[sentenceNo] = OrderedDict()
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
                        logging.info('saving history procedure:%s - %s', str(concept), str(d.sd.Procedure[concept]['desc']))
                        d.sd.historyProcedure[start] = concept
                    else:
                        logging.info('saving procedure:%s - %s', str(concept), str(d.sd.Procedure[concept]['desc']))
                        # Check if this is a hysterectomy
                        # If the AIHW code for this procedure is '7', then this is a hysterectomy procedure.
                        # We only need to check the 'cervix' site because, for hysterectomies, the AIHW code is '7' for all sites.
                        if d.sd.Procedure[concept]['site']['cervix'] == '7':
                            d.sd.hysterectomy.add((concept, sentenceNo))
                        else:
                            d.sd.otherProcedure.add((concept, sentenceNo))
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
                        d.sd.solution['unsatFinding'] = concept
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
                    if subsite == 'cervix':
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

    # Now look through each sentence for Site/Finding pairs
    d.sd.grid = []
    d.sd.solution['cervixDone'] = False
    d.sd.solution['endomDone'] = False
    for sentenceNo in range(len(d.sentences)):            # Step through each sentence
        # Check if at least one Site was found in this sentence
        if len(SentenceSites[sentenceNo]) == 0:
            continue
        # Check if at least one Finding was found in this sentence
        if len(SentenceFindings[sentenceNo]) == 0:
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
                    gridAppend(sentenceNo, FindingStart, thisSite, thisSiteHistory, thisFinding, findingCode, subSiteCode)
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
    for sentenceNo in range(len(d.sentences) - 1):            # Step through each sentence - except that last one - no where to look forward from there
        # Check if there is a remaining found Finding in this sentence
        if len(SentenceFindings[sentenceNo]) == 0:
            logging.debug('No unmatched findings in sentence(%d)', sentenceNo)
            continue

        # Check a number of the sentences around this Finding
        maxGap = 2            # Sites are really only valid for two sentences (unless the grid is empty)
        if len(d.sd.grid) == 0:
            maxGap = 4        # in which case they are valid for 4
        # Find the Sites across these sentences
        localSites = []
        for sno in range(max(0, sentenceNo - maxGap), min(sentenceNo + maxGap, len(d.sentences))):
            if sno == sentenceNo:        # No sites in this sentence matched
                localSites.append((sno, 0))        # Add a marker for the "sentence containing this Finding"
                findingIndex = len(localSites)
                continue
            if len(SentenceSites[sno]) == 0:
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
                for SSindex, siteInfo in enumerate(localSites):
                    sno, SiteStart = siteInfo
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
                    gridAppend(sentenceNo, FindingStart, thisSite, thisSiteHistory, thisFinding, findingCode, subSiteCode)
                    # Delete this finding and move onto the next one
                    del SentenceFindings[sentenceNo][FindingStart][FSsubIndex]
                    if len(SentenceFindings[sentenceNo][FindingStart]) == 0:
                        del SentenceFindings[sentenceNo][FindingStart]
                    # Mark the site as used
                    SentenceSites[bestSno][bestSiteStart][bestSiteSubIndex] = (thisSite, thisSiteHistory, True)

    # Report unused Sites
    for sentenceNo, sites in SentenceSites.items():
        for SiteStart in sites:
            for SSsubIndex in range(len(SentenceSites[sentenceNo][SiteStart])):
                thisSite, thisSiteHistory, thisSiteUsed = SentenceSites[sentenceNo][SiteStart][SSsubIndex]
                if thisSiteUsed:
                    continue
                logging.info('Unused Site in sentence(%s):%s - %s', sentenceNo, thisSite, d.sd.Site[thisSite]['desc'])

    # Report unused Findings
    for sentenceNo, findings in SentenceFindings.items():
        for FindingStart in findings:
            for FSsubIndex in range(len(SentenceFindings[sentenceNo][FindingStart])):
                thisFinding, thisFindingHistory = SentenceFindings[sentenceNo][FindingStart][FSsubIndex]
                if thisFinding in d.sd.SiteDefault:    # Check if we have a default site
                    thisSite = d.sd.SiteDefault
                    siteCode = d.sd.Site[thisSite]['site']
                    subSiteCode = d.sd.Site[thisSite]['subsite']
                    findingCode = d.sd.Finding[thisFinding][siteCode]
                    gridAppend(sentenceNo, FindingStart, thisSite, thisSiteHistory, thisFinding, findingCode, subSiteCode)
                else:
                    logging.warning('Unused Finding in sentence(%s):%s - %s', sentenceNo, thisFinding, d.sd.Finding[thisFinding]['desc'])

    # Make sure there is something in the grid
    if len(d.sd.grid) == 0:    # We have no Site/Finding pairs (which means no usable Findings or they would have been handled above)
        logging.info('Empty grid')
        # We may have usable sites (Report Sites) in the document, which we can pair with 'nothing found' - check each in order
        # However, they are only report sites if all the associated concepts are found in the coded histopathology report
        foundSites = []
        for setNo, siteInfo in enumerate(d.sd.ReportSites):     # The Report Sites and their concept lists
            conceptNo = 0           # Step through the concepts for this Report Site
            for sentenceNo, sentence in enumerate(d.sentences):            # Step through each sentence
                document = sentence[6]      # Sentences hold mini-documents
                for start in sorted(document, key=int):        # We step through all concepts in this sentence
                    for j in range(len(document[start])):            # Step through the list of alternate concepts at this point in this sentence
                        concept = document[start][j]['concept']
                        if document[start][j]['used']:        # Skip used concepts [only Findings get 'used']
                            continue
                        if document[start][j]['history']:            # Skip historical concepts
                            continue
                        concept = document[start][j]['concept']
                        isNeg =  document[start][j]['negation']        # Check that the negation matches

                        # Check if this alternate concept at 'start' is the next one in this Report Site sequence of concept in this set
                        found = False
                        thisNeg =  siteInfo[conceptNo][1]        # The desired negation
                        if concept == siteInfo[conceptNo][0]:    # A matching concept
                            if thisNeg == isNeg:
                                found = True        # With a mathing negation
                            elif (isNeg in ['2', '3']) and (thisNeg in ['2', '3']):
                                found = True        # Or a near enough negation (both ambiguous)
                        if not found:    # Check the special case of a repetition of the first concept in the set
                            # We don't handle repetitions within a set - just a repetition of the first concept
                            # i.e.looking for concept 'n' - found concept 0 [this set, array of concepts in dict, first entry, concept]
                            if concept == siteInfo[0][0]:
                                # Found the first concept - restart the multi-sentence counter
                                conceptNo = 0
                            continue
                        logging.debug('Concept (%s) (for sentence Report Site Sequence concept set[%d]) found', concept, setNo)
                        conceptNo += 1      # Found so proceed to the next concept in this Report Site concept set
                        if conceptNo == len(d.sd.ReportSites[setNo]):
                            # We have a full concept sequence set - so save this Report Site
                            foundSites.append(d.sd.ReportSites[setNo][0])

        # Now check the foundSites to see if we can use any of them
        for thisSite in foundSites:
            subsite = d.sd.Site[thisSite]['subsite']
            if subsite == 'cervix':         # A 'cervix' type Site
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
                logging.debug('cervical ReportSite:%s', str(thisSite))
                gridAppend(0, 0, thisSite, False, thisFinding, findingCode, subsite)
            elif subsite == 'endom':        # An 'endom' type Site
                if d.sd.solution['endomDone']:
                    continue
                if d.sd.solution['unsatFinding'] is not None:
                    Finding = d.sd.solution['unsatFinding']
                    findingCode = 'ON'      # Not applicable
                elif d.sd.solution['endomFound']:
                    Finding = d.sd.normalEndomCode
                    findingCode = 'ON'      # Not applicable
                else:
                    Finding = d.sd.noAbnormality
                    findingCode = 'E1'      # Negative
                gridAppend(0, 0, thisSite, False, Finding, findingCode, subsite)
                logging.debug('endometrial ReportSite:%s', thisSite)
            else:
                logging.info('other ReportSite:%s', thisSite)
                if d.sd.solution['unsatFinding'] is not None:
                    gridAppend(0, 0, thisSite, False, d.sd.solution['unsatFinding'], 'ON', '')
                else:
                    gridAppend(0, 0, thisSite, False, d.sd.noAbnormality, 'ON', '')
                break

    # Now add any 'normal' finding for any missing things - there may have been no Report Sites
    logging.info('cervixFound:%s, cervixDone:%s', d.sd.solution['cervixFound'], d.sd.solution['cervixDone'])
    if d.sd.solution['cervixFound'] and not d.sd.solution['cervixDone']:
        gridAppend(0, 0, d.sd.cervixUteri, False, d.sd.normalCervixCode, 'S1', 'cervix')
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
            # We only need to check the 'cervix' site because, for hysterectomies, the AIHW code is '7' for all sites.
            if d.sd.Procedure[histProc]['site']['cervix'] == '7':
                d.sd.hysterectomy.add((histProc, sentenceNo))
            else:
                d.sd.otherProcedure.add((histProc, sentenceNo))
            reportedProcs.add(histProc)
            del d.sd.historyProcedure[histStart]        # Remove as we have moved this to hyterectomy or otherProcedure

    # Now lets work out those Procedures - start by finding the top site
    # We have some defaults in case the grid only has 'Topography not assigned'
    topSite = d.sd.grid[0][0]
    if topSite != '':
        TopSite = d.sd.Site[topSite]['site']
        TopSubSite = d.sd.Site[topSite]['subsite']
        if TopSubSite == 'notStated':
            TopSubSite = 'other'
    else:
        TopSite = 'cervix'
        TopSubSite = 'cervix'
    logging.debug('topSite:%s', str(TopSite))

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
            d.sd.reportSN_CTprocedure['code'] = 'WARNING'
            d.sd.reportSN_CTprocedure['desc'] = 'No Procedure specified'
            d.sd.reportAIHWprocedure['code'] = 'WARNING'
            d.sd.reportAIHWprocedure['desc'] = 'No Procedure specified'
        else:
            logging.info('Other procedure(%s):%s - %s',
                              rankProc, d.sd.Procedure[rankProc]['snomed_ct'], d.sd.Procedure[rankProc]['desc'])
            d.sd.reportSN_CTprocedure['code'] = d.sd.Procedure[rankProc]['snomed_ct']
            d.sd.reportSN_CTprocedure['desc'] = d.sd.Procedure[rankProc]['desc']
            AIHWProc = d.sd.Procedure[rankProc]['site'][TopSite]
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
        logging.warning('Unused Hysterectomy procedure in sentence(%s):%s - %s', sno, proc, d.sd.Procedure[proc]['desc'])
        d.sd.solution['otherHysterectomies'].append([d.sd.Prodecure[proc]['snomed_ct'], d.sd.Procedure[proc]['desc'], '7', d.sd.AIHWprocedure['7']])
        reportedProcs.add(proc)

    # Report any unused procedures
    d.sd.solution['otherProcedures'] = []
    for proc, sno in d.sd.otherProcedure:
        if proc in reportedProcs:
            continue
        logging.warning('Unused Procedure in sentence(%d):%s - %s', sno, proc, d.sd.Procedure[proc]['desc'])
        if TopSubSite not in d.sd.Procedure[proc]['rank']:
            thisRank = int(d.sd.Procedure[proc]['rank']['cervix'])
        else:
            thisRank = int(d.sd.Procedure[proc]['rank'][TopSubSite])
        AIHWProc = d.sd.Procedure[proc]['site'][TopSite]
        if AIHWProc == '99':
            d.sd.solution['otherProcedures'].append([d.sd.Procedure[proc]['snomed_ct'], d.sd.Procedure[proc]['desc'], 'WARNING', 'No Applicable Procedure specified'])
        else:
            d.sd.solution['otherProcedures'].append([d.sd.Procedure[proc]['snomed_ct'], d.sd.Procedure[proc]['desc'], AIHWProc, d.sd.AIHWprocedure[AIHWProc]])
        reportedProcs.add(proc)
    return


def reportJSON():
    '''
    Assemble the response as a dictionary.
    reportHTML converts this into HTML.
    The Flask routine turns this into JSON which will be returned to the HTTP service requester.
    '''

    response = {}
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
            thisSiteCodeLen = 0
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
        col3Len = 5
    else:
        col3Len = AIHWlen + 1       # Allow for a trailing space
    headerLen = col1Len + col2Len + col3Len + 7     # four '+' characters and three leading spaces
    headerLine = '-' * (headerLen)
    boxLine = '+-' + '-' * col1Len + '+-' + '-' * col2Len + '+-' + '-' * col3Len + '+'
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

    logging.info('reportHTML')

    message = '<h2>AutoCoding of a Histopathology Report</h2>'
    response = reportJSON()
    siteLen = 0
    findLen = 0
    aihwLen = 4
    for row in response['grid']:
        SiteLen = len(row['site']) + len(row['site description']) + 1    # Allow for a trailing space
        FindingLen = len(row['finding']) + len(row['finding description']) + 1    # Allow for a trailing space
        AIHWlen = len(row['AIHW'])
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

    message += f"+-{'-':{siteLen}}+-{'-':{findLen}}+-{'-':{aihwLen}}+\n"
    message += f"| {'Site':{siteLen}}| {'Finding':{findLen}}| {'AIHW':{aihwLen}}|\n"
    message += f"+-{'-':{siteLen}}+-{'-':{findLen}}+-{'-':{aihwLen}}+\n"

    # Next print the Grid (it is already in descending S, then descending E, then descending O order)
    for row in response['grid']:
        message += f"| {row['site'] + ' - ' + row['site description']:{siteLen}}"
        message += f"|  {row['finding'] + ' - ' + row['finding description']:{findLen}}"
        message += f"| {row['AIHW']:{aihwLen}}|\n"
    message += f"+-{'-':{siteLen}}+-{'-':{findLen}}+-{'-':{aihwLen}}+\n\n"

    # Now output the AIHW results
    message += 'AIHW\n'
    if response['AIHWprocedure']['code'] != '':
        message += f"Procedure: { response['O']['desc']} - {response['AIHWprocedure']['desc']}\n"
    else:
        message += 'Procedure: WARNING - No Procedure specified\n'
    message += f"S: {response['S']['code']} - {response['S']['desc']}\n"
    message += f"E: {response['E']['code']} - {response['E']['desc']}\n"
    message += f"O: {response['O']['desc']} - { response['O']['desc']}\n"
    message += '</pre><br>'
    if len(response['otherHysterectomies']) > 0:
        SCTcodeWidth = len('SCT code')
        SCTdescWidth = len('SCT hysterectomy description')
        AIHWcodeWidth = len('AIHW code')
        AIHWdescWidth = len('AIHW hysterectomy description')
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
        message += f"+-{'-':{SCTcodeWidth}}+-{'-':{SCTdescWidth}}+-{'-':{AIHWcodeWidth}}+-{'-':{AIHWdescWidth}}+\n"
        message += f"| {'SCT code':{SCTcodeWidth}}| {'SCT hysterectomy description':{SCTdescWidth}}"
        message += f"| {'AIHW code':{AIHWcodeWidth}}| {'AIHW hysterectomy description':{AIHWdescWidth}}|\n"
        message += f"+-{'-':{SCTcodeWidth}}+-{'-':{SCTdescWidth}}+-{'-':{AIHWcodeWidth}}+-{'-':{AIHWdescWidth}}+\n"
        for row in response['otherHysterectomies']:
            message += f'| {row[0]:{SCTcodeWidth}}| {row[1]:{SCTdescWidth }}'
            message += f'| {row[2]:{AIHWcodeWidth}}| {row[3]:{AIHWdescWidth}}|\n'
        message += f"+-{'-':{SCTcodeWidth}}+-{'-':{SCTdescWidth}}+-{'-':{AIHWcodeWidth}}+-{'-':{AIHWdescWidth}}+\n"
        message += '</pre><br>'

    if len(response['otherProcedures']) > 0:
        SCTcodeWidth = len('SCT code')
        SCTdescWidth = len('SCT procedure description')
        AIHWcodeWidth = len('AIHW code')
        AIHWdescWidth = len('AIHW procedure description')
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
        message += f"+-{'-':{SCTcodeWidth}}+-{'-':{SCTdescWidth}}+-{'-':{AIHWcodeWidth}}+-{'-':{AIHWdescWidth}}+\n"
        message += f"| {'SCT code':{SCTcodeWidth}}| {'SCT hysterectomy description':{SCTdescWidth}}"
        message += f"| {'AIHW code':{AIHWcodeWidth}}| {'AIHW hysterectomy description':{AIHWdescWidth}}|\n"
        message += f"+-{'-':{SCTcodeWidth}}+-{'-':{SCTdescWidth}}+-{'-':{AIHWcodeWidth}}+-{'-':{AIHWdescWidth}}+\n"
        for row in response['otherProcedures']:
            message += f'| {row[0]:{SCTcodeWidth}}| {row[1]:{SCTdescWidth }}'
            message += f'| {row[2]:{AIHWcodeWidth}}| {row[3]:{AIHWdescWidth}}|\n'
        message += f"+-{'-':{SCTcodeWidth}}+-{'-':{SCTdescWidth}}+-{'-':{AIHWcodeWidth}}+-{'-':{AIHWdescWidth}}+\n"
        message += '</pre><br>'
    return message
