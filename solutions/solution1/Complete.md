# This is the "Introduction" worksheet from the "complete.xlsx" workbook

This is the configuration worksheet for completing the autocoding of histopathology reports.

# HISTORICAL CONTENTS WITHIN A DOCUMENT
Documents often contain things that are reference to things that have happened in the past.
Things that were true in the past are not always true in the present, so it is often necessary, when analysing a document, to ignore 'history'.
Tagging whole sentence, and parts of sentences, as 'history' makes it possible to ignore historical facts when analysing a document.

## history markers
History markers are words or phrases that indicate that the following sentences are the start of a section of history or the start of a section of non-history (the body of the document)

The layout is thee columns; a 'regular expression', a boolean to indicate that the marker is case sensitive and a boolean to indicate type of history marker.
* The regular expression is the pattern that indicates the start of history or non-history (the body of the document).
* The first boolean is TRUE to indicate that the marker is case sensitive - upper and lower case must match. FALSE means that a match that ignores case is a match.
* The second boolean is true to indicate that the marker marks the start of a section of history, false indicate that the marker marks the start of a section of non-history (the body of the document).

The  history markers are regular expression. White space within the history marker must be specified as \s+, brackets must be specified as \( and \).
History markers are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

## pre history
Pre-history markers are words or phrases that occur before concepts and which indicate that the concept is from a previoius encounter or test (historical)

The layout a single  columns; a 'regular expression'.
* Pre-history markers are regular expressions.
White space within the pre-history marker must be specified as \s+, brackets must be specified as \( and \). 
Pre-history markers are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.


# DOCUMENT SECTIONS
Some document have 'sections' and the interpretation of a concept may vary depending upon the semantic significance of the section in which the concept is found.
For instance the assertion that a definite finding in 'Executive Summary' would override any ambivalence about the same concept in any other sections of the document.

## section markers
Section markers are words or phrases that indicate that the following sentences are part of a specific section of the text document.

The layout is thee columns; a 'regular expression', a section code and a boolean to indicate the the marker is case sensitive.
* The boolean is TRUE to indicate that the marker is case sensitive - upper and lower case must match. FALSE means that a match that ignores case is a match.
* The regular expression is the pattern that indicates the start of history or non-history (the body of the document).
* The  section markers are regular expression. White space within the history marker must be specified as \s+, brackets must be specified as \( and \).
Section markers usually start with the character '^' - indicating that the text is at the start of a sentence.
Section  markers are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

## equivalents
Solution equivalent concepts (SolutionIDs) - MetaThesaurus concepts found in sentence, but the solution uses a different equivalent  concept.
Some concepts have multiple, equivalent definitions in the MetaThesaurus. Solutions can use the 'equivalents' configuration to map these multiples into a single concept.
Solution concepts (SolutionIDs) can be MetaThesaurus ConceptIDs, but are not restricted to MetaThesaurus ConceptIDs; the just have to be alphanumeric codes.
Solution equivalents are a direct replacement; the original MetaThesaurus ConceptID is removed and replaced with SolutionID.
To specify a negated concept, prepend the '-' character to the concept ID. To specify an ambiguous concept, prepend two question mark characters (?) to the concept ID.

Layout is two or more columns
* 'SolutionID'
* one or more columns of MetaThesaurusIDs.

HINT: use MetaThesaurus ConceptIDs as Solution ConceptIDs wherever possible. This will aid in the clarity of the solution as MetaThesarus Concept IDs have well defined semantic meanings.


# CONCEPT NEGATION AND CONCEPT AMBIGUITY
MetaMapLite will recognize the word 'not' and will mark the next concept as 'negated', but this is a very limited negation concept.
Sentences often imply negation of a set of concepts, such as "not a, or b, or c", which is 'not a', 'not b', 'not c'.
Extending negation solves this problem, however sentence often contain words like "but" which imply different negation before and after this word.

These words form 'but boundaries', so that "not a, or b, or c, but definitely x and y and z" must become 'not a', 'not b', 'not c', 'have x', 'have y', 'have z'
Negation can be expressed using words or phrases other than 'not', such as "without any".

Sometimes these words or phases occur before a concept and sometime they occur after a concept.
Some negation words or phrases imply negation to the immediately preceding or following concept, and only the immediately preceding or following concpet.
Other negation words or phrases imply negation to all preceding or following concepts, but not across a but boundary.
Some negation words or phrases don't imply complete negation, but rather a dilution of an assertion to a more ambiguous statement.

