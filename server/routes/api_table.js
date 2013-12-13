
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

exports.joinTable = function(data){
	var tableid = data.tableid;
    global.tables[tableid]['players'][this.id] = {
    	id : this.id,
    	name : req.session.name
    };
    emitOnTable(tableid, 
    {
		'event': 'join',
		'userid': this.id,
		'table': global.tables[tableid]
		// 'name': this.username 
	});
// 	var tableid = req.params.tableid;
//     global.tables[tableid]['players'][req.session.userid] = {
//     	id : req.session.userid,
//     	name : req.session.name
//     };

// 	res.json(global.tables[tableid]);

// 	for(idx in global.table_sockets[tableid]){
		
// 		global.table_sockets[tableid][idx]
// 			.emit('table:' + tableid, 
// 				{
// 					'event': 'join',
// 					'userid': req.session.userid,
// 					'name': req.session.name 
// 				}
// 		);
// 	}
};

exports.getTable = function(req, res){
	res.json(global.tables[req.params.tableid]);
}

exports.updateTable = function(req, res){
	// userid = req.params.userid;
	// req.session.name = req.body.name;
	// exports.getUser(req, res)
};

exports.register = function(data){
	if(!global.table_sockets[data.tableid]){
		global.table_sockets[data.tableid] = [];
	}

	global.table_sockets[data.tableid].push(this);
	registerTableMethodsOnSocket(socket, data.tableid);
};

registerTableMethodsOnSocket = function(socket, tableid){
	prefix = "table:"+tableid+":";
	socket.on(prefix + "join", function(a,b,c){
		console.log(a,b,c)
	});
};

emitOnTable = function(tableid, data) {
	for(idx in global.table_sockets[tableid]){
		global.table_sockets[tableid][idx]
			.emit("table:"+tableid, data);
	}
};