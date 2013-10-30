    # Python Scripts for the Call of Cthulhu LCG definition for OCTGN
    # Copyright (C) 2013  Jason Cline

    # This python script is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with this script.  If not, see <http://www.gnu.org/licenses/>.

###==================================================File Contents==================================================###
# This file contains the basic table actions in CoC. They are the ones the player calls when they use an action in the menu.
# Many of them are also called from the autoscripts.
# Note:  These scripts are heavily based on the ones from Android:Netrunner and Star Wars.  Special thanks to Konstantine Thoukydides and all his work.
###=================================================================================================================###

import re
import collections

#---------------------------------------------
# Global Variables
#---------------------------------------------
gameSetup = False
firstTurn = True
restoredInsane = 0
opponent = None
unpaidCard = None
reversePlayerChk = False

#---------------------------------------------
# Phases
#---------------------------------------------

def showCurrentPhase(): # Just say a nice notification about which phase you're on.
   committedStory = eval(getGlobalVariable('Committed Story'))
   if committedStory != []:
      notify(storyPhases[num(getGlobalVariable('Story Phase'))])
   else: 
      notify(phases[num(me.getGlobalVariable('Phase'))])

def nextPhase(group = table, x = 0, y = 0, setTo = None):  
	# Function to take you to the next phase. 
	global firstTurn
	if not gameReady():
		whisper("One or more players have not completed setup yet.")
		return
	if not gameStarted():
		whisper("The game has not yet been started.")
		return
	debugNotify(">>> nextPhase()") #Debug
	mute()
	committedStory = eval(getGlobalVariable('Committed Story'))
	if committedStory != []:
		debugNotify("We got committed story: {}".format(committedStory))
		phase = num(getGlobalVariable('Story Phase'))
		if setTo: phase = setTo
		else: phase += 1
		#if phase == 4: revealEdge(forceCalc = True) # Just to make sure it wasn't forgotten.
		setGlobalVariable('Story Phase',str(phase))
		showCurrentPhase()
		if not setTo:
			if phase == 1: delayed_whisper(":::NOTE::: You can now start selecting engagement participants by double-clicking on them")
			elif phase == 5: finishEngagement() # If it's the reward unopposed phase, we simply end the engagement immediately after
	else:
		debugNotify("Normal Phase change")
		phase = num(me.getGlobalVariable('Phase'))
		if not me.isActivePlayer:
			debugNotify("Not currently the active player")
			#if debugVerbosity >= 2: notify("### Active Player: {}".format(getGlobalVariable('Active Player'))) #Debug
			if not confirm("Your opponent has not finished their turn yet. Are you sure you want to jump to your turn?"): return
			me.setActivePlayer() # new in OCTGN 3.0.5.47 
			me.setGlobalVariable('Phase','1')
			#setGlobalVariable('Active Player', me.name)
			phase = 1
		else: 
			debugNotify("Normal Phase change")
			if phase == -1: phase = 1 # This is for the first phase of the LS player.
			else: phase += 1
			me.setGlobalVariable('Phase',str(phase)) # Otherwise, just move up one phase
		if phase == 1: goToRefresh()
		elif phase == 2: goToDraw()
		elif phase == 3: goToResource()
		elif phase == 4: goToOperations()
		elif phase == 5: 
			if firstTurn:
				notify(":::NOTICE::: {} skips their first story phase".format(me))
				firstTurn = False
				debugNotify("Turn End - Skipping Story Phase")
				me.setGlobalVariable('Phase','0')
				atTimedEffects(Time = 'End')
				notify("=== {} has ended their turn ===.".format(me))
				me.setGlobalVariable('resourcesToPlay','1')
				opponent.setActivePlayer()
				for card in table:
					if card.markers[mdict['Activation']]: card.markers[mdict['Activation']] = 0
			else: goToStory()
		elif phase == 6:
			me.setGlobalVariable('Phase','0')
			atTimedEffects(Time = 'End')
			notify("=== {} has ended their turn ===.".format(me))
			me.setGlobalVariable('resourcesToPlay','1')
			opponent.setActivePlayer()
			for card in table:
				if card.markers[mdict['Activation']]: card.markers[mdict['Activation']] = 0
			
			
