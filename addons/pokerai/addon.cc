#define BUILDING_NODE_EXTENSION
#include <node.h>

#include <stdint.h>

#include <cstdio>

#include <limits>
#include <sstream>
#include <string>
#include <vector>

#include "holdem/src/arena.h"
#include "holdem/src/arenaEvents.h"

static const double CHIP_DENOM = 0.01; // Minimum bet denomination

struct PokerAiReveal {
  std::string playerName;
  playernumber_t seatNum;
  DeckLocation card1;
  DeckLocation card2;
  std::string outcome; // will be blank if the player mucks
  
  PokerAiReveal() : seatNum(-1) {}
};

class PokerAiShowdown {
public:
  PokerAiShowdown() : fHandNum(-1) {}

  void execute(
    HoldemArena &fTable
    ,
    playernumber_t lastHighbet
    ,
    const std::vector<DeckLocationPair> & holeCards
    ,
    const CommunityPlus &community
    ,
    std::ostream &showdownlog
  ) {
    fHandNum = fTable.handnum;

    fTable.PrepShowdownRound(community, showdownlog);

    fReveals.clear();
    std::vector<ShowdownRep> winners;
    ///------------------------------------
    ///  GENERATE A LIST OF WINNERS
    HoldemArenaShowdown w(&fTable,lastHighbet);
    while(w.bRoundState != '!')
    {
      PokerAiReveal result;
      result.seatNum = w.WhoIsNext();
      result.playerName = fTable.ViewPlayer(result.seatNum)->GetIdent();

      CommunityPlus hand;
      hand.AddToHand(holeCards[w.WhoIsNext()].first);
      hand.AddToHand(holeCards[w.WhoIsNext()].second);
      Reveal response = w.RevealHand(hand, community, showdownlog);

      if(response.outcome != "") {
        // Player revealed
        result.outcome = response.outcome;
        result.card1 = holeCards[w.WhoIsNext()].first;
        result.card2 = holeCards[w.WhoIsNext()].second;
      }
      fReveals.push_back(PokerAiReveal());
    }
    winners.assign(w.winners.begin(),w.winners.end());
    // fTable.compareAllHands(community, lastHighBet, winners, showdownlog);
    ///------------------------------------

    fTable.ProcessShowdownResults(winners, showdownlog);

  }

  handnum_t handNum() const { return fHandNum; }
  const std::vector<PokerAiReveal> &reveals() const { return fReveals; }

private:
  std::vector<PokerAiReveal> fReveals;
  handnum_t fHandNum;
}
;


class PokerAiRoundSetup {


public:

  PokerAiRoundSetup() : fB(0) {
    clear();// TODO(from yuzisee): Set random seed?
  }
  ~PokerAiRoundSetup() {
    clear();
  }

  void clear() {
    if (fB) {
      delete fB;
      fB = 0;
    }

    fComSize = 0;

    fCommunity.SetEmpty();
 
    fDealtHolecards.clear();
 
    fPlayerCount = 0;

  }
 
  // Return false on error
  bool startNewHand(const handnum_t handnum, HoldemArena& myTable, const BlindValues & blinds, std::ostream & gamelog) {
    clear();

    // == Init
    printf("== Init\n");

    fPlayerCount = myTable.NumberAtTable();

    // == Deal cards
    printf("== Deal cards\n");

    r.ShuffleDeck();

    Hand newCard;
    for (playernumber_t i=0; i<fPlayerCount; ++i) {
      newCard.SetEmpty(); r.DealCard(newCard);
      DeckLocation a;
      a.SetByIndex(r.dealt.GetIndex());

      DeckLocation b;
      newCard.SetEmpty(); r.DealCard(newCard);
      b.SetByIndex(r.dealt.GetIndex());

      fDealtHolecards.push_back(DeckLocationPair(a, b));
    }

    for (size_t i=0; i<5; ++i) {
      newCard.SetEmpty(); r.DealCard(newCard);

      fDealtCommunity[i].SetByIndex(r.dealt.GetIndex());
    }

    // == Begin the first round
    printf("== Begin the first round\n");
 
    myTable.BeginInitialState(handnum);
    myTable.BeginNewHands(gamelog, blinds,false);

    // true: first betting round of the hand
    // 3: flop, turn, river remaining
    myTable.PrepBettingRound(true,3);  


    return startBettingRound(myTable, &gamelog);

  }

