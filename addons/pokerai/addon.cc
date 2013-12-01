#define BUILDING_NODE_EXTENSION
#include <node.h>

#include <stdint.h>
#include <string>
#include <vector>
#include <cstdio>

#include "holdem/src/arena.h"

static const double CHIP_DENOM = 0.01; // Minimum bet denomination

class PokerAiInstance {

public:
  PokerAiInstance(std::string &cOnDiskId, double startingChips)
  :
  fOnDiskId(cOnDiskId)
  ,
  fGamelog(new std::ofstream(cOnDiskId.c_str(), std::ios_base::app))
  ,
  fTable(CHIP_DENOM, *fGamelog, true, true)
  ,
  fHandNum(0)
  ,
  fB(reinterpret_cast<void *>(0))
  ,
  fComSize(0)
  {}

  ~PokerAiInstance() {
    if (b) {
      delete b;
    }

    fGamelog->close();
    delete fGamelog;
  }

  bool startNewHand() {
    ++handNum;

    struct BlindValues bl;
    bl.SetSmallBigBlind(5.0);

    myTable.BeginInitialState(handNum);
    myTable.BeginNewHands(bl, false);

    return startBettingRound(0);
    // TODO(from yusizee): Pre-deal all hands and all community cards here and store them in memory.
  }

  handnum_t handNum() const {
    return fHandNum;
  }

  // Returns empty string on error
  std::string actionOn() const {
    if (!b) {
      // error
      return "";
    }

    const playernumber_t curIndex = b->WhoIsNext();

    if (curIndex < 0) {
      return "";
    }

    if (curIndex >= SEATS_AT_TABLE) {
      return "";
    }

    return fTable.ViewPlayer(curIndex)->GetIdent();
  }

