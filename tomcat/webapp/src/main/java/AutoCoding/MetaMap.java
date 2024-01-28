package AutoCoding;

import javax.servlet.ServletException;
import javax.servlet.ServletContext;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.BufferedReader;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Optional;
import java.util.Map;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.Enumeration;


import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import bioc.BioCDocument;

import gov.nih.nlm.nls.ner.MetaMapLite;
import gov.nih.nlm.nls.metamap.document.FreeText;
import gov.nih.nlm.nls.metamap.lite.types.Entity;
import gov.nih.nlm.nls.metamap.lite.types.Ev;
import gov.nih.nlm.nls.utils.StringUtils;
import gov.nih.nlm.nls.types.Sentence;
import gov.nih.nlm.nls.types.Annotation;

import AutoCoding.MetaMapConfig;

import gov.nih.nlm.nls.metamap.lite.resultformats.ResultFormatter;
import gov.nih.nlm.nls.metamap.lite.resultformats.ResultFormatterRegistry;


//
/**
 * A simple Java launcher for auto-coding Clinical Reports using MetaMapLite
 */
public class MetaMap extends HttpServlet { 
  /** log4j logger instance */
  private static final Logger logger = LogManager.getLogger(MetaMap.class);
  // rootPath, dataPath and configPath are instantiated by SampleWebAppConfig class.
  /** root of servlet directory */
  public static String rootPath = "/";
  /** data subdirectory of servlet directory */
  public static String dataPath = "data/";
  /** config subdirectory of servlet directory */
  public static String configPath = "config/";
  Properties properties;

  /* Gleaned from
   * https://stackoverflow.com/questions/2999376/whats-the-right-way-of-configuring-the-path-to-a-sqlite-database-for-my-servlet
   */
  public MetaMap() {

  }