Analysis usually focuses on finding positive and negative assertions in a document.
Marking concepts as ambiguous ensures that they do not contribute to any false positive or false negative conclusions.

## but boundaries
But boundaries are words or phrases that mark the end of a context when extending or looking for negation or ambiguity.
Concepts after a But boundary are not negated, unless there is a negated concept after the but boundary.

Each But boundary words or phrases is a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).
Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

Layout is one column
* 'But_boudaries'

## pre negations
Pre-negations are words or phrases that occur anywhere before a concept, but not before a but boundary, and which negate the concepts.
This negation may extend to subsequent concepts due to negation extension

Pre-negations are regular expressions. White space within the pre-negations must be specified as \s+, brackets must be specified as \( and \).
Pre-negations are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

Layout is one or more column(s)
* 'Pre_negations'
* zero or more columns of MetaThesaurusID.
If there are no MetaThesurusIDs on the same line as a Pre-negation, then this Pre_negations applies to all MetaThesaurusIDs.
If there are one or more MetaThesaurusIDs on the same line as the Pre-negation, then this Pre-negation only applies to the listed MetaThesaurusIDs.

## immediate pre negations
Immediate pre-negations are words or phrases that occur immediately before a concept, but not before a but boundary, and which negate the concept.
This negation may extend to subsequent concepts due to negation extension.

Immedicate pre-negations are regular expressions. White space within pre-negations must be specified as \s+, brackets must be specified as \( and \).
Immediate pre-negations are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanum. character.

Layout is one or more column(s)
* 'Immediate_pre_negations'
* zero or more columns of MetaThesaurusID.
If there are no MetaThesurusIDs on the same line as an Immedidate pre-negation, then this Immediate pre-negations applies to all MetaThesaurusIDs.
If there are one or more MetaThesaurusIDs on the same line as the Immediate pre-negation, then this Immediate pre-negation only applies to the listed MetaThesaurusIDs.

## post negations
Post negations patterns are words or phrases that occur anywheher after a concept, but not after a but boundary, and which negate the concepts
This negation may extend to subsequent concepts due to negation extension.

Post negation exeception patterns are words or phrases which, when they occurr after a concept, contra indicate the matching post negation pattern.

Post negations words or phrases are regular expressions. White space within the post negations must be specified as \s+, brackets must be specified as \( and \).

Post negations exception words or phrases are regular expressions. White space within the post negations must be specified as \s+, brackets must be specified as \( and \).

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

Layout is two columns
* 'Post_negations'
* 'Exceptions'

## immediate post negations
Immediate post negation patterns are words or phrases that occur immediately after a concept, but not after a but boundary, and which negate the concept.
This negation may extend to subsequent concepts due to negation extension.

Immediate post negation exeception patterns are words or phrases which, when they occurr after a concept, contra indicate the matching immediate post negation pattern.

Immediate post negation words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Immediate post negation exception words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

Layout is two columns 
* 'Immediate_post_negation'
* 'Exceptions'

## pre ambiguous
Pre-ambiguous patterns are words or phrases that occur anywhare  before a concept, but not before a but boundary, and which make the concepts ambiguous.

Pre-ambiguous words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

Layout is one or more column(s)
* 'Pre_ambiguous'
* zero or more columns of MetaThesaurusID.
If there are no MetaThesurusIDs on the same line as a Pre-ambiguous pattern, then this Pre-ambiguous pattern applies to all MetaThesaurusIDs.
If there are one or more MetaThesaurusIDs on the same line as the Pre-ambiguous pattern, then this Pre-ambiguous pattern only applies to the listed MetaThesaurusIDs.

## immediate pre ambiguous
Immedidate pre-ambiguous patterns are words or phrases that occur immediately before a concept, but not before a but boundary, and which make the concept ambiguous.

Immediate pre-ambiguous words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character
.
Layout is one or more column(s)
* 'Immediate_pre_ambiguous'
* zero or more columns of MetaThesaurusID.
If there are no MetaThesurusIDs on the same line as an Immedidate pre-ambiguous pattern, then this Immediate pre-ambiguous] pattern applies to all MetaThesaurusIDs.
If there are one or more MetaThesaurusIDs on the same line as the Immediate pre-ambiguous pattern, then this Immediate pre-ambiguous pattern only applies to the listed MetaThesaurusIDs.