  // Return true on success, false on error
  bool makeBet(playernumber_t seatNum, double amount) {
    if (!b) {
      return false;
    }

    if (seatNum != b->WhoIsNext()) {
      return false;
    }

    // === Make the bet ===
    b->MakeBet(amount);

    // Epilog
    switch(b->bBetState) {
      case 'b':
        // More betting is taking place.
        return true;
      case 'C':
        // The round is done. Go on to the next round.

        if (retval.seat_number == -1) {
          // INCONSISTENT RESULT!
          return false;
        }
        delete b;       
        startNextBettingRound();
        return true;
      case 'F':
        // The hand is done. Go on to the next hand.

        if (retval.seat_number != -1) {
          // INCONSISTENT RESULT!
          return false;
        }
        delete b;
        return true;
      default:
        return false;
  }

private:
  const std::string fOnDiskId;
  std::ofstream * const fGamelog;
  HoldemArena fTable;
  handnum_t fHandNum;
  HoldemArenaBetting * fB;

  CommunityPlus fCommunity;
  int8 fComSize;

  bool startNextBettingRound() {
    switch(fComSize) {
      case 0:
        // Finished, pre-flop, start post-flop
        return startBettingRound(3);
      case 3:
        return startBettingRound(4);
      case 4:
        return startBettingRound(5);
      case 5:
        // TODO(from yuzisee): Go through the entire showdown, store the result, and move on to the next hand.
        return true;
      default:
        return false;
    }
  }

  bool startBettingRound(int8 comSize) {
    fComSize = comSize;

    switch(comSize) {
      case 0:
      //Preflop
      // true: first betting round of the hand
      // 3: flop, turn, river remaining
        fTable.PrepBettingRound(true,3);  
        fCommunity.SetEmpty();
        break;
      case 3:
      //Flop
        fTable.PrepBettingRound(false,2);
        fCommunity.AddToHand(fDealtCommunity[0]);
        fCommunity.AddToHand(fDealtCommunity[1]);
        fCommunity.AddToHand(fDealtCommunity[2]);
        break;
      case 4:
      // Turn
        fTable.PrepBettingRound(false,1);
        fCommunity.AddToHand(fDealtCommunity[3]);
        break;
      case 5:
        fTable.PrepBettingRound(false,0);
        fCommunity.AddToHand(fDealtCommunity[4]);
        break;
      default:
        return false;
    }

    b = new HoldemArenaBetting(&fTable, fCommunity, fComSize);

    if (b) {
      return true;
    } else {
      return false;
    }
  }
}
;

// Returns v8LittleEndianPtr.IsEmpty() on error.
static v8::Handle<v8::Array> marshallPtr(const PokerAiInstance * const table) {

  printf("marshallPtr(%p)\n", table);

  const uintptr_t instance = reinterpret_cast<uintptr_t>(table);

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
static PokerAiInstance * unmarshallPtr(const v8::Handle<v8::Array> &v8LittleEndianPtr)
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

  PokerAiInstance * const table = reinterpret_cast<PokerAiInstance * const>(instance);

  printf("unmarshallPtr = %p\n", table);

  return table;
}

// Read args[0] and interpret as a ``PokerAiInstance *`` handle
// Returns 0 on error
static PokerAiInstance * readFirstArgumentAsTable(const v8::Arguments& args) {

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

  PokerAiInstance * const table = unmarshallPtr(v8LittleEndianPtr);

  // === Health check!

  if (!(cOnDiskId == table->fOnDiskId)) {
    return 0;
  }


  // === Return result

  return table;

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



  // === Construct table

  const PokerAiInstance * const table = new PokerAiInstance(cOnDiskId, startingChips);

  // === Initialize seats & players

  for(size_t k=0; k<seats->Length(); ++k) {


    if (seats->Get(k)->IsNull() || seats->Get(k)->IsUndefined()) {

      v8::ThrowException(v8::Exception::TypeError(v8::String::New("TODO we don't allow gaps in the seats for now...")));
      return scope.Close(v8::Undefined());
      // Don't fill this seat?
      //printf("Seat %lu left empty.\n", k); 

    } else {
      if (seats->Get(k)->IsObject()) {

        v8::Local<v8::Object> filledSeat = seats->Get(k)->ToObject();
        v8::Local<v8::Value> argPlayerIdent = filledSeat->Get(v8::String::NewSymbol("id"));
        v8::Local<v8::Value> argBot = filledSeat->Get(v8::String::NewSymbol("bot"));

        if (argPlayerIdent->IsString() && argBot->IsBoolean()) {

          v8::String::Utf8Value v8PlayerIdent( argPlayerIdent->ToString() );
          std::string cPlayerIdent(*v8PlayerIdent);

          if (cPlayerIdent.size() == 0) {
            v8::ThrowException(v8::Exception::TypeError(v8::String::New("Player .id canot be blank.")));
            return scope.Close(v8::Undefined());
          }

          bool cBot = argBot->BooleanValue();

          if (cBot) {
            v8::ThrowException(v8::Exception::TypeError(v8::String::New("TODO table->AddStrategyBot(cPlayerIdent.c_str(), startingChips, 'R');")));
            return scope.Close(v8::Undefined());
          } else {
            table->AddHumanOpponent(cPlayerIdent.c_str(), startingChips);
          }

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
  // === Marshall/serialize table instance pointer
 
  v8::Handle<v8::Array> v8LittleEndianPtr = marshallPtr(table);
  const PokerAiInstance * const verify = unmarshallPtr(v8LittleEndianPtr);

  // Couldn't create the array...
  if (v8LittleEndianPtr.IsEmpty()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("v8 failed creating an array")));
    return scope.Close(v8::Undefined());
  }


  if (verify != table) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Self-table failed.")));
    return scope.Close(v8::Undefined());
  }

  // === Start the first hand (AUTOMATIC)

  table->startFirstHand();

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

  const PokerAiInstance * const table = readFirstArgumentAsTable(args);

  if (!table) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object containg .id (must be a string) and ._instance (must be an array of uint32 values)")));
    return scope.Close(v8::Undefined());
  }



  // === Destruct table

  delete table;

  // === Return result

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("success"), v8::Boolean::New(true));

  return scope.Close(obj);
}


v8::Handle<v8::Value> GetStatus(const v8::Arguments& args) {
  v8::HandleScope scope;

  // === Validate arguments

  if (args.Length() != 1) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Wrong number of arguments")));
    return scope.Close(v8::Undefined());
  }

  // === Read arguments

  const PokerAiInstance * const table = readFirstArgumentAsTable(args);

  if (!table) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object containg .id (must be a string) and ._instance (must be an array of uint32 values)")));
    return scope.Close(v8::Undefined());
  }

  // === Return result

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("currentHand"), v8::Uint32::New(table->handNum()));
  obj->Set(v8::String::NewSymbol("actionOn"), v8::String::New(table->actionOn()));

  return scope.Close(obj);
}

