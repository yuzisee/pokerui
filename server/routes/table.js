
exports.newTable = function(req, res, next){
    var tableId = randomStr(5);
    global.tables[tableId] = {
        'id': tableId,
        'players': [], // Seated players
        'totalSeats': global.pokerai.getMaxSeats(),
        'hands' = []
    };

    console.log('Created table ' + tableId);

    //req.session.lastTableId = tableId; // Remember the last table you created in case you disconnect right there
    res.json(global.tables[tableId]);
};

var crypto = require('crypto');
 
function randomStr(length) {
  // Start with base64, convert to a nicer base32
  var blocks = 2;
  var base64str = crypto.randomBytes(blocks*3).toString('base64');
  return base64str.toLowerCase()
      .replace('0','2')
      .replace('1','3')
      .replace('5','4')
      .replace('8','6')
      .replace('+','7')
      .replace('/','9');
}