## post ambiguous
Post ambiguous patterns are words or phrases that occur anywhere after a concept, but not after a but boundary, and which make the concepts ambiguous.

Post ambiguous exeception patterns are words or phrases which, when they occurr after a concept, contra indicate the matching post ambiguous pattern.

Post ambiguous words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Post ambiguous exception words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

Layout is two columns
* 'Post_ambiguous'
* 'Exceptions'

## immediate post ambiguous
Immediate post ambiguous patterns are words or phrases that occur immediately after a concept, but not after a but boundary, and which make the concept ambiguous.

Immediate post ambiguous exeception patterns are words or phrases which, when they occurr after a concept, contra indicate the matching immediate post ambiguous pattern.

Immediate post ambiguous words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Immediate post ambiguous exception words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

Layout is two column
* 'Immediate_post_ambiguous'
* 'Exceptions'


# CONCEPT MODIFYING WORDS AND PHRASES
Like negation, there are words and phrases that modify the interpretation of a concept. Sometimes that modification transforms a concept into a different concept.

## pre modifiers
Pre-modifiers are words or phrases that occur immediately before a concept (white space only) and which modify the immediately following concept into a different Solution concept (SolutionID).

Pre-modifier words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Solution concepts (SolutionIDs) can be MetaThesaurus ConceptIDs, but are not restricted to MetaThesaurus ConceptIDs; the just have to be alphanumeric codes.

Order matters here as concepts can get modified to concepts that then get modified again to another concept.

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

To specify a negated concept, prepend the '-' character to the concept ID. To specify an ambiguous concept, prepend two question mark characters (?) to the concept ID.

Layout is three columns
* MetaThesaurusID
* SolutionID
* 'modifier'

HINT: use MetaThesaurus ConceptIDs as Solution ConceptIDs wherever possible. This will aid in the clarity of the solution as MetaThesarus Concept IDs have well defined semantic meanings.

# post modifiers
Post-modifiers are words or phrases that occur immediately after a concepts (white space only) and which modify the immediately preceding concept into a different Solution concept (SolutionID).

Post-modifier words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \) , and commas must be specified as \,

Solution concepts (SolutionIDs) can be MetaThesaurus ConceptIDs, but are not restricted to MetaThesaurus ConceptIDs; the just have to be alphanumeric codes.

Order matters here as concepts can get modified to concepts that then get modified again to another concept.

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

To specify a negated concept, prepend the '-' character to the concept ID. To specify an ambiguous concept, prepend two question mark characters (?) to the concept ID.

Layout is three columns
* MetaThesaurusID
* SolutionID
* 'modifier'

HINT: use MetaThesaurus ConceptIDs as Solution ConceptIDs wherever possible. This will aid in the clarity of the solution as MetaThesarus Concept IDs have well defined semantic meanings.


# WORDS AND PHRASES THAT ARE A CONCEPT
In the 'prepare' phase you can replace words or phrases that MetaMapLite is not going to recognise with clinical terms that MetaMapLite will recognise.
An alternative, where a word or phrase is a known clinical concept, is to map the word or phrase to a concept using 'sentence_concepts'.

## sentence concepts
Sentence concepts are the words or phrases that are commonly used within sentences but are **unknown** to MetaMapaLite and which imply a Solution concept (SolutionID).
These are checked on a sentence by sentence basis, after MetaMapLite coding.
Neither order nor case is important; order within the sentence is preserved and these words or phrases get coded as additional Solution concepts (SolutionIDs) in the sentence.

Sentence concept words/phrases **cannot** be things that MetaMapLite is going to find. If they are you will be defining something twice.

Also, unlike 'terms' in document preparation, you cannot define the long form, followed by the short form, because both will be found.
Instead you would configure an sentece concept for the short form and a second sentence concept for the additional words or phrases that convert the short form to the long form.
Then you would configure a concept set (see below) to identify the short form SolutionID followed by the additional words or phrases SolutionID and map those to a third SolutionID - being the SolutionID for the long form.

Solution concepts (SolutionIDs) can be MetaThesaurus ConceptIDs, but are not restricted to MetaThesaurus ConceptIDs; the just have to be alphanumeric codes.

