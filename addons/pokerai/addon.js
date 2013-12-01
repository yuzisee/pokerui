var addon = require('./build/Release/pokerai');

var obj1 = addon.createTable('hello');
var obj2 = addon.createTable('world');
console.log(obj1); // 'hello world'
console.log(obj2);

