# Example 1
This is an example of AutoCoding histopathology reports - specifically, histopathology report of samples
which were investigated for any signs of cancer. In this case, the site of interest is the female reproductive system,
with specific interest in cervical cancer, triggered by the human papillomavirus virus.

Most of the code in the associated solution Python scripts ("prepare.py", "complete.py" and "analyze.py") is required
to instanciate the business requirement, which are complex. The business requires that all 'relevant' diagnoses be reported
where 'relevant' is restricted to just a limited number of sites (21) and just a limited number of findings or conditions (167)
plus a limited number of procedures (27) where those procedures were mentioned in the histopathology report. All of these have
to be reported as SNOMED_CT codes, so mapping from **UMLS** to SNOMED_CT is required. Fortunately this is part of the **UMLS**
and can be found in the the file 'META/MRCONSO.RRF' when you get when you download the current version of the
[Unified Medical Language System (UMLS)](http://www.nlm.nih.gov/research/umls/).

However, it does mean that the required level of specificity is diagnosis represented as Site/Finding pairs, so that
diagnoses with an irrelevant Site can be discarded, as can diagnoses with an irrelevent Finding. To do this the "analyze()"
function has to do quite a bit of work. Fortunately, the core AutoCoding Clinical Document project code does all the heavy
lifting of looking for sets of codes a lower levels of specificity and adding the appropriate codes. What remains all the 'implied' coding.
* procedures that are only ever done at one site so the Site is implied and can be added to the clinical document (d.sentences)
* findings or conditions that have an implied site (appendecitus implies Site === appendix). These implied Sites can be added to the clinical document (d.sentences).
* diagnosis codes that imply both a site and condition or finding. These implied Site/Finding pairs can be added to the clinical document (d.sentences).

Unfortunately Site/Finding pairs are not always nicely adjacent in histopathology reports. Sometimes the Site is a section heading
and all the Finding in the body of the section need to be paired with the Site asssociated with the section heading. Hence, a lot of the
code in "analyze()" is dedicated to doing juxtopositional analysis; finding a Site and looking for "nearby" Findings, of looking for a Finding
and then looking around for the nearest Site.

The final wrinkle comes from the business requirement that the extracted diagnoses and procedures need to passed through a clinical
decision application based upon Decision Model Notation (DMN) using [pyDMNrules] (https://pypi.org/project/pyDMNrules/).
And whilst the reporting must be done in SNOMED_CT, the clincial decision rules a based upon Australian Institure of Health and Welfare (AIHW)
S, E and O codes. Also, the clinical decision model requires only the most critical diagnosis and the most relevant procedure. Hence, a lot
of the code in the "analyze()" function is dedicated to the mapping, and the selection of "most critical" and "most relevant".

## prepare.py
### configure()
Reads in two solution specific relating to idiosyncratic list markers and the list of legitimately hyphenated words.
Hyphens in histopathology reports are often markup so this solution replaces them with spaces prior to coding
to prevent codes being erroneously negated. However, any words identified as legitimately hyphenated by the solution are left unchanged.

### CheckHyphenated()
Replaces hyphens/dashes to spaces, except for legitimately hyphenated words.

### solutionCleanDocument()
Deal with the idiosyncratic list markers in the clinical document (d.rawClinicalDocument) and create the prepared document (d.preparedDocument).

### checkPreamble()
Histopathology reports sometimes have "CLINICAL INFORMATION" as a header, which is an introducer for some historical information (preamble).
Unfortunately, this heading is sometimes split over multiple lines. The core AutoCoding Clinical Documents project only looks for preamble markers
within a single sentence and does not look for split markers. Fortunately, it calls "d.sp.checkPreamble()" in case the solution has better
solution specific logic that can identify other preamble markers.

## complete.py
### requireConcept()
In histopathology reports, pathologist sometimes prefix a clinical term with the "?" character, to indicate that the clinical term
was not present, but may be worth further investigation. This short hand for "query XXX" means that concept "XXX" is not required
in the coded clinical document (d.sentences).

### solutionCheckHistory()
Provide a 'belts and braces' check for the 'CLINICAL INFORMATION' heading that can be split over multiple lines.

### solutionAddAdditionalConcept()
This function is called every time and additional concept is added to the coded clinical document (d.sentences).
So it is a convenient place to check if the newly added concept implies something, and if it does, add the implied
concepts.

### initializeNegation()
Initializes the solution negation status, because there is solution specific negation logic.

### extendNegation()
Negation has been extended at the current point in the current sentence, but only for 'known concepts' (d.knownConcepts).
There is no requirement for a solution to add any solution specific SolutionIDs to 'known concepts' [they will get added
if they are contained in the "solutionConcepts" returned by any of the "configure()" functions]. This code steps through
the concepts at this point in the current sentence, looking for solution Finding codes and extends negation to them.

### higherConceptFound()
If the higher concept, which has been found as part of "set" processing is a solution Diagnosis code or a solution Finding code
then all the codes in the matching set should be marked as used to prevent duplicate coding.

### addFinalConcepts()
This function steps through the coded document (d.sentences) looking for solution concepts that imply other solution concepts.
This may be duplication of the logic in "solutionAddAdditionalConcept()" but fortunately the AutoCoding Clinical Documents project
will not add a code to a sentence at a point, if that code already exist in that sentence, at that point.

## analyze.py
### configure()
This function loads in several solution specific worksheets. Some of these are actually used in the "complete" phase,
but their integrity can't be checked until some of the "analzye" worksheets have been loaded. Forturnately, all configuration
is done before any clinical document coding, so the order in which things are loaded does not matter. And it makes more sense
to load and check these worksheets during "analyze" configuration, rather than load them, uncheck, during "complete" configuration
and then go back and validate them after "analyze" configuration.

### analyze()
This function is very solution specific. It goes through the coded histopathology report (d.sentences) identfying Sites and Findings
of interest and, at the same time, noting any Procedures.

Next it performs a juxtoposition analysis; identifying Site/Finding pairs. In a well formed histopathology report you expect observation
or condition to be reported with reference to the body part where it was observed. Similarly, you would not expect to find an anatomical
site being mentioned with no obervation about that site. Unfortunately, not all histopathology reports are well formed. So, after the
justopositional analysis, the "analyze()" function reports all unpaired Sites and unpaired Findings.

The remaining code does the mapping to AIHW and identification of "most critical" and "most relevant". It also deals with the edge
cases, such as where the juxtoposition analysis found no Site/Finding pair; possibly because the sample was unsatisfactory or because no
cancer was observed.