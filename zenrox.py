#!/usr/bin/env python2

from __future__ import print_function

from suds.client import Client
from bunch import Bunch
import requests

from collections import OrderedDict
import datetime as DT
import urllib
import json
import logging
import os
import argparse
import sys
import curses
import string
import re

INDEXCHRS = string.digits + string.lowercase

DEBUG = False

MOBAPI = 'https://m.tenrox.net/2014R3/tenterprise/api/'

LOGFILENAME = 'zenrox.log'
LOGFILE = None
CURSESSCR = None
def log(msg, *args):
    line = (msg % args).encode('utf-8')
    assert all([c not in line for c in ['\r', '\n']])
    if LOGFILE is not None:
        print(line, file=LOGFILE)
    if CURSESSCR is None:
        print(line, file=sys.stdout)
    else:
        CURSESSCR.move(0, 0)
        CURSESSCR.clrtoeol()
        CURSESSCR.addstr(line)
        CURSESSCR.refresh()


def getclient(org, svc):
    url = 'https://{}.tenrox.net/TWebService/{}.svc?singleWsdl'.format(org, svc)
    client = Client(url)
    # Tenrox forces a redirect to https, but the wsdl says http connection.
    # Unfortunately this redirection doesn't work with suds. This is a magic
    # option which apparently overrides the location in the wsdl.
    client.options.location = url
    return client

def weekstart(date):
    if date.day <= 7:
        return date - DT.timedelta(days=date.day-1)
    return date - DT.timedelta(days=date.weekday())

def weekend(date):
    startdate = weekstart(date)
    # First Sunday after this date (inclusive)
    enddate = startdate + DT.timedelta(days=6-startdate.weekday())
    # Make sure beginning and end are in same month
    while enddate.month != startdate.month:
        assert enddate > startdate
        enddate -= DT.timedelta(days=1)
    return enddate

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

    keys = set(['AccessType', 'ActionType', 'ActualWorkHours', 'AssignCompleted', 'AssignmentName', 'ClientName', 'ClientUniqueId', 'CurrentTimeBudget', 'Custom1', 'DirtyStatus', 'ElapsedTime', 'EmailAddress', 'EnableEtc', 'EndDate', 'Etc', 'EtcEndDate', 'EtcStartDate', 'FirstName', 'IsBillable', 'IsFunded', 'IsLeaveTime', 'IsOverHead', 'IsPayable', 'IsRandD', 'LastName', 'LastTimeEntryDate', 'Note', 'ProjectId', 'ProjectManagerFullName', 'ProjectManagerID', 'ProjectName', 'ProjectSchedId', 'ProjectScheduling', 'QueryLevel', 'ShowAssignment', 'ShowETC', 'StartDate', 'TaskColor', 'TaskName', 'TaskUniqueId', 'TimeEntries', 'UniqueId', 'UserId', 'UserIdNo', 'WorkTypeName', 'WorkTypeUniqueId', 'WorkflowEntryId'])

    def __init__(self, obj, *args, **kwargs):
        super(Assignment, self).__init__(*args, **kwargs)
        assert obj.__class__.__name__ == 'Assignment'
        assert set([kv[0] for kv in obj]) == self.keys
        self._obj = obj

        assert obj.AccessType == 1
        assert obj.IsLeaveTime is False

        self.uid = obj.UniqueId
        self.project_id = obj.ProjectId
        self.project_name = obj.ProjectName
        self.task_id = obj.TaskUniqueId
        self.task_name = obj.TaskName

