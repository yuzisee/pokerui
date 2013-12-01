#define BUILDING_NODE_EXTENSION
#include <node.h>

#include <stdint.h>
#include <string>
#include <vector>
#include <cstdio>

class Test {
  public:
    Test(std::string onDiskId, double startingChips)
    :
    fA(startingChips)
    ,
    fOnDiskId(onDiskId)
    {}
    ~Test() {}

    const std::string &onDiskId() const {
        return fOnDiskId;
    }

  private:
    const double fA;
    const std::string fOnDiskId; 
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
static const Test * const unmarshallPtr(v8::Handle<v8::Array> v8LittleEndianPtr)
{
  uintptr_t instance = 0; // 4 bytes: 0xffffffff mask
  for(size_t k=v8LittleEndianPtr->Length(); k > 0; --k) {

    if (!v8LittleEndianPtr->Get(0)->IsUint32()) {
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

// This function will be wrapped with 
//   v8::FunctionTemplate::New(StartTable)->GetFunction()
// to return a handle that v8 can invoke.
v8::Handle<v8::Value> StartTable(const v8::Arguments& args) {
  v8::HandleScope scope;

  // === Validate arguments
  
  if (args.Length() != 2) {
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

  // === Read arguments

  v8::Local<v8::String> argOnDiskId = args[0]->ToString();
  v8::String::Utf8Value v8OnDiskId(argOnDiskId);
  // Utf8Value's operator*() gives you a null terminated character array.
  std::string cOnDiskId(*v8OnDiskId);

  double startingChips = args[1]->NumberValue();


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

  if (!args[0]->IsObject()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object")));
    return scope.Close(v8::Undefined());
  }

  v8::Local<v8::Object> arg0 = args[0]->ToObject();

  if (!arg0->Get(v8::String::NewSymbol("id"))->IsString()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New(".id must be a string")));
    return scope.Close(v8::Undefined());
  }

  if (!arg0->Get(v8::String::NewSymbol("_instance"))->IsArray()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("._instance must be an array")));
    return scope.Close(v8::Undefined());
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

  if (!test) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("._instance must contain uint32 values")));
    return scope.Close(v8::Undefined());
  }

  // === Destruct table

  if (cOnDiskId == test->onDiskId()) {
    // Sanity check passed!
    delete test;
  } else {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Data corruption: onDiskId doesn't match")));
    return scope.Close(v8::Undefined());
  }


  // === Return result

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("success"), v8::Boolean::New(true));

  return scope.Close(obj);
}

// This creates the prototype/global/static (e.g. pokerai.exports.startTable())
void Init(v8::Handle<v8::Object> exports) {

  
/*
  pokerai.exports.startTable('tableId', 1500) // TODO ['playerId1,', 'playerId2', None, None, 'playerId3', ...]
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
}

// Our target is named "pokerai". See binding.gyp for more
NODE_MODULE(pokerai, Init)
// TODO(from yuzisee): What thread does this run on? The javascript thread?

