#define BUILDING_NODE_EXTENSION
#include <node.h>

#include <stdint.h>
#include <string>
#include <vector>
#include <cstdio>

// TODO(from yuzisee): Replace with actual holdem engine
class Test {
  public:
    Test(std::string onDiskId, double startingChips)
    :
    //fA(startingChips)
    //,
    fOnDiskId(onDiskId)
    ,
    fHandNum(0)
    {}
    ~Test() {}

    const std::string &onDiskId() const {
        return fOnDiskId;
    }

    int handNum() const {
      return fHandNum;
    }

    void incrHandNum() {
      ++fHandNum;
    }

  private:
    //const double fA;
    const std::string fOnDiskId;
    int fHandNum;
};

// Returns v8LittleEndianPtr.IsEmpty() on error.
static v8::Handle<v8::Array> marshallPtr(const Test * const test) {

  printf("marshallPtr(%p)\n", test);

  const uintptr_t instance = reinterpret_cast<uintptr_t>(test);

  std::vector<uint32_t> cLittleEndianPtr; // 4 bytes: 0xffffffff mask
  uintptr_t i = instance;
  while(i) {
    cLittleEndianPtr.push_back(i & 0xffffffff);
    i >>= 32;
  }

  v8::Handle<v8::Array> v8LittleEndianPtr = v8::Array::New(cLittleEndianPtr.size());
  if (!v8LittleEndianPtr.IsEmpty()) {
    
    for(size_t k=0; k<cLittleEndianPtr.size(); ++k) {
      v8LittleEndianPtr->Set(k, v8::Uint32::New(cLittleEndianPtr[k]));
    }

  }

  return v8LittleEndianPtr;

}

// Return 0 on error
static const Test * unmarshallPtr(const v8::Handle<v8::Array> &v8LittleEndianPtr)
{
  uintptr_t instance = 0; // 4 bytes: 0xffffffff mask
  for(size_t k=v8LittleEndianPtr->Length(); k > 0; --k) {

    if (!v8LittleEndianPtr->Get(k-1)->IsUint32()) {
      return 0;
    }

    const uint32_t i = v8LittleEndianPtr->Get(k-1)->Uint32Value();
    instance <<=32;
    instance |= i;
  }

  const Test * const test = reinterpret_cast<const Test * const>(instance);

  printf("unmarshallPtr = %p\n", test);

  return test;
}

// Read args[0] and interpret as a ``Test *`` handle
// Returns 0 on error
static const Test * readFirstArgumentAsTable(const v8::Arguments& args) {

  // === Validate arguments

  if (!args[0]->IsObject()) {
    return 0;
  }

  v8::Local<v8::Object> arg0 = args[0]->ToObject();

  if (!arg0->Get(v8::String::NewSymbol("id"))->IsString()) {
    return 0;
  }

  if (!arg0->Get(v8::String::NewSymbol("_instance"))->IsArray()) {
    return 0;
  }



  // === Read arguments

  v8::Local<v8::String> argOnDiskId = arg0->Get(v8::String::NewSymbol("id"))->ToString();
  v8::String::Utf8Value v8OnDiskId(argOnDiskId);
  // Utf8Value's operator*() gives you a null terminated character array.
  std::string cOnDiskId(*v8OnDiskId);

  v8::Handle<v8::Array> v8LittleEndianPtr = v8::Handle<v8::Array>::Cast(
      arg0->Get(v8::String::NewSymbol("_instance"))
    );

  // === Unmarshall/unserialize table instance pointer

  const Test * const test = unmarshallPtr(v8LittleEndianPtr);

  // === Health check!

  if (!(cOnDiskId == test->onDiskId())) {
    return 0;
  }


  // === Return result

  return test;

}


