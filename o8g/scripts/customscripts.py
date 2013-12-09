    # Python Scripts for the Call of Cthulhu LCG definition for OCTGN
    # Copyright (C) 2013  Jason Cline   
    # Based heavily on the Python Scripts for the Android:Netrunner LCG definition for OCTGN
    # Copyright (C) 2012  Konstantine Thoukydides

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
# This file contains the autoscripting for cards with specialized effects. So called 'CustomScripts'
# * UseCustomAbility() is used among other scripts, and it just one custom ability among other normal core commands
# * CustomScipt() is a completely specialized effect, that is usually so unique, that it's not worth updating my core commands to facilitate it for just one card.
###=================================================================================================================###

def UseCustomAbility(Autoscript, announceText, card, targetCards = None, notification = None, n = 0): # not used yet.
    announceString = announceText 
    return announceString

def CustomScript(card, action = 'PLAY'): # Scripts that are complex and fairly unique to specific cards, not worth making a whole generic function for them.
    if debugVerbosity >= 1: notify(">>> CustomScript() with action: {}".format(action)) #Debug
    mute()
    discardPile = me.piles['Discard Pile']
    objectives = me.piles['Objective Deck']
    deck = me.piles['Deck']
    if card.name == '* Professor Hermann Mulder' and action == 'CardPlayed' and card.owner == me:
        if debugVerbosity >= 2: notify("### Professor Hermann Mulder")
        characterList = [c for c in table if c.type == 'Character' and c.orientation != Rot270]
        if len(characterList) >= 6:
            notify("There are too many characters in play.  {} is driven insane.")
            makeInsane(card,verbose=False)
    else: notify("{} uses {}'s ability".format(me,card)) # Just a catch-all.
