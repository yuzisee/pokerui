
/*
 * GET home page.
 */

exports.table = function(req, res){
  // res.render('index', { title: 'Express' });
  res.sendfile('../client/index.html');
};