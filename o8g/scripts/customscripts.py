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
    debugNotify(">>> CustomScript() with action: {}".format(action)) #Debug
    mute()
    discardPile = me.piles['Discard Pile']
    deck = me.piles['Deck']
    if card.name == '* Professor Hermann Mulder' and action == 'CardPlayed' and card.owner == me:
        debugNotify("Professor Hermann Mulder")
        characterList = [c for c in table if fetchProperty(c,'Type') == 'Character' and c.orientation != Rot270]
        if len(characterList) >= 6:
            notify("There are too many characters in play.  {} is driven insane.".format(card.name))
            makeInsane(card,verbose=False)
        else: return 'ABORT'
    elif card.name == '* Paul Lemond':
        debugNotify("Paul Lemond")
        chosenCard = None
        cardList = [c for c in table if c.orientation != Rot270 and c.highlight != DummyColor and c.highlight != UnpaidColor and fetchProperty(c,'Type') == 'Character']
        choiceList = makeChoiceListfromCardList(cardList)
        debugNotify("Choices: {}".format(choiceList))
        cardChoice = SingleChoice("Choose a character for Paul Lemond to gain the icons of.",choiceList)
        if cardChoice == None: 
            whisper("No choice made.  Aborting")
            return 'ABORT'
        else: chosenCard = cardList[cardChoice]
        if chooseAndDrainDomain(1) == 'ABORT': 
            whisper("Unable to pay for ability. Aborting")
            return 'ABORT'
        notify("{} activates {}'s ability, targeting {}".format(me,card.name,chosenCard.name))
        modifyCard(card,modifier = 'Add', property = 'Icons', duration = 'PhaseEnd', modification = chosenCard.Icons)
    elif card.name == 'Shotgun':
        debugNotify("Shotgun")
        host = getAttached(card)
        if host:
            modifyCard(host, modifier = 'Add', property = 'AutoAction', duration = '{}LeavesPlay'.format(card._id), modification = 'whileCommitted:Drain1-isCost$$whileCommitted:Deal1Wound-DemiAutoTargeted-atCharacter-alsoCommitted-choose1')
    elif card.name == 'Paddy Wagon':
        debugNotify("Paddy Wagon")
        host = getAttached(card)
        if host:
            modifyCard(host, modifier = 'Add', property = 'AutoScript', duration = '{}LeavesPlay'.format(card._id), modification = 'onDamage:Drain2-isCost$$onDamage:Put1Wound Prevention-DemiAutoTargeted-atCharacter-alsoCommitted-choose1')
    elif card.name == 'Small Price to Pay':
        debugNotify("Small Price to Pay")
        myCharacter = findTarget('DemiAutoTargeted-atCharacter-ofMine-choose1')
        if len(myCharacter) != 1:
            notify("No target of {}'s chosen.  Aborting".format(me.name))
            return 'ABORT'
        opponentsCharacter = findTarget('DemiAutoTargeted-atCharacter-ofOpponent-choose1')
        if len(opponentsCharacter) != 1:
            notify("No target of {}'s chosen. Aborting".format(ofWhom('ofOppoent').name))
            return 'ABORT'
        targets = []
        targets.extend(myCharacter)
        targets.extend(opponentsCharacter)
        choiceList = makeChoiceListfromCardList(targets)
        debugNotify("Choices: {}".format(choiceList))
        cardChoice = SingleChoice("Choose a character to drive insane.",choiceList)
        if cardChoice == None: 
            whisper("No choice made.  Aborting")
            return 'ABORT'
        else:
            insaneName = cardChoice.name
            woundName = ''
            if makeInsane(cardChoice) == 'ABORT':
                return 'ABORT'
            else:
                for c in targets:
                    if c != cardChoice:
                        if addMarker(c, 'Wound', silent = True) == 'ABORT': return 'ABORT'
                        else: woundName = c.name
                notify("{} plays {}, driving {} insane, and wounding {}.".format(me,card.name, insaneName, woundName))
    elif card.name == '* Professor Albert Wilmarth':
        debugNotify("Add Code to put an icon on Albert.") # ---
    else: notify("{} uses {}'s ability".format(me,card)) # Just a catch-all.

def markerScripts(card, action = 'USE'):
    return False