Sentence concept words or phrases are a regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

To specify a negated concept, prepend the '-' character to the concept ID. To specify an ambiguous concept, prepend two question mark characters (?) to the concept ID.

HINT: use MetaThesaurus ConceptIDs as Solution ConceptIDs wherever possible. This will aid in the clarity of the solution as MetaThesarus Concept IDs have well defined semantic meanings.


# MULTI-SENTENCE AND CONCEPT DRIVEN NEGATIONS
Negation can cross multiple sentences, such as "All of the following are untrue".
These gross negation must have a start (starting pattern) and an end (ending pattern), both of which must exist within a defined, limited, number of sentences.
Sometimes a concept can be so authoritative that once it has been asserted to be negative, it effectively overrides other concepts.
These overridden concepts are configured as lists and every concept in the list is negated when a negated instance of the authoratative concept is found.

## gross_negotiations
Gross-negations are pairs of words or phrases that surround a set of concepts, all of which are negated.

The gross negation markers are regular expressions; white space must be specified as \s+, brackets must be specified as \( and \).

The gross negation markers are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanum. character.

Layout is three colums
* 'Start Negation'
* 'End Negation'
* Sentences - being the maximum number of sentences between 'Start Negation' and 'End Negation'

## sentence_negation_lists
Sentence negation lists are lists of MetaThesaurus ConceptIDs which must be negated, or made ambiguous when a negated MetaThesaurusID or SolutionID is found
in the same sentence in the matching section(s) of the document. The negated MetaThesaurusID or SolutionID is deemed definitive and overrides all the MetaThesaurusID in the list.

Sentence negation lists are checked on a sentence by sentence basis before any of the sets are processed and again after all of the sets are processed.

'Section' is a section code from 'section_markers' or 'All' for all sections.

'Negate' is TRUE/True to negate all the concepts in the list and FALSE/False to just make them ambiguous.

To specify a negated concept in the list prepend the '-' character to the concept ID. To specify an ambiguous concept in the list prepend two question mark characters (?) to the concept ID.

Layout is four or more column(s)
* 'MetaThesaurusID'
* 'Section'
* 'Negate\
* one or more columns of MetaThesaurusIDs

## document negation lists
Document negation lists are lists of MetaThesaurusIDs which must be negated or made ambiguous, when a negated instance of the MetaThesaurusID or SolutionID is found anywhere
in the same section(s) of the document. The negated MetaThesaurusID or SolutionID is deemed definitive and overrides all the MetaThesaurusID in the list.

Document negation lists are checked on a sentence by sentence basis before any of the sets are processed and again after all of the sets are processed.

'Section' is a section code from 'section_markers' or 'All' for all sections. 

'Negate' is TRUE/True to negate all the concepts in the list and FALSE/False to just make them ambiguous.

To specify a negated concept in the list prepend the '-' character to the concept ID. To specify an ambiguous concept in the list prepend two question mark characters (?) to the concept ID.

Layout is four or more column(s)
* 'MetaThesaurusID'
* 'Section'
* 'Negate'
* one or more columns of MetaThesaurusIDs


# CONCEPT SETS
Concept sets are sets of MetaThesaurus ConceptIDs and/or Solution concepts (SolutionIDs) which, when found, imply an additional SolutionID.
These additional SolutionIDs are added to the document, in the sentence, at the point where the last conceptID in the set is found.

Additional SolutionIDs can be 'Asserted', in which case they become a replacement for all the conceptIDs in the set.

When an additional SolutionID is 'Asserted', all the conceptIDs in the matching set of conceptIDs will be marked as 'Used'.
'Used' conceptIDs cannot be used for matching when checking for any subsequent concept sets.

Additional SolutionIDs are not marked as 'Used' and hence then can become part ot a subsequent concept set.
So order is important, not just the order within each concept set, but also the order in which the concept sets are processed.

Concepts sets are processed in the following order - 
1. Single sentence Sequence Sets - strict sequence, then non-strict sequence.
2. Multiple sentence Sequence Sets - strict sequence, then non-strict sequence.
3. Sentence Unsequenced Sets - single sentence, then multi-sentence
4. Document Sets -  sequenced, then unsequenced.

To specify a negated concept, prepend the '-' character to the concept ID. To specify an ambiguous concept, prepend two question mark characters (?) to the concept ID.

