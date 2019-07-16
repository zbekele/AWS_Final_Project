################## AWS Linux Server Configuration Project #############################

About the project:
This tutorial will guide you through the steps to take a baseline installation of a Linux server and prepare it to host your Web applications. You will then secure your server from a number of attack vectors, install and configure a database server, and deploy one of your existing Flask-based Web applications onto it.

############## Grader Login infrormation ##############

#01: Working with Amazon Lightsail AWS Instances

AWS (Amazon Web Services) Lightsail is a cloud computing service that you can use to host web applications and website. AWS service is one of the requirements for this project.  
You will need an AWS Lightsail account and a domain name (optional) to setup the AWS service.

- Step 1: Create a Lightsail Instance - After you sign into the AWS service, click on `Create Instance` - Choose `Linux/Unix` platform, then select Ubuntu 16.04 as the operating system - Towards at the end of the screen, choose a plan best work for your instance - Keep the default name or rename your new instance - Click the `Create` button and your instance will be created

* for more information please visit: https://geekflare.com/lightsail-hosting-joomla/

#02: Establish ssh connection to AWS server and upgrade installed packages

- Download the Default Private Key form Amazon Lightsail Account
- Move this private key file into the local folder `~/.ssh`
- In your terminal change the Private Key file privilege type: `chmod 600 ~/.ssh/Private Key`.
- Connect to the instance via the terminal: `ssh -i ~/.ssh/Private Key ubuntu@http://3.214.89.141`

- upgrade installed packages
  sudo apt-get update
  sudo apt-get upgrade
  sudo apt-get update && sudo apt-get dist-upgrade \*security updates issue resolved

#03: Changing default SSH port to 2200

- Edit the `/etc/ssh/sshd_config` file: `sudo vi /etc/ssh/sshd_config`.
- Change the port `22` to `2200`.
- to save press Esc
  Press : (colon)
  Enter the following: q!

#04: Configure the Firewall to only allow incoming connections to ssh port 2200, HTTP port 80, and NTP port 123:

sudo ufw status -The UFW should be inactive.
sudo ufw default deny incoming -Deny any incoming traffic.
sudo ufw default allow outgoing -Enable outgoing traffic.
sudo ufw allow 2200/tcp -Allow incoming tcp packets on port 2200.
sudo ufw allow www -Allow HTTP traffic in.
sudo ufw allow 123/udp -Allow incoming udp packets on port 123.
sudo ufw deny 22 -Deny tcp and udp packets on port 53.
sudo ufw enable -Turn UFW on

sudo ufw status -Check the status of UFW

The output:

    2200/tcp ALLOW Anywhere
    80/tcp ALLOW Anywhere
    123/udp ALLOW Anywhere
    22 DENY Anywhere
    2200/tcp (v6) ALLOW Anywhere (v6)
    80/tcp (v6) ALLOW Anywhere (v6)
    123/udp (v6) ALLOW Anywhere (v6)
    22 (v6) DENY Anywhere (v6)

- The firewall and port settings are listed in the Networking tab of your instance's
  management page in the Amazon Lightsail console.

  Add Custom porst 80(TCP), 123(UDP), and 2200(TCP)

* References

- https://lightsail.aws.amazon.com/ls/webapp/us-east-1/instances/Ubuntu-512MB-Virginia-1/networking
- https://github.com/SDey96/Udacity-Linux-Server-Configuration-Project

#05: Automatic updates
sudo apt-get install unattended-upgrades #Enable automatic security updates

- Uncomment the line `${distro_id}:${distro_codename}-updates` from `/etc/apt/apt.conf.d/50unattended-upgrades` and save
- Please make changes below in order to upgrades are downloaded and installed every day:
  Form `/etc/apt/apt.conf.d/20auto-upgrades`
  APT::Periodic::Update-Package-Lists "1";
  APT::Periodic::Download-Upgradeable-Packages "1";
  APT::Periodic::AutocleanInterval "7";
  APT::Periodic::Unattended-Upgrade "1";
  sudo dpkg-reconfigure --priority=low unattended-upgrades #Enable the change

  sudo apt-get update
  sudo apt-get dist-upgrade
  sudo shutdown -r now
  sudo service apache2 restart #Restart Apache

* References

