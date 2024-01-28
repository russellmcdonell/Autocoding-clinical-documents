# Autocoding-clinical-documents
Extract codes from clinical documents to support automated clinical decision processes

## Outline
This project leverages [MetaMapLite](https://lhncbc.nlm.nih.gov/ii/tools/MetaMap/run-locally/MetaMapLite.html)
to find clinical terms in free text documents. **MetaMapLite** uses the [Unified Medical Language System (UMLS)](http://www.nlm.nih.gov/research/umls/) as it's code/description database. **MetaMapLite** scans a free text document looking for terms and phrases that match the descriptions in **UMLS** and returns the matching **UMLS** codes. And if that was all there was to it, then this project wouldn't exist.

The problem is that you have to wrap code around **MetaMapLite** in order to create a solution for any specific Use Case.
* You may have to pre-process the document; replace abbreviations with their full description, correct any common typos etc. **MetamapLite** will only recognise correct medical terms.
* You may need to analyse the document to identify any sections of past conditions/illnesses and exclude these if you are attempting to determine any current conditions/illnesses.
* You may have to post-process the sentences and **UMLS** codes returned by **MetaMapLite**. **MetaMapLite** does recognize negation in front of a medical term, but doesn't extend that negation to subsequent medical terms in the sentence.
* You may need to map **UMLS** codes to some other coding system [**ULMS** has mapping tables for doing this].
* You may need to do some analysis; a cancer registry may want to know about only the cancer terms and what type of cancer and discard the rest; a cervical cancer surveylance and management program would want to know the type of cancer and where it was found, discarding all non-cervical cancer findings.
* You may need to do juxtoposition analysis of the codes, looking for Body Part (Topology) and Finding (Morphology) pairs in order to determine diagnosies. Even this may be too granular for a clinic decision about treatment plans and actions.
* You may need to pass these site/finding pairs (diagnosies) through some  decision logic to prioritize them in order to determine the most appropriate action plan/care plan/care pathway.

This project provides a configurable framework for all of these sorts of activities. It helps you develop and maintain multiple configurations as you may have multiple Use Case. No single solution will cater for all clinical document autocoding requirements.
* You may need to pre-analyse documents and route them to specific solutions based upon the source (Pathology laboratory or Endoscopic application).
* You may need to route anatomical pathology reports to different solutions based up the different software used by different pathology services.
* You may need to route documents to different solutions based upon the reporting pathologist, because different pathologists use different templates for the same investigative procedure.

This project aims to make the configuration and building of different solutions as simple as possible by identifying common, reusable components. Routing different document to different solutions is left as an exercise for the reader.

## Installation
The **Autocoding clinical documents** solution has been developed in Python. **MetaMapLite** is a Java library. A small amount of Java code facilitates the integration of Python and Java. That Java code is an API wrapper which gets combined with the **MetaMapLite** library to create a WAR file that can be run on a Tomcat server. The **Autocoding clinical documents** solution makes API calls to access the **MetaMapLite** functionality. That Java code can be found in the **tomcat** folder and is based upon and an extension to, the sample code 
