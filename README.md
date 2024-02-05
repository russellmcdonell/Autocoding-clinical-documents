# Autocoding-clinical-documents
Extract codes from clinical documents to support automated clinical decision processes

# Outline
The **AutoCoding Clinical Documents** project leverages [MetaMapLite](https://lhncbc.nlm.nih.gov/ii/tools/MetaMap/run-locally/MetaMapLite.html)
to find clinical terms in free text documents. **MetaMapLite** uses the [Unified Medical Language System (UMLS)](http://www.nlm.nih.gov/research/umls/) as it's code/description database. **MetaMapLite** scans a free text document looking for terms and phrases that match the descriptions in **UMLS** and returns the matching **UMLS** codes. And if that was all there was to it, then this project wouldn't exist.

The problem is that you have to wrap code around **MetaMapLite** in order to create a solution for any specific Use Case.
* You may have to pre-process the document; replace abbreviations with their full description, correct any common typos etc. **MetamapLite** will only recognise correct medical terms.
* You may need to analyse the document to identify any sections of past conditions/illnesses and exclude these if you are attempting to determine any current conditions/illnesses.
* You may have to post-process the sentences and **UMLS** codes returned by **MetaMapLite**. **MetaMapLite** does recognize negation in front of a medical term, but doesn't extend that negation to subsequent medical terms in the sentence.
* You may need to map **UMLS** codes to some other coding system [**ULMS** has mapping tables for doing this].
* You may need to do some analysis; a cancer registry may want to know about only the cancer terms and what type of cancer and discard the rest; a cervical cancer surveylance and management program would want to know the type of cancer and where it was found, discarding all non-cervical cancer findings.
* You may need to do juxtoposition analysis of the codes, looking for Body Part (Topology) and Finding (Morphology) pairs in order to determine diagnosies. Even this may be too granular for a clinic decision about treatment plans and actions.
* You may need to pass these site/finding pairs (diagnosies) through some  decision logic to prioritize them in order to determine the most appropriate action plan/care plan/care pathway.

The **AutoCoding Clinical Documents** project provides a configurable framework for all of these sorts of activities. It helps you develop and maintain multiple configurations as you may have multiple Use Cases. No single solution will cater for all clinical document autocoding requirements.
* You may need to pre-analyse documents and route them to specific solutions based upon the source (Pathology laboratory or Endoscopic application).
* You may need to route anatomical pathology reports to different solutions based up the different software used by different pathology services.
* You may need to route documents to different solutions based upon the reporting pathologist, because different pathologists use different templates for the same investigative procedure.

The **AutoCoding Clinical Documents** project works best for tightly constrained Use Cases; a specific part of the body with a specific subset
of clinical conditions, where a diagnosis and clincal recommendatation or suggested pathway is required. It is flexible enough that it can
handle a vast array of different clinical document structures within a tightly constrained Use Case, such as the histopathology reports,
from all the differnt pathologist, in all the different pathology laboratories, for "breast leasions". It can also cater for more general cases,
such as autocoding all discharge summaries and nursing notes for discharge patients; so long as detailed analysis of those codes is not required,
or is can be done by some other specialist application, such as an application to determine a Diagnostic Related Group (DRG) from any, arbitrary
set of SNOMED codes.

The **AutoCoding Clinical Documents** project aims to make the configuration and building of different solutions as simple as possible by identifying common, reusable components. This is the recommended strategy when tackling a large, broad project with conflicting requirements or terminologies, such as when the same acronym has different meanings for different clinical specialties. Here you would split the 'solution' into two separate solutions,
and route one type of document to the first 'solution' and the remaining documents to the 'second' solution. Sorting clinical documents into different
bundles, and those different bundles of documents to different solutions is left as an exercise for the reader.

# Installation
The **Autocoding clinical documents** solution has been developed in Python. **MetaMapLite** is a Java library. A small amount of Java code facilitates the integration of Python and Java. That Java code is an API wrapper which gets combined with the **MetaMapLite** library to create a WAR file that can be run on a Tomcat server. The **Autocoding clinical documents** solution makes API calls to access the **MetaMapLite** functionality implemented in the **AutoCoding.war** servlet. The Java code and configuration for the **AutoCoding.war** servlet can be found in the **tomcat** folder and is based upon, and is an extension to, the **Example MetaMapLite in a Servlet instance** code that can be downloaded from the **MetaMapLite** website.

# Configuration
Each Use Case will require a distinct **AutoCoding Clinical Documents** solution. However, each Use Case or 'solution' will be based up
a distinct type of clinical document; different document layouts, different content/focus of interest. These variabilities make it impossible to build 'solution'; there will be as many unique and different **AutoCoding Clinical Documents** solutions are there are different clinical documents. And those differences are difficult to describe with just data and parameter configuration; often Python script coding will be required to handle the nuances of particular clinical document structures.

To facliltate this complexity, each 'solution' must have it's own folder under the **solutions** folder. In each 'solution' folder there will be three
Python scripts (**prepare.py**, **complete**.py and **analyse.py**), each with it's associated configuration data (**prepare.xlsx**, **complete.xlsx** and **analyse.xlsx**).

## prepare.py/prepare.xlsx
Document preparation is the process of "cleaning up" the document so that it is in an appropriate state for **MetaMapLite** coding. Much of this can
be done with data/configuration. The following is a list of things you may need to configure and/or cater for in the **prepare.py** script.
### Correct Clinical Terminology
**MetaMapLite** will only recognize correct clinical terminology. Hence, acronyms, abbreviations and local terms have to be replaced with their correct clinical description. For instance "transformation zone" is a common local term found in histopathology reports, but the correct clincal term is "entire squamouscolumnar juction of urerine cervix". If the **UMLS** code 'C0459469 - Entire squamocolumnar junction of uterine cervix', and it's matching **SNOMED** code of 280451001, are important to this Use Case, then this 'solution' must define a regular expression pattern of 'transformation\s+zone' as a "term" to be replaced with "entire squamocolumnar junction of uterine cervix".
### Preamble (historical information)
Some clinical documents start with previous findings/observations as a sort of context to the body of the document.
Some terms and acronmym in this "preamble" have a different meaning to the normal meaning when those same terms or acromnys
are used in the body of the clinical document. The 'solution' may need to identify this "preamble" and map these "preamble terms" to their "preamble" meaning so that **MetaMapLite** can assign the correct codes to these same terms or acronyms when they occur in the body of the clinical document.
### Labels (section headings)
Labels or section headings often include clinical terms, being the subject of what follows. However, a heading doesn't imply that the matching
finding/observation was observed. For instance, a label of "CERVICAL MALIGNANCY" doesn't imply a finding of cervical cancer, but rather that the
possibility of "CERVICAL MAIGNANCY" was investigated. Sometimes you have to map Labels to a no-clinical wording so that they **are not** coded
to **UMLS** by **MetaMapLite**. The **AutoCoding Clinical Documents** project uses the existance of a non-historical, not negated, not ambiguous
 **UMLS** code to indicate a current finding/observation.
### Lists (and list markers)
List markers indicate the start of a new section/concept. Which means that the previous section is complete, even if it didn't end with a full stop.
Dashes and hyphens in list markers do not, generally, imply a hyphenated word. For the 'solution' you may chose to replace them with spaces,
except for some configured hyphenated words that are know to occur in list markers.

## complete.py/complete.xlsx
Cleaning up the clinical document and extracting the **UMLS** codes using **MetaMapLite** isn't the end of the problem. The **UMLS** codes
returned by **MetaMapLite** are in reality in a somewhat 'raw' state. Configuring the 'coding completion' process requires detailed
clinical knowledge in the specific area associated with the Use Case for which a 'solution' is being configure. It requires detailed knowledge
of the documents being autocoded; both the structure and the clinical terminology that will be found in these clinical documents.
Often this configuration has to be done iteratively, with clinical documents being both autocoded and manually coded and then comparing the results.
It may even be necessary to run the **AutoCoding Clinical Documents** 'solution' with verbose logging enabled in order to track down
the factors that lead to any discrepancies. Periodic manual coding of autocoded clinical documents should be performed, with results being compared to identify descrepancies as a quality process in order to identify any changes in document structure, layout, language etc.

The 'coding completion' process is very largely a data driven configuration; almost all of the code is generic and applicable to all Use Cases.

### Sections
Clinical documents often have sections, with section headers, and there may be different significance assigned to the information in different sections.
For instance, a "FINAL CONCLUSION" section may just summarize things already stated in the body of the clinical document.
As such, findings/observations in the "FINAL CONCLUSION" section should not be counted as implying that the clinical document asserted
these findings/observations twice - the patient didn't have twice as much 'obesity' simply because it was stated twice; once in the body of the clinical
document and then again in the "FINAL CONCLUSION". The 'solution' may need to identify sections by their headings, or section markers, and assign a code
to them, so that **UMLS** codes found in these sections can be treated differently during the analysis.
### History
Clinical documents often contain statements about things that were previous findings/observations. if the 'solution' is only concerned with
the current findings/observations, then these historical statements, with their historical findings/observations need to be identified
so that these previous findings/observations can be ignored during the analysis.
#### History Markers
History markers define sections of the clinical document containing previous findings/observations. These usually include any "Preamble" markers,
but may include additional sections of historical information; sections in which "preamble terms" mapping is not required or relevant.
#### Pre-history Phrases
Unfortunately, historical information doesn't just exist in history sections. Often sentences in the body of the clinical document switch
from current findings/observations to historical finding/observations. For instance, "is consistent with" usually introduces a reference
to a historical finding/observation.
### Equivalents
**UMLS** codes are very 'fine grained' - distinct codes for marginally different findings/observations. The 'solution' may deem multiple **UMLS** codes
to be effectively 'equivalent' in this Use Case. The analysis can be simplified if multiple 'equivalent' **UMLS** codes can be mapped to a single **UMLS** code.
### Negation
**MetaMapLite** does handle negation, but not negation propogation. So, " *not 'a', or 'b', or 'c'* " will be coded to ['not a', 'b', 'c']. The **AutoCoding Clinical Documents** project will recognize 'not a' and propogate that negation to create ['not a', 'not b', 'not c']. However, you cannot
propegate negation to the end of the sentence if there is a negation terminator in the sentence. For example, " *not 'a' or 'b' or 'c', but 'x' and 'y' and 'z'* " has the negation terminator of "but". The **AutoCoding Clinical Document** project can be configured with a list of negation termination
words that are likely to be found in the set of clinical documents associated with this Use Case. In this example, the **AutoCoding Clinical Documents** project will change the negation of the codes to ['not a', 'not b', 'not c', 'x', 'y', 'z'].
#### Pre-Negation
Sometimes "not" is not the only word or phase use to indicate that what follows in negated. Analysis of the clinical documents associated with
this Use Case may reveal many different words of phases, such as "absence of" or "does not demonstrate".
#### Immediate Pre-Negation
Sometimes a word other than "not" preceeds a finding/observation, but it is intended to negate only the one, following, finding/observation.
For instance, in the phrase " *benign tumor* " the word "benign" negates the finding/observation of "tumor", but that negation shouldn't be
propegated to any further findings/observations in the current sentence.
#### Post-Negation
Sometimes one or more findings/observations are stated, followed by a word or phrase that implies that those findings/observations were not
found/observed, such as " *not included* ".
#### Immediate Post-Negation
Sometimes a finding/observation is stated, followed by a word or phrase that implies that this singular finding/observation was not
found/observed, such as " *is not seen* ".
#### Sentence Negation Lists
Sometimes the negation of a concept in a sentence implies that other, related concepts, in the same sentence will be, or should be, negated.
When the **AutoCoding Clinical Documents** project finds one of these negated concepts in a sentence it will negate all the related concepts
in the same sentence.
#### Document Negation Lists
Sometimes the negation of a concept in a clinical document implies that other, related concepts, in the clinical document will be,
or should be, negated. When the **AutoCoding Clinical Documents** project finds one of these negated concepts in the clinical document
it will negate all the related concepts in the clinical document.
#### Gross Negation
Sometimes a clinical document will contain an absolute, definitive statement, usually near the end in any conclusion, about the non-existence
of one or more concepts. When the **AutoCoding Clinical Documents** project finds one of these absolute assertions it will negate the concepts
contained in this gross negation wherever, and whenever, they occur in the clinical document.
### Ambiguity
Unfortunately clinical documents sometimes contains assertions that something is "unknown". Usually, **UMLS** codes whose status in "unknown" or "abmiguous" are excluded from any clinical analysis.
#### Pre-Ambiguous
These are words or phrases that indicate that the following findings/observations are "not found" such as " *no clear evidence of* ".
#### Immediate Pre-Ambiguous
These are words, phrases or even characters the imply that the single following finding/observation is ambiguous, such a " *query* " or just " *?* ".
#### Post-Ambiguous
Sometimes one or more findings/observations are stated, followed by a word or phase that implies that those findings/obserations are ambiguous, such as " *cannot be excluded* ".
#### Immediate Post-Ambiguous
Sometimes a finding/observation is stated, followed by a word or phase that implies that this singula finding/obseration is ambiguous. It can b something as simple as just " *?* ".
### Modifiers
Sometimes a word or phrase before or after a **UMLS** code can modify the meaning of that **UMLS** code. This can result in the **UMLS** code being mapped to another **UMLS** code. This mapping can map a **UMLS** code that was not part of the analysis into a **UMLS** code that is part of the analysis, such as when a specialized form of concept is mapped to a more generalized concept. Or it could be that the specialized form of the concept means that it should be excluded from the analysis, in which case the mapping would be to a new **UMLS** code that is not part of the analysis.
#### Pre-Modifiers
Pre-modifiers are words or phrases that preceed the **UMLS** code, such as " *low-grade* ".
#### Post-Modifiers
Post-modifiers are words or phrases that follow a **UMLS** code, such as " *favoured to be low grade* ".
### Concepts
Often the interpretation of a clinical document can be enhanced by the addition of extra/higher concepts which are derived from
either the text itself, or from sequences of **UMLS** codes returned by **MetaMapLite**. A 'solution' may even define solution specific
concepts/descriptions that are outside and additional to **UMLS**.
#### Sentence Concepts
Words or phrases within the clinical document may match a **UMLS** concept even if the word or phrase don't exactly match the **UMLS** decription.
Sometimes it's possible to 'fix' this using **terms** during the preparation phase. At other times it is just as easy to assign
an extra/higher concept. For example, " *insufficient for an accurate assessment* " can be assigned the extra/higher **UMLS** code of
" *C0332630 - Insuffient tissue for diagnosis* ".
#### Strict Sequential Sentence Concept Sets
Often a specific sequence of consecutive concepts, within one sentence can imply a higher compound concept which is relevant to the analysis.
#### Sequential Sentence Sentence Concept Sets
Often a specific sequence of concepts, possibly with other intervening concepts, within one sentence can imply a higher compound concept
which is relevant to the analysis.
#### Multiple Sentence Strict Sequential Sentence Concept Sets
It is possible that a specific sequence of consecutive concepts, crossing more than one sentence, can imply a higher compound concept
which is relevant to the analysis.
#### Multiple Sentence Sequential Sentence Concept Sets
It is possible that a specific sequence of concepts, possibly with other intervening concepts, crossing more than one sentences,
can imply a higher compound concept which is relevant to the analysis.
#### Sentence Concept Sets
Often a specific set of concepts, in any sequence, possibly with other intervening concepts, within one sentence can imply a higher compound concept
which is relevant to the analysis.
#### Multiple Sentence Concept Sets
Often a specific set of concepts, in any sequence, possibly with other intervening concepts, crossing one pr more sentences,
can imply a higher compound concept which is relevant to the analysis.
#### Document Sequence Concept Sets
It is possible that a specific set of concepts, occuring in a specific sequence in the clinical document, possibly with other intervening concepts,
can imply a higher compound concept which is relevant to the analysis.
#### Document Concept Sets
It is possible that a specific set of concepts in the clinical document can imply a higher compound concept which is relevant to the analysis.

## analyse.py/analyse.xlsx
The possible 'analysis' configurations are as many and as varied as all the possible uses for the **AutoCoding Clinical Documents** project.
The **UMLS** codes can be as specific as a disease (Morphology) or a site (Topology) or as general as a diagnosis.
If the 'analysis' has to find all diagnosis, then some Python code to do juxtoposition analysis may be required;
looking for adjacent disease/site pairs in sentences and mapping those to specific disease diagnoses.
However, it is not always possible to pair up any disease with any site. Some **UMLS** disease codes may have
to be restricted to being paired with a small set of **UMLS** site codes.

Or the 'solution' may choose to "standardize" the **UMLS** codes by looking for any diagnosis codes returned by **MetaMapLite**
and adding their implied disease/site code pairs. Similarly, some **UMLS** disease codes have an implied site that can be added and paired
with the **UMLS** disease code.

The 'solution' may pass those disease/site code pairs through some form of clinical decision process, perhaps something
based upon DMN - Decision Model Notation, for which there is a Python module (pyDMNrules)[https://pypi.org/project/pyDMNrules/],
in order to determine the most significant diagnisis/diagnoses.

Alternately, or perhaps as well, the 'solution' may need to identify **UMLS** codes that imply procedures. If the 'solution' is supporting
some form of mandatory reporting, then it is likely that all the **UMLS** codes will need to be mapped to the required reporting codeset,
such as SNOMED_CT or ICD-10 (**UMLS** provides mappings to all the well known coding systems).
Again, some sort of decision logic may be required to organize the reporting codes into a priority order.

Or perhaps, after juxtoposition and standardization, there is no analysis; the **UMLS** codes are the output and some other
application does any analysis or provides the clinical decision support logic.

As you can see, the 'analysis' is heavliy dependant upon the business requirements for the 'solution' and much less dependant
upon the 'clinical' requirements. Whatever the 'solution', it is likely that the 'analysis' will have a lot of logic built in Python rather
than logic built with data configuration. Hence, it is difficult to provide any guidance as to how the **UMLS** codes, automatically extracted
from each clinical document, should be processed.