def goToRefresh(group = table, x = 0, y = 0): # Go directly to the Refresh phase
   global Stored_Attachments
   global restoredInsane
   if debugVerbosity >= 1: notify(">>> goToRefresh(){}".format(extraASDebug())) #Debug
   atTimedEffects(Time = 'Start')   
   mute()
   global firstTurn
   me.setGlobalVariable('Phase','1')
   showCurrentPhase()
   if not Automations['Start/End-of-Turn/Phase']: return
   insaneCards = [card for card in table if card.controller == me and cardStatus(card) == "Insane"]
   exhaustedCards = [card for card in table if card.controller == me and cardStatus(card) == "Exhausted"]
   myDomains = [card for card in table if card.controller == me and cardStatus(card) == "Domain"]
   debugNotify("Insane card count: {}".format(len(insaneCards)))
   if len(insaneCards) == 1 and restoredInsane == 0:
      notify("Automatically restoring {} (Only insane character)".format(insaneCards[0]))
      restoreCard(insaneCards[0])
      restoredInsane += 1
   elif len(insaneCards) > 1:
      whisper("You may restore one of your insane characters before moving to the next phase")
   if not firstTurn: notify(":> {} readied all their eligible cards".format(me))
   for card in exhaustedCards:
      readyCard(card)
   for card in myDomains:
      clearedDomains = 0
      att = getAttachments(card)
      if len(att) > 0:
         for subatt in att:
            if Card(subatt).name == "Drain Token":
               Stored_Attachments[subatt] = ""
               Card(subatt).moveTo(me.piles['Discard Pile'])
               clearedDomains += 1
         if clearedDomains: notify("{} refreshed {} domains.".format(me,clearedDomains))
   atTimedEffects(Time = 'afterCardRefreshing') 

def goToDraw(group = table, x = 0, y = 0): # Go directly to the Draw phase
   global firstTurn
   if debugVerbosity >= 1: notify(">>> goToDraw(){}".format(extraASDebug())) #Debug
   atTimedEffects(Time = 'afterRefresh') # We put "afterRefresh" in the refresh phase, as cards trigger immediately after refreshing. Not after the refresh phase as a whole.
   mute()
   me.setGlobalVariable('Phase','2')
   showCurrentPhase()
   if not Automations['Start/End-of-Turn/Phase']: return
   if firstTurn: draw()
   else: drawMany(count=2)
   nextPhase()


def goToResource(group = table, x = 0, y = 0):
	if debugVerbosity >= 1: notify(">>> goToResource(){}".format(extraASDebug())) #Debug
	atTimedEffects(Time = 'afterDraw')   
	mute()
	me.setGlobalVariable('Phase','3')
	showCurrentPhase()
	
def goToOperations(group = table, x = 0, y = 0):
	if debugVerbosity >= 1: notify(">>> goToOperations(){}".format(extraASDebug())) #Debug
	atTimedEffects(Time = 'afterResource')   
	mute()
	me.setGlobalVariable('Phase','4')
	showCurrentPhase()
	
def goToStory(group = table, x = 0, y = 0):
	if debugVerbosity >= 1: notify(">>> goToStory(){}".format(extraASDebug())) #Debug
	atTimedEffects(Time = 'afterOperations')   
	mute()
	me.setGlobalVariable('Phase','5')
	showCurrentPhase()
#---------------------------------------------
# Game Setup
#---------------------------------------------
def createStartingCards():
	try:
		debugNotify(">>> createStartingCards()") #Debug
		if me.hasInvertedTable() == True: 
			table.create("a8cec1b8-1121-4612-80c4-c66a437cc2e0", -31, -300, 1)
			table.create("f22ee55c-8f47-4174-a7a4-985731a74d30", -131, -300, 1)
			table.create("d8a151e4-28c8-4653-b826-ebda237b776b", 69, -300, 1)
		else: 
			table.create("0054c047-1887-4a5d-b11b-b70f3cff3a0a", -31, 212, 1)
			table.create("593da3cb-290b-426e-9eec-1b3fd3465a2d", -131, 212, 1)
			table.create("46cfc241-12ea-4d15-91f5-0facf26a9d82", 69, 212, 1)
	except: notify("!!!ERROR!!! {} - In createStartingCards()\n!!! PLEASE INSTALL MARKERS SET FILE !!!".format(me))

def intSetup(group, x = 0, y = 0):
   debugNotify(">>> intSetup(){}".format(extraASDebug())) #Debug
   global gameSetup, opponent
   mute()
   versionCheck()
   cardsOnTable = [card for card in table if card.controller == me]
   debugNotify("cardsOnTable: {}".format(len(cardsOnTable)))
   if len(cardsOnTable) and not confirm("Are you sure you want to setup for a new game? (This action should only be done after a table reset)"): return
   if not table.isTwoSided() and not confirm(":::WARNING::: This game is designed to be played on a two-sided table. Things will be extremely uncomfortable otherwise!! Please start a new game and makde sure the  the appropriate button is checked. Are you sure you want to continue?"): return
   chooseSide()
   opponent = ofwhom('ofOpponent')
   #for type in Automations: switchAutomation(type,'Announce') # Too much spam.
   deck = me.piles['Deck']
   debugNotify("Checking Deck ({})".format(len(deck)), 3)
   if len(deck) == 0:
      whisper ("Please load a deck first!")
      return
   debugNotify("Reseting Variables", 3)
   resetAll()
   for card in me.hand:
         whisper(":::Warning::: You are not supposed to have any cards in your hand when you start the game")
         card.moveToBottom(me.piles['Deck'])
         continue
   debugNotify("Checking Illegality", 3)
   deckStatus = checkDeck(deck)
   debugNotify("Deck Status: {}".format(deckStatus))
   if not deckStatus:
      if not confirm("We have found illegal cards in your deck. Bypass?"): return
      else:
         notify("{} has chosen to proceed with an illegal deck.".format(me))
   debugNotify("Creating Starting Cards", 3)
   createStartingCards()
   debugNotify("Shuffling Deck", 3)
   shuffle(me.piles['Deck'])
   debugNotify("Drawing 8 Cards", 3)
   notify("{}'s {} is shuffled ".format(me,pileName(me.piles['Deck'])))
   drawMany(me.piles['Deck'], 8)
   debugNotify("Reshuffling Deck", 3)
   shuffle(me.piles['Deck']) # And another one just to be sure
   me.resourcesToPlay = 3
   gameSetup == True
   whisper("Target each domain, and play a card to it as a resource.  Once all players have done this, the game can begin.")
  # executePlayScripts(Identity,'STARTUP')

