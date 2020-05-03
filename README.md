Renters' Rights
===============

[![Build Status](https://travis-ci.com/codeforkyana/renters-rights.svg?branch=master)](https://travis-ci.com/codeforkyana/renters-rights) [![codecov](https://codecov.io/gh/codeforkyana/renters-rights/branch/master/graph/badge.svg)](https://codecov.io/gh/codeforkyana/renters-rights)

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

About
-----------------
This application is built to help renters take advantage of their rights.
It was created by [Code for Kentuckiana](https://codeforkentuckiana.org) in conjunction with partners from the [Metropolitan Housing Coalition](http://www.metropolitanhousing.org) and the [Kentucky Equal Justice Center](https://www.kyequaljustice.org).

The application will evolve to include additional features, but the initial version will support:

* Uploading and storing documents, such as leases
* Uploading and storing timestamp-verified images of rental unit conditions
* Generation of a verified photo report (to provide third-party documentation of condition to landlords)
* Generation of form letters (e.g. lease termination, request for repair, etc.)
* Generation of Kentucky Small Claims Court complaints

Some additional features that have been discussed:

* Links to other renter resources, such as agencies and online tools
* Email reminders about important events (e.g. rent due dates, lease termination dates, etc.)    

Getting up and running
-----------------
`renters-rights` is written in Python using the Django web framework. Postgres is used as a database.

In order to facilite cross-platform development, Docker is used to build and run the application and database. This means that you don't have to worry about installing Python, app dependencies, or a database on your local machine. All you need to have is Docker.

### What is Docker?
> Docker is a tool designed to make it easier to create, deploy, and run applications by using containers. Containers allow a developer to package up an application with all of the parts it needs, such as libraries and other dependencies, and ship it all out as one package. By doing so, thanks to the container, the developer can rest assured that the application will run on any other Linux machine regardless of any customized settings that machine might have that could differ from the machine used for writing and testing the code.
 
Source: [https://opensource.com/resources/what-docker](https://opensource.com/resources/what-docker)

### Installing Dependencies

#### Docker
*Mac*

Download the [Mac](https://store.docker.com/editions/community/docker-ce-desktop-mac) installer, and follow instructions.

*Windows*

Download the [Windows](https://store.docker.com/editions/community/docker-ce-desktop-windows) installer and follow the installation insturctions.  Be sure to install docker-compose as well.

Note that for Windows, Docker requires 64bit Windows 10 Pro, Enterprise, or Education, and Docker also requires that virtualization be enabled. Check out the [what to know before you install](https://docs.docker.com/docker-for-windows/install/#what-to-know-before-you-install) document for more info. It is completely possible to run Renters' Rights without Docker, and we can work on documentation and scripts to make that process easier if we have contributors who can't run Docker. Docker is just handy because it makes it so developers don't have to install or manage installations, and because it mimicks the production environment.

*Linux*

Follow instructions to install docker engine for your distro at the [Docker Installation](https://docs.docker.com/engine/install/) page.  Be sure to install docker-compose in addition to docker engine.  You'll also want to follow [Linux Post-Installation Instructions](https://docs.docker.com/engine/install/linux-postinstall/) as well.

#### Make
*Windows*

Get [Make for Windows](http://gnuwin32.sourceforge.net/packages/make.htm).  An easy way is to get it from [Chocolatey](https://chocolatey.org/).  Once Chocolatey is installed:  `choco install make`

*Linux*

`sudo apt-get install make`

### Cloning the Repo
*Windows*

Ensure that git will not modify line endings before cloning:  `git config --global core.autocrlf false`  Then clone as usual.  After cloning, take these steps to ensure that git will respect line-endings during future changes:  

> // Run commands below in project directory, so that git will not attempt to mess with line endings within this project
> git config core.eol lf 
> git config core.autocrlf false

*Mac/Linux*

Clone as usual.

### Running the App
*Windows*

Ensure that Docker is running with Linux containers, not Windows containers.  Then follow instructions for *All* below.

*All*

Open a terminal, navigate to the Renters' Rights directory, and run this command: `make begin`.

This command will start the application in debug mode along with a Postgres database instance. Each of these runs in its own container, which you'll see start. `make begin` will also set up the database by running [migrations](https://docs.djangoproject.com/en/2.1/topics/migrations/) and installing [fixtures](https://docs.djangoproject.com/en/2.1/howto/initial-data/#providing-data-with-fixtures).

You can view the site by going to [http://localhost/](http://localhost/) in your browser.

You can log into the admin site by going to [http://localhost/admin/](http://localhost/admin/) and logging in with the username `admin` and the password `pass` (this user is created via the fixtures in the `noauth` app).

### Stoping the App
To stop the app, run `make stop`.

### Viewing Logs
To view logs, run `make tail`.
If you want to start the app and automatically show logs, you can combine the `begin` and `tail` commands: `make begin tail`.

Advanced Topics
-----------------
### Running a subset of tests
You can use test labels as described in the [Django testing documentation](https://docs.djangoproject.com/en/2.2/topics/testing/overview/#running-tests) to run a subset of tests.

For example, to run a single test:
`make test labels=noauth.tests.test_views.CodeViewTests.test_validate_and_get_redirect_uri_returns_next_page_from_auth_code`

Or to run all tests in a class:
`make test labels=noauth.tests.test_views.CodeViewTests`

### Debugging via `pdb`
`pdb` is the Python debugger, and it provides a useful way to interact with a running program.

If you need to debug Renters' Rights Python code, add the following `breakpoint()` at the point where you would like your breakpoint. The app will stop execution when it reaches this line.

To interact with `pdb`, open a new terminal and run `make attach`.

Deploying to your Heroku account
-----------------
If you want to run your own instance of this application, you can easily deploy it to your Heroku account.

Start by clicking this button:

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

You'll need to fill in the required configuration variables, particularly the ones for your SMTP (email) provider and for S3.

You will also need to create an administrator account to use to log in:

- Navigate to your app in the Heroku console (e.g. `https://dashboard.heroku.com/apps/<APP NAME>`)
- Select `Run Console` from the `More` menu
- Enter `bash` and click `Run`
- Wait for the console to connect
- Run `./manage.py createsuperuser`
- Enter the required information
- Log in at [https://APP_NAME.herokuapp.com/admin/](https://APP_NAME.herokuapp.com/admin/) 

TODO: Instructions for configuring S3. Recommendations for SMTP host. 
