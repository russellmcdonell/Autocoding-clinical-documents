package AutoCoding;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;

import javax.servlet.ServletContext;
import javax.servlet.ServletContextEvent;
import javax.servlet.ServletContextListener;
import gov.nih.nlm.nls.ner.MetaMapLite;

public class MetaMapConfig implements ServletContextListener {
  /** log4j logger instance */
  private static final Logger logger = LogManager.getLogger(MetaMap.class);

  public void contextInitialized(ServletContextEvent event) {
    ServletContext ctx = event.getServletContext();
    String rootPath = ctx.getRealPath("/");
    // logger.warn("Config:rootPath:" + rootPath);
    MetaMapLite instance = MetaMapLiteFactory.newInstance(rootPath);
    ctx.setAttribute("MetaMapLiteInstance", instance);
  }
  public void contextDestroyed(ServletContextEvent event) {
  }
}