  /* This is either a browser requesting a display page for data entry, or an application passing data to be coded */
  @Override
  public void doGet(HttpServletRequest request, HttpServletResponse response)
    throws ServletException, java.io.IOException {

    try {
      String contextPath = request.getContextPath();
      String page = "<html>\n" +
	"<head>\n<title>AutoCode a Clinical Text Document</title>\n</head>\n<body>\n" +
	"<h1>AutoCode a Clinical Text Document</h1>\n" +
	"<h2>Past your Clinical Text Document below - then click the AutoCode button</h2>\n" +
	"<form method=\"post\" enctype=\"x-www-form-urlencoded\" action=\"" + request.getContextPath() + "/MetaMapLite\">\n" +
        "<textarea type=\"text\" name=\"document\" style=\"height:70%; width:70%; word-wrap:break-word; word-break:break-word\"></textarea>\n" +
	"<p><input type=\"submit\" value=\"AutoCode this please\">\n" +
	"</form>\n" +
	"</body>\n</html>" ;
      PrintWriter out = response.getWriter();
      out.print(page);
      out.flush();
      out.close();
      response.setStatus(HttpServletResponse.SC_OK);
    } catch (Exception e) {
      response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR,
			 "Internal server error");
    }
  }

  public void doPost(HttpServletRequest request, HttpServletResponse response)
    throws ServletException,java.io.IOException {

    String contextPath = request.getContextPath();
    String contentType = request.getHeader("content-type");
    String acceptType = request.getHeader("accept");
    Boolean isJSON = acceptType.equals("application/json");
    ServletContext ctx = request.getServletContext();
    MetaMapLite metaMapLiteInst = (MetaMapLite)ctx.getAttribute("MetaMapLiteInstance");

    if (contentType.equals("application/x-www-form-urlencoded")) {
      // test parameters
      String inputText = request.getParameter("document");
      if (inputText == null) {
	response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Missing a document");
	return;
      } else if (inputText.trim().length() == 0)  {
	response.sendError(HttpServletResponse.SC_BAD_REQUEST, "Empty document");
	return;
      }
      try {
	BioCDocument document = FreeText.instantiateBioCDocument(inputText);
	List<BioCDocument> documentList = new ArrayList<BioCDocument>();
	// List<Sentence> sentenceList = new ArrayList<Sentence>();
	document.setID("1");
	documentList.add(document);
	List<Entity> entityList = metaMapLiteInst.processDocumentList(documentList);
	List<Sentence> sentenceList = metaMapLiteInst.getSentenceList(documentList);
	PrintWriter out = response.getWriter();

	if (isJSON) {
	  String thisJSON = "{";
	  response.setContentType("text/json");
	  Boolean firstConcept = true;
	  thisJSON += "\"concepts\":[";
	  for (Entity entity: entityList) {
	    for (Ev ev: entity.getEvSet()) {
	      if (firstConcept) {
		firstConcept = false;
	      } else {
		thisJSON += ",";
	      }
	      thisJSON += "{\"" + ev.getConceptInfo().getCUI() + "\":{";
	      thisJSON += "\"start\":" + String.format("%d", ev.getStart()) + ",";
	      thisJSON += "\"length\":" + String.format("%d", ev.getLength()) + ",";
	      thisJSON += "\"partOfSpeech\":\"" + ev.getPartOfSpeech() + "\",";
	      String thisText = ev.getText();
	      thisText = thisText.replace("\\", "\\\\");
	      thisText = thisText.replace("\b", "\\b");
	      thisText = thisText.replace("\f", "\\f");
	      thisText = thisText.replace("\n", "\\n");
	      thisText = thisText.replace("\r", "\\r");
	      thisText = thisText.replace("\t", "\\t");
	      thisText = thisText.replace("\"", "\\\"");
	      thisJSON += "\"text\":\"" + thisText + "\",";
	      thisJSON += "\"isNegated\":" + entity.isNegated() + "}}";
	    }
	  }
	  thisJSON += "],\"sentences\":[";
	  Boolean firstSentence = true;
	  for (Sentence sentence: sentenceList) {
	    if (firstSentence) {
	      firstSentence = false;
	    } else {
	      thisJSON += ",";
	    }
	    thisJSON += "{\"start\":" + String.format("%d", sentence.getOffset()) + ",";
	    String thisText = sentence.getText();
	    thisText = thisText.replace("\\", "\\\\");
	    thisText = thisText.replace("\b", "\\b");
	    thisText = thisText.replace("\f", "\\f");
	    thisText = thisText.replace("\n", "\\n");
	    thisText = thisText.replace("\r", "\\r");
	    thisText = thisText.replace("\t", "\\t");
	    thisText = thisText.replace("\"", "\\\"");
	    thisJSON += "\"text\":\"" + thisText + "\"}";
	  }
	  thisJSON += "]}";
	  out.print(thisJSON);
	} else {
	  out.print("<html>\n<head>\n<title>AutoCoded Clinical Text Document</title>\n<style>");
	  out.print("table, th, td {border: 1px solid black; border-collapse: collapse;}\n");
	  out.print("</style>\n</head>\n<body>\n");
	  out.println("<h2>AutoCoded Clinical Text Document</h2>");
	  out.println("<h3>Original clinical text document</h3>");
	  out.println("<textarea style=\"height:40%; width:70%; word-wrap:break-word; word-break:break-word\">" + inputText + "</textarea>");
	  out.println("<br><h3>Sentences</h3><table><tr><th>Offset</th><th>Sentence</th></tr>");
	  for (Sentence sentence: sentenceList) {
	    out.println("<tr><td>" + String.format("%d", sentence.getOffset()) + "</td><td>" + sentence.getText() + "</td></tr>");
	  }
	  out.println("</table>");
	  out.println("<p><h3>Entity list:" + entityList.size() + " entities</h3>");
	  out.print("<table><tr><th>Offset</th><th>Length</th><th>Neg</th><th>Matched Text</th>");
	  out.println("<th>Concept</th><th>SemTypes</th><th>PreferredName</th></tr>");
	  for (Entity entity: entityList) {
	    String negated = String.format("%b", entity.isNegated());
	    for (Ev ev: entity.getEvSet()) {
	      out.println("<tr><td>" + String.format("%d", ev.getOffset()) + "</td>" +
			  "<td>" + String.format("%d", ev.getLength()) + "</td><td>" + negated + "</td>" +
			  "<td>" + ev.getText() + "</td><td>" + ev.getConceptInfo().getCUI() + "</td>" +
	  		  "<td>" + StringUtils.join(ev.getConceptInfo().getSemanticTypeSet(), "|") + "</td>" +
			  "<td>" + ev.getConceptInfo().getPreferredName() + "</td></tr>");
	    }
	  }
	  out.println("</table>");
          out.println("<br>");
          out.println("<a href=\"" + request.getContextPath() + "/MetaMapLite\">let's AutoCode some more</a>");
	  out.print("</body></html>" );
	}
	out.flush();
	out.close();
	response.setStatus(HttpServletResponse.SC_OK);
      } catch (Exception e) {
	String serverError = "Internal server error";
	serverError += " (" + e.getMessage() + ")";
	response.sendError(HttpServletResponse.SC_INTERNAL_SERVER_ERROR, serverError);
      }
    } else {
      String page = "<html>\n" +
	"<head>\n<title>AutoCode a Clinical Text Document</title>\n</head>\n<body>\n" +
	"<h1>AutoCode a Clinical Text Document</h1>\n" +
	"<h2>Past your Clinical Text Document below - then click the AutoCode button</h2>\n" +
	"<form method=\"post\" enctype=\"x-www-form-urlencoded\" action=\"" + request.getContextPath() + "/MetaMapLite\">\n" +
        "<textarea type=\"text\" name=\"document\" style=\"height:70%; width:70%; word-wrap:break-word; word-break:break-word\"></textarea>\n" +
	"<p><input type=\"submit\" value=\"AutoCode this please\">\n" +
	"</form>\n" +
	"</body>\n</html>" ;
      PrintWriter out = response.getWriter();
      out.print(page);
      out.flush();
      out.close();
      response.setStatus(HttpServletResponse.SC_OK);
    }
  }
}
