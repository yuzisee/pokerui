
/**
 * Module dependencies.
 */

var express = require('express');
var routes = require('./routes');
var table = require('./routes/table');
var user = require('./routes/user');
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
app.use(express.session({secret: '9YUv495s928Nl5vhaha1212'}));
app.use(app.router);
app.use(express.static(path.join(__dirname, 'public')));
app.use("/client", express.static(path.join(__dirname, '/../client')));

// development only
if ('development' == app.get('env')) {
  app.use(express.errorHandler());
}

app.get('/', routes.index);
app.get('/table', table.table);
app.get('/table/new', table.newTable);
app.get('/table/:tableId', table.loadTable);
app.get('/user/name', user.getName);
app.get('/user/name/:newName', user.setName);

http.createServer(app).listen(app.get('port'), function(){
  console.log('Express server listening on port ' + app.get('port'));
});
