
/*
 * Manage user and things
 */

exports.getName = function(req, res){
  res.json({name:req.session.playerName});
};

exports.setName = function(req, res){
  req.session.playerName = req.params.newName;
  exports.getName(req,res);
};