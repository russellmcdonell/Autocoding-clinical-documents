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
    message = '<html><head><title>AutoCoding Clinical Documents</title><link rel="icon" href="data:,"></head><body style="font-size:120%">'
    message += d.sa.reportHTML()
    message += '</p></body></html>'
    return Response(response=message, status=200)
