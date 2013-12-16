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
import sys

iteration = 0
#---------------------------------------------
# Phases
#---------------------------------------------

def showCurrentPhase(): # Just say a nice notification about which phase you're on.
    storyPhase = num(getGlobalVariable('Story Phase'))
    if storyPhase != -1:
        notify(storyPhases[num(getGlobalVariable('Story Phase'))])
    else: 
        notify(phases[num(me.getGlobalVariable('Phase'))])

def nextPhase(group = table, x = 0, y = 0, setTo = None):  
    # Function to take you to the next phase. 
    opponent = ofwhom('ofOpponent')
    if not gameReady():
        whisper("One or more players have not completed setup yet.")
        return
    if not gameStarted():
        if not confirm("The game has not yet begun.  Would you like to begin it now?"): return
        else:
            startGame(table)
            return
    debugNotify(">>> nextPhase()") #Debug
    mute()
    committedStory = getGlobalVariable('Current Story')
    currentStories = eval(getGlobalVariable('Committed Stories'))
    if Automations['Start/End-of-Turn/Phase'] and num(getGlobalVariable('Story Phase')) > -1:
        setGlobalVariable('lastStruggleResults',"(0,0)")
        phase = num(getGlobalVariable('Story Phase'))
        if (phase == 1 and (len(getPlayers())==1 or not me.isActivePlayer )) or (phase != 1 and me.isActivePlayer):
            struggleIcons = eval(getGlobalVariable('struggleIcons'))
            if phase == 1 or phase == 0: clearTargets()
            if phase == 3 and len(struggleIcons) == 0: setGlobalVariable('storyResolution', "True")
            if phase == 2 and committedStory == "None" :
                if len(currentStories) > 0: phase = 2
                else: phase = 6
            elif phase == 3 and len(struggleIcons) > 0: phase = 3            
            elif phase == 4 and eval(getGlobalVariable('storyResolution')): phase = 4
            elif setTo: phase = setTo
            else: phase += 1
            #if phase == 4: revealEdge(forceCalc = True) # Just to make sure it wasn't forgotten.
            setGlobalVariable('Story Phase',str(phase))
            showCurrentPhase()
            if not setTo:
                if phase == 1: 
                    myStories = eval(me.getGlobalVariable('committedCharacters'))
                    if len(myStories) > 0 and len(eval(getGlobalVariable('Committed Stories'))) == 0:
                        committedStories = []
                        for key, val in myStories.iteritems():
                            committedStories.append(num(key))
                        setGlobalVariable('Committed Stories',str(committedStories))
                    if len(eval(getGlobalVariable('Committed Stories'))) > 0:
                        notify("{} may now commit characters to stories.  Target the story (shift-click) and then double click the characters to commit to it. Ctrl-Enter or 'Next Phase' to continue.".format(opponent))
                    else:
                        setGlobalVariable('Story Phase',"-1")
                        nextPhase()
                elif phase == 2:
                    if me.isActivePlayer: goToSelectStory()
                    else:
                        for player in getPlayers():
                            if player.isActivePlayer: remoteCall(player,"goToSelectStory",[])
                elif phase == 3: 
                    if me.isActivePlayer: goToIconStruggles()
                    else:
                        for player in getPlayers():
                            if player.isActivePlayer: remoteCall(player,"goToIconStruggles",[])
                elif phase == 4:
                    goToDetermineSuccess()
                elif phase == 5: finishStory() # If it's the reward unopposed phase, we simply end the engagement immediately after
                elif phase >= 6:
                    setGlobalVariable('Story Phase', "-1")
                    nextPhase()
        else: notify("{} tried to advance to the next Story Phase, but does not have control yet.".format(me))
    else:
        debugNotify("Normal Phase change")
        phase = num(me.getGlobalVariable('Phase'))
        if not me.isActivePlayer:
            debugNotify("Not currently the active player")
            #debugNotify("### Active Player: {}".format(getGlobalVariable('Active Player'))) #Debug
            if not confirm("Your opponent has not finished their turn yet. Are you sure you want to jump to your turn?"): return
            me.setActivePlayer() # new in OCTGN 3.0.5.47 
            me.setGlobalVariable('Phase','1')
            #setGlobalVariable('Active Player', me.name)
            phase = 1
        else: 
            debugNotify("Normal Phase change")
            if phase == -1: phase = 1 # This is for the first phase of the LS player.
            else:
                atTimedEffects("EndPhase")
                phase += 1
            me.setGlobalVariable('Phase',str(phase)) # Otherwise, just move up one phase
        if phase == 1: goToRefresh()
        elif phase == 2: goToDraw()
        elif phase == 3: goToResource()
        elif phase == 4: goToOperations()
        elif phase == 5: 
            if turnNumber() == 1:
                notify(":::NOTICE::: {} skips their first story phase".format(me))
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
    Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
    debugNotify(">>> goToRefresh(){} - {}".format(extraASDebug(),num(me.getGlobalVariable('Phase')))) #Debug
    atTimedEffects(Time = 'Start')   
    mute()
    me.setGlobalVariable('Phase','1')
    me.setGlobalVariable('resourcesToPlay','1')
    me.setGlobalVariable('restoredInsane','0')
    showCurrentPhase()
    if not Automations['Start/End-of-Turn/Phase']: return
    autoRefresh(verbose = False)
    atTimedEffects(Time = 'afterCardRefreshing') 
    nextPhase()


def goToDraw(group = table, x = 0, y = 0): # Go directly to the Draw phase
    debugNotify(">>> goToDraw(){}".format(extraASDebug())) #Debug
    atTimedEffects(Time = 'afterRefresh') # We put "afterRefresh" in the refresh phase, as cards trigger immediately after refreshing. Not after the refresh phase as a whole.
    mute()
    me.setGlobalVariable('Phase','2')
    showCurrentPhase()
    if not Automations['Start/End-of-Turn/Phase']: return
    if turnNumber() == 1: draw()
    else: drawMany(count=2)
    nextPhase()


def goToResource(group = table, x = 0, y = 0):
    debugNotify(">>> goToResource(){}".format(extraASDebug())) #Debug
    atTimedEffects(Time = 'afterDraw')   
    mute()
    me.setGlobalVariable('Phase','3')
    showCurrentPhase()
    
def goToOperations(group = table, x = 0, y = 0):
    debugNotify(">>> goToOperations(){}".format(extraASDebug())) #Debug
    atTimedEffects(Time = 'afterResource')   
    mute()
    me.setGlobalVariable('Phase','4')
    showCurrentPhase()
    
def goToStory(group = table, x = 0, y = 0):
    debugNotify(">>> goToStory(){}".format(extraASDebug())) #Debug
    atTimedEffects(Time = 'afterOperations')   
    mute()
    me.setGlobalVariable('Phase','5')
    showCurrentPhase()
    if not Automations['Start/End-of-Turn/Phase']: return
    notify("{} may now commit characters to stories.  Target the story (hift-click) and then double click the characters to commit to it. Ctrl-Enter or 'Next Phase' to continue.".format(me))
#---------------------------------------------
# Story Phases
#---------------------------------------------
def goToSelectStory(group = table, x = 0, y = 0):
    targetedStories = [c for c in table if c.targetedBy and c.targetedBy == me and (cardStatus(c) == "Story" or cardStatus(c) == "Conspiracy")]
    if len(targetedStories) > 1:
        delayed_whisper("NOTICE:  You may only target one story at a time for resolution.  Please Resolve and try again.")
        return
    currentStory = getGlobalVariable('Current Story')
    if len(targetedStories) == 0:
        notify("Resolve Stores: {} should now target a story (double click) and then continue (Next phase or Ctrl-enter)".format(me.name))
    else:
        if currentStory != "None":
            notify("NOTICE:  There is already a current story. This should never happen. Please notify the developer.")
        else:
            setGlobalVariable('Current Story',str(targetedStories[0]._id))
            nextPhase()
        