## sent strict seq concept sets
Sentence strict sequence concept sets are sets of MetaThesaurus ConceptIDs which, when found in strict sequence in a sentence, imply a Solution concept (SolutionID).
There must not be other any concepts in the sentence between the concepts in the set. Alternate concepts at the same point in the sentence are permitted.

Sentence strict sequence concept sets are checked on a sentence by sentence basis.
When all members of a sentence strict sequence concept set are found adjacent and in sequence, in a sentence, then the SolutionID becomes an 'additional' concept attached to the sentence
at the point in the sentence where the last concept in the set was found.

If the additional SolutionID is 'Asserted' then all the concepts used to match the strict sequence set are marked as 'Used'.

To specify a match with a negated concept, prepend the '-' character to the concept ID. To specify a match with ambiguous concept, prepend two question mark characters (?) to the concept ID.

Layout is three or more columns
* 'SolutionID'
* 'Asserted'
* one or more MetaThesaurusIDs.

## sentence sequence concept sets
Sentence sequence concept sets are sets of MetaThesaurus ConceptIDs which, when found in sequence in a sentence, imply a Solution concept (SolutionID).
There can be other concepts in the sentence between the concepts in the sentence sequence concept set, but the concepts must occur in the specified sequence.

Sentence sequence concept sets are checked on a sentence by sentence basis.
When all members of a sentence sequence concept set are found, in sequence,  in a sentence, then the SolutionID becomes an 'additional' concept attached to the sentence
at the point in the sentence where the last concept in the set was found.

If the additional SolutionID is 'Asserted' then all the concepts used to match the strict sequence set are marked as 'Used'.

To specify a match with a negated concept, prepend the '-' character to the concept ID. To specify a match with ambiguous concept, prepend the '?' character to the concept ID.

Layout is four or more columns
* 'SolutionID'
* 'Sentences'
* 'Asserted'
* one or more MetaThesaurusIDs.

## multi sent strict seq conc sets
Multi-sentence strict sequence concept sets are sets of MetaThesaurus ConceptIDs which, when found in strict sequence across multiple sentences, imply a Solution concept (SolutionID).

There must not be other any concepts in the sentences between the concepts in the set. Alternate concepts at the same point in the sentence are permitted.

Multi-sentence strict sequence concept sets are checked on a sentence by sentence basis.
When all members of a multi-sentence strict sequence concept set are found adjacent and in sequence, across adjacent sentences, then the SolutionID becomes an 'additional' concept attached
to the last sentence, at the point in the last sentence where the last concept in the set was found.

If the additional SolutionID is 'Asserted' then all the concepts used to match the strict sequence set are marked as 'Used'.

To specify a match with a negated concept, prepend the '-' character to the concept ID. To specify a match with ambiguous concept, prepend two question mark characters (?) to the concept ID.

Layout is four or more columns
* 'SolutionID'
* 'Sentences'
* 'Asserted'
* one or more MetaThesaurusIDs.

## multi sentence seq concept sets
Multi-sentence sequence concept sets are sets of MetaThesaurus ConceptIDs which, when found in sequence across multiple sentences, imply a Solution concept (SolutionID).
There can be other concepts in the sentence between the concepts in the sentence sequence concept set, but the concepts must occur in the specified sequence.

Sentence sequence concept sets are checked on a sentence by sentence basis.
When all members of a multi-sentence sequence concept set are found adjacent and in sequence, across adjacent sentences, then the SolutionID becomes an 'additional' concept attached
to the last sentence, at the point in the last sentence where the last concept in the set was found.

If the additional SolutionID is 'Asserted' then all the concepts used to match the strict sequence set are marked as 'Used'.

To specify a match with a negated concept, prepend the '-' character to the concept ID. To specify a match with ambiguous concept, prepend two question mark characters (?) to the concept ID.

Layout is four or more columns
* 'SolutionID'
* 'Sentences'
* 'Asserted'
* one or more MetaThesaurusIDs.

## sentence concept sets
Sentence concept sets are sets of MetaThesaurus ConceptIDs which, when found in a sentence, in any order, imply a Solution concept (SolutionID).

These are checked on a sentence by sentence basis after all the sentence sequence concept sets are checked.
When all members of a sentence concept set are found,  in a sentence, then the SolutionID becomes an 'additional' concept attached to the sentence,
at the point in the sentence where the last concept in the set was found in the sentence.