// This function will be wrapped with 
//   v8::FunctionTemplate::New(StartTable)->GetFunction()
// to return a handle that v8 can invoke.
v8::Handle<v8::Value> StartTable(const v8::Arguments& args) {
  v8::HandleScope scope;

  // === Validate arguments
  
  if (args.Length() != 3) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Wrong number of arguments")));
    return scope.Close(v8::Undefined());
  }

  if (!args[0]->IsString()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a string")));
    return scope.Close(v8::Undefined());
  }

  if (!args[1]->IsNumber()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Second argument must be a number")));
    return scope.Close(v8::Undefined());
  }

  if (!args[2]->IsArray()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Third argument must be an array of seats")));
    return scope.Close(v8::Undefined());
  }

  v8::Handle<v8::Array> seats = v8::Handle<v8::Array>::Cast( args[2]->ToObject() );

  // === Read arguments

  v8::Local<v8::String> argOnDiskId = args[0]->ToString();
  v8::String::Utf8Value v8OnDiskId(argOnDiskId);
  // Utf8Value's operator*() gives you a null terminated character array.
  std::string cOnDiskId(*v8OnDiskId);

  double startingChips = args[1]->NumberValue();


  for(size_t k=0; k<seats->Length(); ++k) {


    if (seats->Get(k)->IsNull() || seats->Get(k)->IsUndefined()) {

      // Don't fill this seat!
      printf("Seat %lu left empty.\n", k); 

    } else {
      if (seats->Get(k)->IsObject()) {

        v8::Local<v8::Object> filledSeat = seats->Get(k)->ToObject();
        v8::Local<v8::Value> argPlayerIdent = filledSeat->Get(v8::String::NewSymbol("id"));
        v8::Local<v8::Value> argBot = filledSeat->Get(v8::String::NewSymbol("bot"));

        if (argPlayerIdent->IsString() && argBot->IsBoolean()) {

          v8::String::Utf8Value v8PlayerIdent( argPlayerIdent->ToString() );
          std::string cPlayerIdent(*v8PlayerIdent);

          bool cBot = argBot->BooleanValue();

          printf("Seat %lu requested! ident=%s bot=%d\n", k, cPlayerIdent.c_str(), cBot); 

        } else {
          v8::ThrowException(v8::Exception::TypeError(v8::String::New("Filled seats must specify .id and .bot")));
          return scope.Close(v8::Undefined());
        }
      } else {
        v8::ThrowException(v8::Exception::TypeError(v8::String::New("Each seat must be null, undefined, or a valid Object containing .bot and .playerId")));
        return scope.Close(v8::Undefined());
      }
    }


  }


  // === Construct table

  const Test * const test = new Test(cOnDiskId, startingChips);

  // === Marshall/serialize table instance pointer
 
  v8::Handle<v8::Array> v8LittleEndianPtr = marshallPtr(test);
  const Test * const verify = unmarshallPtr(v8LittleEndianPtr);

  // Couldn't create the array...
  if (v8LittleEndianPtr.IsEmpty()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("v8 failed creating an array")));
    return scope.Close(v8::Undefined());
  }


  if (verify != test) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Self-test failed.")));
    return scope.Close(v8::Undefined());
  }

  // === Return result

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("id"), argOnDiskId);
  obj->Set(v8::String::NewSymbol("_instance"), v8LittleEndianPtr);

  return scope.Close(obj);
}

v8::Handle<v8::Value> ShutdownTable(const v8::Arguments& args) {
  v8::HandleScope scope;

  // === Validate arguments

  if (args.Length() != 1) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Wrong number of arguments")));
    return scope.Close(v8::Undefined());
  }

  // === Read arguments

  const Test * const test = readFirstArgumentAsTable(args);

  if (!test) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object containg .id (must be a string) and ._instance (must be an array of uint32 values)")));
    return scope.Close(v8::Undefined());
  }



  // === Destruct table

  delete test;

  // === Return result

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("success"), v8::Boolean::New(true));

  return scope.Close(obj);
}

// Create a JSON object of the form:
//  {'id': 'Nav', 'action': 'raiseTo', 'amount': 5.0}
static v8::Local<v8::Object> betToJson(std::string id, std::string action, double amount) {
  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("id"), v8::String::New(id.c_str()));
  obj->Set(v8::String::NewSymbol("action"), v8::String::New(action.c_str()));
  obj->Set(v8::String::NewSymbol("amount"), v8::Number::New(amount));
  return obj;
}


// Create a JSON object of the form:
//  {'checkpoint': 'flop'}
static v8::Local<v8::Object> checkpointToJson(std::string name) {
  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("checkpoint"), v8::String::New(name.c_str()));
  return obj;
}