  bool startNextBettingRound(HoldemArena& myTable, std::ostream *spectateLog) {
    if (!fB) {
      // Can't find previous betting round!!
      return false;
    }

    delete fB;
    fB = 0;

    switch(fComSize) {
      case 0:
        // Finished, pre-flop, start post-flop
        fComSize = 3;

        myTable.PrepBettingRound(false,2);
        fCommunity.AddToHand(fDealtCommunity[0]);
        fCommunity.AddToHand(fDealtCommunity[1]);
        fCommunity.AddToHand(fDealtCommunity[2]);

        return startBettingRound(myTable, spectateLog);
      case 3:
        // Finished flop betting round, show turn and begin turn betting round
        fComSize = 4;

        myTable.PrepBettingRound(false,1);
        fCommunity.AddToHand(fDealtCommunity[3]);

        return startBettingRound(myTable, spectateLog);
      case 4:
        // Finished turn betting round, show river and begin river betting round
        fComSize = 5;

        myTable.PrepBettingRound(false,0);
        fCommunity.AddToHand(fDealtCommunity[4]);

        return startBettingRound(myTable, spectateLog);
      case 5:
        // Since hasNextBettingRound() is false, you shouldn't be calling startNextBettingRound() at this time.
        return false;
      default:
        return false;
    }
  }


  const CommunityPlus &community() const { return fCommunity; }
  const std::vector<DeckLocationPair> & holeCards() const { return fDealtHolecards; }
  bool hasCurrentBettingRound() const {
    if (fB) {
      return true;
    } else {
      return false;
    }
  }
  HoldemArenaBetting &b() { return *fB; }
  const HoldemArenaBetting &b() const { return *fB; }

  bool hasNextBettingRound() {
    if (fComSize == 5) {
      return false;
    }

    return true;
  }


private:
  RandomDeck r;
  playernumber_t fPlayerCount;
  std::vector<DeckLocationPair> fDealtHolecards;
  DeckLocation fDealtCommunity[5];

  CommunityPlus fCommunity;
  int8 fComSize;
  HoldemArenaBetting * fB;

  bool startBettingRound(HoldemArena& myTable, std::ostream * spectateLog) {
    if (fB) {
      printf("Error: fB already exists\n");
      return false;
    }

    fB = new HoldemArenaBetting(&myTable, fCommunity, fComSize, spectateLog);

    if (fB) {
      printf("startBettingRound() OK");
      return true;
    } else {
      printf("Error: malloc failed");
      return false;
    }
  }

};

struct PokerAiMakeBet {
  bool bSuccess; // true if no errors
  playernumber_t fHighbetIdx; // This is the last player to raise.

  struct MinRaiseError fMinRaiseMsg;
  double fAdjustedRaiseTo; // This is populated to your actual bet. If it doesn't match your intended bet it was because of minRaise rules.

  bool bRoundDone; // If true, this betting round has concluded

  // If 'F' all betting rounds have concluded due to all-fold.
  // If 'C' all betting rounds have concluded and we're at the showdown.
  char bHandDone;

  PokerAiMakeBet(playernumber_t seatNum, HoldemArena &fTable, PokerAiRoundSetup &fTableRound, double amount, std::ostream &gamelog, PokerAiShowdown * const out) :
  bSuccess(false)
  ,
  fHighbetIdx(-1)
  ,
  fAdjustedRaiseTo(std::numeric_limits<double>::signaling_NaN())
  ,
  bRoundDone(false)
  ,
  bHandDone('\0')
  {
    // NOTE ABOUT EARLY RETURNS: bSuccess is false by default.

    if (!fTableRound.hasCurrentBettingRound()) {
      // error
      return;
    }

    if (seatNum != fTableRound.b().WhoIsNext()) {
      // error
      return;
    }

    // === Make the bet ===
    printf("=== Make the bet\n");

    HoldemAction action(fTableRound.b().MakeBet(amount, &fMinRaiseMsg));

    // === Read the result ===
    HoldemArena::ToString(action, gamelog);
    const char newState = fTableRound.b().bBetState;
    fHighbetIdx = fTableRound.b().playerCalled;

    if (fMinRaiseMsg.result != fMinRaiseMsg.result) {
      // NaN msg, so our bet was untouched.
      fAdjustedRaiseTo = amount;
    } else {
      fAdjustedRaiseTo = fMinRaiseMsg.result;
    }

    // === Epilog
    printf("=== Epilog\n");

    switch(newState) {
      case 'b':
        printf("MakeBet() success\n");
        // More betting is taking place.
        bSuccess = true;
        return;
      case 'C':
        // The round is done. Go on to the next round.

        if (fHighbetIdx == -1) {
          // INCONSISTENT RESULT!
          return;
        }
        
        if (fTableRound.hasNextBettingRound()) {
          fTableRound.startNextBettingRound(fTable, &gamelog);
          bSuccess = true;
          bRoundDone = true;
          return;
        } else {
          // All betting rounds complete.

          out->execute(fTable, fHighbetIdx, fTableRound.holeCards(), fTableRound.community(), gamelog);

          fTableRound.clear();
          bSuccess = true;
          bRoundDone = true;
          bHandDone = newState;
          return;
        }
      case 'F':
        // The hand is done. Go on to the next hand.

        if (fHighbetIdx != -1) {
          // INCONSISTENT RESULT!
          return;
        }

        fTableRound.clear();
        bSuccess = true;
        bRoundDone = true;
        bHandDone = newState;
        return;
      default:
        printf("Error: Unknown newState %c\n", newState);
        return;
    }
  }
}
;

