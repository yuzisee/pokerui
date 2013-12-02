var addon = require('./build/Release/pokerai');

var obj1 = addon.startTable('MYTABLE.txt', 1500, [{'id': 'Nav', 'bot': false}, {'id': 'Joseph', 'bot': false}]); //, null]);
console.log(obj1);

console.log(addon.getActionSituation(obj1, 2));
console.log(addon.getStatus(obj1));

console.log(addon.getHoleCards(obj1, 1));

addon.performAction(obj1, {'_playerId': 'Nav', '_seatNumber': 0, '_action': 'raiseTo', 'amount': 50.0});

var outcome1 = addon.getOutcome(obj1, 4);

console.log(outcome1);
//console.log("But what are Nav's cards?")
//console.log(outcome1['handsRevealed']['Nav']['cards']);

var rsp1 = addon.shutdownTable(obj1);

console.log(rsp1);
