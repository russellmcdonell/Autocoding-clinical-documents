# pylint: disable=invalid-name, unused-variable, line-too-long, no-name-in-module
'''
This module implements the AutoCoding Clinical Documents project as a Flask website and api service

'''

# Import all the modules that make life easy
import logging
from flask import jsonify, url_for, request, Response
from __main__ import app
import functions as f
import data as d



@app.route('/', methods=['GET'])
def splash():
    '''
    Display the Welcome message
    '''
    message = '<html><head><title>AutoCoding Clinical Documents</title><link rel="icon" href="data:,"></head><body style="font-size:120%">'

    message += '<h1>AutoCode a Clinical Document</h1><h2>Paste your Clinical Document below - then click the AutoCode button</h2>'
    message += f'<form method="post" action ="{url_for("splash")}">'
    message += '<textarea type="text" name="document" style="height:70%; width:70%; word-wrap:break-word; word-break:break-word"></textarea>'
    message += '<p><input type="submit" value="AutoCode this please"/></p>'
    message += '</form>'
    message += '<p><b><u>WARNING:</u></b>This is not a production service. '
    message += 'There is no security/login requirements on this service.'
    message += 'It is recommended that you obtain a copy of the source code from <a href="https://github.com/russellmcdonell/AutoCoding_Clinical_Documents">GitHub</a></br>'
    message += 'and run it on your own server/laptop with appropriate security.'
    message += 'This in not production ready software.'
    message += '</p></body></html>'
    return Response(response=message, status=200)

@app.route('/', methods=['POST'])
def FlaskAutoCoding():
    '''
    AutoCode the document
    '''

    # Get the POSTed data
    data = {}
    if request.content_type == 'application/x-www-form-urlencoded':         # From the web page
        for variable in request.form:
            value = request.form[variable].strip()
            if value != '':
                data[variable] = value
    else:                                                                   # From an api call
        data = request.get_json()

    # Check if a JSON or HTML response is required
    wantsJSON = False
    for i, (mimeType, quality) in enumerate(request.accept_mimetypes):
        if mimeType == 'application/json':
            wantsJSON = True

    if 'document' not in data:
        if wantsJSON:
            logging.critical('No document in request')
            newData = d.sa.reportJSON(False)
            return jsonify(newData)
        else:
            message = '<html><head><title>AutoCoding Clinical Documents</title><link rel="icon" href="data:,"></head><body style="font-size:120%">'
            message += '<h2 style="text-align:center">No document</h2>'
            message += f'<p style="text-align:center"><b><a href="{url_for("splash")}">AutoCode another Clinical Document</a></b></p></body></html>'
            return Response(response=message, status=200)

    # Now AutoCode the clinical document
    document = data['document']
    d.rawClinicalDocument = ''
    for line in document.split('\n'):
        d.rawClinicalDocument += line.rstrip() + '\n'
    success = f.AutoCode()
    if success != d.EX_OK:
        if wantsJSON:
            logging.critical('AutoCoding failed for document:%s', d.rawClinicalDocument)
            newData = d.sa.reportJSON(False)
            return jsonify(newData)
        else:
            message = '<html><head><title>AutoCoding Clinical Documents</title><link rel="icon" href="data:,"></head><body style="font-size:120%">'
            message += '<h2 style="text-align:center">AutoCoding of this Clinical Document failed</h2>'
            message += f'<p style="text-align:center"><b><a href="{url_for("splash")}">AutoCode another Clinical Document</a></b></p></body></html>'
            return Response(response=message, status=200)

    if wantsJSON:
        # Return the results dictionary
        newData = d.sa.reportJSON(True)
        return jsonify(newData)

    # Return HTML
    message = '<html><head><title>AutoCoding Clinical Documents</title><link rel="icon" href="data:,">'
    message += '<script type="text/javascript">\n'
    message += 'var toggleVisibility = function(element) {\n'
    message += "    if(element.style.display=='block'){\n"
    message += "        element.style.display='none';\n"
    message += '    } else {\n'
    message += "        element.style.display='block';\n"
    message += '    }\n'
    message += '};\n'
    message += '</script>\n'
    message += '</head><body style="font-size:120%">'
    message += d.sa.reportHTML()
    message += '</p>'
    message += f'<p style="text-align:center"><b><a href="{url_for("splash")}">AutoCode another clinical document</a></b></p>'

    message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'raw'" + '))">Initial Document</li></u>\n'
    message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'prepared'" + '))">Prepared Document</li></u>\n'
    message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'NLP'" + '))">MetaMapLite coded Document</li></u>\n'
    message += '        <br><u><li style="display:block" onClick="toggleVisibility(document.getElementById(' + "'complete'" + '))">Completely coded Document</li></u>\n'

    message += '<div id="raw" style="display:none"><h3>Raw Input</h3><pre>\n'
    message += d.rawClinicalDocument
    message += '</pre></div>\n'
    message += '<div id="prepared" style="display:none"><h3>Prepared Input</h3><pre>\n'
    message += d.preparedDocument
    message += '</pre></div>\n'
    message += '<div id="NLP" style="display:none"><h3>MetaMapLite coded Document</h3><pre>\n'
    message += renderDocument(d.codedSentences)
    message += '</pre></div>\n'
    message += '<div id="complete" style="display:none"><h3>Completely coded Document</h3><pre>\n'
    message += renderDocument(d.completedSentences)
    message += '</pre></div>\n'

    message += '</p></body></html>'
    return Response(response=message, status=200)


