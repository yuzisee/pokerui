{
  "targets": [
    {
      "target_name": "pokerai",
      "dependencies": ["libholdem"],
      "include_dirs": ['../../../pokerai/'],
      "sources": [ "addon.cc" ]
    },
    {
      "target_name": "libholdem",
      "type": "static_library",
      "sources": [ '<!@(ls -1 ../../../pokerai/holdem/src/*.cpp)' ]
    }
  ]
}
