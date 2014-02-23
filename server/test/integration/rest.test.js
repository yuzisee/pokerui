
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
      console.log(resp);
      done();
    });
  });
});
