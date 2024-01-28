package AutoCoding;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.Properties;
import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import gov.nih.nlm.nls.ner.MetaMapLite;

/**
 * Describe class MetaMapLiteFactory here.
 *
 *
 * Created: Wed Apr 26 16:05:12 2017
 *
 * @author <a href="mailto:wjrogers@mail.nih.gov">Willie Rogers</a>
 * @version 1.0
 */
public class MetaMapLiteFactory {
  /** log4j logger instance */
  private static final Logger logger = LogManager.getLogger(MetaMap.class);

  /**
   * Creates a new <code>MetaMapLiteFactory</code> instance.
   *
   */
  public MetaMapLiteFactory() {

  }

  public static MetaMapLite newInstance(String rootPath) {
    String configPath = rootPath + "config";
    String dataPath = rootPath + "data";
    // logger.warn("Factory:rootPath:" + rootPath);
    // logger.warn("Factory:dataPath:" + dataPath);
    // logger.warn("Factory:configPath:" + configPath);
    MetaMapLite metaMapLiteInst;
    try {
      String configPropertyFilename = configPath + "/metamaplite.properties";
    
      // load user properties from file
      Properties properties = new Properties();
      properties.load(new FileReader(configPropertyFilename));

      // update the model and index directories
      properties.setProperty("metamaplite.models.directory", dataPath + "/" +
			     properties.getProperty("metamaplite.models.directory"));
      properties.setProperty("metamaplite.index.directory", dataPath + "/" +
			     properties.getProperty("metamaplite.index.directory"));

      // Expand Models and Index directories
      MetaMapLite.expandModelsDir(properties, properties.getProperty("metamaplite.models.directory"));
      MetaMapLite.expandIndexDir(properties, properties.getProperty("metamaplite.index.directory"));

      metaMapLiteInst = new MetaMapLite(properties);
      return metaMapLiteInst;
    } catch (IllegalAccessException iae) {
      throw new RuntimeException(iae);
    } catch (NoSuchMethodException nsme) {
      throw new RuntimeException(nsme);
    } catch (InstantiationException ie) {
      throw new RuntimeException(ie);
    } catch (ClassNotFoundException cnfe) {
      throw new RuntimeException(cnfe);
    } catch (FileNotFoundException fnfe) {
      throw new RuntimeException(fnfe);
    } catch (IOException ioe) {
      throw new RuntimeException(ioe);
    }
  }
}
