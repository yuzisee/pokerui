
/*
 * Manage tables and things
 */

exports.getAll = function(req, res){
  	res.json(global.tables);
};

exports.postAll = function(req, res){
	// if(!req.session.userid) {
	// 	req.session.userid = (""+Math.random()).substring(2,7);
	// 	global.users.push(req.session.userid);
	// }

	// req.params = {'userid': req.session.userid};
	// exports.getUser(req, res);
};

exports.joinTable = function(req, res){
	var tableid = req.params.tableid;
    global.tables[tableid]['players'][req.session.userid] = {
    	id : req.session.userid,
    	name : req.session.name,
    	bot: false
    };
	res.json(global.tables[tableid]);
};

exports.getTable = function(req, res){
	res.json(global.tables[req.params.tableid]);
}

exports.updateTable = function(req, res){
	// userid = req.params.userid;
	// req.session.name = req.body.name;
	// exports.getUser(req, res)
};

exports.startGame = function(req, res){
	// TODO(from yuzisee): What happens if you call startGame twice? We must make sure we don't do that.
	var tableid = req.params.tableid;
	// console.log(global.tables[tableid]['players']);
	players = [];
	for(userid in global.tables[tableid]['players']){
		players.push(global.tables[tableid]['players'][userid]);
	}

	var pokeraiInstance = pokerai.startTable(tableid + '.txt', 1500, players);
	global.tables[tableid]['instance'] = pokeraiInstance;
	// TODO(from yuzisee): You have to call pokeraiInstance.shutdownTable() at some point to save state, etc.

	var actionSituation = global.pokerai.getActionSituation(pokeraiInstance, 1);
	var chipCounts = actionSituation.chipCountsSinceCheckpoint;

	// Initialize action situation
	global.tables[tableid]['hand'] = [];
	global.tables[tableid]['hand'][1] = {};
	global.tables[tableid]['hand'][1]['actionSituation'] = {'bets': [],
		'chipCountsAtHandStart': chipCounts,
		'chipCountsSinceCheckpoint': chipCounts,
		'dealerOn': actionSituation,
		'communitySoFar': actionSituation.communitySoFar}

	global.tables[tableid]['state'] = "STARTED"
	res.json(global.tables[tableid]);
};

exports.getLiveStatus = function(req, res){
	var tableid = req.params.tableid;
	var pokeraiInstance = global.tables[tableid]['instance'];

	res.json(pokerai.getStatus(pokeraiInstance))
};

exports.getActionSituation = function(req, res) {
	var tableid = req.params.tableid;
	var handNum = req.params.handNum;
	res.json(global.tables[tableid]['hand'][handNum]['actionSituation']);
};

exports.getOutcome = function(req, res) {
	var tableid = req.params.tableid;
	var handNum = req.params.handNum;
	res.json(global.tables[tableid]['hand'][handNum]['outcome']);
};

exports.getHolecards = function(req, res) {
	var tableid = req.params.tableid;
	var handNum = req.params.handNum;
	var seatNum = req.params.seatNum;
	var pokeraiInstance = global.tables[tableid]['instance'];

        var currentHandNum = pokerai.getStatus(pokeraiInstance).currentHand;
	// TODO(from yuzisee): Assert that currentHandNum === handNum and otherwise tell the user something went wrong

	res.json(pokerai.getHoleCards(pokeraiInstance, seatNum));
};

exports.performAction = function(req, res){

	var tableid = req.params.tableid;
	var handNum = req.params.handNum;
	var pokeraiInstance = global.tables[tableid]['instance'];

        var currentHandNum = pokerai.getStatus(pokeraiInstance).currentHand;
	// TODO(from yuzisee): Assert that currentHandNum === handNum and otherwise tell the user something went wrong

	var actionRequested = req.body;
	var requestedBetAmount = actionRequested.amount;
	var actionTaken = pokerai.performAction(pokeraiInstance, req.body);
	actionRequested.amount = actionTaken.adjustedBetTo;

	global.tables[tableid]['hand'][handNum]['actionSituation']['bets'].push(actionRequested);
	if (pokeraiAction['checkpoint']) {
		global.tables[tableid]['hand'][handNum]['actionSituation']['bets'].push({'checkpoint': pokeraiAction.checkpoint});

		var actionSituation = pokerai.getActionSituation(pokeraiInstance, 1);
		var chipCounts = actionSituation.chipCountsSinceCheckpoint;

		global.tables[tableid]['hand'][handNum]['actionSituation']['chipCountsSinceCheckpoint'] = chipCounts;
		global.tables[tableid]['hand'][handNum]['actionSituation']['communitySoFar'] = actionSituation.communitySoFar;

		if (pokeraiAction['checkpoint'] == 'showdown') {
			global.tables[tableid]['hand'][handNum]['outcome'] = pokerai.getOutcome(pokeraiInstance, handNum);
		}
	}

	console.log('Bet request amount=' + requestedBetAmount + " actual=" + actionTaken.adjustedBetTo);

	res.json(pokeraiAction)
};