
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
	tableid = req.params.tableid;
	table = global.tables[tableid];
	
	if(table.state != "WAITING"){
		global.tables[tableid]['status'] = global.pokerai.getStatus(table['instance']);
	}

	res.json(table);
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

	var pokeraiInstance = global.pokerai.startTable(tableid + '.txt', 1500, players);
	global.tables[tableid]['instance'] = pokeraiInstance;
	// TODO(from yuzisee): You have to call pokeraiInstance.shutdownTable() at some point to save state, etc.

	var status = global.pokerai.getStatus(pokeraiInstance);

	var actionSituation = global.pokerai.getActionSituation(pokeraiInstance, status['hand']);

	// Initialize action situation
	global.tables[tableid]['hand'] = [];
	global.tables[tableid]['status'] = status;
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

exports.getActionOn = function(req, res){
	var tableid = req.params.tableid;
	var pokeraiInstance = global.tables[tableid]['instance'];

	res.json(global.pokerai.getStatus(pokeraiInstance))
};

// exports.getHand = function(req, res) {
// 	var tableid = req.params.tableid;
// 	var handNum = req.params.handNum;
// 	res.json(global.tables[tableid]['hand'][handNum]);
// };

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

    var currentHandNum = global.pokerai.getStatus(pokeraiInstance).currentHand;
    if(currentHandNum != handNum){
    	throw "Handnum doesn't match";
    }
	// TODO(from yuzisee): Assert that currentHandNum === handNum and otherwise tell the user something went wrong

	res.json(global.pokerai.getHoleCards(pokeraiInstance, seatNum));
};

exports.performAction = function(req, res){

	var tableid = req.params.tableid;
	var handNum = req.params.handNum;
	var pokeraiInstance = global.tables[tableid]['instance'];

    var currentHandNum = global.pokerai.getStatus(pokeraiInstance).currentHand;
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

exports.getActionSituation = function(req, res){

    var tableid = req.params.tableid;
    var handNum = req.params.handNum;

    res.json(global.tables[tableid]['hand'][handNum]['actionSituation'])
};