def renderDocument(sentences):
    '''
    Render d.preparedDocument as lines with codes from 'sentences'
    '''

    # Output each sentence followed by the codes
    renderedLines = []
    lineStart = 0
    lineEnd = 0
    sentenceNo = 0
    for line in d.preparedDocument.split('\n'):
        thisLine = line.strip()
        lineStart = lineEnd
        lineEnd += len(thisLine) + 1
        # logging.debug('renderDocument() - rendering line %s, from %d to %d', thisLine, lineStart, lineEnd)
        renderedLines.append(thisLine)
        if sentenceNo == len(sentences):
            continue
        while (sentences[sentenceNo][2] + sentences[sentenceNo][3]) < lineStart:
            # logging.debug('renderDocument() - skipping sentence %d, from %d to %d, (%s)',
            #               sentenceNo, sentences[sentenceNo][2], sentences[sentenceNo][2] + sentences[sentenceNo][3], sentences[sentenceNo][4])
            sentenceNo += 1
            if sentenceNo == len(sentences):
                break
        if sentenceNo == len(sentences):
            continue
        codeLines = []
        while sentences[sentenceNo][2] + sentences[sentenceNo][3] < lineEnd:
            # logging.debug('renderDocument() - rendering sentence %d, from %d to %d, (%s)',
            #               sentenceNo, sentences[sentenceNo][2], sentences[sentenceNo][2] + sentences[sentenceNo][3], sentences[sentenceNo][4])
            document = sentences[sentenceNo][6]    # Sentences hold mini-documents
            for start in sorted(document, key=int):        # We step through all concepts, in sequence across this sentence
                # logging.debug('renderDocument() - checking codes as %s with start %d and end %d', start, lineStart, lineEnd)
                if start < lineStart:
                    continue
                if start > lineEnd:
                    break
                for j in range(len(document[start])):            # Step through the list of alternate concepts at this point in this sentence
                    concept = document[start][j]['concept']        # This concept
                    if concept not in d.solutionMetaThesaurus:
                        continue
                    codeAt = thisLine.find(document[start][j]['text'])
                    if codeAt == -1:
                        continue
                    # logging.debug('renderDocument() - rendering concept (%s) at %d', concept, codeAt)
                    foundLine = None
                    for i, codeLine in enumerate(codeLines):
                        if len(codeLine) + 2 < codeAt:
                            foundLine = i
                            break
                    else:
                        foundLine = len(codeLines)
                        codeLines.append('')
                    pad = codeAt - len(codeLines[foundLine])
                    codeLines[foundLine] += ' ' * pad
                    codeLines[foundLine] += '<span style="color:blue;background-color:aqua">'
                    codeLines[foundLine] += concept + f"[{document[start][j]['text']}]({d.solutionMetaThesaurus[concept]['description']})"
                    codeLines[foundLine] += '</span>'
            else:
                break
            sentenceNo += 1
            if sentenceNo == len(sentences):
                break
        renderedLines += codeLines
    return '\n'.join(renderedLines)
