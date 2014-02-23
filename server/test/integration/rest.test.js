/**
 * Module dependencies
 */

var request = require('request');
var expect = require('expect.js');
var _ = require('lodash-node');

LOCAL_SERVER_URL = 'http://localhost:3000/';
TEST_USERNAME = 'test@a.com';


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

  it("should create a new table and let me sit at it, while updating my activeTables list", function(done){
    request.post(LOCAL_SERVER_URL + 'api/table', {jar:cookieJar}, function(err,resp,body){
      expect(resp.statusCode).to.eql(200);
      var responseBody = JSON.parse(body);
      var tableid = responseBody['id'];
      var totalSeats = responseBody['totalSeats'];
      expect(tableid).to.be.a('string'); // We get a valid table id
      console.log('tableid = ' + tableid);
      expect(4 <= tableid.length && tableid.length <= 5).to.be.ok(); // The table id has a correct length
      expect(responseBody).to.have.property('players'); // The table has a players list...
      expect(responseBody['players']).to.have.length(0); // ... but no seated players yet
      expect(totalSeats > 2).to.be.ok(); // Some valid number of seats

      // Okay, let's sit at this table
      request.post(LOCAL_SERVER_URL + 'api/table/' + tableid + '/join', {jar:cookieJar}, function(err,resp,body){
        expect(resp.statusCode).to.eql(200);
        console.log(body);
        var responseBody = JSON.parse(body);
        expect(tableid).to.be(responseBody['id']); // We should get back the same tableid we requested
        expect(totalSeats).to.be(responseBody['totalSeats']); // We should get back the same totalSeats as before
        expect(responseBody).to.have.property('players'); // The table has a players list...
        expect(responseBody['players']).to.eql([{'username': TEST_USERNAME, 'bot': false, 'seat': 0}]); // ... and now we're setting at it!

        // Okay, so did our user's activeTables get updated?
        request.get(LOCAL_SERVER_URL + 'api/session', {jar:cookieJar}, function(err,resp,body){
          expect(resp.statusCode).to.eql(200);
          var responseBody = JSON.parse(body);
          var expected = {'username': TEST_USERNAME, 'activeTables': {}};
          expected['activeTables'][tableid] = {'seat': 0};
          expect(responseBody).to.eql(expected); // Even if we disconnect at this point we can find this table again (and which seat we're in)
          done();
        });
      });
    });
  });

});
