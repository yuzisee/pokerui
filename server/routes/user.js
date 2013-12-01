
/*
 * Manage user and things
 */

exports.getAll = function(req, res){
  	res.json(global.users);
};

exports.postAll = function(req, res){
	if(!req.session.userid) {
		req.session.userid = (""+Math.random()).substring(2,7);
		global.users.push(req.session.userid);
	}

	req.params = {'userid': req.session.userid};
	exports.getUser(req, res);
};

exports.getUser = function(req, res){
	userid = req.params.userid;

	if (!req.session.name){
		req.session.name = "Unknown";
	}

	var user = {
		'id'  : userid,
		'name': req.session.name
	}

	res.json(user);
};

exports.postUser = function(req, res){
	// userid = req.params.userid;
	req.session.name = req.body.name;
	exports.getUser(req, res)
};