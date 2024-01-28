# Introduction
This is just anecdotal documentation of what worked best for me.
This code is based up and an extension to, the [MetaMapLite Servlet](https://lhncbc.nlm.nih.gov/ii/tools/MetaMap/run-locally/MetaMapLite.html) sample code. I used the **MetaMapLite** files and built a WAR file which I then ran in a Docker tomcat container.

# Requirements
You will need "ant" installed (e.g. C:/Program Files/Ant/apache-ant-1-10.14).
You will need to set "ANT_HOME" to that folder and add $ANT_HOME/bin to your PATH..
You will also need to install an instance of the Java Development Kit (jdk) (e.g. C:/Program Files/Java/jdk-18.0.2.1).
You will need to set "JAVA_HOME" to that folder and add $JAVA_HOME/bin to your PATH..

I was running "cygwin" and had Oracle Java already installed, which meant I had to prepend the jdk to my PATH

    $ export ANT_HOME="/c/Program Files/Ant/apache-ant-1.10.14"
    $ PATH=$PATH:$ANT_HOME/bin
    $ export JAVA_HOME="/c/Program Files/Java/jdk-18.0.2.1"
    $ PATH=$JAVA_HOME/bin:$PATH

# Folder Structure
This folder structure mirrors the folder structure for the **MetaMapLite Servlet** example and is documented in the **README** files.
Here the top folder is **tomcat** (was 'metamaplite-sample-webapp) and the next folder down is **webapp** (was 'sample-webapp').
After that the folder structures almost identical; the **inverted file indices** and **tables** files are under the **data/ivf** folder,
just moved down two folder levels, being the release (e.g. 2022AB) and the base (e.g. USAbase).
This reflects the structure of these files when you download them from the [MetaMapLite](https://lhncbc.nlm.nih.gov/ii/tools/MetaMap/run-locally/MetaMapLite.html) website. However the source code in the **src** folder and some of the configuration is different.

# Missing Files
This repository does not contain the large, binary and data files which you will need to download from the **MetaMapLite** website.
* **Inverted Index and Tables files** - e.g. **2022AB UMLS Level 0+4+9 Dataset**. There's a place holder for these files in the folder structure (**tomcat/webapp/data/ivf**),
but you should use the latest version. When you do the name of the folder under **tomcat/webapp/data/ivf** may change. If it does you'll need
to edit the **metamaplite.index.directory** line in the **config/metamaplite.properties** file.
* **Model Files** - these need to be installed in the **tomcat/webapp/data/models** folder. The model file were ...
  * **en-chunker.bin**
  * **en-pos-maxent.bin**
  * **en-pos-perceptron.bin**
  * **en-sent.bin**
  * **en-token.bin**

* **Library Files** - these need to be installed in the **tomcat/webapp/lib** folder
  * **metamaplite-3.4-SNAPSHOT-standalone.jar** - this file must be placed in the **tomcat/webapp/lib** folder. You can find this file by downloading
the **Example MetaMapLite in a Servlet instance** file, unpacking it and looking in the **sample-webapp/lib** folder.
  * The other library files were **log4j-api-2.1.jar**, **log4j-core-2.1.jar** and **servlet-api.jar** which were also found in the **Example MetaMapLite in a Servlet instance** in the **sample-webapp/lib** folder.

# Building the WAR file
Ant does all the hard work here. In the **tomcat/webapp** folder, type the following commands.

    $ ant clean
    $ ant build-war
  
If everything is configured correctly, that will build the file **target/AutoCoding.war** which can be run under Tomcat.

**NOTE:** '$ ant build-war' can take 2-3 min, even on a fast laptop.

# Running Tomcat
There are many ways of running a Tomcat server. I choose to run Tomcat in a Docker container. There is a **docker-compose.yaml** file
in the **tomcat** folder for doing this [You may want to change the timezone (TZ) setting].
The following command should fetch the Tomcat image and run it.

    $ docker-compose up -d

Unfortunately that doesn't get you very far as, by default, no apps are running in the default configuration.
You have to do a little bit of "magic" do get even a basic Tomcat server running. The folder on the Tomcat server
that defines the running apps is called **webapps**. By default it is empty. However, the standard apps and their configuration
is there - it's just in a folder called **webapps.dist**. You need to copy everything from **webapps.dist** to **webapps**.
To do this you have to run commands on the docker image itself. I use Cygwin, so I have to prepend "winpty" to my
docker commands to trick docker into thinking Cygwin's 'mintty' is a TTY. The following commands worked for me.

    $ winpty docker exec -it tomcat bash
    root@6ea7fbe15909:/usr/local/tomcat# cd webapps.dist
    root@6ea7fbe15909:/usr/local/tomcat/webbaps.dist# cp -R * ../webapps/.
    root@6ea7fbe15909:/usr/local/tomcat/webbaps.dist# exit

Now you should see a basic Tomcat screen at http://localhost:8080

Unfortunately you don't have control; you can't login as a manager and you can't use "localhost" to access the Manager App.
In fact no one can login in because there's no valid username/passwords defined in the file **conf/tomcat-users.xml**.
The file **new_tomcat-users.xml** in the **tomcat** folder is an example of how to define users and passwords for Tomcat.
You must edit this file and set you own users/password; otherwise russell.mcdonell will be able to login to your Tomcat server
with administration rights. To establish your new users/passwords you can use the following commands.

    $ docker cp new_tomcat-users.xml tomcat:/usr/local/tomcat/conf/tomcat-users.xml
    $ docker exec tomcat chmod 600 ./conf/tomcat-users.xml

To access the Manager App from "localhost" you will need to update the **webapps/manager/META-INF/context.xml** file.
The **new_context.xml** file in the **tomcat** folder has the updated configuration that should give you this access.
It can be uploaded to the Tomcat server using the following commands.

    $ docker cp new_context.xml tomcat:/usr/local/tomcat/webapps/manager/META-INF/context.xml
    $ docker exec tomcat chmod 600 ./webapps/manager/META-INF/context.xml

# Deploying the AutoCoding.war file
Unfortunately you **AutoCoding.war** file will be bigger that then default maximum, so you will need to "fix" another
configuration file - **webapps/manager/META-INF/web.xml**. The file **new_web.xml** in the **tomcat** folder
has a much larger maximum file size for uploads. You can update the **webapps/manager/META-INF/web.xml** file with the following commands.

    $ docker cp new_context.xml tomcat:/usr/local/tomcat/webapps/manager/META-INF/web.xml
    $ docker exec tomcat chmod 644 ./webapps/manager/META-INF/web.xml


You should now be able to login to the Manager App using the "Manager App" button and upload your **AutoCoding.war** file.
In the Manager section you will see a list of the applications that are loaded/running, followed by a **Deploy** section.
There are two part to the **Deploy** section, the second of which has the heading **WAR file to deploy**.
In this section you can choose the **AutoCoding.war** file that you have built and deploy it to the Tomcat server.
It should deploy successfully and start running as part of the deployment.

**NOTE:** Deploying **AutoCoding.war** can take up to 30seconds, even on a fast laptop.

