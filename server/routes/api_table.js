
/*
 * Manage tables and things
 */

exports.getAll = function(req, res){
     res.json(global.tables);
};

exports.postAll = function(req, res){
   // if(!req.session.userid) {
   //    req.session.userid = (""+Math.random()).substring(2,7);
   //    global.users.push(req.session.userid);
   // }

   // req.params = {'userid': req.session.userid};
   // exports.getUser(req, res);
};

// 1. Update global.users to mark that this is now an active table for this user
// 2. Update global.tables to mark that this table has an additional player
exports.joinTable = function(req, res){
   var tableid = req.params.tableid;
   console.log('joinTable()');
   console.log(req.session);
   console.log(global.users);
   if (tableid in global.users[req.session.username]['activeTables']) {
      console.log('You are already at this table. Can we indicate this somehow?');
   } else {

      var table = global.tables[tableid];
      var seat = table['players'].length;

      if (seat >= table['totalSeats']) {
         throw 'This table is full.';
      }

      if ('instance' in table) {
         throw 'This table has already started playing. You cannot join after the fact, sorry!';
      }

      global.users[req.session.username]['activeTables'][tableid] = {'seat': seat};
      table['players'].push({
         "username": req.session.username,
         "seat": seat,
         "bot": false
      });
   }
   exports.getTable(req, res);
};

exports.getTable = function(req, res){
   var tableid = req.params.tableid;
   var table = global.tables[tableid];
   
   if('instance' in table){
      global.tables[tableid]['actionOn'] = global.pokerai.getActionOn(table['instance']);
   }

   res.json(table);
}

exports.startGame = function(req, res){
   var tableid = req.params.tableid;
   var table = global.tables[tableid];

   // What happens if you call startGame twice? We must make sure we don't do that.
   if('instance' in table) {
      throw 'Table already started. Ignoring request to start game again.';
   }

   // console.log(global.tables[tableid]['players']);

// global.tables[tableid] has the following form:
// {
//   'id': tableId,
//   'players': [{"username": "my@haha1212.com", "bot": false, "seat": 0}, ...], // Seated players
//   'totalSeats': global.pokerai.getMaxSeats()
// };
   var startTablePlayers = [];
   for(var i=0; i<table['totalSeats']; ++i) {
      if (i<table['players'].length) {
         var p = table['players'][i];
         startTablePlayers.push({'id': p['username'], 'bot': p['bot']});
      } else {
         //TODO(from yuzisee): It looks like we don't actually expect the nulls anymore? See addon.cc
         //startTablePlayers.push(null);
      }
   }
// global.startTable expects the following players array:
// [
//   {'id': 'playerId1', 'bot': false}
//   ,
//   {'id': 'playerId2', 'bot': true}
//   ,
//   {'id': 'playerId3', 'bot': false}
//   ,
//   null
//   ,
//   null
//   ,
//   ...
// ]
   console.log(startTablePlayers);
   var STARTING_CHIPS = 1500;
   var pokeraiInstance = global.pokerai.startTable(tableid + '.logs', STARTING_CHIPS, startTablePlayers);
   global.tables[tableid]['instance'] = pokeraiInstance;
   // TODO(from yuzisee): You have to call pokeraiInstance.shutdownTable() at some point to save state, etc.

   var actionOn = global.pokerai.getActionOn(pokeraiInstance);

   var actionSituation = global.pokerai.getActionSituation(pokeraiInstance, actionOn['currentHand']);

   // Initialize action situation
   global.tables[tableid]['hand'] = [];
   global.tables[tableid]['actionOn'] = actionOn;
   global.tables[tableid]['hand'][0] = 
   {   
      'bets': [],
      'chipCount': actionSituation.chipsAtRound,
      'chipsAtRound': actionSituation.chipsAtRound,
      'dealer': actionSituation.dealer,
      'community': actionSituation.community
   };

   global.tables[tableid]['state'] = "STARTED"
   exports.getTable(req, res);
};


// exports.getHand = function(req, res) {
//    var tableid = req.params.tableid;
//    var handNum = req.params.handNum;
//    res.json(global.tables[tableid]['hand'][handNum]);
// };

function getOutcome(req, res) {
   var tableid = req.params.tableid;
   var handNum = req.params.handNum;
   res.json(global.tables[tableid]['hand'][handNum]['outcome']);
};

function getHolecards(req, res) {
   var tableid = req.params.tableid;
   var handNum = req.params.handNum;
   var seatNum = req.params.seatNum;
   var pokeraiInstance = global.tables[tableid]['instance'];

   var currentHandNum = global.pokerai.getActionOn(pokeraiInstance).currentHand;
   if(currentHandNum != handNum){
      throw "Handnum doesn't match";
   }
   // TODO(from yuzisee): Assert that currentHandNum === handNum and otherwise tell the user something went wrong

   res.json(global.pokerai.getHoleCards(pokeraiInstance, seatNum));
};

function getActionSituation(req, res){

    var tableid = req.params.tableid;
    var handNum = req.params.handNum;

    res.json(global.tables[tableid]['hand'][handNum]['actionSituation'])
};

exports.getStatus = function(req, res){
    res.json({})
}

exports.performAction = function(req, res){

   var tableid = req.params.tableid;
   var handNum = req.params.handNum;
   var pokeraiInstance = global.tables[tableid]['instance'];

   var currentHandNum = global.pokerai.getActionOn(pokeraiInstance).currentHand;
   if(handNum != currentHandNum) throw "Hand not current hand!";

   var actionRequested = req.body;
   var requestedBetAmount = actionRequested.amount;
   var actionTaken = global.pokerai.performAction(pokeraiInstance, req.body);
   actionRequested.amount = actionTaken.adjustedBetTo;

   global.tables[tableid]['hand'][handNum]['actionSituation']['bets'].push(actionRequested);
   if (actionTaken['checkpoint']) {
      global.tables[tableid]['hand'][handNum]['actionSituation']['bets'].push({'checkpoint': actionTaken.checkpoint});

      var actionSituation = global.pokerai.getActionSituation(pokeraiInstance, handNum);
      var chipCounts = actionSituation.chipCountsSinceCheckpoint;

      global.tables[tableid]['hand'][handNum]['actionSituation']['chipCountsSinceCheckpoint'] = chipCounts;
      global.tables[tableid]['hand'][handNum]['actionSituation']['communitySoFar'] = actionSituation.communitySoFar;

      if (actionTaken['checkpoint'] == 'showdown') {
         global.tables[tableid]['hand'][handNum]['outcome'] = global.pokerai.getOutcome(pokeraiInstance, handNum);
      }
   }

   console.log('Bet request amount=' + requestedBetAmount + " actual=" + actionTaken.adjustedBetTo);

   res.json(actionTaken)
};

