#define BUILDING_NODE_EXTENSION
#include <node.h>


v8::Handle<v8::Value> CreateObject(const v8::Arguments& args) {
  v8::HandleScope scope;

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("msg"), args[0]->ToString());

  return scope.Close(obj);
}

void Init(v8::Handle<v8::Object> exports, v8::Handle<v8::Object> module) {
  module->Set(v8::String::NewSymbol("exports"),
      v8::FunctionTemplate::New(CreateObject)->GetFunction());
}

NODE_MODULE(addon, Init)