def checkDeck(group):
	debugNotify(">>> checkDeck(){}".format(extraASDebug())) #Debug
	notify (" -> Checking deck of {} ...".format(me))
	ok = True
	loDeckCount = len(group)
	debugNotify("About to check min deck size.", 4) #Debug
	if loDeckCount < 50: 
		ok = False
		notify ( ":::ERROR::: Only {} cards in {}'s Deck. {} Needed!".format(loDeckCount,me,50))
	mute()
	debugNotify("About to move cards into me.ScriptingPile", 4) #Debug
	for card in group: card.moveTo(me.ScriptingPile)
	if len(players) > 1: random = rnd(1,100) # Fix for multiplayer only. Makes Singleplayer setup very slow otherwise.
	debugNotify("About to check each card in the deck", 4) #Debug
	counts = collections.defaultdict(int)
	CardLimit = {}
	for card in me.ScriptingPile:
		counts[card.name] += 1
	if counts[card.name] > 3:
	 notify(":::ERROR::: Only 3 copies of {} allowed.".format(card.name))
	 ok = False
	if len(players) > 1: random = rnd(1,100) # Fix for multiplayer only. Makes Singleplayer setup very slow otherwise.
	for card in me.ScriptingPile: card.moveToBottom(group) # We use a second loop because we do not want to pause after each check
	if ok: notify("-> Deck of {} is OK!".format(me))
	debugNotify("<<< checkDeckNoLimit() with return: {}.".format(ok), 3) #Debug
	return (ok)
	
def startGameRandom(group, x = 0, y = 0):
	if not gameReady():
		whisper("One or more players have not completed setup yet.")
		return
	if gameStarted():
		whisper("The game has already begun.")
		return
	n = rnd(1, len(players))
	players[n-1].setActivePlayer()
	for player in players:
		player.setGlobalVariable('resourcesToPlay','1')
	notify("{} has started the game, selecting a random start player.  {} will take the first turn.".format(me,players[n-1].name))

def startGameMe(group, x = 0, y = 0):	
	if not gameReady():
		whisper("One or more players have not completed setup yet.")
		return
	if gameStarted():
		whisper("The game has already begun.")
		return
	if not confirm("Are you sure you want to start the game as first player?"): return
	me.setActivePlayer()
	notify("{} has started the game, and has opted to take the first turn.".format(me))
	

#---------------------------------------------
# Pile Actions
#---------------------------------------------
def shuffle(group):
   debugNotify(">>> shuffle(){}".format(extraASDebug())) #Debug
   group.shuffle()

def draw(group=me.piles['Deck']):
	debugNotify(">>> draw(){}".format(extraASDebug())) #Debug
	global newturn
	mute()
	if len(group) == 0:
		whisper(":::ERROR::: No more cards in your stack")
	card = group.top()
	card.moveTo(me.hand)
	notify("{} draws a card.".format(me))

def drawMany(group = me.piles['Deck'], count = None, destination = None, silent = False):
	debugNotify(">>> drawMany(){}".format(extraASDebug())) #Debug
	debugNotify("source: {}".format(group.name), 2)
	if destination: debugNotify("destination: {}".format(destination.name), 2)
	mute()
	if destination == None: destination = me.hand
	SSize = len(group)
	if SSize == 0: return 0
	if count == None: count = askInteger("Draw how many cards?", 5)
	if count == None: return 0
	if count > SSize :
		count = SSize
		whisper("You do not have enough cards in your deck to complete this action. Will draw as many as possible")
	for c in group.top(count):
		c.moveTo(destination)
	if not silent: notify("{} draws {} cards.".format(me, count))
	debugNotify("<<< drawMany() with return: {}".format(count), 3)
	return count

#------------------------------------------------------------------------------
# Card Actions
#------------------------------------------------------------------------------
def restoreCharacter(card, x = 0, y = 0):
	global restoredInsane
	phase=getGlobalVariable('Phase')
	if phase != 0:
		whisper("You may only restore a character during your Refresh Phase.")
		return
	if restoredInsane > 0:
		whisper("You may only restore one insane character during your Refresh Phase.")
		return
	if cardStatus(card) != "Insane":
		whisper("This card is not Insane.")
		return
	if card.controller != me:
		whisper("Please choose one of your own Insane cards to restore.")
		return
	restoreCard(card)
	restoredInsane += 1
	notify("{} restored {} to sanity.".format(me,card.name))

