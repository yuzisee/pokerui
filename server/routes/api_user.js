
/*
 * Manage user and things
 */

exports.getAll = function(req, res){
     res.json(global.users);
};

/*
exports.postAll = function(req, res){
   if(!req.session.userid) {
      req.session.userid = (""+Math.random()).substring(2,7);
      global.users.push(req.session.userid);
   }

   req.params = {'userid': req.session.userid};
   exports.getUser(req, res);
};
*/


exports.getUser = function(req, res) {
   if(!req.session.userid) {
      req.session.userid = (""+Math.random()).substring(2,7);
      global.users.push(req.session.userid);
   }

   res.json({id:req.session.userid});
};

exports.getUser = function(req, res) {
   if (!req.session.username){
      throw 'Please create a session first. For now you just POST to /api/login with {"username": my_email_address}';
   }

   var user = {
      'name': req.session.username,
      // What table am I currently sitting at?
      // (e.g. if you disconnect and reconnect, using your session ID we should know which tables you need to reconnect to)
      'activeTables': global.users[req.session.username]['activeTables']
   }

   res.json(user);
};

// For now, just set your username
exports.updateUser = function(req, res){
   var username = req.body.username;
   if (typeof username != 'string') {
      throw 'POST data must be a JSON object that defines "username" as a string';
   }
   if (username.length > 3) {
      // We have a valid username. Claim it!
      req.session.username = username;
      // If this user doesn't already exist, go ahead and make a blank one
      if (!(username in global.users)) {
          global.users[username] = {'activeTables': {}}
      }
      // okay, return the user now
      exports.getUser(req, res)
   } else {
      throw 'username must be more than 3 characters';
   }
};