- Ubuntu Documentation, [Automatic Updates](https://help.ubuntu.com/lts/serverguide/automatic-updates.html).

<a name="step_5_3"></a>

## Give `grader` access

### Step 6: Create access to grader and give sudo permission:

    sudo adduser grader   #Add user and enter a password twice
    sudo visudo                 #Edits the sudoers file and add `grader`
    grader  ALL=(ALL:ALL) ALL   #add sudo privileges to `grader` user

#Resources
https://github.com/SDey96/Udacity-Linux-Server-Configuration-Project

### Step 8: Create an SSH key pair for `grader` using the `ssh-keygen` tool

1.  Create an SSH key pair for grader using the ssh-keygen tool on your local machine. Save it in ~/.ssh path
2.  Deploy public key on development environment
    - On your local machine, read the generated public key cat ~/.ssh/FILE-NAME.pub
    - On your virtual machine
      mkdir .ssh
      touch .ssh/authorized_keys
      nano .ssh/authorized_keys
      Copy the public key to this authorized_keys file on the virtual machine and save
3.  Run chmod 700 .ssh and chmod 644 .ssh/authorized_keys on your virtual machine to change file permission
4.  Restart SSH: sudo service ssh restart
5.  Now you are able to login in as grader:
    ssh -i ~/.ssh/key_for_grader -p 2200 grader@3.214.89.141
6.  You will be asked for grader's password. To disable it, open configuration file again:
    sudo nano /etc/ssh/sshd_config
7.  Change PasswordAuthentication yes to no
8.  Restart SSH: sudo service ssh restart

- References

https://github.com/yiyupan/Linux-Server-Configuration-Udacity-Full-Stack-Nanodegree-Project

#09: Configure the timezone to UTC and Install and configure Apache to serve a Python mod_wsgi application from 'grader'

sudo dpkg-reconfigure tzdata #configure the time zone
sudo apt-get install apache2 #install Apache
sudo apt-get install libapache2-mod-wsgi-py3 #Install the Python 3 mod_wsgi package
sudo a2enmod wsgi #enable mod_wsgi

#10: Install and configure PostgreSQL from 'grader'

sudo apt-get install postgresql #install PostgreSQL
sudo su - postgres #Switch to the `postgres` user mode
psql #PostgreSQL terminal

- Create the `catalog` user with a password and give them the ability to create databases:

  postgres=# CREATE ROLE catalog WITH LOGIN PASSWORD 'catalog';
  ALTER ROLE catalog CREATEDB;

                                     List of roles

  Role name | Attributes | Member of
  -----------+------------------------------------------------------------+-----------
  catalog | Create DB | {}
  postgres | Superuser, Create role, Create DB, Replication, Bypass RLS | {}

* Exit psql: `\q`.
* Switch back to the `grader` user: `exit`.
* Create a new Linux user called `catalog`: `sudo adduser catalog`. Enter password and fill out information.
* Give to `catalog` user the permission to sudo. Run: `sudo visudo`.
* Search for the lines that looks like this:

  ```
  root    ALL=(ALL:ALL) ALL
  grader  ALL=(ALL:ALL) ALL
  ```

* Below this line, add a new line to give sudo privileges to `catalog` user.

  ```
  root    ALL=(ALL:ALL) ALL
  grader  ALL=(ALL:ALL) ALL
  catalog  ALL=(ALL:ALL) ALL
  ```

* Save and exit using CTRL+X and confirm with Y.
* Verify that `catalog` has sudo permissions. Run `su - catalog`, enter the password, run `sudo -l` and enter the password again. The output should be like this:

  ```
  Matching Defaults entries for catalog on ip-172-26-13-170.us-east-2.compute.internal:
      env_reset, mail_badpass,
      secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin

  User catalog may run the following commands on ip-172-26-13-170.us-east-2.compute.internal:
      (ALL : ALL) ALL
  ```

* While logged in as `catalog`, create a database: `createdb catalog`.
* Run `psql` and then run `\l` to see that the new database has been created. The output should be like this:
  ```
                                    List of databases
     Name    |  Owner   | Encoding |   Collate   |    Ctype    |   Access privileges
  -----------+----------+----------+-------------+-------------+-----------------------
   catalog   | catalog  | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
   postgres  | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 |
   template0 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
             |          |          |             |             | postgres=CTc/postgres
   template1 | postgres | UTF8     | en_US.UTF-8 | en_US.UTF-8 | =c/postgres          +
             |          |          |             |             | postgres=CTc/postgres
  (4 rows)
  ```
* Exit psql: `\q`.
* Switch back to the `grader` user: `exit`.

#Reference

https://github.com/yiyupan/Linux-Server-Configuration-Udacity-Full-Stack-Nanodegree-Project

#11: Install git and copy catalog application from github to AWS (from grader)

1.  Run \$ sudo apt-get install git
2.  Create dictionary: \$ mkdir /var/www/catalog
3.  CD to this directory: \$ cd /var/www/catalog
4.  Clone the catalog app: \$ sudo git clone RELEVENT-URL catalog
5.  Change the ownership: \$ sudo chown -R ubuntu:ubuntu catalog/
6.  CD to /var/www/catalog/catalog
7.  Change file application.py to init.py: \$ mv application.py **init**.py
8.  Change line app.run(host='0.0.0.0', port=8000) to app.run() in init.py file
9.  database_setup.py replace:
    
    #engine = create_engine("sqlite:///catalog.db")
    engine = create_engine('postgresql+psycopg2://postgres:PASSWORD@localhost/catalog')
10. Run: `python data.py` This will populate the database and table

#Reference

https://github.com/yiyupan/Linux-Server-Configuration-Udacity-Full-Stack-Nanodegree-Project

#12: Install Flask App and packages

python -m pip install --upgrade pip
sudo pip install httplib2
sudo pip install requests
sudo pip install --upgrade oauth2client
sudo pip install sqlalchemy
sudo pip install flask
sudo apt-get install libpq-dev
sudo pip install psycopg2

#13: Set up and enable a virtual host

- Add the following line in `/etc/apache2/mods-enabled/wsgi.conf` file
  to use Python 3.

  ```
  #WSGIPythonPath directory|directory-1:directory-2:...
  WSGIPythonPath /var/www/catalog/catalog/venv3/lib/python3.5/site-packages
  ```

- Create `/etc/apache2/sites-available/catalog.conf` and add the
  following lines to configure the virtual host:

  ```
  <VirtualHost *:80>
  ServerName 3.214.89.141
  ServerAlias 3.214.89.141.xip.io
  ServerAdmin zele.bekele@gmail.com
    WSGIScriptAlias / /var/www/FlaskApp/catalog.wsgi
    <Directory /var/www/FlaskApp/catalog/>
    	Order allow,deny
  	  Allow from all
    </Directory>
    Alias /static /var/www/FlaskApp/catalog/static
    <Directory /var/www/FlaskApp/catalog/static/>
  	  Order allow,deny
  	  Allow from all
    </Directory>
    ErrorLog ${APACHE_LOG_DIR}/error.log
    LogLevel warn
    CustomLog ${APACHE_LOG_DIR}/access.log combined
  </VirtualHost
  ```

- Enable virtual host: `sudo a2ensite catalog`. The following prompt will be returned:

  ```
  Enabling site catalog.
  To activate the new configuration, you need to run:
    service apache2 reload
  ```

- Reload Apache: `sudo service apache2 reload`.

#Resources

- [Getting Flask to use Python3 (Apache/mod_wsgi)](https://stackoverflow.com/questions/30642894/getting-flask-to-use-python3-apache-mod-wsgi)
- [Run mod_wsgi with virtualenv or Python with version different that system default](https://stackoverflow.com/questions/27450998/run-mod-wsgi-with-virtualenv-or-python-with-version-different-that-system-defaul)

### Step 14.3: Set up the Flask application

- Create `catalog.wsgi` under `/var/www/catalog/ directory and add the list of line below
  #!/usr/bin/python
  import sys
  import logging
  logging.basicConfig(stream=sys.stderr)
  sys.path.insert(0, "/var/www/catalog/catalog/")
  sys.path.insert(1, "/var/www/catalog/")

  from catalog import app as application
  application.secret_key = "..."

#Resource

- Flask documentation, [Working with Virtual Environments](http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/#working-with-virtual-environments)

# Step 14.6: Launch the Web Application

- Disable the default Apache site: `sudo a2dissite 000-default.conf`.
- Change the ownership of the project directories: `sudo chown -R www-data:www-data catalog/`.
- Restart Apache again: `sudo service apache2 restart`.
- Open your browser to http://3.214.89.141.xip.io
