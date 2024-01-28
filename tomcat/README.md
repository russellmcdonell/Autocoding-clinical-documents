# Example MetaMapLite Servlet.

## Compiling
    
See the file build.xml in the top level directory for more information
on the "clean" and "build-war" targets.    

    ant clean
    ant build-war

build-war compiles the source code if necessary and combines the java
class files and the supporting data and configuration files into a web
archive file compatible with most servlet engines (including Apache
Tomcat and Jetty).

## Development Directory Organization

Below is a pictorial representation of a possible directory
organization for a servlet containing MetaMapLite.  The
main properties file "metamaplite.properties" resides in the "config"
directory.  The inverted file indexes used by MetaMapLite reside in
the "ivf" directory.  The opennlp models reside in data/models
directory.

     webapp/
         |
         +- config
         +- data
         |   |
         |   +- ivf
         |   |   |
         |   |   +- 2022AB    (from MetaMapLite website)
         |   |       |
         |   |       +- USAbase
         |   |           |
         |   |           +- indices
         |   |           |   |
         |   |           |   +- cuiconcept
         |   |           |   +- cuisourceinfo
         |   |           |   +- cuist
         |   |           |
         |   |           +- tables
         |   +- models
         |
         +- lib    [metamaplite-3.6.2rc8-standalone.jar]
         +- src
         |   |
         |   +- main
         |       |
         |       +- java
         |       |   |
         |       |   +- sample
         |       |   
         |       +- webapp
         |           |
         |           +- WEB-INF
         |               |
         |               +- WebContent
         |               +- classes
         |                   |
         |                   +- sample
         |                   
         +- target
             |
             +- web
                 |
                 +- sample
    
An attempt has been made to make the directory structure somewhat
comformant to Maven's recommended directory organization to allow
relatively painless migration to Maven if desired.

## Classes

### Constructor - sample.SampleWebApp.java

The constructor for the sample.SampleWebApp class expected the
properties that have file paths to use paths relative to "data"
directory within the servlet container directory
(webapp/<servlet-name>).  The config file is located in "config"
within the servlet application directory.

The data and config file path are stored in static variables dataPath
and configPath which are initialized by the Servlet Context listener
sample.SampleWebAppConfig.  The static variable rootPath is also
initializer by the listener and refers to the root on the servlet
container.

### Servlet Context Listener - sample.SampleWebAppConfig.java

Listener for Servlet Context during servlet startup.  The listener
sets the static variables rootPath, dataPath and configPath in the
sample.SampleWebApp class.  The listener is referenced in
WEB-INF/web.xml using the "listener" element:

    <listener>
      <listener-class>sample.SampleWebAppConfig</listener-class>
    </listener>

## Organization Of War file and Deployment directory

The war file generated through the "build-war" ant task contains the
following directories:

    Directory              Contents
    ---------------------------------------------------------
	./                     index.html
    META-INF/              Manifest
	WEB-INF/               application descriptors, etc.
    WEB-INF/classes/       Java class files
	WEB-INF/lib/           third party libraries
    config/                configuration files
    data/                  special terms file
    data/ivf               inverted file indexes
    data/models            OpenNLP models


The tree representation of the directory organization of web archive
(war) file and deployment directory follows:

    sample-webapp/
       |
       +- META-INF
       +- WEB-INF
       |   |
       |   +- classes
       |   |   |
       |   |   +- sample
       |   |   
       |   +- lib
       |   
       +- config
       +- data
           |
           +- ivf
           |   |
           |   +- strict
           |       |
           |       +- indices
           |       |   |
           |       |   +- cuiconcept
           |       |   +- cuisourceinfo
           |       |   +- cuist
           |       |   
           |       +- tables
           |       
           +- models
      
See the Java Servlet Specification (http://download.oracle.com/otn-pub/jcp/servlet-3.0-fr-eval-oth-JSpec/servlet-3_0-final-spec.pdf) for more information.

See Apache Tomcat Application Developer's Guide
(https://tomcat.apache.org/tomcat-6.0-doc/appdev/deployment.html) for
more information about deployment.


