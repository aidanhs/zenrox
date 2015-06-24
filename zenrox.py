#!/usr/bin/env python

from suds.client import Client
from bunch import Bunch
import xml.etree.ElementTree as ET
import datetime as DT

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)

def getclient(org, svc):
    url = 'https://{}.tenrox.net/TWebService/{}.svc?singleWsdl'.format(org, svc)
    client = Client(url)
    # Tenrox forces a redirect to https, but the wsdl says http connection.
    # Unfortunately this redirection doesn't work with suds. This is a magic
    # option which apparently overrides the location in the wsdl.
    client.options.location = url
    return client

services = [
    'LogonAs',

    #'Assignments',
    #'BusinessUnits',
    #'ChargeEntries',
    #'Clients',
    #'ClientInvoices',
    #'ClientInvoiceOptions',
    #'Contact',
    #'Currencies',
    #'CustomFields',
    #'ExecuteStoredProcedure',
    #'ExpenseEntries',
    #'ExpenseItems',
    #'ExpenseReports',
    #'Groups',
    #'MapData',
    #'Milestones',
    #'Notes',
    #'Projects',
    #'Sites',
    #'Skills',
    #'Tasks',
    #'TaxGroupDetails',
    #'TaxGroups',
    #'TimeEntries',
    'Timesheets',
    #'Users',
    #'Worktypes',
]

clients = Bunch()

def init(org):
    for service in services:
        clients[service] = getclient(org, service)

def getts(auth, userid, weekstart):
    assert weekstart - DT.timedelta(days=weekstart.weekday()) == weekstart
    respstr = clients.Timesheets.service.QueryTimesheetsDetails(auth, userid, weekstart)
    resp = ET.fromstring(unicode(respstr).encode('utf-8'))
    assert resp.find('.//Success').text == 'true'
    valstr = resp.find('.//Value').text
    val = ET.fromstring(valstr.encode('utf-8'))
    return val

def main():
    org, username, password = open('.tenacct').read().strip().split(':')
    init(org)
    auth = clients.LogonAs.service.AuthUser(org, username, password, '', True)
    userid = int(ET.fromstring(auth).find('.//UniqueId').text)

    # Get a monday
    startdate = DT.date(year=2015, month=05, day=19)
    weekstart = startdate - DT.timedelta(days=startdate.weekday())

    ts = getts(auth, userid, weekstart)

if __name__ == '__main__':
    main()