// Create a JSON object of the form:
//  {'id': 'Nav', 'action': 'raiseTo', 'amount': 5.0}
static v8::Local<v8::Object> betToJson(const char * const id, const char * const action, double amount) {
  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("id"), v8::String::New(id));
  obj->Set(v8::String::NewSymbol("action"), v8::String::New(action));
  obj->Set(v8::String::NewSymbol("amount"), v8::Number::New(amount));
  return obj;
}


// Create a JSON object of the form:
//  {'checkpoint': 'flop'}
static v8::Local<v8::Object> checkpointToJson(const char * const name) {
  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("checkpoint"), v8::String::New(name));
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

  const PokerAiInstance * const table = readFirstArgumentAsTable(args);

  if (!table) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object containg .id (must be a string and must match the onDiskId provided to startTable) and ._instance (must be an array of uint32 values)")));
    return scope.Close(v8::Undefined());
  }

  const uint32_t handNum = args[1]->Uint32Value();

  if (handNum < 1) {
    return scope.Close(v8::Undefined());
  }

  // === Populate bets

  v8::Handle<v8::Array> bets = v8::Array::New(6);
  bets->Set(0, betToJson("Nav", "smallBlind", 5.0));
  bets->Set(1, betToJson("Joseph", "bigBlind", 10.0));
  bets->Set(2, betToJson("Nav", "call", 10.0));
  bets->Set(3, checkpointToJson("flop"));
  bets->Set(4, betToJson("Nav", "raiseTo", 10.0));
  bets->Set(4, betToJson("Joseph", "check", 10.0));
 
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



// Create a JSON object of the form:
// {'cards', ['9s', 'Th'], 'outcome': 'Full House: Nines over Tens'}
static v8::Local<v8::Object> showdownToJson(const char * const card0, const char * const card1, const char * const outcome) {
  v8::Local<v8::Array> cards = v8::Array::New(2);
  cards->Set(0, v8::String::New(card0));
  cards->Set(1, v8::String::New(card1));

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("cards"), cards);
  obj->Set(v8::String::NewSymbol("outcome"), v8::String::New(outcome));
  return obj;
}

// Create a JSON object of the form:
// {'cards', [], 'outcome': 'muck'}
static v8::Local<v8::Object> muckToJson() {
  v8::Local<v8::Array> cards = v8::Array::New(0);

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("cards"), cards);
  obj->Set(v8::String::NewSymbol("outcome"), v8::String::New("muck"));
  return obj;
}





v8::Handle<v8::Value> GetOutcome(const v8::Arguments& args) {
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

  const PokerAiInstance * const table = readFirstArgumentAsTable(args);

  if (!table) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object containg .id (must be a string and must match the onDiskId provided to startTable) and ._instance (must be an array of uint32 values)")));
    return scope.Close(v8::Undefined());
  }

  const uint32_t handNum = args[1]->Uint32Value();

  if (handNum < 1) {
    return scope.Close(v8::Undefined());
  }

  // === Populate handsRevealed

  v8::Handle<v8::Object> handsRevealed = v8::Object::New();
  handsRevealed->Set(v8::String::NewSymbol("Nav"), showdownToJson("9s", "Th", "Full House: Nines over Tens"));
  handsRevealed->Set(v8::String::NewSymbol("Joseph"), muckToJson());
 
 
  // === Return result


  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("winner"), v8::String::New("Nav"));
  obj->Set(v8::String::NewSymbol("handsRevealed"), handsRevealed);

  return scope.Close(obj);

}


v8::Handle<v8::Value> GetHoleCards(const v8::Arguments& args) {
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

  const PokerAiInstance * const table = readFirstArgumentAsTable(args);

  if (!table) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object containg .id (must be a string and must match the onDiskId provided to startTable) and ._instance (must be an array of uint32 values)")));
    return scope.Close(v8::Undefined());
  }

  const uint32_t seatNumber = args[1]->Uint32Value();

  if (seatNumber > 12) {
    return scope.Close(v8::Undefined());
  }

  // === Populate holeCards

  v8::Local<v8::Array> cards = v8::Array::New(2);
  cards->Set(0, v8::String::New("Th"));
  cards->Set(1, v8::String::New("9s"));

 
  // === Return result


  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("cards"), cards);
  obj->Set(v8::String::NewSymbol("_playerId"), v8::String::New("Nav"));

  return scope.Close(obj);

}