def goToIconStruggles(group = table, x = 0, y = 0):
    global iteration
    mute()
    debugNotify(">>> goToIconStruggles()")
    c = num(getGlobalVariable('Current Story'))
    card = Card(c)
    resolve = getGlobalVariable('iconResolution')
    resolveReady = -1
    storyIcons = getStoryIcons(card)
    setGlobalVariable('struggleIcons',str(storyIcons))
    if len(storyIcons) == 0: nextPhase()
    currentStruggle = storyIcons[0]
    if resolve != '': 
        resolveStruggle()
        return
    if eval(getGlobalVariable('awaitingPlayers')):
        for player in getPlayers():
            if num(player.getGlobalVariable('iconTotal')) > -1:
                if resolveReady == -1: resolveReady = 1
            if num(player.getGlobalVariable('iconTotal')) == -1:
                if resolveReady > -1: resolveReady = 0
        debugNotify("Resolve: |{}|".format(resolveReady))
        if resolveReady == 1:
            setGlobalVariable('awaitingPlayers',"False")
            iteration = 0
            notify("{} Struggle: Comparing icon totals.".format(currentStruggle))
            tempTotal = -1
            tempWinner = None
            difference = 0
            for player in getPlayers():
                iconTotal = num(player.getGlobalVariable('iconTotal'))
                if iconTotal > tempTotal:
                    difference = iconTotal - tempTotal
                    tempTotal = iconTotal
                    tempWinner = player
                elif iconTotal == tempTotal:
                    difference = 0
                    tempWinner = None
                notify("{} Struggle: {}: {}".format(currentStruggle, player,player.getGlobalVariable('iconTotal')))
                if player != me: remoteCall(player,"clearIconTotals",[])
                else: clearIconTotals()
            if not tempWinner and tempTotal > 0:
                fastFound = None
                multiFastFound = False
                for player in getPlayers():
                    if eval(player.getGlobalVariable('hasFast')) and not fastFound: fastFound = player
                    elif eval(player.getGlobalVariable('hasFast')) and fastFound: multiFastFound = True
                if fastFound and not multiFastFound:
                    notify("{} Struggle: Icons tied, but {} has a character with the Fast keyword.".format(currentStruggle, player.name))
                    tempWinner = player
            if not tempWinner:
                notify("{} Struggle: No Winner, play responses or proceed to the next action (Ctrl-Enter)".format(currentStruggle))
                del storyIcons[0]
                setGlobalVariable('struggleIcons',str(storyIcons))
                setGlobalVariable('iconResolution','')
                setGlobalVariable('resolutionPending',"False")
            else:
                notify("{} Struggle: {} is the winner.".format(currentStruggle,tempWinner.name))
                setGlobalVariable('iconResolution',"('{}','{}', '{}')".format(tempWinner.name,currentStruggle, difference))
                setGlobalVariable('resolutionPending',"True")
                resolveStruggle()
        else:
            iteration += 1
            if iteration > 100:
                notify(":::WARNING::: Something went wrong.  Not all players were able to process their icon information.")
                iteration = 0
                return
            else: 
                update()
                goToIconStruggles()
                return
    else:
        debugNotify("Current Icon to Resolve: {}".format(currentStruggle))
        iteration = 0
        setGlobalVariable('awaitingPlayers',"True")
        for player in getPlayers(): 
            if player != me: remoteCall(player,"iconUpdate",[currentStruggle]) # change this for the current struggle
            else: iconUpdate(currentStruggle)
        goToIconStruggles()

def goToDetermineSuccess(group = table, x = 0, y = 0):
    mute()
    debugNotify(">>> goToDetermineSuccess()")
    resolveReady = -1
    if not eval(getGlobalVariable('storyResolution')):
        notify("Story resolved. Play responses or proceed to the next action (Ctrl-Enter)")
        return
    global iteration
    c = num(getGlobalVariable('Current Story'))
    card = Card(c)
    if eval(getGlobalVariable('awaitingPlayers')):
        for player in getPlayers():
            if num(player.getGlobalVariable('iconTotal')) > -1:
                if resolveReady == -1: resolveReady = 1
            if num(player.getGlobalVariable('iconTotal')) == -1:
                if resolveReady > -1: resolveReady = 0
        if resolveReady == 1:
            setGlobalVariable('awaitingPlayers',"False")
            iteration = 0
            mySkill = num(me.getGlobalVariable('iconTotal'))
            if mySkill > 0:
                notify("Determining story success")
                highestOpponentSkill = -1
                for player in getPlayers():
                    if player != me and num(player.getGlobalVariable('iconTotal')) > highestOpponentSkill: highestOpponentSkill = num(player.getGlobalVariable('iconTotal'))
                    notify("Story Resolution: {}: {}".format(player.name,player.getGlobalVariable('iconTotal')))
                    if player != me: remoteCall(player,"clearIconTotals",[])
                    else: clearIconTotals()
                debugNotify("Comparing: {} - {}".format(mySkill,highestOpponentSkill))
                if mySkill > highestOpponentSkill:
                    notify("{} has succeeded at {}.  Adding a success token.".format(me,card.name))
                    addSuccess(card)
                    runAutoScripts('StorySuccess',card)
                    if highestOpponentSkill <= 0:
                        notify("{} was unopposed.  Adding another success token.".format(me))
                        addSuccess(card)
                        runAutoScripts('StoryUnopposed',card)
                elif mySkill <= highestOpponentSkill:
                    notify("{} did not successfully win {}".format(me.name,card.name))
                    runAutoScripts('StoryFailed',card)
            else:
                notify("{}'s Skill total was 0 or less. {} was not a success.".format(me,card.name))
                runAutoScripts('StoryFailed',card)
            setGlobalVariable('storyResolution',"False")
            goToDetermineSuccess()
        else:
            iteration += 1
            if iteration > 100:
                notify(":::WARNING::: Something went wrong.  Not all players were able to process their icon information.")
                iteration = 0
                return
            else: 
                update()
                goToDetermineSuccess()
                return
    else:
        debugNotify("Gathering remaining committed Skill.")
        iteration = 0
        setGlobalVariable('awaitingPlayers',"True")
        for player in getPlayers(): 
            if player != me: remoteCall(player,"iconUpdate",["Skill"]) # change this for the current struggle
            else: iconUpdate("Skill")
        goToDetermineSuccess()






def finishStory():
    debugNotify(">>> finishStory()")
    for player in getPlayers():
        if player != me: 
            remoteCall(player,'clearCommitted',[])
            remoteCall(player,'clearIconTotals',[])
        else: 
            clearCommitted()
            clearIconTotals()
    currentStory = num(getGlobalVariable('Current Story'))
    tempStories = eval(getGlobalVariable('Committed Stories'))
    tempStories.remove(currentStory)
    setGlobalVariable('Committed Stories',str(tempStories))
    setGlobalVariable('Current Story',"None")
    if len(tempStories) > 0: setGlobalVariable('Story Phase',"2")
    else: setGlobalVariable('Story Phase',"-1")
    setGlobalVariable('iconResolution',"")
    setGlobalVariable('resolutionPending',"False")
    setGlobalVariable('storyResolution',"False")
    setGlobalVariable('awaitingPlayers',"False")
    setGlobalVariable('struggleIcons',"[]")
    clearTargets()
    nextPhase()
    
    
def resolveStruggle():
    mute()
    currentStory = Card(num(getGlobalVariable('Current Story')))
    debugNotify(">>> resolveStruggle()")
    resolve = eval(getGlobalVariable('iconResolution'))
    resolutionPending = eval(getGlobalVariable('resolutionPending'))
    if resolutionPending:
        update()
        if len(getPlayers()) > 1 and (resolve[1] == 'Terror' or resolve[1] == 'Combat'):
            for player in getPlayers():
                if player.name != resolve[0]: 
                    if player != me: remoteCall(player,"struggleResults",[resolve[1],me])
                    else: struggleResults(resolve[1],me)
        elif resolve[1] == 'Investigation' or resolve[1] == 'Arcane':
            for player in getPlayers():
                if player.name == resolve[0]: 
                    if player != me: remoteCall(player,"struggleResults",[resolve[1],me])
                    else: struggleResults(resolve[1],me)
        else:
            notify("{} Resolution: Single Player Mode, nobody to penalize.".format(resolve[1]))
            setGlobalVariable('resolutionPending',"False")
            resolveStruggle()
            return
    else:
        storyIcons = eval(getGlobalVariable('struggleIcons'))
        currentStruggle = storyIcons[0]
        setGlobalVariable('lastStruggleResults',"('{}',{})".format(resolve[0], resolve[2]))
        notify("{} resolved. Play responses or proceed to the next action (Ctrl-Enter)".format(currentStruggle))
        runAutoScripts('StruggleResolved',currentStory)
        del storyIcons[0]
        setGlobalVariable('struggleIcons',str(storyIcons))
        setGlobalVariable('iconResolution',"")
        return
    debugNotify("<<< resolveStruggle()")
    
