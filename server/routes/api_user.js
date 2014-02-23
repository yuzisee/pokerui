
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

exports.getUser = function(req, res) {
   if(!req.session.userid) {
      req.session.userid = (""+Math.random()).substring(2,7);
      global.users.push(req.session.userid);
   }

   res.json({id:req.session.userid});
};
*/

exports.getUser = function(req, res) {
   //console.log('getUser()');

   if (!req.session.username){
      throw 'Please create a session first. For now you just POST to /api/login with {"username": my_email_address}';
   }

   //console.log(req.session);

   var user = {
      'username': req.session.username,
      // What table am I currently sitting at?
      // (e.g. if you disconnect and reconnect, using your session ID we should know which tables you need to reconnect to)
      'activeTables': global.users[req.session.username]['activeTables']
   }

   res.json(user);
};

// For now, just set your username
exports.updateUser = function(req, res){
   var username = req.body.username;
   console.log('updateUser()');
   console.log(req.body);
   if (typeof username != 'string') {
      throw 'POST data must be a JSON object that contains the key "username" with a string value';
   }
   if (username.length > 3) {
      console.log('We have a valid username. Claim it!');
      console.log(req.session);
      req.session.username = username;
      if (!(username in global.users)) {
          console.log('this user does not already exist, go ahead and make a blank one');
          global.users[username] = {'activeTables': {}}
          console.log(global.users);
      }
      console.log('okay, return the user now');
      exports.getUser(req, res)
   } else {
      throw 'username must be more than 3 characters';
   }
};



