
/**
 * Module dependencies
 */

var request = require('request');
var assert = require('assert');

LOCAL_SERVER_URL = 'http://localhost:3000/'

describe('Run through an end-to-end test of the full REST API', function(){
  it("should create a new table", function(done){
    request.post(LOCAL_SERVER_URL + 'api/table', {form:{}}, function(err,resp,body){
      assert.equal(resp.statusCode, 200);
      var responseBody = JSON.parse(body);
      assert.equal(typeof responseBody['id'], 'string');
      assert.ok(responseBody['id'].length > 0); // We get an ID
      assert.equal(responseBody['players'].length, 0); // No seated players yet at an empty table
      assert.ok(responseBody['totalSeats'] > 2); // Some valid number of seats
      done();
    });
  });
});