def struggleResults(type, originator):
    mute()
    currentStory = Card(num(getGlobalVariable('Current Story')))
    committedCharacters = eval(me.getGlobalVariable('committedCharacters')).get(currentStory._id,[])
    setGlobalVariable('resolutionPending',"False")
    if type == 'Terror':
        notify("Resolve Terror Struggle: {} must drive one character insane.".format(me))
        tempCards = [c for c in table if c._id in committedCharacters and (cardStatus(c) == "InPlay" or cardStatus(c) == "Exhausted") and getIcons(c,"Terror") == 0] 
        if len(tempCards) > 0:
            cardIDs = []
            cardNames = []
            for c in tempCards:
                cardIDs.append(c._id)
                cardNames.append(c.name)
            cardChoice = SingleChoice("Choose a character to drive insane.",cardNames)
            if cardChoice == None:
                if confirm("Are you sure you want to skip resolving the Terror Struggle?"):
                    notify("{} has skipped the Terror Resolution and chosen not to drive a character insane.".format(me))
            else:
                card = Card(cardIDs[cardChoice])
                makeInsane(card)
        else:
            notify("Terror Resolution: {} doesn't have any eligible characters to be driven insane.".format(me))
    elif type == 'Combat':
        notify("Resolve Combat Struggle: {} must wound one character.".format(me))
        tempCards = [c for c in table if c._id in committedCharacters and (cardStatus(c) == "InPlay" or cardStatus(c) == "Exhausted")] 
        if len(tempCards) > 0:
            cardIDs = []
            cardNames = []
            for c in tempCards:
                cardIDs.append(c._id)
                cardNames.append(c.name)
            cardChoice = SingleChoice("Choose a character to wound.",cardNames)
            if cardChoice == None:
                if confirm("Are you sure you want to skip resolving the Combat Struggle?"):
                    notify("{} has skipped the Combat Resolution and chosen not to wound a character.".format(me))
                else: setGlobalVariable('resolutionPending',"True")
            else:
                card = Card(cardIDs[cardChoice])
                notify("Card: {}".format(card.name))
                addRemWound(card,amount=1)
        else:
            notify("Combat Resolution: {} doesn't have any eligible characters to wound.".format(me))
    elif type == 'Arcane':
        notify("Resolve Arcane Struggle: {} may ready one participating character.".format(me))
        tempCards = [c for c in table if c._id in committedCharacters and (cardStatus(c) == "Exhausted")]
        if len(tempCards) > 0:
            cardIDs = []
            cardNames = []
            for c in tempCards:
                cardIDs.append(c._id)
                cardNames.append(c.name)
            cardChoice = SingleChoice("You may choose a character to ready.  Cancel if you choose not to do so.",cardNames)
            if cardChoice == None:
                if confirm("Are you sure you don't want to ready a character?"):
                    notify("{} chose not to ready a character.".format(me))
                else: setGlobalVariable('resolutionPending',"True")
            else:
                rc = Card(cardIDs[cardChoice])
                readyCard(rc,verbose = True)
        else:
            notify("Arcane Resolution: {} doesn't have any exhausted characters to ready.".format(me))
    elif type == 'Investigation':
        notify("Resolve Investigation Struggle: {} may add a success token to the current story.".format(me))
        committedStory = Card(num(getGlobalVariable("Current Story")))
        if confirm("Do you want to add a success token to {}?".format(committedStory.name)):
            addSuccess(committedStory)
        else:
            notify("{} chose not to add a success token to {}.".format(me,committedStory.name))
    if originator != me: remoteCall(originator,'resolveStruggle',[])
    else: resolveStruggle()
    
#---------------------------------------------
# Game Setup
#---------------------------------------------
def createStartingCards():
    try:
        debugNotify(">>> createStartingCards()") #Debug
        activeDomains = eval(me.getGlobalVariable('activeDomains'))
        # notify("Stories: {}".format(activeStories))
        for key, val in domainPositions.iteritems():
            debugNotify('Key: {}'.format(key))
            if re.search('Domain',key):
                dom = activeDomains.get(key,'?')
                debugNotify(dom,2)
                # notify('Story: {}'.format(story))
                if dom != '?':
                    cardOnTable = [c for c in table if c._id == dom]
                    if len(cardOnTable) == 0: 
                        dom = '?'
                        del activeDomains[key]
                        me.setGlobalVariable('activeDomains',str(activeDomains))
                if dom == '?':
                    notify('Playing Domain Card')
                    domainCard, x, y = val
                    debugNotify("Pos: {},{} - Card: {}".format(x,y,domainCard),2)
                    card = table.create(domainCard,0,0,1)
                    debugNotify("Card: {}".format(card.name),2)
                    newpos = positionOffset(card,val[1],val[2])
                    card.moveToTable(newpos[0],newpos[1])
                    card.orientation = Rot270
                    activeDomains[key] = card._id
                    me.setGlobalVariable('activeDomains',str(activeDomains))
    except: 
        e = sys.exc_info()
        notify("!!!ERROR!!! {} - In createStartingCards()\n!!! PLEASE INSTALL MARKERS SET FILE !!!".format(e))

def intSetup(group, x = 0, y = 0):
    debugNotify(">>> intSetup(){}".format(extraASDebug())) #Debug
    mute()
    cardsOnTable = [card for card in table if card.controller == me]
    debugNotify("cardsOnTable: {}".format(len(cardsOnTable)))
    if len(cardsOnTable) and not confirm("Are you sure you want to setup for a new game? (This action should only be done after a table reset)"): return
    if not table.isTwoSided() and not confirm(":::WARNING::: This game is designed to be played on a two-sided table. Things will be extremely uncomfortable otherwise!! Please start a new game and makde sure the  the appropriate button is checked. Are you sure you want to continue?"): return
    opponent = ofwhom('ofOpponent')
    me.setGlobalVariable('opponent',opponent.name)
    whisper('Opponent: {}'.format(opponent.name))
    #for type in Automations: switchAutomation(type,'Announce') # Too much spam.
    deck = me.piles['Deck']
    storyDeck = shared.piles['Story Deck']
    debugNotify("Checking Deck ({})".format(len(deck)), 3)
    if len(deck) == 0:
        whisper ("Please load a deck first!")
        return
    firstPlayer = num(getGlobalVariable('firstPlayer'))
    if firstPlayer == -1:
        if num(me.getGlobalVariable('playerside')) == -1:
            whisper("Please wait until first player has been chosen.")
            return
        elif confirm("First player has not yet been chosen.  Do you wish to do so now?  A random player will be given the choice of first player.  Once that has been done, please re-run Setup (Ctrl-Shift-S)"):
            determineFirstPlayer()
        else:
            return
    firstPlayer = num(getGlobalVariable('firstPlayer'))
    if firstPlayer == -1: return
    else: firstPlayer = Player(firstPlayer)
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
    if int(me.getGlobalVariable('playerside')) == 1:
        if len(storyDeck) > 0:
            filterStoryDeck(storyDeck)
        if len(storyDeck) == 0:
            story = []
            sd = []
            for key, val in storyDecks.iteritems():
                story.append(key)
                sd.append(val)
            deckchoice = SingleChoice("Choose a Story Deck to load",story)
            if deckchoice == None:
                whisper("Please load a story deck before continuing.")
                return
            else:
                storyload = sd[deckchoice]
                for id in storyload:
                    card = table.create(id,0,0,1,True)
                    card.moveTo(shared.piles['Story Deck'])
                shared.piles['Story Deck'].shuffle()
                notify("{} loaded the {}".format(me,story[deckchoice]))
        elif len(storyDeck) < 10 and not confirm("The Story Deck should have at least 10 cards.\n\nContinue?"):
            return
        else:
            notify("{} loaded a Story deck with {} cards.".format(me,len(storyDeck)))
        debugNotify("Setting up the Story Cards",3)
        replenishStoryCards()
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
    whisper("Target each domain (double-click or shift-click), and play a card to it as a resource.  Once all players have done this, the game can begin.")
  # executePlayScripts(Identity,'STARTUP')
