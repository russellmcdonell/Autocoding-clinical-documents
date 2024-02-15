# Solutions
There are a number of common things that all solutions must provide/specify - specifically Python scripts and Excel workbooks.
All of these must exist in each solution specific folder. For example, if the solution is called "Notes" then the folder
"./solution/Notes" must exist and it must contain the files "MetaThesaurus.xlsx", "solutionData.py", "prepare.xlsx", "prepare.py",
"complete.xlsx", "complete.py", "analyze.xlsx" and "analyze.py".

There are also a number of data structures that are shared.
Core data that is shared between the **AutoCoding Clinical Documents** project Python script ("AutoCoding.py") and parts of the solution specific
Python code are defined in the core "data.py" module. None of the definitions in this module should be touched or changed.
Solution specific Python scripts should/must import this data with "import data as d".

There are a number of Python functions used by the **AutoCoding Clinical Documents** project that may be useful to solution specific Pythyon scripts.
These can be found in the core "functions.py" module. Solution specific Python scripts can import these functions with "import functions a f".
These functions should not be changed or modified as the **AutoCoding Clinical Documents** project depends upon their existence
and currently defined behaviour. However, you can add additional functions where you believe there is functionality that
will be required by multiple, different solutions. The aim here is to make the solution specific Python scripts as small as possible
so that they can be 'focused' on just the idiosyncracities of each Use Case.