class AssignmentAttr(object):

    keys = set(['AccessType', 'AssignmentComp', 'AssignmentName', 'AssignmentUid', 'BusinessUnitName', 'BusinessUnitUid', 'ChargeName', 'ChargeUid', 'ClientName', 'ClientUid', 'ComponentName', 'ComponentUid', 'Dirty', 'ETC', 'ETCChanged', 'EndDate', 'HasTimeEntry', 'IsBillable', 'IsCustom', 'IsDefault', 'IsETCEditable', 'IsFunded', 'IsNonWorkingTime', 'IsPayable', 'IsRandD', 'ManagerUid', 'PercentComplete', 'PhaseName', 'PhaseUid', 'PortfolioName', 'PortfolioUid', 'ProductName', 'ProductUid', 'ProjectName', 'ProjectUid', 'ShowETC', 'SiteName', 'SiteUid', 'StartDate', 'TaskName', 'TaskUid', 'TeamName', 'TeamUid', 'TemplateUid', 'TitleName', 'TitleUid', 'UniqueID', 'UserGroupName', 'UserGroupUid', 'UserUid', 'WorkTypeName', 'WorkTypeUid'])

    def __init__(self, obj, *args, **kwargs):
        super(AssignmentAttr, self).__init__(*args, **kwargs)
        assert obj.__class__.__name__ == 'AssignmentAttribute'
        assert set([kv[0] for kv in obj]) == self.keys
        self._obj = obj

        assert obj.HasTimeEntry is True
        assert obj.AccessType == 1
        assert obj.IsNonWorkingTime is False

        self.uid = obj.UniqueID
        self.assignment_id = obj.AssignmentUid

class Entry(object):

    keys = set(['Approved', 'AssignmentAttributeUid', 'AssignmentUid', 'BUnitUid', 'Billed', 'ChargeUid', 'CreatedByUid', 'CreationDate', 'DoubleOvertime', 'EntryDate', 'EntryState', 'HasNotes', 'IsBillable', 'IsCustom', 'IsDirty', 'IsFunded', 'IsNonWorking', 'IsPayable', 'IsRandD', 'Overtime', 'PhaseUid', 'Posted', 'RegularTime', 'Rejected', 'SiteName', 'SiteUid', 'TaskUid', 'TimeEntryNotes', 'TimesheetUid', 'TotalTime', 'UniqueID', 'UpdateDate', 'UpdatedByUid', 'UserUid', 'hasError'])

    def __init__(self, obj, *args, **kwargs):
        super(Entry, self).__init__(*args, **kwargs)
        assert obj.__class__.__name__ == 'TimesheetEntry'
        assert set([kv[0] for kv in obj]) == self.keys
        self._obj = obj

        assert obj.IsNonWorking is not True # TODO
        assert obj.TotalTime == obj.RegularTime + obj.Overtime + obj.DoubleOvertime

        self.uid = obj.UniqueID
        self.note = None
        self.assignment_id = obj.AssignmentUid
        self.assignment_attr_id = obj.AssignmentAttributeUid
        self.date = DT.datetime.strptime(obj.EntryDate, '%m/%d/%Y').date()
        self.time = DT.timedelta(seconds=obj.TotalTime)

        if obj.TimeEntryNotes is not None:
            subobjs = obj.TimeEntryNotes.TimesheetNote
            assert len(subobjs) == 1
            self.note = subobjs[0].Description