def filterStoryDeck(group):
    ok = True
    for card in group: card.moveTo(me.ScriptingPile)
    counts = collections.defaultdict(int)
    for card in me.ScriptingPile:
        if card.controller != me: card.setController(me)
        counts[card.name] +=1
        if counts[card.name] > 1: card.delete()
        if card.Type != 'Story': card.delete()
    for card in me.ScriptingPile: card.moveToBottom(group)
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
    if len(getPlayers()) > 1: random = rnd(1,100) # Fix for multiplayer only. Makes Singleplayer setup very slow otherwise.
    debugNotify("About to check each card in the deck", 4) #Debug
    counts = collections.defaultdict(int)
    CardLimit = {}
    for card in me.ScriptingPile:
        counts[card.name] += 1
    if counts[card.name] > 3:
     notify(":::ERROR::: Only 3 copies of {} allowed.".format(card.name))
     ok = False
    if len(getPlayers()) > 1: random = rnd(1,100) # Fix for multiplayer only. Makes Singleplayer setup very slow otherwise.
    for card in me.ScriptingPile: card.moveToBottom(group) # We use a second loop because we do not want to pause after each check
    if ok: notify("-> Deck of {} is OK!".format(me))
    debugNotify("<<< checkDeckNoLimit() with return: {}.".format(ok), 3) #Debug
    return (ok)
    
def startGame(group, x = 0, y = 0):
    mute()
    if not gameReady():
        whisper("One or more players have not completed setup yet.")
        return
    if gameStarted():
        whisper("The game has already begun.")
        return
    firstPlayer = Player(num(getGlobalVariable('firstPlayer')))
    firstPlayer.setActivePlayer()
    for player in getPlayers():
        remoteCall(player, 'setResourcesToPlay',[1])
    notify("{} has started the game.  {} will take the first turn.".format(me.name,firstPlayer.name))

def setResourcesToPlay(amount):
    me.setGlobalVariable('resourcesToPlay',str(amount))
    
def startGameRandom(group, x = 0, y = 0):
    mute()
    if not gameReady():
        whisper("One or more players have not completed setup yet.")
        return
    if gameStarted():
        whisper("The game has already begun.")
        return
    n = rnd(1, len(getPlayers()))
    getPlayers()[n-1].setActivePlayer()
    setGlobalVariable('firstPlayer',getPlayers()[n-1].name)
    for player in getPlayers():
        player.setGlobalVariable('resourcesToPlay','1')
    notify("{} has started the game, selecting a random start player.  {} will take the first turn.".format(me,getPlayers()[n-1].name))

def startGameMe(group, x = 0, y = 0):
    mute()
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
# Table Actions
#---------------------------------------------
def iconUpdate(type = "Skill"): 
    mute()
    me.setGlobalVariable('hasFast',"False")
    currentStory = Card(num(getGlobalVariable('Current Story')))
    committedCharacters = eval(me.getGlobalVariable('committedCharacters')).get(currentStory._id,[])
    debugNotify("### Characters: {}".format(committedCharacters))
    tempCards = [c for c in table if c._id in committedCharacters and (cardStatus(c) == "InPlay" or cardStatus(c) == "Exhausted")] 
    iconTotal = 0
    if len(tempCards) > 0:
        for char in tempCards:
            if type == "Skill": icons = getSkill(char)
            else:  icons = getIcons(char,type)
            iconTotal += icons
            if hasKeyword(char,'Fast'): me.setGlobalVariable('hasFast',"True")
    me.setGlobalVariable('iconTotal',str(iconTotal))
        
def clearIconTotals():
    mute()
    debugNotify("{} clears icons totals".format(me.name))
    me.setGlobalVariable('iconTotal',"-1")
    me.setGlobalVariable('hasFast',"False")

def clearCommitted():
    currentStory = Card(num(getGlobalVariable('Current Story')))
    committedCharacters = eval(me.getGlobalVariable('committedCharacters')).get(currentStory._id,[])
    tempCards = [c for c in table if c._id in committedCharacters]
    if len(tempCards) > 0:
        for char in tempCards:
            char.arrow(char,False)
    tempCommitted = eval(me.getGlobalVariable('committedCharacters'))
    del tempCommitted[currentStory._id]
    me.setGlobalVariable('committedCharacters',str(tempCommitted))
def autoRefresh(group = table, x = 0, y = 0, verbose = True):
    if Automations['Start/End-of-Turn/Phase']: 
        whisper("NOTICE: This action is only to be used if you're not using Phase automations.")
        return
    insaneCards = [card for card in table if card.controller == me and cardStatus(card) == "Insane"]
    exhaustedCards = [card for card in table if card.controller == me and cardStatus(card) == "Exhausted"]
    myDomains = [card for card in table if card.controller == me and cardStatus(card) == "Domain"]
    restoredInsane = int(me.getGlobalVariable('restoredInsane'))
    debugNotify("Insane card count: {}".format(len(insaneCards)))
    if verbose: notify("{} automatically refreshes their side of the table.".format(me))
    if len(insaneCards) >= restorableCharacters():
        while restoredInsane < restorableCharacters() and len(insaneCards) > 0:
            remaining = restorableCharacters() - restoredInsane
            plural = 's'
            if remaining == 1: plural = '' 
            choiceList = makeChoiceListfromCardList(insaneCards)
            choice = SingleChoice("You may restore {} card{} to sanity. Choose one.".format(remaining, plural),choiceList)
            if choice == None: continue
            else:
                restoreCard(insaneCards[choice])
                insaneCards.remove(insaneCards[choice])
                restoredInsane += 1
                me.setGlobalVariable('restoredInsane', str(restoredInsane))
    elif len(insaneCards) > 0:
        for card in insaneCards():
            restoreCard(card)
            restoredInsane += 1
            me.setGlobalVariable('restoredInsane',str(restoredInsane))
    if len(exhaustedCards) > 0: 
        notify(":> {} readied all their eligible cards".format(me))
        for card in exhaustedCards:
            readyCard(card)
    for card in myDomains:
        clearedDomains = 0
        att = getAttachments(card)
        if len(att) > 0:
            for subatt in att:
                if Card(subatt).name == "Drain Token":
                    Stored_Attachments[subatt] = ""
                    setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
                    destroyCard(Card(subatt), auto=True)
                    clearedDomains += 1
            if clearedDomains: notify("{} refreshed {} domains.".format(me,clearedDomains))

#---------------------------------------------
# Pile Actions
#---------------------------------------------
def shuffle(group):
    debugNotify(">>> shuffle(){}".format(extraASDebug())) #Debug
    group.shuffle()

def draw(group=me.piles['Deck']):
    debugNotify(">>> draw(){}".format(extraASDebug())) #Debug
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
def useCard(card,x=0,y=0):
   debugNotify(">>> useCard(){}".format(extraASDebug())) #Debug
   if card.highlight == None:
      card.highlight = SelectColor
      notify ( "{} uses the ability of {}.".format(me,card) )
   else:
      if card.highlight == DummyColor:
         whisper(":::WARNING::: This highlight signifies that this card is a lingering effect left behind from the original\
                \nYou cannot clear such cards, please use the trash action to remove them.")
         return
      notify("{} clears {}.".format(me, card))
      card.highlight = None
      card.target(False)