class PokerAiInstance {

public:
  PokerAiInstance(std::string &cOnDiskId, double startingChips)
  :
  fOnDiskId(cOnDiskId)
  ,
  fGamelog(cOnDiskId.c_str(), std::ios_base::app)
  ,
  fHandNum(0)
  ,
  fTable(CHIP_DENOM, true, true)
  {
  }

  ~PokerAiInstance() {
    fGamelog.close();
  }

  void addHuman(const std::string &ident, double chips) {
    fTable.AddHumanOpponent(ident.c_str(), chips);
  }

  bool startFirstHand() {
    ++fHandNum;

    BlindValues bl;
    bl.SetSmallBigBlind(5.0);
    // TODO(from yuzisee): Create a new HoldemArena every time?
    
    return fTableRound.startNewHand(fHandNum, fTable, bl, fGamelog);
  }

  bool startNextHand() {
    // To start a new hand, you first RefreshPlayers to clean up the previous hand.
    fTable.RefreshPlayers(&fGamelog); ///New Hand (handnum is also incremented now)
    return startFirstHand();
  }

  handnum_t handNum() const {
    return fHandNum;
  }

  // Returns empty string on error
  std::string actionOn() const {
    if (!fTableRound.hasCurrentBettingRound()) {
      // error
      return "";
    }

    const playernumber_t curIndex = fTableRound.b().WhoIsNext();

    if (curIndex < 0) {
      // error
      return "";
    }

    if (curIndex >= SEATS_AT_TABLE) {
      // error
      return "";
    }

    return fTable.ViewPlayer(curIndex)->GetIdent();
  }

  // Return true on success, false on error
  PokerAiMakeBet makeBet(playernumber_t seatNum, double amount) {
    PokerAiMakeBet result(seatNum, fTable, fTableRound, amount, fGamelog, &fLastShowdown);

    return result;
  }

  // returns 0 on error
  const DeckLocationPair * holeCards(playernumber_t seatNum) const {
    if(seatNum > fTable.NumberAtTable()) {
      return 0;
    }

    if (!fTableRound.holeCards().size() < seatNum) {
      return 0;
    }

    return fTableRound.holeCards().data() + seatNum;
  }
  
  const PokerAiShowdown &reveals() const { return fLastShowdown; }

  const std::string & playerName(playernumber_t seatNum) const { return fTable.ViewPlayer(seatNum)->GetIdent(); }

  const std::string fOnDiskId;
private:
  std::ofstream fGamelog;
  handnum_t fHandNum;

  HoldemArena fTable;
  PokerAiRoundSetup fTableRound;
  PokerAiShowdown fLastShowdown;


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

  PokerAiInstance * const table = new PokerAiInstance(cOnDiskId, startingChips);

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
            table->addHuman(cPlayerIdent, startingChips);
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
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Self-test failed.")));
    return scope.Close(v8::Undefined());
  }

  // === Start the first hand (AUTOMATIC)

  bool success = table->startFirstHand();
  if (!success) {
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("startFirstHand() failed.")));
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
  obj->Set(v8::String::NewSymbol("actionOn"), v8::String::New(table->actionOn().c_str()));

  return scope.Close(obj);
}

// Create a JSON object of the form:
//  {'id': 'Nav', 'action': 'raiseTo', 'amount': 5.0}
static v8::Local<v8::Object> betToJson(const char * const id, const playernumber_t seatNum, const char * const action, double amount) {
  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("_playerId"), v8::String::New(id));
  obj->Set(v8::String::NewSymbol("_seatNumber"), v8::Uint32::New(seatNum));
  obj->Set(v8::String::NewSymbol("_action"), v8::String::New(action));
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
  bets->Set(0, betToJson("Nav", 0, "smallBlind", 5.0));
  bets->Set(1, betToJson("Joseph", 1, "bigBlind", 10.0));
  bets->Set(2, betToJson("Nav", 0, "call", 10.0));
  bets->Set(3, checkpointToJson("flop"));
  bets->Set(4, betToJson("Nav", 0, "raiseTo", 10.0));
  bets->Set(4, betToJson("Joseph", 1, "check", 10.0));
 
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


