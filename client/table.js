angular.module('pokerui', ['ngResource'])
	.factory('User', function($resource){
		return $resource('/api/user/:userId', {userId:'@id'});
	})
	.factory('Table', function($rootScope, $resource){
		var tables = [];
		$rootScope.tables = tables;
		var TableResource = $resource(
			'/api/table/:tableId', 
			{
				tableId:'@id'
			},
			{
				join: { 
					method:'POST', 
					url	: '/api/table/:tableId/join'
				}
			}
		);
		return function(tableId, callback){
			var res = new TableResource.get({tableId:tableId}, function(table){
				tables.push(table);
				callback(table);
			});
		};
	})
	.factory('socket', function ($rootScope) {
		var socket = io.connect('http://localhost:3000');
		return {
			on: function (eventName, callback) {
				socket.on(eventName, function () {  
					var args = arguments;
					$rootScope.$apply(function () {
						callback.apply(socket, args);
					});
				});
			},
			emit: function (eventName, data, callback) {
				socket.emit(eventName, data, function () {
					var args = arguments;
					$rootScope.$apply(function () {
						if (callback) {
							callback.apply(socket, args);
						}
					});
				})
			}
		};
	})
	.controller('PkTable', function PkTable($scope, $timeout, User, Table, socket) {

		$scope.user = new User();
		$scope.user.$save({}, function(resource){
			$scope.user = resource;
		});

		$scope.tableid = window.location.pathname.split('/table/')[1];

		var table = Table($scope.tableid, function(table){
			$scope.table = table
		});
		
		socket.emit('table:register', {
			tableid: $scope.tableid
		});
		
		socket.on('table:' + $scope.tableid,  function (message) {
			console.log(message);
		});
		
		// debugger;
		// var table = new Table({tableId:$scope.tableId});
		// (function tick() {
			// var table = Table.get(
			// 	{tableId: $scope.tableId}, 
			// 	function(table){
			// 		$scope.table = table;
			// 		// $timeout(tick, 3000);
			// 	});
			// // }

			// var table = Table.get(
			// 	{tableId: $scope.tableId+"asd"}, 
			// 	function(table){
			// 		// $scope.table = table;
			// 		// $timeout(tick, 3000);
			// 	});
			// }
		// )();
		$scope.connect = function(){

		}


		$scope.saveUser = function(user){
			user.$save(function(user){
				$scope.user = user;
			});
		}

		$scope.joinTable = function(){
			console.log("Emiting on " + 'table:'+$scope.tableid+':join');
			socket.emit('table:'+$scope.tableid+':join');
			// $scope.table.$join(function(table){
			// 	$scope.table = table;
			// });
		}
	}
);