v8::Handle<v8::Value> PerformAction(const v8::Arguments& args) {
  v8::HandleScope scope;

  // === Validate arguments

  if (args.Length() != 2) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Wrong number of arguments")));
    return scope.Close(v8::Undefined());
  }

  if (!args[1]->IsObject()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Second argument must be a Javascript object")));
    return scope.Close(v8::Undefined());
  }

  // === Read arguments

  v8::Local<v8::Object> arg1 = args[1]->ToObject();

  if (arg1->Get(v8::String::NewSymbol("_playerId"))->IsString()) {
    // Extra sanity check that the player ID is correct.
  }

  if (arg1->Get(v8::String::NewSymbol("_action"))->IsString()) {
    // Extra sanity check on your action?
  }

  if (!arg1->Get(v8::String::NewSymbol("_seatNumber"))->IsUint32()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Second argument must contain ._seatNum (for now) -- we will get rid of this requirement later.")));
    return scope.Close(v8::Undefined());
  }

  if (!arg1->Get(v8::String::NewSymbol("amount"))->IsNumber()) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Second argument must contain .amount")));
    return scope.Close(v8::Undefined());
  }

  double amount = arg1->Get(v8::String::NewSymbol("amount"))->NumberValue();
  uint32_t seatNum = arg1->Get(v8::String::NewSymbol("_seatNumber"))->Uint32Value();

  PokerAiInstance * const table = readFirstArgumentAsTable(args);

  if (!table) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("First argument must be a object containg .id (must be a string and must match the onDiskId provided to startTable) and ._instance (must be an array of uint32 values)")));
    return scope.Close(v8::Undefined());
  }

  // === Apply the action

  bool success = table->makeBet(seatNum, amount);
  if (!success) {
    v8::ThrowException(v8::Exception::ReferenceError(v8::String::New("It was not your turn!")));
    return scope.Close(v8::Undefined());
  }

  // === No return value

  return scope.Close(v8::Undefined());

}











// This creates the prototype/global/static (e.g. pokerai.exports.startTable())
void Init(v8::Handle<v8::Object> exports) {

  
/*
  pokerai.exports.startTable(tableId, 1500, [{'id': 'playerId1', 'bot': false}, {'id': 'playerId2', 'bot': true}, {'id': 'playerId3', 'bot': false}, null, null, ...])
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
  pokerai.exports.getStatus({ 'id': <onDiskId>, '_instance': <instanceHandle> })
  JSON Response:
  {
    'currentHand': 4,
    'actionOn': <playerId>
  }
*/
  exports->Set(v8::String::NewSymbol("getStatus"),
     v8::FunctionTemplate::New(GetStatus)->GetFunction());


 
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
 
/*
  pokerai.exports.getOutcome({ 'id': <onDiskId>, '_instance': <instanceHandle> }, handNum)
  JSON Response:
  {
    'winner': 'Nav',
    'handsRevealed': {
            'Nav': {'cards', ['9s', 'Th'], 'outcome': 'Full House: Nines over Tens'},
            'Joseph': {'cards', [], 'outcome': 'muck'}
           }
  }
*/
  exports->Set(v8::String::NewSymbol("getOutcome"),
     v8::FunctionTemplate::New(GetOutcome)->GetFunction());

/*
  pokerai.exports.getHoleCards({ 'id': <onDiskId>, '_instance': <instanceHandle> }, seatNum)
  JSON Response:
  {
    '_playerId': 'Nav',
    'holeCards': ['9s', 'Th']
  }
*/
  exports->Set(v8::String::NewSymbol("getHoleCards"),
     v8::FunctionTemplate::New(GetHoleCards)->GetFunction());


/*
  pokerai.exports.performAction({ 'id': <onDiskId>, '_instance': <instanceHandle> }, {'_playerId': 'Joseph', '_seatNumber': 2, 'action': 'call', 'amount': 10.0})
*/
  exports->Set(v8::String::NewSymbol("performAction"),
     v8::FunctionTemplate::New(PerformAction)->GetFunction());


}

// Our target is named "pokerai". See binding.gyp for more
NODE_MODULE(pokerai, Init)
// TODO(from yuzisee): What thread does this run on? The javascript thread?