## Solution MetaThesaurus
MetaMapLite returns MetaThesaurus concepts. So the vast majority of the configuration will be in terms of
MetaThesaurus codes. The "Solution MetaThesaurus.xlsx" workbook has one worksheet - "Solutions MetaThesaurus",
which lists all the code and description of all codes that are valid in configuration workbooks for this specific solution.
The MetaThesaurus code can be found in the file 'META/MRCONSO.RRF' when you download the current version of the
[Unified Medical Language System (UMLS)](http://www.nlm.nih.gov/research/umls/).

The Solution MetaThesaurus is only used to validate the configuration worksheets, but the **AutoCoding Clinical Documents** project
will not run if it is not present, or if there are any codes in any configuration worksheet that are not
listed in the Solution MetaThesaurus.

## Solution specific data
There will be data that parts of the solution specific Python scripts will need/want to share, either between different phases (prepare/complete/analyze)
or even between different functions within a phase. To support this the "solutionData.py" module must exist in the solution specific folder.
This will be imported by the **AutoCoding Clinical Documents** project using the "importlib" module. This data can be accessed
by any solution specific Python script by prefixing "d.sd." to the name of the data structure.
For instance, a solution may assemble a list of hyphenated words. This list would be defined as "hyphenatedWords = []" in "solutionData.py",
but would be references as "for word in d.sd.hyphenatedWords:" in any solution specific Python script.

## AutoCoding
After the command line arguments have been processed and checked the AutoCoding Clinical Documents project
will read in any standard configuration files for each of the three phases ("prepare", "complete" and "analyze").
The AutoCoding Clinical Documents project will then load the three Python scripts for each of the phases ("prepare",
"complete" and "analyze") as modules and call each of there "configure()" functions, so that each phase is
configured before any clinical documents are processed.

The AutoCoding Clinical Documents project will then read a file or files and process each file
by calling the core "AutoCode()" function, which manages the four phases of the AutoCoding process.
1. Preparing the clinical document into a state ready for coding by **MetaMapLite**.
2. Coding the prepared clinical document using **MetaMapLite**.
3. Completing the coding, using sentence information and the MetaThesaurus codes returned by **MetaMapLite**.
4. Analyzing the set of codes assemble by both **MetaMapLite** and the code completion Python scripting.

## Prepare the Clinical Document for AutoCoding.
The "prepare" phase of AutoCoding clinical documents requires one Excel workbook ("prepare.xlsx") and
one Python script "prepare.xlsx" which must exist in the solution specific folder.
However most of the cleaning and preparing is done by the main code - "AutoCoding.py" - in the core "cleanDocument()" functions.

### cleanDocument()
The core "cleanDocument()" function starts by calling the solution specific "solutionCleanDocument()" function, which must
exist in the "prepare.py" Python script. The solution specific "solutionCleanDocument()" function takes the raw, clinical document,
from 'd.rawClinicalDocument', does any specific solution cleaning, and places the cleaned document in 'd.preparedDocument'.

Solution specific "solutionCleanDocument()" scripts do not need to do any of the following cleansing, which will be done be the
main "cleanDocument()" function.

* Replace any labels with their label replacement text (as configured in "prepare.xlsx")
* Replace any commonly used terms (acronyms/slang/shorthand) with their correct clinical terms (as configured in "prepare.xlsx")
* Check for 'preamble' (as configured in "prepare.xlsx") and replace any preamble terms with the required preable text (as configured in "prepare.xlsx")

This will create the fully prepared document ('d.preparedDocument') ready for coding using **MetaMapLite**.

## Complete the Clinical Document for AutoCoding.
The "complete" phase is clinically the most technical and difficult to configure.
It may be necessary to create this configuration by 'trial and error' - create a minimal configuration with little or no analysis
and run some documents through it. Then check the logs for new/unconfigured concepts; things in the documents that are not catered
for in the current configuration. Then figure out where those new/unconfigured codes will fit into the completed configuration.
For that, the assistance of an experienced clinical coder, who is very familiar with this Use Case, will be invaluable.

The "complete" phase of AutoCoding clinical documents requires one Excel workbook ("complete.xlsx") and
one Python script "complete.py" which must exist in the solution specific folder. Fortunately most of the logic
here is contained in the core "AutoCode()" function. Most of the configuration challenge will be in the confuguration
or the 25 or so Excel worksheets. These worksheet contain most of the logic associated with creating
an interpretable/analyzable set of clinical concepts. Again, the assistance of an experienced clinical coder,
who is very familiar with this Use Case, will be invaluable. In the end, the AutoCoding Clinical Document project
is just an "expert system" - a system configured with the knowledge of experts, which attempts to emulate what those
experts would do with each clinical document. A lot of the validation of any configuration will be done by comparing
the manually coded result with the AutoCoded output.

However, there are a number of "complete.py" functions that must exist and can provide additional solution specific
assistance to the coding completion process.

### requireConcept()
This function is called for every MetaThesaurus code that is about to be added to the main "sentences" data structure
(one of the mini-documents associated with a specific sentence). The "requireConcept()" function has the final say
as to where or not a MetaThesaurus code gets added to the "sentences" data structure.

### addRawConcepts()
This function is called after all the MetaThesaurus codes have been added to the "sentences" data structure, but before
an negation or "sets" processing. The "addRawConcepts()" function lets the solution to add an additional codes to the
"sentences" structure, to any sentence, at any point in the sentence.

### initializeNegation()
A solution may have some additional negation logic. The "initializeNegation()" function is the place where solution
specific negation variables can be initialized before negation checking begins.

### extendNetation()
This function is called for each sentence, for each point in the sentence where a concept has been found
after all negation has been completed for all concepts at this point in this sentence. The AutoCoding Clinical Document project
only does negation extension for "known concepts" (thing in the d.knownConcepts set()). The "prepare", "complete" and "analyze"
Python scripts have "configure()" functions that can load other codes to the solution specific data.
There is no requirement for those functions to return those codes in 'configConcepts'; the AutoCoding Clinical Documents project would
have no visibility of those codes. However, the solution may wish, under certain circumstances, to extend negation to these codes.

### addSolutionConcepts()
This function is called after all negation extension has been completed, but before any "set" processing.
The "addSolutionConcepts()" function lets the solution to add an additional codes to the
"sentences" structure, to any sentence, at any point in the sentence.

### addFinalConcepts()
This function is called after all "set" processing has been completed. The "set" processing scans sentences
and the document as a whole looking for sequences of codes which imply an analytically important concept
which must be added to the document as a solution code (SolutionID - can be a MetaThesaurus code, but doesn't have to be).
The aim is to create a set of interpretable/analyzable codes at the appropriate level of specificity. The "sets" processing
aims to add codes at the right level of specificity from a set of codes as a lower level of specificity.

The "addFinalConcepts()" function is a place where you may do the opposite of the "sets" processing; identify **UMLS** codes
that imply one or more solution codes at the level that is appropriate for intended analysis.

### complete()
This function is called after all other code completion processing and before any analysis processing.
The "complete()" function is a place where any final completion coding can be performed.

## Analyze the Clinical Document for AutoCoding.
Analysis of the completed codes will as varied as the number of different Use Cases for the AutoCoding Clinical Documents project.
So, for the "analyze" phase there is only one analysis function, "analyze()" which is where all the analysis logic
must exist. There are also a small number of  reporting functions.

The "analyze" phase of AutoCoding clinical documents requires one Excel workbook ("analyze.xlsx") and
one Python script "analyze.py" which must exist in the solution specific folder.

### analyze()
The "analyze()" function has to process the data in the 'd.sentences' data structure and populate the 'results'
data structure(s) in the solution shared data. The form of the 'results' data structure(s) will vary from
solution (Use Case) to solution, including the name(s) of those data structure(s) and their form. The assembled
'results' will then be reported by one of the reporting functions.

### resultsFile()
The "resultsFile()" function is passed a folder name and file name which it will use to create a file.
The file name will not have a file extension; the "resultsFile()" function will need to append the file extension
that is appropriate to the type of file that it will create (.txt, .xlsx etc). Alternately, the "analyze" "configure()"
function could define a database name, connection string, table etc in the solution share data and the "resultsFile()"
function could ignore the folder name and file name and, instead, write the data to a database.

### resultsHTML()
The "resultsHTML()" function must return the 'results' as valid HTML to be placed in the \<body>\</body> of the 'results'
webpage on the Flask website.

### resultsJSON()
The "resultsJSON()" function must return the 'results' as a single JSON string, which will be returned
as 'applicatin/json' to a caller of the AutoCoding Clinical Documents api that is created by Flask.
