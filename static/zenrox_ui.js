(function () {
'use strict';

var LoginBox = React.createClass({
  getInitialState: function() {
    return { username: '', password: '' };
  },
  handleChange: function (e) {
    var elt = e.currentTarget;
    var o = {};
    o[elt.name] = elt.value;
    this.setState(o);
  },
  handleLogin: function (e) {
    this.props.onLogin(this.state);
  },
  render: function () {
    return (<div>
      Username: <input disabled={this.props.disabled} type="text" name="username"
                       value={this.state.username} onChange={this.handleChange} />&nbsp;
      Password: <input disabled={this.props.disabled} type="password" name="password"
                       value={this.state.password} onChange={this.handleChange} />&nbsp;
      <button disabled={this.props.disabled} onClick={this.handleLogin}>Login</button>
    </div>);
  },
});

var TimeSheet = React.createClass({
  getTs: function (getPrev, getNext) {
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
  },
  componentDidMount: function () {
    this.getTs(false, false);
  },
  getInitialState: function () {
    /*
     * assignments: an array of objects each with property: uid
     * entries: a mapping from yyyy-mm-dd string to entry object
     * entry: a mapping from assignment_id to num_hours
     */
    var today = (new Date()).toISOString().slice(0, 10);
    return { weekdate: today, assignments: [], entries: {} };
  },
  render: function () {
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
  },
});

window.ZenroxUI = React.createClass({
  getAcct: function () {
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
  },
  componentDidMount: function () {
    this.getAcct();
  },
  getInitialState: function() {
    return { username: null, disableLogin: true };
  },
  handleLogin: function (creds) {
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
  },
  render: function() {
    var loginElt;
    if (this.state.username === null) {
    } else {
    }
    return (
      <div>
        <LoginBox username={this.state.username} onLogin={this.handleLogin} disabled={this.state.disableLogin} />
        <div>
            {this.state.username !== null ?
                'Logged in as ' + this.state.username : 'Not logged in'}
        </div>
        {this.state.username !== null ? <TimeSheet /> : undefined}
      </div>
    );
  },
});

})();
