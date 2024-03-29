#define BUILDING_NODE_EXTENSION
#include <node.h>

// This function will be wrapped with 
//   v8::FunctionTemplate::New(CreateObject)->GetFunction()
// to return a handle that v8 can invoke.
v8::Handle<v8::Value> CreateObject(const v8::Arguments& args) {
  v8::HandleScope scope;

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("msg"), args[0]->ToString());

  return scope.Close(obj);
}

// This creates the prototype/global/static (e.g. pokerai.exports.createTable())
void Init(v8::Handle<v8::Object> exports) {
  exports->Set(v8::String::NewSymbol("createTable"),
     v8::FunctionTemplate::New(CreateObject)->GetFunction());
  // TODO(from yuzisee): What thread does this run on? The javascript thread?
}


NODE_MODULE(addon, Init)

