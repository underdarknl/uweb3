# New and improved: µWeb3

Since µWeb inception we have used it for many projects, and while it did its job, there were plenty of rough edges. This new version intends to remove those and pull it into the current age.

# Notable changes

* wsgi complaint interface
* python3 native
* Better handling of strings and automatic escaping
* More options for template engines
* More options for SQL / database engines


## Example projects

The following example applications for newWeb exist:

* [newWeb-info](https://github.com/edelooff/newWeb-info): This demonstrates most µWeb3 features, and gives you examples on how to use most of them.
* [newWeb-logviewer](https://github.com/edelooff/newWeb-logviewer): This allows you to view and search in the logs generated by all µWeb and µWeb3 applications.

# µWeb3 installation

The easiest and quickest way to install µWeb3 is using Python's `virtualenv`. Install using the setuptools installation script, which will automatically gather dependencies.

```bash
# Set up the Python3 virtualenv
python3 -m venv env
source env/bin/activate

# Install uWeb3
python3 setup.py install

# Or you can install in development mode which allows easy modification of the source:
python3 setup.py develop

cd uweb3/scaffold

python3 serve.py
```

## Ubuntu issues
On some ubuntu setups venv is broken and therefore does not install the activation scripts.

```bash
# Set up the Python3 virtualenv on Ubuntu
python3 -m venv--without-pip env
source env/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python
deactivate
source env/bin/activate

# then proceed to install µWeb3 like before.
```

# µWeb3 database setup

Setting up a database connection with µWeb3 is easy, navigate to the settings.ini file in the scaffold folder and add the following fields to the file:
``` 
[mysql] OR [sqlite]
host = 'host'
user = 'username'
password = 'pass'
database = 'dbname'
```
To access your database connection simply use the connection attribute in any class that inherits from PageMaker.

# Config settings
If you are working on µWeb3 core make sure to enable the following setting in the config:
``` 
[development]
dev = True
```
This makes sure that µWeb3 restarts every time you modify something in the core of the framework aswell.

µWeb3 also has an inbuild protection for XSRF. To make use of it enable the following setting in the config: 
```
[security]
xsrf_enabled = True
```
Now on every request it checks if there is a XSRF cookie in place. If there is no cookie it will create one.
Every post request it will validate the first input field with the tag 'xsrf'. 
If the cookie and the post request match the 'incorrect_xsrf_token' flag will stay on the default(False). 
If however they do not match this flag will be set to True. 
To secure your routes make sure to decorate them with the 'checkxsrf' decorator.

To automaticly generate a hidden input with a xsrf token make use of the {{ xsrf [variable_with_xsrf_token]}} function.

# Routing
The default way to create new routes in µWeb3 is to create a folder called routes. 
In the routes folder create your pagemaker class of choice, the name doesn't matter as long as it inherits from PageMaker.
After creating your pagemaker be sure to add the route endpoint to routes list in base/__init__.py. 

# Added by me so you know who to blame when shit breaks:
- In uweb3 __init__ a class called HotReload
- In pagemaker __init__:
  - A classmethod called loadModules that loads all pagemaker modules inheriting from PageMaker class
  - A XSRF class
    - Generates a xsrf token and creates a cookie if not in place
    - Validates the xsrf token in a post request if the enable_xsrf flag is set in the config.ini
- In requests:
  - Self.method attribute
  - Method called Redirect #Moved from the response class to the request class so cookies that are set before a redirect are actually set.
- In pagemaker/new_login Users class:
  - Create user
  - Find user by name
  - Create a cookie with userID + secret
  - Validate if user messed with given cookie and render it useless if so
- In pagemaker/new_decorators:
  - Loggedin decorator that validates if user is loggedin based on cookie with userid
  - Checkxsrf decorator that checks if the incorrect_xsrf_token flag is set
- In templatepaser:
  - A function called _TemplateConstructXsrf that generates a hidden input field with the supplied value: {{ xsrf [xsrf_variable]}}
- In libs/sqltalk
  - Tried to make sqltalk python3 compatible by removing references to: long, unicode and basestring
  - So far so good but it might crash on functions that I didn't use yet