v8::Handle<v8::Value> GetActionSituation(const v8::Arguments& args) {
  v8::HandleScope scope;

  // === Validate arguments

  if (args.Length() != 2) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Wrong number of arguments")));
    return scope.Close(v8::Undefined());
  }

  if (!args[1]->IsUint32()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Second argument must be an unsigned integer")));
    return scope.Close(v8::Undefined());
  }

  // === Read arguments

  const Test * const test = readFirstArgumentAsTable(args);

  if (!test) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object containg .id (must be a string and must match the onDiskId provided to startTable) and ._instance (must be an array of uint32 values)")));
    return scope.Close(v8::Undefined());
  }

  const uint32_t handNum = args[1]->Uint32Value();

  // === Populate bets

  v8::Handle<v8::Array> bets = v8::Array::New(5);
  bets->Set(0, betToJson("Nav", "smallBlind", 5.0));
  bets->Set(1, betToJson("Joseph", "bigBlind", 10.0));
  bets->Set(2, betToJson("Nav", "call", 10.0));
  bets->Set(3, checkpointToJson("flop"));
  bets->Set(4, betToJson("Nav", "raiseTo", 10.0));
 
  // === Populate chipCounts

  v8::Handle<v8::Object> chipCounts = v8::Object::New();
  chipCounts->Set(v8::String::NewSymbol("Nav"), v8::Number::New(500.0));
  chipCounts->Set(v8::String::NewSymbol("Joseph"), v8::Number::New(450.0));
 
 
  // === Populate community

  v8::Handle<v8::Array> community = v8::Array::New(3);
  community->Set(0, v8::String::New("2h"));
  community->Set(1, v8::String::New("Th"));
  community->Set(2, v8::String::New("2c"));
 


  // === Return result


  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("pot"), bets);
  obj->Set(v8::String::NewSymbol("chipCounts"), chipCounts);
  obj->Set(v8::String::NewSymbol("dealerOn"), v8::String::New("Nav"));
  obj->Set(v8::String::NewSymbol("community"), community);

  return scope.Close(obj);

}

// This creates the prototype/global/static (e.g. pokerai.exports.startTable())
void Init(v8::Handle<v8::Object> exports) {

  
/*
  pokerai.exports.startTable(tableId, 1500, [{'id': 'playerId1', 'bot': false}, {'id': 'playerId2', 'bot': true}, None, None, {'id': 'playerId3', 'bot': false}, ...])
  JSON Response:
  {
    'id': <onDiskId>
    '_instance': <instanceHandle>
  }
*/
  exports->Set(v8::String::NewSymbol("startTable"),
     v8::FunctionTemplate::New(StartTable)->GetFunction());
  
/*
  pokerai.exports.shutdownTable({ 'id': <onDiskId>, '_instance': <instanceHandle> })
  JSON Response:
  {
    'success': True/False
  }
*/
  exports->Set(v8::String::NewSymbol("shutdownTable"),
     v8::FunctionTemplate::New(ShutdownTable)->GetFunction());

 
/*
  pokerai.exports.getActionSituation({ 'id': <onDiskId>, '_instance': <instanceHandle> }, handNum)
  JSON Response:
  {
    'bets': [
            {'id': 'Nav', 'action': 'smallBlind', 'amount': 5.0},
            {'id': 'Joseph', 'action': 'bigBlind', 'amount': 10.0},
            {'id': 'bot1', 'action': 'fold', 'amount': -1},
            {'id': 'bot2', 'action': 'raiseTo', 'amount': 25.0},
            {'id': 'bot3', 'action': 'call', 'amount': 25.0},
            ...
            {'checkpoint': 'flop'},
            {'id': 'Nav', 'action': 'check', 'amount': 0.0}
           ],
    'chipCounts': {
            'id1': 500.0,
            ...
            }
    'dealerOn': <playerId>
    'community': ['Kh', 'Ts', '9h'],
  }
*/
  exports->Set(v8::String::NewSymbol("getActionSituation"),
     v8::FunctionTemplate::New(GetActionSituation)->GetFunction());

}

// Our target is named "pokerai". See binding.gyp for more
NODE_MODULE(pokerai, Init)
// TODO(from yuzisee): What thread does this run on? The javascript thread?

