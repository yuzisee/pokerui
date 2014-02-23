
/**
 * Module dependencies.
 */

var express = require('express');
var table = require('./routes/table');
var api_user = require('./routes/api_user');
var api_table = require('./routes/api_table');
// global.pokerai = require('../addons/pokerai/build/Release/pokerai');
global.randCard  = function(){
	cards = ['s','h','c','d'];
	return ""+Math.floor(Math.random()*9+1)+cards[Math.floor(Math.random()*3+1)];
}

global.pokerai = {
	'startTable': function(f, chips, players){
		chipsAtRound = {};
		holeCards = {};
		for(idx in players) {
			player = players[idx];
			chipsAtRound[player.id] = chips;
			holeCards[player.id] = [global.randCard(), global.randCard()];
		}

		return {
			players: players,
			holeCards: holeCards,
			startChips: chips,
			hand: 0,
			currentPlayer: 0,
			dealer: 0,
			community: [],
			chipsAtRound: chipsAtRound
		}
	},

	'getActionOn': function(instance){
		return {
			hand: instance.hand,
			actionOn: instance.players[instance.currentPlayer].id
		}
	},

	'getActionSituation': function(instance, hand){
		return {
			dealer: instance.dealer,
			community: instance.community,
			chipsAtRound: instance.chipsAtRound
		}
	}
}
var http = require('http');
var path = require('path');

var app = express();

// all environments
app.set('port', process.env.PORT || 3000);
app.use(express.favicon());
app.use(express.logger('dev'));
app.use(express.json());
app.use(express.urlencoded());
app.use(express.methodOverride());
app.use(express.cookieParser());
app.use(express.bodyParser());
app.use(express.session({secret: '9YUv495s928Nl5vhaha1212'}));
app.use(app.router);

// development only
if ('development' == app.get('env')) {
  app.use(express.errorHandler());
}


// Global where we keep a list of all users
global.users = [];
// Routes to REST /api/user
app.get('/api/userid', api_user.getUserId);
app.get('/api/user', api_user.getAll);
app.post('/api/user', api_user.postAll);
app.get('/api/user/:userid', api_user.getUser);
app.post('/api/user/:userid', api_user.updateUser);
app.get('/api/user/:userid/active_tables', api_user.activeTables);


// Routes to REST /api/table
global.tables = {};
app.get('/api/table', api_table.getAll);
app.post('/api/table', table.newTable); // get a new (unused) tableId so you can start a table -- replaces /table/new
app.get('/api/table/:tableid', api_table.getTable);
app.post('/api/table/:tableid', api_table.updateTable); // ?
app.post('/api/table/:tableid/join', api_table.joinTable); // Sit down at the table
app.post('/api/table/:tableid/start_game', api_table.startGame); // Vote to start the game

// Whose turn is it? Which hand are we on?
// This GET call will give you at least the :handNum and :seatNum you need for the next section
// (e.g. enough to know who is next to POST to /api/table/:tableid/hand/:handNum/seat/:seatNum/action)
app.get('/api/table/:tableid/action_on', api_table.getActionOn);

app.get('/api/table/:tableid/hand/:handNum/actions', api_table.getActionSituation); // Get all actions so far, in hand handNum

app.post('/api/table/:tableid/hand/:handNum/seat/:seatNum/action', api_table.performAction); // try performing an action -- the server will tell you what action you were actually allowed to take (accounting for minRaise, etc.)
app.get('/api/table/:tableid/hand/:handNum/seat/:seatNum/holecards', api_table.getHolecards);
app.get('/api/table/:tableid/hand/:handNum/outcome', api_table.getOutcome);


// This is just a summary of /api/table/:tableid/hand/:handNum/actions, which you could get in a loop...
// app.get('/api/table/:tableid/hand/:handNum', api_table.getHand);
// ...but nowadays 


http.createServer(app).listen(app.get('port'), function(){
  console.log('Express server listening on port ' + app.get('port'));
});
