var addon = require('./build/Release/pokerai');

var obj1 = addon.createTable('hello');
var obj2 = addon.createTable('world');
console.log(obj1.msg+' '+obj2.msg); // 'hello world'

