# This is the "Introduction" worksheet from the "prepare.xlsx" workbook

This is the "prepare" configuration workbook for preparing histopathology reports for autocoding.

# BASE CONFIGURATION ITEMS
## labels
* The list of labels that are used at the start of lines to indicate the context of what follows.
* Labels contain clinical terms should not be coded, so we replace them with with non-clinical labels.
e.g. "HIGH BLOOD PRESSURE: not measured" should not be coded to 'high blood pressure'.
* Labels also terminate the previous sentence if required.
* Defining non-clinical labels will prevent a sequence of lines, consisting of just labels, being concatenated into a single sentence.
* Order is not important, but case is important.

The layout is two colums; a 'regular expression' and a replacement 'string'.
+ Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.
Which means that the terms will only be recognised if they are preeed by, and followed by, a boundary between words and non-words.
Note: white space within the labels must be specified as \s+, brackets must be specified as \\( and \\).

## terms
* Terms are commonly used word(s) and their technical equivalent word or phrase.
* These substitutions/replacements are made to the document before any codes or sentences are extracted.
* Order is important, but only if the 'technical equivalent' contains a word that is also a commonly used word, which is also to be replaced. Case is not important.
  * e.g. replace "tollerable BP" with "normal BP" before replacing "BP" with 'blood pressure'.

The layout is two columns; a 'regular expression' of the common word(s) and a replacement 'string'
+ Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.
which means that the terms will only be recognised if they are preeed by, and followed by, a boundary between words and non-words.
Note: white space within the commonly used term must be specified as \s+, brackets must be specified as \\( and \\).

## preamble markers
* Preamble markers are words or phrases that mark the start, or end, a section of preamble (not the body of the document).

The layout is thee columns; a 'regular expression', a boolean to indicate that the marker is case sensitive and a boolean to indicate type of history marker.
* The regular expression is the pattern that indicates the start  or end of as section of preamble.
* The first boolean is TRUE to indicate that the marker is case sensitive - upper and lower case must match. FALSE means that a match that ignores case is a match.
* The second boolean is true to indicate that the marker marks the start of a section of preamble, false to indicate that the marker marks the end of a section of preamble.
* The preamble markers are regular expression. White space within the preamble marker must be specified as \s+, brackets must be specified as \\( and \\).
Preamble markers are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

## preamble terms
* Preamble terms are things that are commonly used in the preamble (before anything clinical) and their non-technical equivalent word or phrase.
These are ususally thing about how the test was performed and the acronyms here sometimes clash with clinical acronyms.
These substitutions/replacements are made to the document before coding.

The layout is two columns; a 'regular expression and a replacement 'string'.
* Regular expressions are prepended with r'\b' if they start with an alphanumeric character and appended with r'\b' if they end with an alphanumeric character.

Note: white space within the commonly used words must be specified as \s+, brackets must be specified as \\( and \\).


# SPECIFIC HISTOPATHOLOGY CONFIGURATION ITEMS
## List markers
* List markers are numbers or letters followed by a ./:/) or similar, at the beginning of a line, which indicate the start of a list item.

The layout is two columns; a 'regular expression' and a boolean to indicate that the marker is case sensitive.
* The regular expression is the pattern that indicates that this line is a list item.
* The boolean is TRUE to indicate that the marker is case sensitive - upper and lower case must match. FALSE means that a match that ignores case is a match.
* The  list markers are regular expression. White space within the list marker must be specified as \s+, brackets must be specified as \\( and \\).
* List  markers are prepended with r'^' so that they only match at the start of a line.

## Hyphenated words
* Hyphenated words that are to be preserved when they occur in headings/lists.
* In headings/lists, hyphens are usually dashes added as presentation trim, which often confuses MetaMapLite.

The layout a single  columns; 'hyphenated words'.

