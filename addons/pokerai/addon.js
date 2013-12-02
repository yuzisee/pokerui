var addon = require('./build/Release/pokerai');

var obj1 = addon.startTable('MYTABLE.txt', 1500, [{'id': 'Nav', 'bot': false}, {'id': 'Joseph', 'bot': false}]); //, null]);
console.log(obj1);

console.log(addon.getActionSituation(obj1, 1));
console.log(addon.getStatus(obj1));

console.log(addon.getHoleCards(obj1, 0)); // Nav's seat
console.log(addon.getHoleCards(obj1, 1)); // Joseph's seat

console.log(addon.performAction(obj1, {'_playerId': 'Nav', '_seatNumber': 0, '_action': 'raiseTo', 'amount': 50.0}));
console.log(addon.getStatus(obj1));

console.log(addon.getActionSituation(obj1, 1));
console.log(addon.performAction(obj1, {'_playerId': 'Joseoh', '_seatNumber': 1, '_action': 'callTo', 'amount': 50.0}));

console.log(addon.getActionSituation(obj1, 1));
console.log(addon.getStatus(obj1));
console.log(addon.getOutcome(obj1, 1));

console.log("Check-check on flop. Note that the dealer goes last in heads-up, so Joseph acts first now");
console.log(addon.performAction(obj1, {'_playerId': 'Joseoh', '_seatNumber': 1, '_action': 'check', 'amount': 0.0}));
console.log(addon.getStatus(obj1));
console.log(addon.getActionSituation(obj1, 1));
console.log(addon.performAction(obj1, {'_playerId': 'Nav', '_seatNumber': 0, '_action': 'check', 'amount': 0.0}));
console.log(addon.getActionSituation(obj1, 1));
// Check-check on turn
console.log(addon.performAction(obj1, {'_playerId': 'Joseoh', '_seatNumber': 1, '_action': 'check', 'amount': 0.0}));
console.log(addon.getActionSituation(obj1, 1));
console.log(addon.performAction(obj1, {'_playerId': 'Nav', '_seatNumber': 0, '_action': 'check', 'amount': 0.0}));
// Check-check on river
console.log(addon.performAction(obj1, {'_playerId': 'Joseoh', '_seatNumber': 1, '_action': 'check', 'amount': 0.0}));
console.log(addon.performAction(obj1, {'_playerId': 'Nav', '_seatNumber': 0, '_action': 'check', 'amount': 0.0}));


var outcome1 = addon.getOutcome(obj1, 1);

console.log(outcome1);
console.log("But what are the cards?")
console.log(outcome1['handsRevealed']);

console.log("################# START NEW HAND ##################\n");

console.log(addon.getActionSituation(obj1, 2));
console.log(addon.getStatus(obj1));

console.log(addon.getHoleCards(obj1, 0)); // Nav's seat
console.log(addon.getHoleCards(obj1, 1)); // Joseph's seat

console.log(addon.performAction(obj1, {'_playerId': 'Joseoh', '_seatNumber': 1, '_action': 'raiseTo', 'amount': 12.01}));

console.log(addon.getActionSituation(obj1, 1));
console.log(addon.getStatus(obj1));

var rsp1 = addon.shutdownTable(obj1);

console.log(rsp1);
