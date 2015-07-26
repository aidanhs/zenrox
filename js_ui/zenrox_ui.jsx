/* @flow */
'use strict';

declare var $: any;
var React = require('react');
var FixedDataTable = require('fixed-data-table');

class LoginBox extends React.Component {
  props: { onLogin: Function; disabled: boolean };
  state: { username: string; password: string };

  constructor(props) {
    super(props);
    this.state = { username: '', password: '' };
  }
  handleChange(e) {
    var elt = e.currentTarget;
    var o = {};
    o[elt.name] = elt.value;
    this.setState(o);
  }
  handleLogin(e) {
    this.props.onLogin(this.state);
  }
  render() {
    return (<div>
      Username: <input disabled={this.props.disabled} type="text" name="username"
                       value={this.state.username} onChange={this.handleChange} />&nbsp;
      Password: <input disabled={this.props.disabled} type="password" name="password"
                       value={this.state.password} onChange={this.handleChange} />&nbsp;
      <button disabled={this.props.disabled} onClick={this.handleLogin}>Login</button>
    </div>);
  }
}

class TimeSheet extends React.createClass {
  props: void;
  state: {
    weekdate: string;
    assignments: Array<{ uid: number; project: string; task: string }>;
    // entries: a mapping from yyyy-mm-dd string to entry object
    // entry: a mapping from assignment_id to num secs
    entries: { [key: string]: { [key: string]: number } };
  };

  constructor(props) {
    super(props);
    var today = (new Date()).toISOString().slice(0, 10);
    self.state = { weekdate: today, assignments: [], entries: {} };
  }

  getTs(getPrev, getNext) {
    if (getPrev && getNext) {
      alert('Cannot get next and previous!');
      return;
    }
    $.ajax({
      method: 'GET',
      url: '/timesheet',
      data: { date: this.state.weekdate, prev: getPrev ? 1 : 0, next: getNext ? 1 : 0 },
      dataType: 'json',
      cache: false,
      success: function (data) {
        this.setState(data);
      }.bind(this),
      error: function () {
        alert('Couldn\'t get timesheet');
      },
    });
  }
  componentDidMount() {
    this.getTs(false, false);
  }
  render() {
    var firstwidth = 600
    var colwidth = 120;

    var entries = this.state.entries;
    var dates = Object.keys(this.state.entries);
    dates.sort();
    var cols = dates.map(function (date, i) {
      return <FixedDataTable.Column label={date} width={colwidth} dataKey={i+1} />
    });
    cols.unshift(<FixedDataTable.Column label='' width={firstwidth} dataKey={0} />);

    var grid = this.state.assignments.map(function (assignment) {
      var assignmentEntries = dates.map(function (date) {
        var numSecs = entries[date][assignment.uid];
        return numSecs / (60 * 60) || '';
      });
      assignmentEntries.unshift(assignment.project + ' - ' + assignment.task);
      return assignmentEntries;
    });

    function rowGetter(rowIndex) {
      return grid[rowIndex];
    }

    return (<div>
      <div>
        <p>Week: {this.state.weekdate}</p>
        <button onClick={this.getTs.bind(this, true, false)}>Prev</button>
        <button onClick={this.getTs.bind(this, false, true)}>Next</button>
      </div>
      <FixedDataTable.Table
        rowHeight={30}
        rowGetter={rowGetter}
        rowsCount={grid.length}
        width={colwidth*(cols.length-1) + firstwidth}
        maxHeight={100000}
        headerHeight={50}>
        {cols}
      </FixedDataTable.Table>
    </div>);
  }
}

class ZenroxUI extends React.component {
  props: void;
  state: { username: ?string; disableLogin: boolean };

  constructor(props) {
    super(props);
    this.state = { username: null, disableLogin: true };
  }
  getAcct() {
    $.ajax({
      url: '/account',
      dataType: 'json',
      cache: false,
      success: function (data) {
        this.setState({
          username: data.username, disableLogin: data.username !== null
        });
      }.bind(this),
      error: function () {
        alert('Couldn\'t get session info');
      },
    });
  }
  componentDidMount() {
    this.getAcct();
  }
  handleLogin(creds) {
    this.setState({ disableLogin: true });
    $.ajax({
      method: 'POST',
      url: '/login',
      data: creds,
      success: function () {
        this.getAcct();
      }.bind(this),
      error: function () {
        alert('Couldn\'t log in');
      },
    });
  }
  render() {
    var loginElt;
    if (this.state.username == null) {
    } else {
    }
    return (
      <div>
        <LoginBox username={this.state.username} onLogin={this.handleLogin} disabled={this.state.disableLogin} />
        <div>
            {this.state.username != null ?
                'Logged in as ' + this.state.username : 'Not logged in'}
        </div>
        {this.state.username !== null ? <TimeSheet /> : undefined}
      </div>
    );
  }
}

React.render(
    React.createElement(ZenroxUI),
    document.getElementById('root')
);
