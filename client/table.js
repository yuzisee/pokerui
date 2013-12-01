angular.module('pokerui', ['ngResource'])
	.factory('User', function($resource){
		return $resource('/api/user/:userId', {userId:'@id'});
	})
	.controller('PkTable', function PkTable($scope, User) {

		$scope.user = new User();
		$scope.user.$save({}, function(resource){
			$scope.user = resource;
		});

		$scope.save = function(user){
			user.$save(function(user){
				$scope.user = user;
			});
		}
	}
);