def clear(card, x = 0, y = 0, silent = False):
   debugNotify(">>> clear() card: {}".format(card), ) #Debug
   mute()
   if not silent: notify("{} clears {}.".format(me, card))
   if card.highlight != DummyColor and card.highlight != RevealedColor and card.highlight != InactiveColor: card.highlight = None
   card.markers[mdict['BaseLink']] = 0
   card.markers[mdict['PlusOne']] = 0
   card.markers[mdict['MinusOne']] = 0
   card.target(False)
   debugNotify("<<< clear()", 3)
   
def clearAll(markersOnly = False, allPlayers = False): # Just clears all the player's cards.
   debugNotify(">>> clearAll()") #Debug
   for card in table:
      if allPlayers: clear(card,silent = True)
      if card.controller == me: clear(card,silent = True)
      if not markersOnly:
         hostCards = eval(getGlobalVariable('Host Cards'))
         if card.isFaceUp and (card.Type == 'Operation' or card.Type == 'Event') and card.highlight != DummyColor and card.highlight != RevealedColor and card.highlight != InactiveColor and not card.markers[mdict['Scored']] and not hostCards.has_key(card._id): # We do not trash "scored" events (e.g. see Notoriety) or cards hosted on others card (e.g. see Oversight AI)
            intTrashCard(card,0,"free") # Clearing all Events and operations for players who keep forgeting to clear them.
   debugNotify("<<< clearAll()", 3)

def restoreCard(card, x = 0, y = 0, verbose = False): # Restores an insane character.
   if cardStatus(card) == "Insane":
      card.isFaceUp = True
      card.orientation = Rot90
      if verbose:notify("{} restored {} to sanity.".format(me,card.name))
   else: debugNotify("Tried to restore a non-insane card: {}".format(card.name))

def makeInsane(card, x = 0, y = 0, verbose=False):
   global Stored_Attachments
   debugNotify(">>> makeInsane({})".format(card.name))
   if cardStatus(card) == "InPlay" or cardStatus(card) == "Exhausted":
      if verbose: notify("{}'s {} is driven insane.".format(me,card.name))
      card.isFaceUp = False
      card.orientation = Rot90
      card.peek()
      for att in getAttachments(card):
         discardedCard = Card(att)
         if verifyAttachment(att, card._id):
            notify("{}'s {} is destroyed when {} is driven insane.".format(discardedCard.controller, discardedCard.name, card.name))
            discardedCard.moveTo(discardedCard.controller.piles['Discard Pile'])
         Stored_Attachments[att] = ""
   else: debugNofity("Tried to drive an inappropriate card insane: {}".format(card.name))

def readyCard(card, x = 0, y = 0,verbose=False):
   if cardStatus(card) == "Exhausted":
      card.orientation = Rot0
      if verbose:notify("{} readied {}".format(me,card.name))
   else: debugNotify("Tried to ready a non-exhausted card: {}".format(card.name))

def exhaustCard(card, x=0, y=0, verbose=False):
   if cardStatus(card) == "InPlay":
      card.orientation = Rot90
      if verbose: notify("{} exhausted {}".format(me,card.name))
   else: debugNotify("Tried to exhaust a non-ready card: {}".format(card.name))
