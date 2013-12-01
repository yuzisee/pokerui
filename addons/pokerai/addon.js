var addon = require('./build/Release/pokerai');

var obj1 = addon.startTable('MYTABLE', 1500, [{'id': 'Nav', 'bot': false}, null, null, {'id': 'Joseph', 'bot': true}, null]);
console.log(obj1);

var rsp1 = addon.shutdownTable(obj1);

console.log(rsp1);
