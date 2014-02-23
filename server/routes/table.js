
exports.newTable = function(req, res, next){
    tableId = randomStr(5);
    global.tables[tableId] = {
        'id': tableId,
        'players': {},
        'state' : 'WAITING'
    };

    req.session.lastTableId = tableId;
    res.redirect('/table/'+tableId);
};

var bases = require('bases');
var crypto = require('crypto');
 
// From: https://gist.github.com/aseemk/3095925
function randomStr(length) {
    var maxNum = Math.pow(62, length);
    var numBytes = Math.ceil(Math.log(maxNum) / Math.log(256));
    if (numBytes === Infinity) {
        throw new Error('Length too large; caused overflow: ' + length);
    }
 
    do {
        var bytes = crypto.randomBytes(numBytes);
        var num = 0
        for (var i = 0; i < bytes.length; i++) {
            num += Math.pow(256, i) * bytes[i];
        }
    } while (num >= maxNum);
 
    return bases.toBase62(num);
}
