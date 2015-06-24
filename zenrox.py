from suds.client import Client
from bunch import Bunch
import xml.etree.ElementTree as ET

import logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)

def getclient(org, svc):
    if svc != 'LogonAs':
        svc = 'sdk/' + svc
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
    #'Timesheets',
    #'Users',
    #'Worktypes',
]

clients = Bunch()

def init(org):
    for service in services:
        clients[service] = getclient(org, service)

def main():
    org, username, password = open('.tenacct').read().strip().split(':')
    init(org)
    authxmlstr = clients.LogonAs.service.AuthUser(org, username, password, '', True)
    authxml = ET.fromstring(authxmlstr)

if __name__ == '__main__':
    main()
