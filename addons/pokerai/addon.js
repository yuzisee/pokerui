var addon = require('./build/Release/pokerai');

var obj1 = addon.startTable('MYTABLE', 1500);
var obj2 = addon.startTable('yourtable', 0.2);
console.log(obj1);
console.log(obj2);

var rsp1 = addon.shutdownTable(obj1);
var rsp2 = addon.shutdownTable(obj2);

console.log(rsp1);
console.log(rsp2);
