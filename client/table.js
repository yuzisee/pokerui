angular.module('pokerui', ['ngResource'])
	.factory('User', function($resource){
		return $resource('/api/user/:userId', {userId:'@id'});
	})
	.factory('Table', function($resource){
		return $resource(
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
	})
	.controller('PkTable', function PkTable($scope, $timeout, $http, User, Table) {

		$http.get('/api/userid').then(function(res){
			$scope.user = new User(res.data);
			$scope.user.$get();
		});
		
		$scope.tableId = window.location.pathname.split('/table/')[1];
		(function tick() {
			var table = Table.get(
				{tableId: $scope.tableId}, 
				function(table){
					$scope.table = table;
					$timeout(tick, 3000);
				});
			}
		)();
		


		$scope.saveUser = function(user){
			user.$save(function(user){
				$scope.user = user;
			});
		}

		$scope.joinTable = function(){
			$scope.table.$join(function(table){
				$scope.table = table;
			});
		}
	}
);