def restoreCharacter(card, x = 0, y = 0):
    restoredInsane = int(me.getGlobalVariable('restoredInsane'))
    phase=getGlobalVariable('Phase')
    if phase != 0:
        whisper("You may only restore a character during your Refresh Phase.")
        return
    restorable = restorableCharacters()
    if restoredInsane >= restorableCharacters():
        if restorable == 1: resText = "one insane character"
        else: resText = "{} insane characters".format(restorable)
        whisper("You may only restore {} during your Refresh Phase.".format(resText))
        return
    if cardStatus(card) != "Insane":
        whisper("This card is not Insane.")
        return
    if card.controller != me:
        whisper("Please choose one of your own Insane cards to restore.")
        return
    restoreCard(card)
    restoredInsane += 1
    me.setGlobalVariable('restoredInsane', str(restoredInsane))
    notify("{} restored {} to sanity.".format(me,card.name))
    if restoredInsane >= restorableCharacters():
        nextPhase()

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
    else: 
        debugNotify("Tried to restore a non-insane card: {}".format(card.name))
        return 'ABORT'
def makeInsane(card, x = 0, y = 0, verbose=False):
    mute()
    Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
    debugNotify(">>> makeInsane({})".format(card.name))
    if cardStatus(card) == "InPlay" or cardStatus(card) == "Exhausted" or cardStatus(card) == "Insane":
        if verbose: notify("{}'s {} is driven insane.".format(me,card.name))
        card.isFaceUp = False
        card.orientation = Rot90
        for player in getPlayers():
            remoteCall(player,'peek', [card])
        if not Automations['Play/Resolve']: return
        for att in getAttachments(card):
            discardedCard = Card(att)
            if verifyAttachment(att, card._id):
                notify("{}'s {} is destroyed when {} is driven insane.".format(discardedCard.controller, discardedCard.name, card.name))
                destroyCard(discardedCard, auto=True)
            Stored_Attachments[att] = ""
            setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
        return
    else: 
        debugNofity("Tried to drive an inappropriate card insane: {}".format(card.name))
        return 'ABORT'

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
    cardType = fetchProperty(card,'Type')
    Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
    phase = num(me.getGlobalVariable('Phase'))
    storyPhase = num(getGlobalVariable('Story Phase'))
    debugNotify(">>> defaultAction(){}".format(extraASDebug())) #Debug
    mute()
    selectedAbility = eval(getGlobalVariable('Stored Effects'))
    targetedStories = [c for c in table if c.targetedBy and c.targetedBy == me and (cardStatus(c) == "Story" or cardStatus(c) == "Conspiracy")]
    if cardType == 'Button': # The Special button cards.
        if card.name == 'Wait!': BUTTON_Wait()
        elif card.name == 'Actions?': BUTTON_Actions()
        else: BUTTON_OK()
        return
    elif selectedAbility.has_key(card._id): # we check via the dictionary, as this can be then used without a highlight via the "Hardcore mode"
        if card.highlight != ReadyEffectColor and card.highlight != OverpaidEffectColor: # If the card has a selectedAbility entry but no highlight, it means the player is in hardcore mode, so we need to light up the card to allow their opponent to react.
            readyEffect(card,True)
            return
        Overpaid = False
        if card.highlight == OverpaidEffectColor: Overpaid = True
        debugNotify("selectedAbility Tuple = {}".format(selectedAbility[card._id]),4)
        if selectedAbility[card._id][4]: preTargets = [Card(selectedAbility[card._id][4])] # The 5th value of the tuple is special target card's we'll be using for this run.
        else: preTargets = None
        debugNotify("preTargets = {}".format(preTargets),3)
        if findMarker(card, "Effects Cancelled"): 
            notify("{}'s effects have been cancelled".format(card))
        else: 
            # Figure out how SelectedAbility is STored.  Pass Overpaid to the execution of autoscripts, somehow.
            splitTargets = selectedAbility[card._id][0].split('$$')
            for targetSeek in splitTargets:
                if re.search(r'(?<!Auto)Targeted', targetSeek) and re.search(r'onPlay', targetSeek) and findTarget(targetSeek,card = card) == []: 
                    if cardType == 'Event': bracketInfo = "(Cancelling will abort the effect and return this card back to your hand. Saying NO will allow you to target and double click this card to try again.)"
                    else: bracketInfo = "(Cancelling will dismiss this react trigger. Saying NO will allow you to target and double click this card to try again.)"
                    if confirm(":::ERROR::: Required Targets for this effect not found! You need to target with shift-click accordingly\
                              \n\nWould you like to completely cancel this effect?\
                                 \n{}".format(bracketInfo)):
                        clearStoredEffects(card,True,False) # Now that we won't cancel anymore, we clear the card's resident effect now, whatever happens, so that it can remove itself from play.
                        if cardType == 'Event': card.moveTo(card.owner.hand)
                        notify("{} has aborted using {}".format(me,card))
                        return
                    else: return # If the script needs a target but we don't have any, abort.
            notify("{} resolves the effects of {}".format(me,card)) 
            clearStoredEffects(card,True,False)# Now that we won't cancel anymore, we clear the card's resident effect now, whatever happens, so that it can remove itself from play.
                                                            # We don't remove it from play yet though, we do it after we've executed all its scripts
            if re.search(r'LEAVING',selectedAbility[card._id][3]): 
                cardsLeaving(card,'append')
            if executeAutoscripts(card,selectedAbility[card._id][0],count = selectedAbility[card._id][5], action = selectedAbility[card._id][3],targetCards = preTargets, overPaid = Overpaid) == 'ABORT': 
                # If we have an abort, we need to restore the card to its triggered mode so that the player may change targets and try again. 
                # Since we've already cleared the card to avoid it's "in-a-trigger" state from affecting effects which remove it from play, we need to re-store it now.
                # Since we already have its tuple stored locally, we just use storeCardEffects to save it back again.
                storeCardEffects(card,selectedAbility[card._id][0],selectedAbility[card._id][1],selectedAbility[card._id][2],selectedAbility[card._id][3],selectedAbility[card._id][4],selectedAbility[card._id][5])
                readyEffect(card,True, overPaid = Overpaid)
                return
        debugNotify("selectedAbility action = {}".format(selectedAbility[card._id][3]),2)
        continueOriginalEvent(card,selectedAbility)
        if cardType == 'Event': 
            runAutoScripts('CardPlayed',card)
            if findMarker(card, "Destination:Draw Deck"):
                notify(" -- {} is moved to the top of {}'s deck".format(card,card.owner))
                rnd(1,100) # To allow any notifications to announce the card correctly first.
                card.moveTo(card.owner.piles['Command Deck'])
            else: card.moveTo(card.owner.piles['Discard Pile']) # We discard events as soon as their effects are resolved.      
    elif card.highlight == UnpaidColor and Automations['Play/Resolve']: purchaseCard(card) # If the player is double clicking on an unpaid card, we assume they just want to bypass complete payment.
    elif cardType == 'Character' and phase == 5 and not findMarker(card,"isAttachment") and targetedStories != [] and ((storyPhase == 1 and not me.isActivePlayer) or ((storyPhase == -1 or storyPhase == 0) and me.isActivePlayer)) and Automations['Play/Resolve']:
        if len(targetedStories) > 1:
            whisper(":::ERROR::: You may only target one story for this action.")
        elif card.orientation == Rot0: 
            if storyPhase == -1:
                setGlobalVariable('Story Phase',"0")
            if card.orientation == Rot0: participate(card, targetedStories[0])
            elif card.orientation == Rot90: clearParticipation(card, targetedStories[0])
    elif fetchProperty(card,'AutoAction') != '' and Automations['Play/Resolve']: useAbility(card)
    elif cardType == 'Character':
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
                setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
                card.moveTo(me.piles['Discard Pile'])
                notify("{} refreshed a domain.".format(me))
            else: return
        else:
            Stored_Attachments[card._id] = ""
            setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
            card.moveTo(me.piles['Discard Pile'])
            notify("{} cleared up a loose drain token.".format(me))
    elif cardStatus(card) == 'Domain': #Add Payment Effects ----
        clearedDomains = 0
        att = getAttachments(card)
        wasdrained = False
        if phase == 3 or phase == -1:
            if card.targetedBy: card.target(False)
            else: card.target(True)
        else:
            if len(att) > 0:
                for subatt in att:
                    if Card(subatt).name == "Drain Token":
                        if confirm("Do you really want to remove this Drain Token?"):
                            Stored_Attachments[subatt] = ""
                            setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
                            Card(subatt).moveTo(me.piles['Discard Pile'])
                            clearedDomains += 1
                if clearedDomains: 
                    notify("{} refreshed {} domains.".format(me,clearedDomains))
                    wasdrained = True
            if wasdrained == False:
                if Automations['Play/Resolve']: generate(card)
                else:
                    xp, yp = card.position
                    token = table.create("d42706b4-2721-439e-a41f-0611d6beb449", xp , yp , 1)
                    storeAttachment(token,card)
                    arrangeAttachments(card)
                    notify("{} drained a domain.".format(me))
    elif (cardType == 'Story' or cardType == 'Conspiracy') and Automations['Play/Resolve']:
        showScore(card)
    else: whisper(":::ERROR::: There is nothing to do with this card at this moment!")
    debugNotify("<<< defaultAction()") #Debug
