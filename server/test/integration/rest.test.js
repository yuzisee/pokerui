/**
 * Module dependencies
 */

var crypto = require('crypto');
var request = require('request');
var expect = require('expect.js');
var _ = require('lodash-node');

LOCAL_SERVER_URL = 'http://localhost:3000/';

 
TEST_USERNAME = crypto.randomBytes(2).toString('hex') + '@' + crypto.randomBytes(4).toString('hex') + '.com';
TEST_USERNAME2 = crypto.randomBytes(2).toString('hex') + '@' + crypto.randomBytes(4).toString('hex') + '.com';

describe('end-to-end test of the full REST API', function(){
  // Use one cookie jar for the entire test
  var cookieJar = request.jar();

  it("should set up our session and initialize our user", function(done){
    request.post(LOCAL_SERVER_URL + 'api/login', {form:{'username': TEST_USERNAME}, jar:cookieJar}, function(err,resp,body){
      expect(resp.statusCode).to.eql(200);
      var responseBody = JSON.parse(body);
      //console.log(resp);
      //console.log(responseBody);
      expect(responseBody['username']).to.eql(TEST_USERNAME); // The server has picked up our username
      expect(responseBody['activeTables']).to.eql({}); // We have no active tables yet, of course.
      done();
    });
  });

  it("should retain our session and give us the same user data back", function(done){
    request.get(LOCAL_SERVER_URL + 'api/session', {jar:cookieJar}, function(err,resp,body){
      expect(resp.statusCode).to.eql(200);
      var responseBody = JSON.parse(body);
      expect(responseBody['username']).to.eql(TEST_USERNAME); // The server remembers our username by session
      expect(responseBody['activeTables']).to.eql({}); // We have no active tables yet, of course.
      done();
    });
  });

  var lastExpectedSessionState;
  var tableId;
  var totalSeats;

  it("should create a new table and let me sit at it, while updating my activeTables list", function(done){
    request.post(LOCAL_SERVER_URL + 'api/table', {jar:cookieJar}, function(err,resp,body){
      expect(resp.statusCode).to.eql(200);
      var responseBody = JSON.parse(body);
      totalSeats = responseBody['totalSeats'];
      tableId = responseBody['id'];
      expect(tableId).to.be.a('string'); // We get a valid table id
      console.log('tableId = ' + tableId);
      expect(tableId).to.have.length(8); // The table id has a correct length
      expect(responseBody).to.have.property('players'); // The table has a players list...
      expect(responseBody['players']).to.have.length(0); // ... but no seated players yet
      expect(totalSeats > 2).to.be.ok(); // Some valid number of seats

      console.log("Okay, let's sit at this table");
      request.post(LOCAL_SERVER_URL + 'api/table/' + tableId + '/join', {jar:cookieJar}, function(err,resp,body){
        expect(resp.statusCode).to.eql(200);
        console.log(body);
        var responseBody = JSON.parse(body);
        expect(tableId).to.be(responseBody['id']); // We should get back the same tableId we requested
        expect(totalSeats).to.be(responseBody['totalSeats']); // We should get back the same totalSeats as before
        expect(responseBody).to.have.property('players'); // The table has a players list...
        expect(responseBody['players']).to.eql([{'username': TEST_USERNAME, 'bot': false, 'seat': 0}]); // ... and now we're sitting at it!

        console.log("Okay, so did our user's activeTables get updated?");
        request.get(LOCAL_SERVER_URL + 'api/session', {jar:cookieJar}, function(err,resp,body){
           expect(resp.statusCode).to.eql(200);
           console.log(body);
           var responseBody = JSON.parse(body);
           lastExpectedSessionState = {'username': TEST_USERNAME, 'activeTables': {}};
           lastExpectedSessionState['activeTables'][tableId] = {'seat': 0};
           expect(responseBody).to.eql(lastExpectedSessionState); // Even if we disconnect at this point we can find this table again (and which seat we're in)
           done();
        });

     
      });
    });
  });

  it("should allow us to reconnect if we lose our cookie and get a new one", function(done){
     // Okay, and can we get it back in this state if we disconnect right now?
     var newCookieJar = request.jar(); // Reset cookie for the next request to simulate reconnection
     request.post(LOCAL_SERVER_URL + 'api/login', {form:{'username': TEST_USERNAME}, jar:newCookieJar}, function(err,resp,body){
        expect(resp.statusCode).to.eql(200);
        var responseBody = JSON.parse(body);
        //console.log(resp);
        //console.log(responseBody);
        expect(responseBody['username']).to.eql(TEST_USERNAME); // The server has picked up our username
        expect(responseBody).to.eql(lastExpectedSessionState); // We disconnected, and it still got us back
        done();
     });
  });

  var cookieJarP2 = request.jar(); // Separate cookie for the second player
  it("should allow a second player to log in", function(done){
     request.post(LOCAL_SERVER_URL + 'api/login', {form:{'username': TEST_USERNAME2}, jar:cookieJarP2}, function(err,resp,body){
        expect(resp.statusCode).to.eql(200);
        var responseBody = JSON.parse(body);
        //console.log(resp);
        //console.log(responseBody);
        expect(responseBody['username']).to.eql(TEST_USERNAME2); // The server has picked up our username
        expect(responseBody['activeTables']).to.eql({}); // We have no active tables yet, of course.
        done();
     });
  });

  it("should allow a second player to sit at the same table", function(done){
        
     request.post(LOCAL_SERVER_URL + 'api/table/' + tableId + '/join', {jar:cookieJarP2}, function(err,resp,body){
        expect(resp.statusCode).to.eql(200);
        var responseBody = JSON.parse(body);
        expect(tableId).to.be(responseBody['id']); // We should get back the same tableId we requested
        expect(totalSeats).to.be(responseBody['totalSeats']); // We should get back the same totalSeats as always
        expect(responseBody).to.have.property('players'); // The table has a players list...
        expect(responseBody['players']).to.eql([
              {'username': TEST_USERNAME, 'bot': false, 'seat': 0}
              ,
              {'username': TEST_USERNAME2, 'bot': false, 'seat': 1}
           ]); // ... and now we're both sitting at it!
        done();
     });
  });

  it("should all run smoothly if player 2 starts the game", function(done){
     request.post(LOCAL_SERVER_URL + 'api/table/' + tableId + '/start_game', {jar:cookieJarP2}, function(err,resp,body){
       expect(resp.statusCode).to.eql(200);
       console.log(body);
       done();
     });
  });

});