static std::string toString(const DeckLocation &d) {
  std::ostringstream s;
  HoldemUtil::PrintCard(s, d.GetIndex());
  return s.str();
}


// Create a JSON object of the form:
// {'cards', ['9s', 'Th'], 'outcome': 'Full House: Nines over Tens'}
static v8::Local<v8::Object> showdownToJson(const DeckLocation &card1, const DeckLocation &card2, const std::string & outcome) {
  v8::Local<v8::Array> cards = v8::Array::New(2);
  cards->Set(0, v8::String::New(toString(card1).c_str()));
  cards->Set(1, v8::String::New(toString(card2).c_str()));

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("cards"), cards);
  obj->Set(v8::String::NewSymbol("outcome"), v8::String::New(outcome.c_str()));
  return obj;
}

// Create a JSON object of the form:
// {'cards', [], 'outcome': 'muck'}
static v8::Local<v8::Object> muckToJson() {
  v8::Local<v8::Array> cards = v8::Array::New(0);

  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("cards"), cards);
  obj->Set(v8::String::NewSymbol("outcome"), v8::String::New("mucks"));
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

  // === Populate handsRevealed

  const handnum_t activeRevealHandNum = table->reveals().handNum();

  if (handNum != activeRevealHandNum) {
    return scope.Close(v8::Undefined());
  }

  v8::Handle<v8::Object> handsRevealed = v8::Object::New();
  for (const struct PokerAiReveal &r : table->reveals().reveals()) {
    if (r.outcome == "") {
      handsRevealed->Set(v8::String::NewSymbol(r.playerName.c_str()), muckToJson());
    } else {
      handsRevealed->Set(v8::String::NewSymbol(r.playerName.c_str()), showdownToJson(r.card1, r.card2, r.outcome));
    }      
  }
 
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


  // === Populate holeCards


  const DeckLocationPair *holeCards = table->holeCards(seatNumber);

  if (!holeCards) {
    return scope.Close(v8::Undefined());
  }

  v8::Local<v8::Array> cards = v8::Array::New(2);
  cards->Set(0, v8::String::New(toString(holeCards->first).c_str()));
  cards->Set(1, v8::String::New(toString(holeCards->second).c_str()));

 
  // === Return result


  v8::Local<v8::Object> obj = v8::Object::New();
  obj->Set(v8::String::NewSymbol("_playerId"), v8::String::New("Nav"));
  obj->Set(v8::String::NewSymbol("_seatNumber"), v8::Uint32::New(seatNumber));
  obj->Set(v8::String::NewSymbol("holeCards"), cards);

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
    v8::ThrowException(v8::Exception::TypeError(v8::String::New("Second argument must contain ._seatNumber (for now) -- we will get rid of this requirement later.")));
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

  printf("== Apply the action\n");

  PokerAiMakeBet info = table->makeBet(seatNum, amount);
  if (!info.bSuccess) {
    v8::ThrowException(v8::Exception::ReferenceError(v8::String::New("It was not your turn!")));
    return scope.Close(v8::Undefined());
  }

  if (info.bHandDone != '\0') {
    // HAND DONE! Clean everything up.
    table->startNextHand();
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
            {'_playerId': 'Nav', '_seatNumber': 0, '_action': 'smallBlind', 'amount': 5.0},
            {'_playerId': 'Joseph', '_seatNumber': 0, '_action': 'bigBlind', 'amount': 10.0},
            {'_playerId': 'bot1', '_seatNumber': 0, '_action': 'fold', 'amount': -1},
            {'_playerId': 'bot2', '_seatNumber': 0, '_action': 'raiseTo', 'amount': 25.0},
            {'_playerId': 'bot3', '_seatNumber': 0, '_action': 'call', 'amount': 25.0},
            ...
            {'checkpoint': 'flop'},
            {'_playerId': 'Nav', '_seatNumber': 0, '_action': 'check', 'amount': 0.0}
           ],
    'chipCounts': {
            'bot2': 500.0,
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
  pokerai.exports.performAction({ 'id': <onDiskId>, '_instance': <instanceHandle> }, {'_playerId': 'Joseph', '_seatNumber': 2, '_action': 'call', 'amount': 10.0})
*/
  exports->Set(v8::String::NewSymbol("performAction"),
     v8::FunctionTemplate::New(PerformAction)->GetFunction());

}

// Our target is named "pokerai". See binding.gyp for more
NODE_MODULE(pokerai, Init)
// TODO(from yuzisee): What thread does this run on? The javascript thread?