def drainDomain(card, x=0, y=0, verbose = True):
    if cardStatus(card) == 'Domain':
        xp, yp = card.position
        token = table.create("d42706b4-2721-439e-a41f-0611d6beb449", xp , yp , 1)
        storeAttachment(token,card)
        arrangeAttachments(card)
        if verbose: notify("{} drained a domain.".format(me))
def showScore(card, x = 0, y = 0):
    whisper("Current Score for {}".format(card.name))
    for player in getPlayers():
        score = eval(player.getGlobalVariable('storyScores')).get(card._id,0)
        whisper("{}: {}".format(player.name,score))
def toggleExhausted(card, x = 0, y = 0):
    mute()
    cardType = fetchProperty(card,'Type')
    if cardType == 'Character' or cardType == 'Support':
        if cardStatus(card) == "InPlay":
            exhaustCard(card,x,y,True)
        elif cardStatus(card) == "Exhausted":
            readyCard(card,x,y,True)
        else: whisper("Card is not ready or exhausted.")
    
def insaneOrSane(card, x = 0, y = 0):
    mute()
    if fetchProperty(card,'Type')=="Character":
        if cardStatus(card) == "InPlay" or cardStatus(card) == "Exhausted":
            makeInsane(card, x, y, True)
        elif cardStatus(card) == "Insane":
            restoreCard(card, x, y, True)
def addWound(card, x=0, y=0):
    addRemWound(card,1)
def remWound(card, x=0, y=0):
    addRemWound(card,-1)
def addRemWound(card, amount = 1, x = 0, y = 0):
    matchCard = [c for c in table if c._id == card._id]
    if len(matchCard) > 0:
        notify("Amount: {} - Markers: {}".format(amount,card.markers[mdict['Wound']]))
        if amount < 0 and abs(amount) > card.markers[mdict['Wound']]: 
            notify("{} removed all of the wounds ({}) from {}".format(me,card.markers[mdict['Wound']], card.name))
            card.markers[mdict['Wound']] = 0
        elif amount < 0:
            card.markers[mdict['Wound']] -= abs(amount)
            plural = 's'
            if abs(amount) == 1: plural = ''
            notify("{} removed {} wound{} from {}".format(me,abs(amount), plural,card.name))
        elif amount > 0:
            card.markers[mdict['Wound']] += amount
            plural = 's'
            if abs(amount) == 1: plural = ''
            notify("{} added {} wound{} to {}".format(me,abs(amount), plural, card.name))
        if card.controller == me: checkMarkers(card)
        else: remoteCall(card.controller,"checkMarkers",[card])
    
def checkMarkers(card, x = 0, y = 0):
    if not Automations['Damage/Scoring']: return
    if card.controller == me:
        hitpoints = 1 + hasKeyword(card, "Toughness")
        if card.markers[mdict['Wound']] >= hitpoints:
            notify("{}'s {} is critically wounded.  Discarding.".format(me,card.name))
            destroyCard(card,auto=True)
        fated = hasKeyword(card,"Fated")
        if fated > 0:
            if card.markers[mdict['Success']] >= fated:
                notify("{}'s {} meets their fate.  Discarding.".format(me,card.name))
                destroyCard(card,auto=True)
        
    
def findUnpaidCard():
    unpaidCard = me.getGlobalVariable('unpaidCard')
    debugNotify(">>> findUnpaidCard() - {}".format(unpaidCard)) #Debug
    cards = [c for c in table if c._id == unpaidCard]
    if len(cards) == 1:
        debugNotify("Unpaid Card: {}".format(cards[0].name),2)
        return cards[0]
    else:
        for card in table:
            if (card.highlight == UnpaidColor or card.highlight == UnpaidAbilityColor) and card.controller == me: return card
    debugNotify("<<< findUnpaidCard()") #Debug
    return None # If not unpaid card is found, return None

def participate(card, target, x = 0, y = 0, silent = False):
    debugNotify(">>> participate(){}".format(extraASDebug())) #Debug
    mute()
    if not me.isActivePlayer:
        committedStories = eval(getGlobalVariable('Committed Stories'))
        if target._id not in committedStories:
            whisper(":::ERROR::: The targeted story is not valid.  Choose a story that your opponent has committed characters to.")
            return
    if cardStatus(card) != "InPlay":
        whisper(":::ERROR::: This Character cannot commit!")
        return
    exhaustCard(card)
    committedCharacters = eval(me.getGlobalVariable('committedCharacters'))
    chars = committedCharacters.get(target._id, [])
    notify("Chars: {}".format(chars))
    chars.append(card._id)
    committedCharacters[target._id] = chars
    notify("Info: {} - {}".format(str(committedCharacters),target))
    me.setGlobalVariable('committedCharacters',str(committedCharacters))
    card.arrow(target, True)
    notify("{} commits {} to story: {}".format(me,card,target))
    executePlayScripts(card, 'COMMIT')
    runAutoScripts('CharacterCommits',card)
    debugNotify("<<< participate()") #Debug
    
def clearParticipation(card, target, x=0,y=0,silent = False): # Clears a unit from participating in a battle, to undo mistakes
    mute()
    committedCharacters = eval(me.getGlobalVariable('committedCharacters'))
    debugNotify("Info: {}".format(committedCharacters))
    thisCommit = committedCharacters[target._id]
    if card.orientation == Rot90 and card._id in thisCommit: 
        thisCommit.remove(card._id)
        if len(thisCommit) > 0:
            committedCharacters[target._id] = thisCommit
        else:
            del committedCharacters[target._id]
        me.setGlobalVariable('committedCharacters',str(committedCharacters))
        card.arrow(card,False)
        card.orientation = Rot0
        if not silent: notify("{} removes {} from the story.".format(me, card))
        stillCommitted = False
        for p in getPlayers():
            if len(eval(p.getGlobalVariable('committedCharacters'))) > 0: stillCommitted = True
        if not stillCommitted:
            setGlobalVariable('Current Story',"None")
            setGlobalVariable('Story Phase',"-1")
    else: whisper(":::ERROR::: Character is not currently committed to this story!")
def chooseAndDrainDomain(resources):
    domainList = [c for c in table if c.controller == me and cardStatus(c) == 'Domain' and getAvailableResources(c) >= resources]
    if len(domainList) == 0:
        whisper("Sorry, you have no available domains to drain for this effect.")
        return 'ABORT'
    dChoiceList = makeChoiceListfromCardList(domainList)
    debugNotify("Domain Choices: {}".format(dChoiceList))
    domainChoice = SingleChoice("Choose a domain to drain for this effect.",dChoiceList)
    if domainChoice == None: 
        whisper("No choice made. Aborting")
        return 'ABORT'
    else: chosenDomain = domainList[domainChoice]
    drainDomain(chosenDomain)
    return 

