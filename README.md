Renters' Rights
===============

[![Build Status](https://travis-ci.com/codeforkentuckiana/swap.svg?token=SpHpFMasorhC4oT8tCio&branch=master)](https://travis-ci.com/codeforkentuckiana/swap) [![codecov](https://codecov.io/gh/codeforkentuckiana/swap/branch/master/graph/badge.svg?token=0nA3LW7RQO)](https://codecov.io/gh/codeforkentuckiana/swap)

About
-----------------
TBD

Getting up and running
-----------------
`renters-rights` is written in Python using the Django web framework. Postgres is used as a database.

In order to facilite cross-platform development, Docker is used to build and run the application and database. This means that you don't have to worry about installing Python, app dependencies, or a database on your local machine. All you need to have is Docker.

### What is Docker?
> Docker is a tool designed to make it easier to create, deploy, and run applications by using containers. Containers allow a developer to package up an application with all of the parts it needs, such as libraries and other dependencies, and ship it all out as one package. By doing so, thanks to the container, the developer can rest assured that the application will run on any other Linux machine regardless of any customized settings that machine might have that could differ from the machine used for writing and testing the code.
 
Source: [https://opensource.com/resources/what-docker](https://opensource.com/resources/what-docker)

### Installing Docker
Download the [Mac](https://store.docker.com/editions/community/docker-ce-desktop-mac) or [Windows](https://store.docker.com/editions/community/docker-ce-desktop-windows) installer and follow the installation insturctions.

Note that for Windows, Docker requires 64bit Windows 10 Pro, Enterprise, or Education, and Docker also requires that virtualization be enabled. Check out the [what to know before you install](https://docs.docker.com/docker-for-windows/install/#what-to-know-before-you-install) document for more info. It is competely possible to run Swap without Docker, and we can work on documentation and scripts to make that process easier if we have contributors who can't run Docker. Docker is just handy because it makes it so developers don't have to install or manage installations, and because it mimicks the production environment.

### Running the App
Open a terminal (Terminal on Mac, Git Command Prompt on Windows), navigate to the Swap directory, and run this command: `make begin`.

This command will start the application in debug mode along with a Postgres database instance. Each of these runs in its own container, which you'll see start. `make begin` will also set up the database by running [migrations](https://docs.djangoproject.com/en/2.1/topics/migrations/) and installing [fixtures](https://docs.djangoproject.com/en/2.1/howto/initial-data/#providing-data-with-fixtures).

You can view the site by going to [http://localhost/](http://localhost/) in your browser.

You can log into the admin site by going to [http://localhost/admin/](http://localhost/admin/) and logging in with the username `admin` and the password `pass` (this user is created via the fixtures in the `noauth` app).

### Stoping the App
To stop the app, run `make stop`.

### Viewing Logs
To view logs, run `make tail`.
If you want to start the app and automatically show logs, you can combine the `begin` and `tail` commands: `make begin tail`.

Contributing
-----------------
If you would like to contribute to this codebase, you need to have a couple of additional Python libraries installed on your machine: [`isort`](https://pypi.org/project/isort/) and [`black`](https://github.com/ambv/black). These libraries are used to do some code formatting during `git commit`.

You can install both of these libraries by running `pipenv install --dev` from your shell in the `swap` directory. If you don't have `pipenv` installed, you can install it by following the [installation instructions](https://pipenv.readthedocs.io/en/latest/#install-pipenv-today).

Advanced Topics
-----------------
### Debugging via `pdb`
`pdb` is the Python debugger, and it provides a useful way to interact with a running program.

If you need to debug Swap Python code, add the following `import pdb; pdb.set_trace()` at the point where you would like your breakpoint. The app will stop execution when it reaches this line.

To interact with `pdb`, open a new terminal and run `docker-attach swap_app_1` (where `swap_app_1` is the name of the container you see when running `docker ps`).