def defaultAction(card, x = 0, y = 0):
   global Stored_Attachments
   phase = num(me.getGlobalVariable('Phase'))
   if debugVerbosity >= 1: notify(">>> defaultAction(){}".format(extraASDebug())) #Debug
   mute()
   selectedAbility = eval(getGlobalVariable('Stored Effects'))
   if card.Type == 'Button': # The Special button cards.
      if card.name == 'Wait!': BUTTON_Wait()
      elif card.name == 'Actions?': BUTTON_Actions()
      else: BUTTON_OK()
      return
      
   elif selectedAbility.has_key(card._id): # we check via the dictionary, as this can be then used without a highlight via the "Hardcore mode"
      if card.highlight != ReadyEffectColor: # If the card has a selectedAbility entry but no highlight, it means the player is in hardcore mode, so we need to light up the card to allow their opponent to react.
         readyEffect(card,True)
         return
      debugNotify("selectedAbility Tuple = {}".format(selectedAbility[card._id]),4)
      if selectedAbility[card._id][4]: preTargets = [Card(selectedAbility[card._id][4])] # The 5th value of the tuple is special target card's we'll be using for this run.
      else: preTargets = None
      debugNotify("preTargets = {}".format(preTargets),3)
      if findMarker(card, "Effects Cancelled"): 
         notify("{}'s effects have been cancelled".format(card))
      else: 
         splitTargets = selectedAbility[card._id][0].split('$$')
         for targetSeek in splitTargets:
            if re.search(r'(?<!Auto)Targeted', targetSeek) and re.search(r'onPlay', targetSeek) and findTarget(targetSeek,card = card) == []: 
               if card.Type == 'Event': bracketInfo = "(Cancelling will abort the effect and return this card back to your hand. Saying NO will allow you to target and double click this card to try again.)"
               else: bracketInfo = "(Cancelling will dismiss this react trigger. Saying NO will allow you to target and double click this card to try again.)"
               if confirm(":::ERROR::: Required Targets for this effect not found! You need to target with shift-click accordingly\
                       \n\nWould you like to completely cancel this effect?\
                         \n{}".format(bracketInfo)):
                  clearStoredEffects(card,True,False) # Now that we won't cancel anymore, we clear the card's resident effect now, whatever happens, so that it can remove itself from play.
                  if card.Type == 'Event': card.moveTo(card.owner.hand)
                  notify("{} has aborted using {}".format(me,card))
                  return
               else: return # If the script needs a target but we don't have any, abort.
         notify("{} resolves the effects of {}".format(me,card)) 
         clearStoredEffects(card,True,False) # Now that we won't cancel anymore, we clear the card's resident effect now, whatever happens, so that it can remove itself from play.
                                             # We don't remove it from play yet though, we do it after we've executed all its scripts
         if re.search(r'LEAVING',selectedAbility[card._id][3]): 
            cardsLeaving(card,'append')
         if executeAutoscripts(card,selectedAbility[card._id][0],count = selectedAbility[card._id][5], action = selectedAbility[card._id][3],targetCards = preTargets) == 'ABORT': 
            # If we have an abort, we need to restore the card to its triggered mode so that the player may change targets and try again. 
            # Since we've already cleared the card to avoid it's "in-a-trigger" state from affecting effects which remove it from play, we need to re-store it now.
            # Since we already have its tuple stored locally, we just use storeCardEffects to save it back again.
            storeCardEffects(card,selectedAbility[card._id][0],selectedAbility[card._id][1],selectedAbility[card._id][2],selectedAbility[card._id][3],selectedAbility[card._id][4],selectedAbility[card._id][5])
            readyEffect(card,True)
            return
      debugNotify("selectedAbility action = {}".format(selectedAbility[card._id][3]),2)
      continueOriginalEvent(card,selectedAbility)
      if card.Type == 'Event': 
         autoscriptOtherPlayers('CardPlayed',card)
         if findMarker(card, "Destination:Command Deck"):
            notify(" -- {} is moved to the top of {}'s command deck".format(card,card.owner))
            rnd(1,100) # To allow any notifications to announce the card correctly first.
            card.moveTo(card.owner.piles['Command Deck'])
         else: card.moveTo(card.owner.piles['Discard Pile']) # We discard events as soon as their effects are resolved.      
   elif card.highlight == UnpaidColor: purchaseCard(card) # If the player is double clicking on an unpaid card, we assume they just want to bypass complete payment.
   elif card.Type == 'Character' and getGlobalVariable('Committed Story') != [] and phase == 6 and not findMarker(card, "isAttachment"): 
      if debugVerbosity >= 2: notify("Card is Unit and it's engagement time") # Debug
      if card.orientation == Rot0: participate(card)
      else: strike(card)
   elif card.AutoAction != '': useAbility(card)
   elif card.Type == 'Character':
      status = cardStatus(card)
      if status == "InPlay":
         exhaustCard(card,x,y,True)
      elif status == "Exhausted":
         readyCard(card,x,y,True)
      elif status == "Insane":
         restoreCard(card,x,y,True)         
   elif card.Name == 'Drain Token':
      if getAttached(card) is not None:
         if confirm("Do you really want to remove this Drain Token?"):
            Stored_Attachments[card._id] = ""
            card.moveTo(me.piles['Discard Pile'])
            notify("{} refreshed a domain.".format(me))
         else: return
      else:
         Stored_Attachments[card._id] = ""
         card.moveTo(me.piles['Discard Pile'])
         notify("{} cleared up a loose drain token.".format(me))
   elif cardStatus(card) == 'Domain': #Add Payment Effects ----
      clearedDomains = 0
      att = getAttachments(card)
      wasdrained = False
      if len(att) > 0:
         for subatt in att:
            if Card(subatt).name == "Drain Token":
               if confirm("Do you really want to remove this Drain Token?"):
                  Stored_Attachments[subatt] = ""
                  Card(subatt).moveTo(me.piles['Discard Pile'])
                  clearedDomains += 1
         if clearedDomains: 
            notify("{} refreshed {} domains.".format(me,clearedDomains))
            wasdrained = True
      if wasdrained == False:
         generate(card)
   else: whisper(":::ERROR::: There is nothing to do with this card at this moment!")
   if debugVerbosity >= 3: notify("<<< defaultAction()") #Debug