class Timesheet(object):

    keys = set(['ActiveSiteUid', 'ActivityGUID', 'AllowEntryInTheAdvance', 'AllowEntryInTheAdvanceType', 'AllowEntryInThePast', 'AllowEntryInThePastType', 'BankedOverTime', 'CanManagerModifyBillable', 'CanManagerModifyPayable', 'DefaultClientUid', 'DefaultProjectUid', 'DefaultWorkTypeUid', 'Details', 'EmployeeType', 'EndDate', 'FunctionalGroupUid', 'FunctionalManagerUid', 'HasAssignments', 'HasErrors', 'HasNotes', 'HasTimeentries', 'HireDate', 'IsTimesheetClosed', 'LeaveTimes', 'LockedDates', 'MasterSiteUid', 'PeriodClosed', 'PersonalDayTime', 'ResourceType', 'RoleObjectType', 'ShowAdjustmentsSection', 'ShowAssignmentsSection', 'ShowLeaveTimeSection', 'ShowNonWorkingTimeSection', 'SickLeaveTime', 'StartDate', 'TemplateName', 'TemplateUid', 'TerminatedDate', 'TimeIncrement', 'TimesheetAssignmentAttributes', 'TimesheetColumns', 'TimesheetEntries', 'TimesheetErrors', 'TimesheetNotes', 'TimesheetStates', 'TimesheetTransitions', 'TotalPeriodOverTime', 'TotalPeriodPayableTime', 'TotalPeriodRegTime', 'UniqueId', 'UserAccessStatus', 'UserFirstName', 'UserID', 'UserLastName', 'UserType', 'UserUID', 'UsersAccessStatus', 'VacationTime', 'WorkflowGUID'])

    def __init__(self, weekdate, obj, *args, **kwargs):
        super(Timesheet, self).__init__(*args, **kwargs)
        assert obj.__class__.__name__ == 'Timesheet'
        assert set([kv[0] for kv in obj]) == self.keys
        self._obj = obj

        assert weekstart(weekdate) == weekdate
        assert len(obj.TimesheetStates.TimesheetState) == 1

        self.uid = obj.UniqueId
        self.startdate = weekdate
        self.numdays = (weekend(weekdate) - weekdate).days + 1
        self.entries = OrderedDict()
        self.assignment_attrs = OrderedDict()
        self.readonly = obj.TimesheetStates.TimesheetState[0].IsReadOnly

        if obj.TimesheetEntries is not None:
            for subobj in obj.TimesheetEntries.TimesheetEntry:
                assert subobj.IsNonWorking in [True, False]
                if subobj.IsNonWorking:
                    continue # TODO: don't skip
                self.entries[subobj.UniqueID] = Entry(subobj)
        if obj.TimesheetAssignmentAttributes is not None:
            for subobj in obj.TimesheetAssignmentAttributes.AssignmentAttribute:
                assert subobj.IsNonWorkingTime in [True, False]
                if subobj.IsNonWorkingTime:
                    continue # TODO: don't skip
                self.assignment_attrs[subobj.UniqueID] = AssignmentAttr(subobj)

clients = Bunch()

def initapi():
    org, username, password = open('.tenacct').read().strip().split(':')
    log('Initialising services')
    for service in services:
        clients[service] = getclient(org, service)
    log('Logging into %s tenrox as %s', org, username)
    auth = clients.LogonAs.service.Authenticate(org, username, password, '', True)
    resp = requests.get(MOBAPI + 'Security', auth=(org + ':' + username, password))
    assert resp.status_code == 200
    mobauth = json.loads(resp.text)['Token'] # this is base64 encoded xml...
    userid = auth.UniqueId
    log('Initialisation complete')
    return userid, auth, mobauth

def get_timesheet(auth, userid, weekdate):
    log('Getting timesheet for week starting %s', weekdate.isoformat())
    tss = clients.Timesheets.service.QueryTimesheetsDetailsTyped(auth, userid, weekdate)
    mytss = tss.MyTimesheets
    assert len(mytss.Timesheet) == 1
    return Timesheet(weekdate, mytss.Timesheet[0])

def get_assignments(auth, userid, weekdate):
    log('Getting assignments for week starting %s', weekdate.isoformat())
    assert weekstart(weekdate) == weekdate
    weekenddate = weekend(weekdate)
    aoa = clients.Assignments.service.QueryByUserIdTyped(auth, userid, weekdate.isoformat(), weekenddate.isoformat())
    assignments = OrderedDict()
    for assignment in aoa.Assignment:
        if assignment.AccessType == 2:
            # these seem to be the old 'training' codes that don't show up any
            # more - most entries appear to have a value of '1'
            continue
        # TODO: handle leave time
        if assignment.IsLeaveTime == True:
            continue
        assignments[assignment.UniqueId] = Assignment(assignment)
    return assignments

