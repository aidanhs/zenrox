#!/usr/bin/env python2

from __future__ import print_function

from suds.client import Client
from bunch import Bunch
from collections import OrderedDict
import xml.etree.ElementTree as ET
import datetime as DT
import logging
import os
import re

DEBUG = False

def log(msg, *args):
    print(msg % args)

def xv(element, xpath, converter=unicode):
    res = element.findall(xpath)
    assert len(res) == 1
    return converter(res[0].text)

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

    'Assignments',
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

class Assignment(object):
    def __init__(self, et, *args, **kwargs):
        super(Assignment, self).__init__(*args, **kwargs)
        assert et.tag == 'Assignment'
        self._et = et

        assert xv(et, 'AccessType') == '1'
        assert xv(et, 'IsLeaveTime') == 'false'

        self.uid = xv(et, 'UniqueId', int)
        self.project_name = xv(et, 'ProjectName')
        self.task_name = xv(et, 'TaskName')

class AssignmentAttr(object):
    def __init__(self, et, *args, **kwargs):
        super(AssignmentAttr, self).__init__(*args, **kwargs)
        assert et.tag == 'AssignmentAttribute'
        self._et = et

        assert xv(et, 'HasTimeEntry') == 'true'
        assert xv(et, 'AccessType') == '1'
        assert xv(et, 'IsNonWorkingTime') == 'false' # TODO

        self.uid = xv(et, 'UniqueID', int)
        self.assignment_id = xv(et, 'AssignmentUid', int)

class Entry(object):
    def __init__(self, et, *args, **kwargs):
        super(Entry, self).__init__(*args, **kwargs)
        assert et.tag == 'TimesheetEntry'
        self._et = et

        assert xv(et, 'IsNonWorking') != 'true' # TODO

        self.uid = xv(et, 'UniqueID', int)
        self.note = None
        self.assignment_id = xv(et, 'AssignmentUid', int)
        self.assignment_attr_id = xv(et, 'AssignmentAttributeUid', int)
        self.date = DT.datetime.strptime(xv(et, 'EntryDate'), '%m/%d/%Y').date()
        self.time = DT.timedelta(seconds=xv(et, 'TotalTime', int))

        for node in et:
            if node.tag == 'TimeEntryNotes':
                if len(node) == 0:
                    continue
                assert len(node) == 1
                self.note = xv(node[0], 'Description')

class Timesheet(object):
    def __init__(self, weekstart, et, *args, **kwargs):
        super(Timesheet, self).__init__(*args, **kwargs)
        assert et.tag == 'Timesheet'
        self._et = et

        self.startdate = weekstart
        self.entries = OrderedDict()
        self.assignment_attrs = OrderedDict()

        for node in et:
            if node.tag == 'TimesheetEntries':
                for subnode in node:
                    # TODO
                    if xv(subnode, 'IsNonWorking') == 'true':
                        continue
                    val = Entry(subnode)
                    self.entries[val.uid] = val
            elif node.tag == 'TimesheetAssignmentAttributes':
                for subnode in node:
                    # TODO
                    if xv(subnode, 'IsNonWorkingTime') == 'true':
                        continue
                    val = AssignmentAttr(subnode)
                    self.assignment_attrs[val.uid] = val

clients = Bunch()

def init(org):
    global DEBUG
    if os.environ.get('DEBUG', '0') == '1':
        DEBUG = True
    if DEBUG:
        logging.basicConfig(level=logging.INFO)
        logging.getLogger('suds.client').setLevel(logging.DEBUG)
    log('Initialising services')
    for service in services:
        clients[service] = getclient(org, service)

def get_timesheet(auth, userid, weekstart):
    log('Getting timesheet for week starting %s', weekstart.isoformat())
    assert weekstart - DT.timedelta(days=weekstart.weekday()) == weekstart
    respstr = clients.Timesheets.service.QueryTimesheetsDetails(auth, userid, weekstart)
    resp = ET.fromstring(unicode(respstr).encode('utf-8'))
    assert xv(resp, 'Success') == 'true'
    valstr = xv(resp, 'Value')
    tss = ET.fromstring(valstr.encode('utf-8')) # Timesheets element
    mytss = tss.findall('MyTimesheets')
    assert len(mytss) == 1
    assert len(mytss[0]) == 1
    return Timesheet(weekstart, mytss[0][0])

def get_assignments(auth, userid, weekstart):
    log('Getting assignments for week starting %s', weekstart.isoformat())
    assert weekstart - DT.timedelta(days=weekstart.weekday()) == weekstart
    weekend = weekstart + DT.timedelta(days=6)
    respstr = clients.Assignments.service.QueryByUserId(auth, userid, weekstart.isoformat(), weekend.isoformat())
    resp = ET.fromstring(unicode(respstr).encode('utf-8'))
    assert xv(resp, 'Success') == 'true'
    valstr = xv(resp, 'Value')
    aoa = ET.fromstring(valstr.encode('utf-8')) # ArrayOfAssignment element
    assignments = OrderedDict()
    for assignment in aoa:
        if xv(assignment, 'AccessType') == '2':
            # these seem to be the old 'training' codes that don't show up any
            # more - most entries appear to have a value of '1'
            continue
        # TODO: handle leave time
        if xv(assignment, 'IsLeaveTime') == 'true':
            continue
        aid = xv(assignment, 'UniqueId', int)
        assignments[aid] = Assignment(assignment)
    return assignments

def makeweek(timesheet, assignments):
    week = OrderedDict()
    for i in range(7):
        week[timesheet.startdate + DT.timedelta(days=i)] = []
    for entry in timesheet.entries.values():
        assignment = assignments[entry.assignment_id]
        week[entry.date].append({
            "assignment": assignment.project_name + ' : ' + assignment.task_name,
            "numhours": entry.time.total_seconds()/60/60,
        })
    return week

def main():
    org, username, password = open('.tenacct').read().strip().split(':')
    init(org)
    log('Logging into %s tenrox as %s', org, username)
    auth = clients.LogonAs.service.AuthUser(org, username, password, '', True)
    userid = xv(ET.fromstring(auth), 'UniqueId', int)

    # Get a monday
    startdate = DT.date(year=2015, month=05, day=25)
    weekstart = startdate - DT.timedelta(days=startdate.weekday())

    # Actually get timesheet
    timesheet = get_timesheet(auth, userid, weekstart)
    assignments = get_assignments(auth, userid, weekstart)

    log('===================')
    log('Possible assignments:')
    for assignment in assignments.values():
        log('%s  -  %s', assignment.project_name, assignment.task_name)
    log('===================')
    log('Timesheets:')
    for date, entries in makeweek(timesheet, assignments).items():
        log('%s %s:', date.isoformat(), date.strftime('%a'))
        for entry in entries:
            log('    %s - %s hrs', entry['assignment'], entry['numhours'])
    log('===================')

if __name__ == '__main__':
    try:
        main()
    except:
        if DEBUG:
            import pdb
            pdb.post_mortem()
        else:
            raise