def insaneOrSane(card, x = 0, y = 0):
   mute()
   if card.type=="Character":
      if cardStatus(card) == "InPlay" or cardStatus(card) == "Exhausted":
         makeInsane(card, x, y, True)
      elif cardStatus(card) == "Insane":
         restoreCard(card, x, y, True)
def findUnpaidCard():
   global unpaidCard
   if debugVerbosity >= 1: notify(">>> findUnpaidCard()") #Debug
   if unpaidCard: return unpaidCard
   else:
      for card in table:
         if (card.highlight == UnpaidColor or card.highlight == UnpaidAbilityColor) and card.controller == me: return card
   if debugVerbosity >= 3: notify("<<< findUnpaidCard()") #Debug
   return None # If not unpaid card is found, return None
#------------------------------------------------------------------------------
# Hand Actions
#------------------------------------------------------------------------------
def currentHandSize(player = me):
   debugNotify(">>> currentHandSize(){}".format(extraASDebug())) #Debug
   #if specialCard.markers[mdict['BrainDMG']]: currHandSize =  player.counters['Hand Size'].value - specialCard.markers[mdict['BrainDMG']]
   #else: currHandSize = player.counters['Hand Size'].value
   currHandSize = player.handSize
   return currHandSize
   
def playResource(card, x = 0, y = 0):
	mute()
	src = card.group
	resourcesToPlay = num(me.getGlobalVariable('resourcesToPlay'))
	currentPhase = num(me.getGlobalVariable('Phase'))
	if currentPhase != -1 and currentPhase != 3:
		whisper("You may only play resources before the game begins and during your Resource phase.")
		return
	if resourcesToPlay > 0:
		target = [c for c in table if c.targetedBy and c.controller == me and c.targetedBy == me and cardStatus(c) == "Domain"]
		debugNotify("Target: {}".format(len(target)),4)
		if len(target) == 1:
			debugNotify(">>> ResourceCount: {}".format(countResources(target[0])),4)
			if turnNumber() == 0 and countResources(target[0]) > 0: 
				whisper("Before game begins, you may only play one resource per domain.")
				return
			x,y = target[0].position
			card.moveToTable(x,y)
			card.orientation ^= Rot180
			addResource(target[0],card)
			resourcesToPlay -= 1
			storeAttachment(card,target[0],False,True)
			debugNotify("Arranging",2)
			arrangeAttachments(target[0])
			target[0].target(False)
			if turnNumber() == 0:
				if resourcesToPlay > 0:
					notify("{} brings in an initial {} resource from their hand.  {} to go.".format(me, card.faction, resourcesToPlay))
					me.setGlobalVariable('gameReady',False)
				else:
					notify("{} brings in an initial {} resource from their hand.  They are ready to begin.".format(me, card.faction))
					me.setGlobalVariable('gameReady',True)
			else: 		
				notify("{} brings in a {} resource from their hand.".format(me, card.Faction))				
			me.setGlobalVariable('resourcesToPlay',resourcesToPlay)
		else: whisper("Please target one of your domains.")
	else: whisper("You've already played all your resources this turn.")
	
def play(card, x = 0, y = 0):
   if debugVerbosity >= 1: notify(">>> play(){}".format(extraASDebug())) #Debug
   global unpaidCard
   mute()
   extraTXT = ''
   target = [c for c in table if c.targetedBy and c.controller == me and c.targetedBy == me and cardStatus(c) == "Domain"]
   if len(target) == 1:
      playResource(card, x, y)
      return
   if ((card.Type == 'Character' or card.Type == 'Support')
      and (me.getGlobalVariable('Phase') != '4')
      and not confirm(":::WARNING:::\n\nNormally this type of card cannot be played outside the Operations phase. Are you sure you want to continue?")):
         return 
   if card.Type == 'Support' and hasSubType(card, 'Attachment.'):
      debugNotify("### Checking for host type",2)
      hostType = re.search(r'Placement:([A-Za-z1-9:_ ]+)', card.AutoScript)
      if hostType:
         if debugVerbosity >= 2: notify("### hostType: {}.".format(hostType.group(1))) #Debug
         host = findTarget('Targeted-at{}'.format(hostType.group(1)))
         if host == []: 
            whisper("ABORTING!")
            return
         else: extraTXT = ' on {}'.format(host[0])
   steadfast = cardSteadfast(card)
   if steadfast: 
      notify("Steadfast: {}".format(steadfast))
      resourceCount = countAllResources(faction = card.Faction)
      notify("Resources: {}".format(resourceCount))
      if resourceCount < steadfast:
         if confirm("This card has a Steadfast Value of {} and you only have {} total {} resource(s).\n\nBypass steadfast restriction?".format(steadfast, resourceCount, card.Faction)):
            extraTXT += " (Bypassing Steadfast Restriction!)"
         else: return
   if re.search(r'[*]',card.Name):
      foundUnique = None
      debugNotify("### Card is Unique",2)
      cardlist = [c for c in table if c.controller == me]
      for c in cardlist:
         if c.name == card.name: 
            foundUnique = c
            break
      if foundUnique:
         if foundUnique.owner == me: confirmTXT = "This card is unique and you already have a copy of {} in play.\n\nBypass uniqueness restriction?".format(foundUnique.name)
         else: confirmTXT = "This card is unique and {} already has a copy of {} in play.\n\nBypass uniqueness restriction?".format(foundUnique.owner.name,foundUnique.name)
         if confirm(confirmTXT):
            extraTXT += " (Bypassing Uniqueness Restriction!)"
         else: return  
   debugNotify("About to move card to table")
   card.moveToTable(270, 20 + yaxisMove(card))
   if checkPaidResources(card) == 'NOK':
      card.highlight = UnpaidColor 
      unpaidCard = card
      notify("{} attempts to play {}{}.".format(me, card,extraTXT))
      # if num(card.Cost) == 0 and card.Type == 'Event': readyEffect(card)
   else: 
      if card.Type == 'Event':
         executePlayScripts(card, 'PLAY') # We do not trigger events automatically, in order to give the opponent a chance to play counter cards
      else:
         placeCard(card)
         notify("{} plays {}{}.".format(me, card,extraTXT))
         executePlayScripts(card, 'PLAY') # We execute the play scripts here only if the card is 0 cost.
         autoscriptOtherPlayers('CardPlayed',card)

