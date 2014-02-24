
/**
 * Module dependencies.
 */

var express = require('express');
var table = require('./routes/table');
var api_user = require('./routes/api_user');
var api_table = require('./routes/api_table');
global.pokerai = require('../addons/pokerai/build/Release/pokerai');
/*
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
		};
	},

	'getActionOn': function(instance){
		return {
			hand: instance.hand,
			actionOn: instance.players[instance.currentPlayer].id
		};
	},

	'getActionSituation': function(instance, hand){
		return {
			dealer: instance.dealer,
			community: instance.community,
			chipsAtRound: instance.chipsAtRound
		};
	},

	'getMaxSeats': function() {
		return 10;
	}
}
*/
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
global.users = {};
// Routes to REST /api/user
app.get('/api/users', api_user.getAll);

// Get the settings in your session cookie
// Example:
// {
//   "username": "me@haha1212.com",
//   "activeTables": {tableid: {"seat": 0}, ...}
// }
app.get('/api/session', api_user.getUser); 

app.post('/api/login', api_user.updateUser); // For now, this stores your username (an e-mail address) into your session cookie


// Routes to REST /api/table
global.tables = {};
app.get('/api/table', api_table.getAll);
app.post('/api/table', table.newTable); // create a new (unused) tableId so you can start a table

// Get the table state
// Example:
// {
//   'id': tableId,
//   'players': [{"username": "my@haha1212.com", "bot": false, "seat": 0}, ...], // Seated players
//   'totalSeats': global.pokerai.getMaxSeats()
// };
//
// If the game has started, the following fields are also included:
//   "actionOn": {"currentHand": 2, "actionOn": 'me@haha1212.com'}
// Use these to determine: Whose turn is it? Which hand are we on?
// If the game has started, this GET call will give you at least the :handNum and :seatNum you need for the later sections
// (e.g. enough to know who is next to POST to /api/table/:tableid/hand/:handNum/seat/:seatNum/action)
app.get('/api/table/:tableid', api_table.getTable);

app.post('/api/table/:tableid/join', api_table.joinTable); // Sit down at the table
app.post('/api/table/:tableid/start_game', api_table.startGame); // Start the game. Any user can trigger this.
app.post('/api/table/:tableid/action', api_table.performAction); // try performing an action -- the server will tell you what action you were actually allowed to take (accounting for minRaise, etc.)

// Gets actionSituation, holeCards, and outcome for a hand, if available.
// Example:
// {
//   hand: 5,
//   yourCards: [...],
/*
    'state': {
       'actions': [
            {'checkpoint': 'preflop'},
            {'username': 'Nav', 'seat': 0, '_action': 'smallBlind', 'amount': 5.0},
            {'username': 'Joseph', 'seat': 0, '_action': 'bigBlind', 'amount': 10.0},
            {'username': 'bot1', 'seat': 0, '_action': 'fold', 'amount': -1},
            {'username': 'bot2', 'seat': 0, '_action': 'raiseTo', 'amount': 25.0},
            {'username': 'bot3', 'seat': 0, '_action': 'call', 'amount': 25.0},
            ...
            {'checkpoint': 'flop'},
            {'username': 'Nav', 'seat': 0, '_action': 'check', 'amount': 0.0}
           ],
       'startingChips': {
            'preflop': {
              'bot2': 500.0,
              ...
              }
            ,
            'flop': {
              ...
            }
       }
       'startingPot': {
            'preflop': {
            }
            ,
            'flop': {
            }
       },
      'dealer': <username>,
      'community': ['Kh', 'Ts', '9h'],
    }
*/
//   },
//   outcome: {...}
// }
app.get('/api/table/:tableid/hand/:handNum', api_table.getStatus);



http.createServer(app).listen(app.get('port'), function(){
  console.log('Express server listening on port ' + app.get('port'));
});
