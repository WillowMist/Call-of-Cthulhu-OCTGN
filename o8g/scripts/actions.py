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


#---------------------------------------------
# Start/End of Turn
#---------------------------------------------

#---------------------------------------------
# Game Setup
#---------------------------------------------
def createStartingCards():
	try:
		debugNotify(">>> createStartingCards()") #Debug
		if me.hasInvertedTable() == True: 
			table.create("a8cec1b8-1121-4612-80c4-c66a437cc2e0", -50, 50, 1)
			table.create("f22ee55c-8f47-4174-a7a4-985731a74d30", -150, 50, 1)
			table.create("d8a151e4-28c8-4653-b826-ebda237b776b", -250, 50, 1)
		else: 
			table.create("0054c047-1887-4a5d-b11b-b70f3cff3a0a", -300, 170, 1)
			table.create("593da3cb-290b-426e-9eec-1b3fd3465a2d", -200, 170, 1)
			table.create("46cfc241-12ea-4d15-91f5-0facf26a9d82", -100, 170, 1)
	except: notify("!!!ERROR!!! {} - In createStartingCards()\n!!! PLEASE INSTALL MARKERS SET FILE !!!".format(me))

def intSetup(group, x = 0, y = 0):
   debugNotify(">>> intSetup(){}".format(extraASDebug())) #Debug
   mute()
   if not startupMsg: fetchCardScripts() # We only download the scripts at the very first setup of each play session.
   versionCheck()
   if not confirm("Are you sure you want to setup for a new game? (This action should only be done after a table reset)"): return
   if not table.isTwoSided() and not confirm(":::WARNING::: This game is designed to be played on a two-sided table. Things will be extremely uncomfortable otherwise!! Please start a new game and makde sure the  the appropriate button is checked. Are you sure you want to continue?"): return
   chooseSide()
   #for type in Automations: switchAutomation(type,'Announce') # Too much spam.
   deck = me.piles['Deck']
   debugNotify("Checking Deck", 3)
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
   if not deckStatus[0]:
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
   executePlayScripts(Identity,'STARTUP')

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


