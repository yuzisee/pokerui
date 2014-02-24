/**
 * Module dependencies
 */

var crypto = require('crypto');
var request = require('request');
var expect = require('expect.js');
var _ = require('lodash-node');

LOCAL_SERVER_URL = 'http://localhost:3000/';

function CreatePlayerForTestWithUsername(username) {
   var cookieJar = request.jar(); // My own cookie jar for my session
   return {
      'getUsername': function() {
         return username;
      }
      ,
      'login': function(callback) {
         request.post(LOCAL_SERVER_URL + 'api/login', {form:{'username': username}, jar:cookieJar}, function(err,resp,body){
            expect(resp.statusCode).to.eql(200);
            //console.log(resp);
            callback(JSON.parse(body));
         });
      }
      ,
      'get': function(apiurl, callback) {
         request.get(LOCAL_SERVER_URL + apiurl, {jar:cookieJar}, function(err,resp,body){
            expect(resp.statusCode).to.eql(200);
            callback(JSON.parse(body));
         });
       }
   };
};

function CreatePlayerForTest() {
   var newUsername = crypto.randomBytes(2).toString('hex') + '@' + crypto.randomBytes(4).toString('hex') + '.com';
   return CreatePlayerForTestWithUsername(newUsername);
}

function CreateTableForTest(callback) {
   request.post(LOCAL_SERVER_URL + 'api/table', function(err,resp,body){
      expect(resp.statusCode).to.eql(200);
      var responseBody = JSON.parse(body);
      callback(responseBody);
   });
};
 


var player1 = CreatePlayerForTest();
var player2 = CreatePlayerForTest(); // Separate cookie for the second player

describe('end-to-end test of the full REST API', function(){
  it("should set up our session and initialize our user", function(done){
    player1.login(function(responseBody){
      //console.log(responseBody);
      expect(responseBody['username']).to.eql(player1.getUsername()); // The server has picked up our username
      expect(responseBody['activeTables']).to.eql({}); // We have no active tables yet, of course.
      done();
    });
  });

  it("should retain our session and give us the same user data back", function(done){
    player1.get('api/session', function(responseBody){
      expect(responseBody['username']).to.eql(player1.getUsername()); // The server remembers our username by session
      expect(responseBody['activeTables']).to.eql({}); // We have no active tables yet, of course.
      done();
    });
  });

  var lastExpectedSessionState;
  var table;
  it("should create a new table and let me sit at it, while updating my activeTables list", function(done){
     CreateTableForTest(function(newTable) {
        table = newTable;
        expect(table['id']).to.be.a('string'); // We get a valid table id
        console.log('tableId = ' + table['id']);
        expect(table.id).to.have.length(8); // The table id has a correct length
        expect(newTable).to.have.property('players'); // The table has a players list...
        expect(newTable['players']).to.have.length(0); // ... but no seated players yet
        expect(newTable.totalSeats > 2).to.be.ok(); // Some valid number of seats

        console.log("Okay, let's sit at this table");
        player1.post('api/table' + table.id + '/join', function(responseBody){
           expect(table.id).to.be(responseBody['id']); // We should get back the same tableId we requested
           expect(table.totalSeats).to.be(responseBody['totalSeats']); // We should get back the same totalSeats as before
           expect(responseBody).to.have.property('players'); // The table has a players list...
           expect(responseBody['players']).to.eql([{'username': player1.getUsername(), 'bot': false, 'seat': 0}]); // ... and now we're sitting at it!
        
           player1.get('api/session', function(responseBody){
              lastExpectedSessionState = {'username': player1.getUsername(), 'activeTables': {}};
              lastExpectedSessionState['activeTables'][tableId] = {'seat': 0};
              expect(responseBody).to.eql(lastExpectedSessionState); // Even if we disconnect at this point we can find this table again (and which seat we're in)
              done();
           });
        });
     });
  });

  var player1Again = CreatePlayerForTestWithUsername(player1.getUsername()); // Reset cookie for the next request to simulate reconnection
  it("should allow us to reconnect if we lose our cookie and get a new one", function(done){
     // Okay, and can we get it back in this state if we disconnect right now?
     player1Again.login(function(responseBody) {
        expect(responseBody['username']).to.eql(TEST_USERNAME); // The server has picked up our username
        expect(responseBody).to.eql(lastExpectedSessionState); // We disconnected, and it still got us back
        done();
     });
  });

  it("should allow a second player to log in", function(done){
     player2.login(function(responseBody){
        expect(responseBody['username']).to.eql(player2.getUsername()); // The server has picked up our username
        expect(responseBody['activeTables']).to.eql({}); // We have no active tables yet, of course.
        done();
     });
  });

  it("should allow a second player to sit at the same table", function(done){
     player2.post('api/table/' + tableId + '/join', function(responseBody){
        expect(table.id).to.be(responseBody['id']); // We should get back the same tableId we requested
        expect(table.totalSeats).to.be(responseBody['totalSeats']); // We should get back the same totalSeats as always
        expect(responseBody).to.have.property('players'); // The table has a players list...
        expect(responseBody['players']).to.eql([
              {'username': player1.getUsername(), 'bot': false, 'seat': 0}
              ,
              {'username': player2.getUsername(), 'bot': false, 'seat': 1}
           ]); // ... and now we're both sitting at it!
        done();
     });
  });


  var handnum;
  it("should all run smoothly if player 2 starts the game", function(done){
     player1.post('api/table/' + tableId + '/start_game'), function(responseBody){
       // Verify that the game has started.
       handnum = responseBody['actionOn']['currentHand']
       expect(handnum).to.be.a('number');
       expect(responseBody['actionOn']['actionOn']).to.eql(player1.getUsername());
       done();
     });
  });

  var expectedActionSituation = {'actions': [], 'startingChips': {'preflop': {}}, 'startingPot': {}, 'dealerOn': player1.getUsername(), 'community': []};
  expectedActionSituation['actions'].push({'checkpoint': 'preflop'});
  expectedActionSituation['actions'].push({'_playerId': player1.getUsername(), '_seatNumber': 0, 'blind': true, 'amount': 0.01});
  expectedActionSituation['actions'].push({'_playerId': player2.getUsername(), '_seatNumber': 1, 'blind': true, 'amount': 0.02});
  expectedActionSituation['startingChips']['preflop'][player1.getUsername()] = 3.0;
  expectedActionSituation['startingChips']['preflop'][player2.getUsername()] = 3.0;
  
  it("should show a fresh table with the same number of chips to all players", function(done){
     player1.get('api/table/' + tableId, function(responseBody){
        expect(responseBody['actionOn']).to.eql({'currentHand': handnum, 'actionOn': player1.getUsername()});

        player1.get('api/table/' + tableId + '/hand/' + handnum, function(responseBody){
          
          expect(responseBody['actions']).to.eql(expectedActionSituation)
          // Verify that the game shows started for P2 as well
          done();
     });
  });

});