def checkPaidResources(card):
   if debugVerbosity >= 1: notify(">>> checkPaidResources()") #Debug
   count = 0
   affiliationMatch = False
   for cMarkerKey in card.markers: #We check the key of each marker on the card
      for resdictKey in resdict:  #against each resource type available
         if debugVerbosity >= 2: notify("About to compare marker keys: {} and {}".format(resdict[resdictKey],cMarkerKey)) #Debug
         if resdict[resdictKey] == cMarkerKey: # If the marker is a resource
            count += card.markers[cMarkerKey]  # We increase the count of how many resources have been paid for this card
            if debugVerbosity >= 2: notify("About to check found resource affiliaton") #Debug
            if 'Resource:{}'.format(card.Faction) == resdictKey: # if the card's affiliation also matches the currently checked resource
               if debugVerbosity >= 3: notify("### Affiliation match. Affiliation = {}. Marker = {}.".format(card.Faction,resdictKey))
               affiliationMatch = True # We set that we've also got a matching resource affiliation
      if cMarkerKey[0] == "Ignores Affiliation Match": 
         if debugVerbosity >= 3: notify("### Ignoring affiliation match due to marker on card. Marker = {}".format(cMarkerKey))
         affiliationMatch = True # If we have a marker that ignores affiliations, we can start ignoring this card's as well
   for c in table:
      debugNotify("Checking: {}".format(c.Name))
      if c.controller == me and re.search("IgnoreAffiliationMatch",c.AutoScript) and chkDummy(c.AutoScript, c): 
         notify(":> Affiliation match ignored due to {}.".format(c))
         affiliationMatch = True
   if debugVerbosity >= 2: notify("About to check successful cost. Count: {}, Faction: {}".format(count,card.Faction)) #Debug
   if card.highlight == UnpaidAbilityColor:
      selectedAbility = eval(getGlobalVariable('Stored Effects'))
      reduction = reduceCost(card, 'USE', selectedAbility[card._id][1] - count, dryRun = True) # We do a dry run first. We do not want to trigger once-per turn abilities until the point where we've actually paid the cost.
      if count >= selectedAbility[card._id][1] - reduction:
         if debugVerbosity >= 3: notify("<<< checkPaidResources(). Return USEOK") #Debug
         reduceCost(card, 'USE', selectedAbility[card._id][1] - count) # Now that we've actually made sure we've paid the cost, we use any ability that reduces costs.
         return 'USEOK'
      else:
         if count >= selectedAbility[card._id][1] - reduction and not affiliationMatch:
            notify(":::WARNING::: Ability cost reached but there is no affiliation match!")
         if debugVerbosity >= 3: notify("<<< checkPaidResources(). Return NOK 1") #Debug
         return 'NOK'      
   else:
      reduction = reduceCost(card, 'PLAY', num(card.Cost) - count, dryRun = True) # We do a dry run first. We do not want to trigger once-per turn abilities until the point where we've actually paid the cost.
      notify("1a- {}".format(reduction))
      if count >= num(card.Cost) - reduction and (card.Faction == 'Neutral' or affiliationMatch or (not affiliationMatch and (num(card.Cost) - reduction) == 0)):
         #notify("1b")
         if countResources(card,card.Faction) >= num(card.Cost) - reduction or not hasKeyword(card,'Loyal.'):
            #notify("1c")
            if debugVerbosity >= 3: notify("<<< checkPaidResources(). Return OK") #Debug
            reduceCost(card, 'PLAY', num(card.Cost) - count) # Now that we've actually made sure we've paid the cost, we use any ability that reduces costs.
            return 'OK'
         else:
            notify(":::WARNING::: Card is Loyal, and there aren't enough {} resources to pay for it.".format(card.Faction))
            if debugVerbosity >= 3: notify("<<< checkPaidResources(). Return NOK 3") #Debug
            return 'NOK'
      else:
         if count >= num(card.Cost) - reduction and not affiliationMatch:
            notify(":::WARNING::: Card cost reached but there is no affiliation match!")
         if debugVerbosity >= 3: notify("<<< checkPaidResources(). Return NOK 2") #Debug
         return 'NOK'
