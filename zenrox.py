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

class Entry(object):
    def __init__(self, et, *args, **kwargs):
        super(Entry, self).__init__(*args, **kwargs)
        assert et.tag == 'TimesheetEntry'

        self.note = None
        self.assignment = (
            int(et.find('.//AssignmentUid').text),
            int(et.find('.//AssignmentAttributeUid').text)
        )
        self.date = DT.datetime.strptime(et.find('.//EntryDate').text, '%m/%d/%Y').date()
        self.time = DT.timedelta(seconds=int(et.find('.//TotalTime').text))

        for node in et:
            if node.tag == 'TimeEntryNotes':
                if len(node) == 0:
                    continue
                assert len(node) == 1
                self.note = node[0].find('.//Description').text

class Timesheet(object):
    def __init__(self, et, *args, **kwargs):
        super(Timesheet, self).__init__(*args, **kwargs)
        assert et.tag == 'Timesheet'

        self.entries = []
        self.assignments = {}

        for node in et:
            if node.tag == 'TimesheetEntries':
                for subnode in node:
                    self.entries.append(Entry(subnode))
            elif node.tag == 'TimesheetAssignmentAttributes':
                for subnode in node:
                    key = (
                        int(subnode.find('.//AssignmentUid').text),
                        int(subnode.find('.//UniqueID').text)
                    )
                    self.assignments[key] = (
                        subnode.find('.//AssignmentName').text,
                        subnode.find('.//ProjectName').text
                    )

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
    tss = ET.fromstring(valstr.encode('utf-8')) # Timesheets element
    for node in tss:
        if node.tag == 'MyTimesheets':
            break
    else:
        assert False
    assert len(node) == 1
    return Timesheet(node[0])

def main():
    org, username, password = open('.tenacct').read().strip().split(':')
    init(org)
    auth = clients.LogonAs.service.AuthUser(org, username, password, '', True)
    userid = int(ET.fromstring(auth).find('.//UniqueId').text)

    # Get a monday
    startdate = DT.date(year=2015, month=05, day=19)
    weekstart = startdate - DT.timedelta(days=startdate.weekday())

    ts = getts(auth, userid, weekstart)
    for entry in ts.entries:
        print ts.assignments[entry.assignment][1]
        print '    ' + entry.date.isoformat() + ': ' + str(entry.time.total_seconds()/60/60)

if __name__ == '__main__':
    main()