# I really really tried to use the official API for this but it's astoundingly
# poorly designed (and documented). The mobile api is much friendlier.
def newentry(mobauth, timesheet, assignment, date, numhours, note=None):
    assert not timesheet.readonly
    numsecs = numhours * 60 * 60
    assert numsecs % 900 == 0
    assert numsecs == int(numsecs)
    numsecs = int(numsecs)

    putval = {"KeyValues": [
        {"IsAttribute": True, "Property": "myproject", "Value": assignment.project_id},
        {"IsAttribute": True, "Property": "task", "Value": assignment.task_id},
        {"IsAttribute": True, "Property": "etc", "Value": None},
        {"IsAttribute": True, "Property": "charge", "Value": "0"},
        {"IsAttribute": False, "Property": "EntryDate", "Value": date.strftime('%m/%d/%Y')},
        {"IsAttribute": False, "Property": "RegularTime", "Value": numsecs},
        {"IsAttribute": False, "Property": "Overtime", "Value": 0},
        {"IsAttribute": False, "Property": "DoubleOvertime", "Value": 0},
        {"IsAttribute": False, "Property": "UniqueId", "Value": -1},
    ]}
    if note is not None:
        putval['Notes'] = [
            {'Description': note, 'IsPublic': True, 'NoteType': 'ALERT', 'UniqueId': -1}
        ]

    url = MOBAPI + 'Timesheets/%s?property=timeentrylite' % (timesheet.uid,)
    headers = {
        'API-Key': mobauth,
        'Accept': 'application/json, text/plain, */*',
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = '=' + urllib.quote(json.dumps(putval))
    resp = requests.put(url, data=data, headers=headers)
    assert resp.status_code == 200

def makeweek(timesheet, assignments):
    week = OrderedDict()
    for i in range(timesheet.numdays):
        week[timesheet.startdate + DT.timedelta(days=i)] = []
    for entry in timesheet.entries.values():
        assignment = assignments[entry.assignment_id]
        week[entry.date].append({
            "assignment": assignment.project_name + ' : ' + assignment.task_name,
            "numhours": entry.time.total_seconds()/60/60,
        })
    return week

def curses_putln(win, msg, *args):
    y, x = win.getyx()
    curses_put(win, msg, *args)
    win.move(y+1, x)
def curses_put(win, msg, *args):
    line = (msg % args).encode('utf-8')
    win.clrtoeol()
    win.addstr(line)

def curses_printtimesheet(win, yofs, timesheet, assignments):
    tsgrid = makeweek(timesheet, assignments)
    win.move(yofs, 0)
    curses_putln(win, 'Possible assignments:')
    for i, assignment in enumerate(assignments.values()):
        curses_putln(win, '%s %s  -  %s', INDEXCHRS[i], assignment.project_name, assignment.task_name)
    curses_putln(win, '')
    curses_putln(win, 'Timesheet:')
    for i, (date, entries) in enumerate(makeweek(timesheet, assignments).items()):
        curses_putln(win, '%s %s %s:', INDEXCHRS[i], date.isoformat(), date.strftime('%a'))
        for entry in entries:
            curses_putln(win, '    %s - %s hrs', entry['assignment'], entry['numhours'])

def action_curses(stdscr):
    global CURSESSCR
    CURSESSCR = stdscr
    stdscr.refresh()
    userid, auth, mobauth = initapi()

    yofs = 2

    weekdate = weekstart(DT.date.today())
    def get_ts():
        return get_timesheet(auth, userid, weekdate)
    def get_asgns():
        return get_assignments(auth, userid, weekdate)
    def redraw_ts(timesheet, assignments):
        stdscr.move(yofs, 0)
        stdscr.clrtobot()
        log('Displaying timesheet for %s', weekdate.isoformat())
        curses_printtimesheet(stdscr, yofs, timesheet, assignments)
        stdscr.redrawwin()
        stdscr.refresh()
        return stdscr.getyx()[0] + 1

    def create_entry():
        curses.echo()
        stdscr.move(tsyofs, 0)
        curses_put(stdscr, 'Assignment: ')
        assignment_char = stdscr.getkey().lower()
        stdscr.move(tsyofs+1, 0)
        curses_put(stdscr, 'Date: ')
        date_char = stdscr.getkey().lower()
        stdscr.move(tsyofs+2, 0)
        curses_put(stdscr, 'Hours: ')
        hoursstr = stdscr.getstr()
        stdscr.move(tsyofs+3, 0)
        curses_put(stdscr, 'Note: ')
        note = stdscr.getstr()
        stdscr.move(tsyofs, 0)
        stdscr.clrtobot()
        curses.noecho()
        log('Got assignment:%s date:%s', assignment_char, date_char)
        assignment_idx = INDEXCHRS.find(assignment_char)
        date_idx = INDEXCHRS.find(date_char)
        if not 0 <= assignment_idx < len(assignments):
            log('Invalid assignment key')
            return
        if not 0 <= date_idx < timesheet.numdays:
            log('Invalid date key')
            return
        if re.match(r'^([0-9]|10|11|12|13|14)(\.(0|00|25|5|50|75))?$', hoursstr) is None:
            log('Invalid number of hours')
            return
        assignment = assignments.values()[assignment_idx]
        date = timesheet.startdate + DT.timedelta(days=date_idx)
        numhours = float(hoursstr)
        log('Saving entry')
        newentry(mobauth, timesheet, assignment, date, numhours, note)
        log('Saved')

    timesheet, assignments = get_ts(), get_asgns()
    tsyofs = redraw_ts(timesheet, assignments)

    while 1:
        char = stdscr.getch()
        if char == ord('q'):
            break
        elif char == ord('c'): # create
            create_entry()
            timesheet = get_ts()
            tsyofs = redraw_ts(timesheet, assignments)
        elif char == ord('m'): # modify
            assert False
        elif char == ord('d'): # delete
            assert False
        elif char == ord('r'): # refresh
            timesheet, assignments = get_ts(), get_asgns()
            tsyofs = redraw_ts(timesheet, assignments)
        elif char == ord('s'): # save
            assert False
        elif char == curses.KEY_LEFT:
            weekdate -= DT.timedelta(days=7)
            timesheet, assignments = get_ts(), get_asgns()
            tsyofs = redraw_ts(timesheet, assignments)
        elif char == curses.KEY_RIGHT:
            weekdate += DT.timedelta(days=7)
            timesheet, assignments = get_ts(), get_asgns()
            tsyofs = redraw_ts(timesheet, assignments)

    CURSESSCR = None
    return 0

def action_printweek(datestr):
    userid, auth, mobauth = initapi()

    # Get a monday
    startdate = DT.datetime.strptime(datestr, '%Y-%m-%d').date()
    weekdate = weekstart(startdate)

    # Actually get timesheet
    timesheet = get_timesheet(auth, userid, weekdate)
    assignments = get_assignments(auth, userid, weekdate)

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
    return 0

def init():
    # Init debug logging if necessary
    global DEBUG, LOGFILE
    LOGFILE = open(LOGFILENAME, 'a')
    if os.environ.get('DEBUG', '0') == '1':
        DEBUG = True
    if DEBUG:
        logging.basicConfig(level=logging.INFO, stream=LOGFILE)
        logging.getLogger('suds.client').setLevel(logging.DEBUG)
        logging.getLogger('requests.packages').setLevel(logging.DEBUG)

def main():
    init()

    actions = ['curses', 'printweek']
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='action', help='Action. One of: ' + ' '.join(actions))

    sub_parsers = {}
    for action in actions:
        sub_parsers[action] = subparsers.add_parser(action)

    sub_parsers['printweek'].add_argument('date', help='select timesheet including this day, format yyyy-mm-dd')

    args = parser.parse_args()

    try:
        if args.action == 'printweek':
            sys.exit(action_printweek(args.date))
        elif args.action == 'curses':
            sys.exit(curses.wrapper(action_curses))
        else:
            assert False
    except SystemExit:
        raise
    except:
        if DEBUG:
            import pdb
            pdb.post_mortem()
        else:
            raise

if __name__ == '__main__':
    main()