def addMarker(card, tokenType,count = 1, silent = False):
   debugNotify(">>> addMarker() with tokenType = {}".format(tokenType))
   mute()
   notStory = True
   if tokenType == 'Success':
        if cardStatus(card) == 'Story' or cardStatus(card) == 'Conspiracy':
            storyScores = eval(me.getGlobalVariable('storyScores'))
            if storyScores.get(card._id,'?') == '?':
                 storyScores[card._id] = count
            else: storyScores[card._id] += count
            me.setGlobalVariable('storyScores', str(storyScores))
            checkStory(card)
            updateScores()
            notStory = False
   if notStory:
       if tokenType == 'Wound' and card.markers[mdict[tokenType]] == 0 and count > 0: # If this is the first damage marker this card gets, then we consider the card to be freshly damaged.
          executePlayScripts(card, 'WOUND')
          if card.markers[mdict['WoundPrevention']]:
              prevent = card.markers[mdict['WoundPrevention']]
              if prevent - count > 0: count = 0
              else: count = count - prevent
              card.markers[mdict['WoundPrevention']] = 0
       card.markers[mdict[tokenType]] += count	
   if not silent: notify("{} adds {} {} to {}.".format(me, count, tokenType, card))
   if tokenType == 'Success' or tokenType == 'Wound':
      executePlayScripts(card, 'MARKERADD{}'.format(tokenType.upper()))
      remoteCall(card.controller, checkMarkers, [card])
      #autoscriptOtherPlayers('{}MarkerAdded'.format(tokenType),card,count) # Don't need it yet, so I reduce the load
   debugNotify("<<< addMarker()")

def subMarker(card, tokenType,count = 1,silent = False):
   debugNotify(">>> subMarker() with tokenType = {}".format(tokenType))
   mute()
   if not silent: notify("{} removes {} {} from {}.".format(me, count, tokenType, card))
   card.markers[mdict[tokenType]] -= count	
   if tokenType == 'Success' or tokenType == 'Damage':
      executePlayScripts(card, 'MARKERSUB{}'.format(tokenType.upper()))
      # autoscriptOtherPlayers('{}MarkerRemoved'.format(tokenType),card,count)  # Don't need it yet, so I reduce the load
   if tokenType == 'Damage' and not card.markers[mdict[tokenType]]:
      executePlayScripts(card, 'HEAL')
      # autoscriptOtherPlayers('CardHealed',card,count)  # Don't need it yet, so I reduce the load
   debugNotify("<<< subMarker()")

def bottomOfDeck(card, x = 0, y = 0, group = me.piles['Deck']):
    notify("{} moved {} to the bottom of {}".format(me,card,group.name))
    card.moveToBottom(group)
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
    if resourcesToPlay > 0 or not Automations['Placement']:
        target = [c for c in table if c.targetedBy and c.controller == me and c.targetedBy == me and cardStatus(c) == "Domain"]
        debugNotify("Target: {}".format(len(target)),4)
        if len(target) == 1:
            debugNotify(">>> ResourceCount: {}".format(countResources(target[0])),4)
            if turnNumber() == 0 and countResources(target[0]) > 0: 
                whisper("Before game begins, you may only play one resource per domain.")
                return
            x,y = target[0].position
            card.moveToTable(x,y)
            card.orientation ^= Rot270
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
            phase = num(me.getGlobalVariable('Phase'))
            if phase == 3 and Automations['Start/End-of-Turn/Phase']: nextPhase()
        else: whisper("Please target one of your domains.")
    else: whisper("You've already played all your resources this turn.")
    
def play(card, x = 0, y = 0):
    debugNotify(">>> play(){}".format(extraASDebug())) #Debug
    mute()
    extraTXT = ''
    target = [c for c in table if c.targetedBy and c.controller == me and c.targetedBy == me and cardStatus(c) == "Domain"]
    if len(target) == 1:
        playResource(card, x, y)
        return
    cardType = fetchProperty(card,'Type')    
    if ((cardType == 'Character' or cardType == 'Support') and Automations['Play/Resolve']
        and (me.getGlobalVariable('Phase') != '4')
        and not confirm(":::WARNING:::\n\nNormally this type of card cannot be played outside the Operations phase. Are you sure you want to continue?")):
            return 
    if cardType == 'Support' and hasSubType(card, 'Attachment.') and Automations['Placement']:
        debugNotify("### Checking for host type",2)
        hostType = re.search(r'Placement:([A-Za-z1-9:_ ]+)', card.AutoScript)
        if hostType:
            debugNotify("### hostType: {}.".format(hostType.group(1))) #Debug
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
            if c.name == card.name and c.orientation != Rot270: 
                foundUnique = c
                break
        if foundUnique:
            if foundUnique.owner == me: confirmTXT = "This card is unique and you already have a copy of {} in play.\n\nBypass uniqueness restriction?".format(foundUnique.name)
            else: confirmTXT = "This card is unique and {} already has a copy of {} in play.\n\nBypass uniqueness restriction?".format(foundUnique.owner.name,foundUnique.name)
            if confirm(confirmTXT):
                extraTXT += " (Bypassing Uniqueness Restriction!)"
            else: return  
    debugNotify("About to move card to table")
    pos = positionOffset(card, 270, 60)
    debugNotify("Position: {}".format(pos))
    card.moveToTable(pos[0],pos[1])
    if checkPaidResources(card) == 'NOK':
        card.highlight = UnpaidColor 
        me.setGlobalVariable('unpaidCard',str(card._id))
        notify("{} attempts to play {}{}.".format(me, card,extraTXT))
        # if num(card.Cost) == 0 and card.Type == 'Event': readyEffect(card)
    else: 
        if card.Type == 'Event':
            executePlayScripts(card, 'PLAY') # We do not trigger events automatically, in order to give the opponent a chance to play counter cards
        else:
            placeCard(card)
            notify("{} plays {}{}.".format(me, card,extraTXT))
            executePlayScripts(card, 'PLAY') # We execute the play scripts here only if the card is 0 cost.
            runAutoScripts('CardPlayed',card)

def checkPaidResources(card):
    debugNotify(">>> checkPaidResources()") #Debug
    count = 0
    affiliationMatch = False
    if not Automations['Payment']: return 'OK'
    for cMarkerKey in card.markers: #We check the key of each marker on the card
        for resdictKey in resdict:  #against each resource type available
            debugNotify("About to compare marker keys: {} and {}".format(resdict[resdictKey],cMarkerKey)) #Debug
            if resdict[resdictKey] == cMarkerKey: # If the marker is a resource
                count += card.markers[cMarkerKey]  # We increase the count of how many resources have been paid for this card
                debugNotify("About to check found resource affiliaton") #Debug
                if 'Resource:{}'.format(card.Faction) == resdictKey: # if the card's affiliation also matches the currently checked resource
                    debugNotify("### Affiliation match. Affiliation = {}. Marker = {}.".format(card.Faction,resdictKey))
                    affiliationMatch = True # We set that we've also got a matching resource affiliation
        if cMarkerKey[0] == "Ignores Affiliation Match": 
            debugNotify("### Ignoring affiliation match due to marker on card. Marker = {}".format(cMarkerKey),3)
            affiliationMatch = True # If we have a marker that ignores affiliations, we can start ignoring this card's as well
    for c in table:
        debugNotify("Checking: {}".format(c.Name))
        if c.controller == me and re.search("IgnoreAffiliationMatch",c.AutoScript) and chkDummy(c.AutoScript, c): 
            notify(":> Affiliation match ignored due to {}.".format(c))
            affiliationMatch = True
    debugNotify("About to check successful cost. Count: {}, Faction: {}".format(count,card.Faction)) #Debug
    if card.highlight == UnpaidAbilityColor:
        selectedAbility = eval(getGlobalVariable('Stored Effects'))
        reduction = reduceCost(card, 'USE', selectedAbility[card._id][1] - count, dryRun = True) # We do a dry run first. We do not want to trigger once-per turn abilities until the point where we've actually paid the cost.
        if count >= selectedAbility[card._id][1] - reduction:
            if count > selectedAbility[card._id][1] - reduction:
                debugNotify("<<< checkPaidResources(). Return USEOKOP")
                reduceCost(card,'USE', selectedAbility[card._id][1] - count)
                return 'USEOKOP'
            debugNotify("<<< checkPaidResources(). Return USEOK") #Debug
            reduceCost(card, 'USE', selectedAbility[card._id][1] - count) # Now that we've actually made sure we've paid the cost, we use any ability that reduces costs.
            return 'USEOK'
        else:
            if count >= selectedAbility[card._id][1] - reduction and not affiliationMatch:
                notify(":::WARNING::: Ability cost reached but there is no affiliation match!")
            debugNotify("<<< checkPaidResources(). Return NOK 1") #Debug
            return 'NOK'      
    else:
        reduction = reduceCost(card, 'PLAY', num(card.Cost) - count, dryRun = True) # We do a dry run first. We do not want to trigger once-per turn abilities until the point where we've actually paid the cost.
        if count >= num(card.Cost) - reduction and (card.Faction == 'Neutral' or affiliationMatch or (not affiliationMatch and (num(card.Cost) - reduction) == 0)):
            if countResources(card,card.Faction) >= num(card.Cost) - reduction or not hasKeyword(card,'Loyal.'):
                debugNotify("<<< checkPaidResources(). Return OK") #Debug
                reduceCost(card, 'PLAY', num(card.Cost) - count) # Now that we've actually made sure we've paid the cost, we use any ability that reduces costs.
                return 'OK'
            else:
                notify(":::WARNING::: Card is Loyal, and there aren't enough {} resources to pay for it.".format(card.Faction))
                debugNotify("<<< checkPaidResources(). Return NOK 3") #Debug
                return 'NOK'
        else:
            if count >= num(card.Cost) - reduction and not affiliationMatch:
                notify(":::WARNING::: Card cost reached but there is no affiliation match!")
            debugNotify("<<< checkPaidResources(). Return NOK 2") #Debug
            return 'NOK'