If the additional SolutionID is Asserted then all the concepts used to match the sentence concept set are marked as 'Used'.

To specify a match with a negated concept, prepend the '-' character to the concept ID. To specify a match with ambiguous concept, prepend two question mark characters (?) to the concept ID.

Layout is three or more columns
* 'SolutionID'
* 'Asserted'
* one or more MetaThesaurusIDs.

## multi sentence concept sets
Multi-sentence concept sets are sets of MetaThesaurus ConceptIDs which, when found across multiple sentences, in any order, imply a Solution concept (SolutionID).

These are checked on a sentence by sentence basis after all the sentence sequence concept sets are checked.
When all members of a multi-sentence concept set are found across adjacent sentences, then the SolutionID becomes an 'additional' concept attached
to the last sentence, at the point in the last sentence where the last concept in the set was found.

If the additional SolutionID is'Asserted' then all the concepts used to match the strict sequence set are marked as 'Used'.

To specify a match with a negated concept, prepend the '-' character to the concept ID. To specify a match with ambiguous concept, prepend two question mark characters (?) to the concept ID.

Layout is four or more columns
* 'SolutionID'
* 'Sentences'
* 'Asserted'
* one or more MetaThesaurusIDs.

## document sequence concept sets
Document sequence concept sets are sets of MetaThesaurus ConceptIDs which, when found in sequence in the document (across all sentences), imply a Solution concept (SolutionID).
There can be other concepts between the concepts in the document sequence concept set, but the concepts must occur in the specified sequence.

Document sequence concept sets are checked on a whole of document basis, after all sentence sets are checked.
When all members of a document sequence concept set are found in sequence, then the SolutionID becomes an 'additional' concept attached
to the last sentence, at the point in the last sentence where the last concept in the set was found.

If the additional SolutionID is 'Asserted' then all the concepts used to match the strict sequence set are marked as 'Used'.

To specify a match with a negated concept, prepend the '-' character to the concept ID. To specify a match with ambiguous concept, prepend the '?' character to the concept ID.

Layout is three or more columns
* 'SolutionID'
* 'Asserted'
* one or more MetaThesaurusIDs.

## document concept sets
Document concept sets are sets of MetaThesaurus ConceptIDs which, when found in the document (across all sentences), imply a Solution concept (SolutionID).

Document sequence concept sets are checked on a whole of document basis, after all sentence sets are checked.
When all members of a document sequence concept set are found then the SolutionID becomes an 'additional' concept attached
to the last sentence, at the point in the last sentence where the last concept in the set was found.

If the additional SolutionID is 'Asserted' then all the concepts used to match the strict sequence set are marked as 'Used'.

To specify a match with a negated concept, prepend the '-' character to the concept ID. To specify a match with ambiguous concept, prepend the '?' character to the concept ID.

Layout is three or more columns
* 'SolutionID'
* 'Asserted'
* one or more MetaThesaurusIDs.

# SolutionMetathesaurus
The Solution MetaThesaurus contains all the MetaThesaurusIDs and SolutionIDs plus their descriptions (including negated and ambiguous forms of these IDS).
The Solution MetaThesaurus worksheet does not constitute part of the solution, and is included in each workbook for documentation purposes only.

There is a SolutionMetaThesaurus.csv file that is generated by the SolutionMetaThesaurus.py script, which is part of the solution, but again only for descriptions in diagnostic messages.

The SolutionMetaThesaurus worksheet is just an import of the SolutionMetaThesaurus.csv file and hence can be refreshed if a new SolutionMetaThesaurur.csv file is created.

Layout is two columns
*'MetaThesaurus Code'
*'Metathesaurus Description'.

# OtherConcepts
Metathesaurus concepts know to exist in documents of this type, but which are known to be irrelevant to this solution.

OtherConcepts is part of the solution but only effects logging.

Concepts in a document that are not part of the solution, and not listed in OtherConcepts
will be logged as "New Concept". The log file should be reviewed for "New Concept"s periodically as part if the routing solution review
as they may indicate changes in reporting standards/processes which need to accomodated in any updated version of the solution.

Layout is two columns
* 'MetaThesaurus Code'
* 'Document text', being the matching text in a document that was matched to this MetaThesaurus Code.

