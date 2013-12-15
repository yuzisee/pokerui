
/**
 * Module dependencies.
 */

var express = require('express');
var routes = require('./routes');
var table = require('./routes/table');
var api_user = require('./routes/api_user');
var api_table = require('./routes/api_table');
var pokerai = require('../addons/pokerai/build/Release/pokerai');
var http = require('http');
var path = require('path');

var app = express();

// all environments
app.set('port', process.env.PORT || 3000);
app.set('views', path.join(__dirname, 'views'));
app.set('clients', path.join(__dirname, '/../client'));
app.set('view engine', 'jade');
app.use(express.favicon());
app.use(express.logger('dev'));
app.use(express.json());
app.use(express.urlencoded());
app.use(express.methodOverride());
app.use(express.cookieParser());
app.use(express.bodyParser());
app.use(express.session({secret: '9YUv495s928Nl5vhaha1212'}));
app.use(app.router);
app.use(express.static(path.join(__dirname, 'public')));
app.use("/client", express.static(path.join(__dirname, '/../client')));

// development only
if ('development' == app.get('env')) {
  app.use(express.errorHandler());
}

// Naked domain!
app.get('/', routes.index);
// Global where we keep a list of all users
global.users = [];
// Routes to REST /api/user
app.get('/api/userid', api_user.getUserId);
app.get('/api/user', api_user.getAll);
app.post('/api/user', api_user.postAll);
app.get('/api/user/:userid', api_user.getUser);
app.post('/api/user/:userid', api_user.updateUser);

// Routes to NON-REST /table
app.get('/table', table.table);
app.get('/table/new', table.newTable);
app.get('/table/:tableid', table.loadTable);

// Routes to REST /api/table
global.tables = {};
app.get('/api/table', api_table.getAll);
app.get('/api/table/:tableid', api_table.getTable);
app.post('/api/table/:tableid', api_table.updateTable);
app.post('/api/table/:tableid/join', api_table.joinTable);
app.post('/api/table/:tableid/startgame', api_table.startGame);
app.get('/api/table/:tableid/status', api_table.getLiveStatus);
app.post('/api/table/:tableid/hand/:handNum/actions', api_table.performAction);
app.get('/api/table/:tableid/hand/:handNum/actions', api_table.getActionSituation);
app.get('/api/table/:tableid/hand/:handNum/outcome', api_table.getOutcome);
app.get('/api/table/:tableid/hand/:handNum/seat/:seatNum/holecards', api_table.getHolecards);

http.createServer(app).listen(app.get('port'), function(){
  console.log('Express server listening on port ' + app.get('port'));
});