def purchaseCard(card, x=0, y=0, manual = True):
    debugNotify(">>> purchaseCard(){}".format(extraASDebug())) #Debug
    if manual and card.highlight != ReadyEffectColor and card.highlight != OverpaidEffectColor: checkPaid = checkPaidResources(card)
    # If this is an attempt to manually pay for the card, we check that the player can afford it (e.g. it's zero cost or has cost reduction effects)
    # Events marked as 'ReadyEffectColor' have already been paid, so we do not need to check them again.
    else: checkPaid = 'OK' #If it's not manual, then it means the checkPaidResources() has been run successfully, so we proceed.
    if checkPaid == 'OK' or confirm(":::ERROR::: You do have not yet paid the cost of this card. Bypass?"):
        # if the card has been fully paid, we remove the resource markers and move it at its final position.
        card.highlight = None
        placeCard(card)
        clrResourceMarkers(card)
        me.setGlobalVariable('unpaidCard',"None")
        
        if checkPaid == 'OK': notify("{} has paid for {}".format(me,card)) 
        else: notify(":::ATTENTION::: {} has played {} by skipping its full cost".format(me,card))
        executePlayScripts(card, 'PLAY') 
        if card.Type != 'Event': runAutoScripts('CardPlayed',card) # We script for playing events only after their events have finished resolving in the default action.
    debugNotify("<<< purchaseCard()") #Debug

def generate(card, x = 0, y = 0):
    debugNotify(">>> generate(){}".format(extraASDebug())) #Debug
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
        for subatt in att:
            c = Card(subatt)
            resourceCount = len(c.properties['Resource Icon'])
            if resourceCount == 2:
                notify('{} drained a domain with a transient resource.  Discarding {}.'.format(me,c.name))
                remResource(card,c)
                destroyCard(c,auto=True)
                arrangeAttachments(card)
        #executePlayScripts(card, 'GENERATE')
        #runAutoScripts('ResourceGenerated',card)
        purchaseCard(unpaidC, manual = False)
    elif (resResult == 'USEOK' or resResult == 'USEOKOP'): 
        xp, yp = card.position
        token = table.create("d42706b4-2721-439e-a41f-0611d6beb449", xp , yp , 1)
        storeAttachment(token,card)
        arrangeAttachments(card)
        notify("{} drained a domain to pay for {}'s effect.".format(me,unpaidC))
        for subatt in att:
            c = Card(subAtt)
            resourceCount = len(c.properties['Resource Icon'])
            if resourceCount == 2:
                notify('{} drained a domain with a transient resource.  Discarding {}.'.format(me,c.name))
                remResource(card,c)
                destroyCard(c,auto=True)
                arrangeAttachments(card)
        #executePlayScripts(card, 'GENERATE')
        #runAutoScripts('ResourceGenerated',card)
        Overpaid = False
        if resResult == 'USEOKOP': Overpaid = True
        readyEffect(unpaidC, overPaid = Overpaid)
    elif resResult == 'NOK':
        whisper(":::ERROR::: Domain does not have enough resources to pay for {}.".format(unpaidC))
        clrResourceMarkers(unpaidC)
    debugNotify("<<< generate()") #Debug
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
    if card.controller == me and (auto or confirm("Are you sure you want to send {} and any attachments to the discard pile?".format(card.name))):
        Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
        att = getAttachments(card)
        for subatt in att:
            del Stored_Attachments[subatt]
            setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
            destroyCard(Card(subatt),auto=True)
        freeCardPlacement(card)
        runAutoScripts('CardDestroyed',card)
        clearCardModifiers('{}LeavesPlay'.format(card._id))
        card.moveTo(card.owner.piles['Discard Pile'])
    else: return
    
def mulligan(group, x = 0, y = 0):
    if turnNumber() != 0:
        whisper("The game has already begun, you can't mulligan now.")
        return
    if len(group) != 8 and not confirm("You don't have the correct number of cards in your hand.  Continue anyway?"): return
    mute()
    for card in group:
        card.moveToBottom(me.deck)
    me.deck.shuffle()
    for card in me.deck.top(8):
        card.moveTo(me.hand)
    notify("{} mulligans.".format(me))
    
def randomDiscard(group):
 mute()
 card = group.random()
 if card == None: return
 card.moveTo(me.piles['Discard pile'])
 notify("{} randomly discards {}.".format(me, card))
 
def determineFirstPlayerNoRandom(group, x=0, y=0, forced = False):
    mute()
    determineFirstPlayer(group, random = False)
    
 
def determineFirstPlayer(group = table, x=0, y=0, random = True, forced = False):
    mute()
    firstPlayerID = num(getGlobalVariable('firstPlayer'))
    if firstPlayerID != -1:
        firstPlayer = Player(firstPlayerID)
        if turnNumber() != 0:
            whisper("The game has already begun. {} has been determined as the first player.".format(firstPlayer.name))
            return
        elif not confirm("The first player has already been determined as {} - {}, but the game has not yet begun.  Do you wish to change this?".format(firstPlayer.name, firstPlayerID)): return
    selectingPlayer = None
    message = ''
    if len(getPlayers()) == 1:
        random = False
        forced = True
    if random:
        n = rnd(1, len(getPlayers()))
        selectingPlayer = Player(n)
        if not forced: notify("{} won the random determination.  Asking them if they want to go first.".format(selectingPlayer.name))
        message = "You won the random determination.  Choose who plays first."
    else:
        selectingPlayer = me
        if not forced: notify("{} chose to pick the starting player.".format(selectingPlayer.name))
        message = "Choose who plays first."
    if not selectingPlayer:
        debugNotify("ERROR:  Nobody to select starting player.")
    if not forced:
        remoteCall(selectingPlayer, 'selectFirstPlayer', [message])
    else:
        setGlobalVariable('firstPlayer',str(selectingPlayer._id))
        notify("First Player Chosen: {}".format(selectingPlayer.name))

def selectFirstPlayer(message = "Choose who plays first"):
    mute()
    playerList = []
    playerIDs = []
    for player in getPlayers():
        playerList.append(player.name)
        playerIDs.append(player._id)
    choice = SingleChoice(message, playerList)
    if not choice:
        notify("{} did not choose a starting player.".format(me.name))
        return
    else:
        firstPlayer = playerIDs[choice]
        setGlobalVariable('firstPlayer',str(firstPlayer))
        notify("First Player Chosen: {}".format(Player(firstPlayer).name))