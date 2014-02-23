
var path = require('path');


exports.loadTable = function(req, res, next){
    var tableId = req.params.tableid;

    if(req.session.lastTableId != tableId){
        console.log("WEIRD! we were last on table " + req.session.lastTableId);
    }
	console.log("TABLE ID: " + tableId);
  	res.sendfile(path.join(__dirname, "/../../client/table.html"));
};

