    # Python Scripts for the Call of Cthulhu LCG definition for OCTGN
    # Copyright (C) 2012  Jason Cline

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
def intSetup(group, x = 0, y = 0):
   debugNotify(">>> intSetup(){}".format(extraASDebug())) #Debug
   global ds, Identity
   mute()
   if not startupMsg: fetchCardScripts() # We only download the scripts at the very first setup of each play session.
   versionCheck()
   if ds and not confirm("Are you sure you want to setup for a new game? (This action should only be done after a table reset)"): return
   ds = None
   if not table.isTwoSided() and not confirm(":::WARNING::: This game is designed to be played on a two-sided table. Things will be extremely uncomfortable otherwise!! Please start a new game and makde sure the  the appropriate button is checked. Are you sure you want to continue?"): return
   chooseSide()
   #for type in Automations: switchAutomation(type,'Announce') # Too much spam.
   deck = me.piles['R&D/Stack']
   debugNotify("Checking Deck", 3)
   if len(deck) == 0:
      whisper ("Please load a deck first!")
      return
   debugNotify("Reseting Variables", 3)
   resetAll()
   debugNotify("Placing Identity", 3)
   for card in me.hand:
      if card.Type != 'Identity':
         whisper(":::Warning::: You are not supposed to have any non-Identity cards in your hand when you start the game")
         card.moveToBottom(me.piles['R&D/Stack'])
         continue
      else:
         ds = card.Side.lower()
         storeSpecial(card)
         me.setGlobalVariable('ds', ds)
   if not ds:
      confirm("You need to have your identity card in your hand when you try to setup the game. If you have it in your deck, please look for it and put it in your hand before running this function again")
      return
   debugNotify("Giving Possible Warning", 3)
   if (ds == 'corp' and me.hasInvertedTable()) or (ds == 'runner' and not me.hasInvertedTable()):
      if not confirm(":::ERROR::: Due to engine limitations, the corp player must always be player [A] in order to properly utilize the board. Please start a new game and make sure you've set the corp to be player [A] in the lobby. Are you sure you want to continue?"): return
   debugNotify("Checking Illegality", 3)
   deckStatus = checkDeck(deck)
   if not deckStatus[0]:
      if not confirm("We have found illegal cards in your deck. Bypass?"): return
      else:
         notify("{} has chosen to proceed with an illegal deck.".format(me))
         Identity = deckStatus[1]
   else: Identity = deckStatus[1] # For code readability
   debugNotify("Placing Identity", 3)
   debugNotify("Identity is: {}".format(Identity), 3)
   if ds == "corp":
      Identity.moveToTable(169, 255)
      rnd(1,10) # Allow time for the ident to be recognised
      modClicks(count = 3, action = 'set to')
      me.MU = 0
      notify("{} is the CEO of the {} Corporation".format(me,Identity))
   else:
      Identity.moveToTable(106, -331)
      rnd(1,10)  # Allow time for the ident to be recognised
      modClicks(count = 4, action = 'set to')
      me.MU = 4
      BL = num(Identity.Cost)
      me.counters['Base Link'].value = BL
      notify("{} is representing the Runner {}. They start with {} {}".format(me,Identity,BL,uniLink()))
   debugNotify("Creating Starting Cards", 3)
   createStartingCards()
   debugNotify("Shuffling Deck", 3)
   shuffle(me.piles['R&D/Stack'])
   debugNotify("Drawing 5 Cards", 3)
   notify("{}'s {} is shuffled ".format(me,pileName(me.piles['R&D/Stack'])))
   drawMany(me.piles['R&D/Stack'], 5)
   debugNotify("Reshuffling Deck", 3)
   shuffle(me.piles['R&D/Stack']) # And another one just to be sure
   executePlayScripts(Identity,'STARTUP')
   initGame()