def purchaseCard(card, x=0, y=0, manual = True):
   if debugVerbosity >= 1: notify(">>> purchaseCard(){}".format(extraASDebug())) #Debug
   global unpaidCard
   if manual and card.highlight != ReadyEffectColor: checkPaid = checkPaidResources(card)
   # If this is an attempt to manually pay for the card, we check that the player can afford it (e.g. it's zero cost or has cost reduction effects)
   # Events marked as 'ReadyEffectColor' have already been paid, so we do not need to check them again.
   else: checkPaid = 'OK' #If it's not manual, then it means the checkPaidResources() has been run successfully, so we proceed.
   if checkPaid == 'OK' or confirm(":::ERROR::: You do have not yet paid the cost of this card. Bypass?"):
      # if the card has been fully paid, we remove the resource markers and move it at its final position.
      card.highlight = None
      placeCard(card)
      clrResourceMarkers(card)
      unpaidCard = None
      if checkPaid == 'OK': notify("{} has paid for {}".format(me,card)) 
      else: notify(":::ATTENTION::: {} has played {} by skipping its full cost".format(me,card))
      executePlayScripts(card, 'PLAY') 
      if card.Type != 'Event': autoscriptOtherPlayers('CardPlayed',card) # We script for playing events only after their events have finished resolving in the default action.
   if debugVerbosity >= 3: notify("<<< purchaseCard()") #Debug
def generate(card, x = 0, y = 0):
   if debugVerbosity >= 1: notify(">>> generate(){}".format(extraASDebug())) #Debug
   mute()
   unpaidC = findUnpaidCard()
   if not unpaidC: 
      whisper(":::ERROR::: You are not attempting to pay for a card or effect. ABORTING!")
      return
   att = getAttachments(card)
   drainTokens = 0
   for subatt in att: 
      if Card(subatt).name == "Drain Token": drainTokens += 1
   if drainTokens > 0 and not confirm("Card is already exhausted. Bypass?"): 
      return
   for cMarkerKey in card.markers:
      for resKey in resdict:
         if resdict[resKey] == cMarkerKey:
            unpaidC.markers[cMarkerKey] += card.markers[cMarkerKey]
   resResult = checkPaidResources(unpaidC)
   if resResult == 'OK': 
      xp, yp = card.position
      token = table.create("d42706b4-2721-439e-a41f-0611d6beb449", xp , yp , 1)
      storeAttachment(token,card)
      arrangeAttachments(card)
      notify("{} drained a domain to pay for {}.".format(me,unpaidC))
      #executePlayScripts(card, 'GENERATE')
      #autoscriptOtherPlayers('ResourceGenerated',card)
      purchaseCard(unpaidC, manual = False)
   elif resResult == 'USEOK': 
      xp, yp = card.position
      token = table.create("d42706b4-2721-439e-a41f-0611d6beb449", xp , yp , 1)
      storeAttachment(token,card)
      arrangeAttachments(card)
      notify("{} drained a domain to pay for {}'s effect.".format(me,unpaidC))
      #executePlayScripts(card, 'GENERATE')
      #autoscriptOtherPlayers('ResourceGenerated',card)
      readyEffect(unpaidC)
   elif resResult == 'NOK':
      whisper(":::ERROR::: Domain does not have enough resources to pay for {}.".format(unpaidC))
      clrResourceMarkers(unpaidC)
   if debugVerbosity >= 3: notify("<<< generate()") #Debug
#------------------------------------------------------------------------------
# Button and Announcement functions
#------------------------------------------------------------------------------

def BUTTON_OK(group = None,x=0,y=0):
   notify("--- {} has no further reactions.".format(me))

def BUTTON_Wait(group = None,x=0,y=0):  
   notify("--- Wait! {} wants to react.".format(me))

def BUTTON_Actions(group = None,x=0,y=0):  
   notify("--- {} is waiting for opposing actions.".format(me))

def declarePass(group, x=0, y=0):
   notify("--- {} Passes".format(me))    
def destroyCard(card, x=0, y=0, auto=False):
   if card.controller == me and (auto or confirm("Are you sure you want to send {} and any attachments to the discard pile?".format(card))):
      global Stored_Attachments
      att = getAttachments(card)
      for subatt in att:
         Stored_Attachments[subatt] = ''
         Card(subatt).moveTo(Card(subatt).owner.piles['Discard Pile'])
      freeUnitPlacement(card)
      card.moveTo(card.owner.piles['Discard Pile'])
   else: return