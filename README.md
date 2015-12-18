= Zenrox

== Getting started

```
$ git clone https://github.com/aidanhs/zenrox.git
Cloning into 'zenrox'...
[...]
$ cd zenrox
$ virtualenv . # create isolated environment for deps
[...]
$ . bin/activate # enter isolated environment
(zenrox) $ pip install -U pip setuptools # get updated python tools
[...]
(zenrox) $ pip install -r requirements.txt
[...]
(zenrox) $ echo 'MyOrgName' > .tenorg
(zenrox) $ echo 'aidanhs:TenroxPassword1' > .tenacct && chmod 600 .tenacct
(zenrox) $ python zenrox.py printweek 2014-04-10
Initialising services
Logging into MyOrgName Tenrox as aidanhs
Initialisation complete
Getting timesheet for week starting 2014-04-07
Getting assignments for week starting 2014-04-07
===================
Possible assignments:
Project 1  -  Task 1
Project 1  -  Task 2
[...]
===================
Timesheets:
2014-04-07 Mon:
    Task 1 : Project 1 - 5.0 hrs
    Task 2 : Project 1 - 1.5 hrs
[...]
===================
```

There's also a proof of concept curses text interface with cryptic keybindings.
Use

 - q to quit
 - c to create an entry
 - r to refresh
 - left arrow to go back in time
 - right arrow to go forward in time

It's fairly unfriendly.

You can use zenrox as a library:

```
(zenrox) $ python
Python 2.6.6 (r266:84292, May 22 2015, 08:34:51)
[...]
>>> import zenrox, datetime
>>> userid, auth, mobauth = initapi()
Initialising services
Logging into MyOrgName Tenrox as aidanhs
Initialisation complete
>>> weekstart = zenrox.weekstart(datetime.date.today())
>>> assignments_dict = zenrox.get_assignments(auth, userid, weekstart)
Getting assignments for week starting 2015-12-14
>>> assignments_list = assignments_dict.values()
>>> print assignments_list[5].task_name + ' ' + assignments_list[5].project_name
Task 1 Project 5
```

The beginnings of a JS UI:

```
$ make prep # one off initialisation, `make server` will run this if necessary
$ make server # start the zenrox server
```

== Ignored E-mail To Upland Software About Official API

Subject: "Tenrox api documentation"

--------

Is there no more up-to-date documentation than that on the website [1]?

There are many issues when comparing it with the current API and there are virtually no examples of use. In addition, both of the 'undocumented' tenrox APIs I'm aware of are more streamlined and friendly than the documented one.

As a concrete example: business units. These are listed as a required field for timesheet entries, but I cannot see any reasonable way of getting a business unit associated with an assignment.
There is a way of querying business unit by project, which I tried, but returned nothing. I continued following the documentation on business unit precedence [2] but step 2 returned nothing and I'm not clear on how to achieve step 3 with the api.

Intercepting the undocumented mobile api (json) identifies a 'timeentrylite' call which does not send the business unit (or any other of the many duplicated details between assignment attributes and entries). Intercepting the undocumented web interface ajax calls reveals a 'SaveEntry' call which also doesn't make any reference to business unit.

So:
1. Is there any documentation on the mobile API?
2. Are there any examples of the WCF API actually in use?

I signed up (with surname aidanhs) to the community forum [3] in the hope that I'd be able to ask some question there.
Unfortunately, contrary to the welcome e-mail "[...] you will not only have interactive access to discussion rooms [...]" I'm given a permission denied error.

I would have raised this via the support portal but the landing page (the community homepage [4]) doesn't appear to have it - possibly related to the broken CSS on that page?

Aidan

[1] https://helpcontent.tenrox.net/Accessing_the_Tenrox_API.htm
[2] https://helpcontentr11.tenroxhosting.com/Business_Unit_Setup__Precedence_Rule.htm
[3] https://upland-software.force.com/Tenrox/apex/Communities_Forum
[4] https://upland-software.force.com/Tenrox/home/home.jsp

--------



https://bitbucket.org/jurko/suds/issue/89/suds-does-not-double-encode-when-necessary
