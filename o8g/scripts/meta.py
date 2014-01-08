       # Python Scripts for the Call of Cthulhu LCG definition for OCTGN
       # Copyright (C) 2013-2014  Jason Cline
       # Based heavily on the scripts for Android:Netrunner and Star Wars by Konstantine Thoukydides

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
# This file contains scripts which are not used to play the actual game, but is rather related to the rules of engine
# * [Generic CoC] functions are not doing something in the game by themselves but called often by the functions that do.
# * In the [Switches] section are the scripts which controls what automations are active.
# * [Help] functions spawn tokens on the table with succint information on how to play the game.
# * [Button] functions are trigered either from the menu or from the button cards on the table, and announce a specific message each.
# * [Debug] if for helping the developers fix bugs
# * [Online Functions] is everything which connects to online files for some purpose, such as checking the game version or displaying a message of the day
###=================================================================================================================###
import re, time
#import sys # Testing
#import dateutil # Testing
#import elementtree # Testing
#import decimal # Testing

try:
       import os
       if os.environ['RUNNING_TEST_SUITE'] == 'TRUE':
              me = object
              table = object
except ImportError:
       pass

Automations = {'Play/Resolve'    : False, # If True, game will automatically trigger card effects when playing or double-clicking on cards. Requires specific preparation in the sets.
           'Start/End-of-Turn/Phase'      : False, # If True, game will automatically trigger effects happening at the start of the player's turn, from cards they control.
           'Damage Prevention'      : True, # If True, game will automatically use damage prevention counters from card they control.
           'Triggers'               : False, # If True, game will search the table for triggers based on player's actions, such as installing a card, or trashing one.
           'WinForms'               : True, # If True, game will use the custom Windows Forms for displaying multiple-choice menus and information pop-ups
           'Damage/Scoring'                 : False,
           'Placement'		:False,
           'Payment'           :False}

debugVerbosity = 0 # At -1, means no debugging messages display

startupMsg = False # Used to check if the player has checked for the latest version of the game.

costModifiers = []


#---------------------------------------------------------------------------
# Generic functions
#---------------------------------------------------------------------------

def ofwhom(Autoscript, controller = me): 
    debugNotify(">>> ofwhom(){}".format(extraASDebug(Autoscript))) #Debug
    targetPL = None
    if re.search(r'o[fn]Opponent', Autoscript):
        if len(getPlayers()) > 1:
            if controller == me: # If we're the current controller of the card who's scripts are being checked, then we look for our opponent
                for player in getPlayers():
                    if int(player.getGlobalVariable('playerside')) == 0: continue # This is a spectator 
                    elif player != me and int(player.getGlobalVariable('playerside')) != int(me.getGlobalVariable('playerside')):
                        targetPL = player # Opponent needs to be not us, and of a different type. 
                                                            # In the future I'll also be checking for teams by using a global player variable for it and having players select their team on startup.
            else: targetPL = me # if we're not the controller of the card we're using, then we're the opponent of the player (i.e. we're trashing their card)
        else: 
             debugNotify("There's no valid Opponents! Selecting myself.",1)
             targetPL = me
    elif re.search(r'o[fn]Either',Autoscript):
        if len(getPlayers()) > 1:
            players = []
            playerNames = []
            for player in getPlayers():
                playerNames.append(player.name)
                players.append(player)
            choice = SingleChoice("Choose a player for this effect. Cancelling will choose you.",playerNames)
            if choice == None: targetPL = me
            else: targetPL = players[choice]
        else: targetPL = me
    elif re.search(r'o[fn]EachPlayer',Autoscript):
        if len(getPlayers()) > 1:
            return getPlayers()
        else: targetPL = me
    else: 
       if len(getPlayers()) > 1:
             if controller != me: targetPL = controller         
             else: targetPL = me
       else: targetPL = me
    debugNotify("<<< ofwhom() returns {}".format(targetPL))
    return targetPL
     
def chooseWell(limit, choiceText, default = None):
     debugNotify(">>> chooseWell(){}".format(extraASDebug())) #Debug
     if default == None: default = 0# If the player has not provided a default value for askInteger, just assume it's the max.
     choice = limit # limit is the number of choices we have
     if limit > 1: # But since we use 0 as a valid choice, then we can't actually select the limit as a number
           while choice >= limit:
                 choice = askInteger("{}".format(choiceText), default)
                 if not choice: return False
                 if choice > limit: whisper("You must choose between 0 and {}".format(limit - 1))
     else: choice = 0 # If our limit is 1, it means there's only one choice, 0.
     return choice

def findMarker(card, markerDesc): # Goes through the markers on the card and looks if one exist with a specific description
     debugNotify(">>> findMarker(){}".format(extraASDebug())) #Debug
     foundKey = None
     if markerDesc in mdict: markerDesc = mdict[markerDesc][0] # If the marker description is the code of a known marker, then we need to grab the actual name of that.
     for key in card.markers:
           debugNotify("Key: {}\nmarkerDesc: {}".format(key[0],markerDesc), 3) # Debug
           if re.search(r'{}'.format(markerDesc),key[0]) or markerDesc == key[0]:
                 foundKey = key
                 debugNotify("Found {} on {}".format(key[0],card), 2)
                 break
     debugNotify("<<< findMarker() by returning: {}".format(foundKey), 3)
     return foundKey
def pileName(group):
     debugNotify(">>> pileName()") #Debug
     debugNotify("pile name {}".format(group.name), 2) #Debug   
     debugNotify("pile player: {}".format(group.player), 2) #Debug
     name = group.name
     debugNotify("<<< pileName() by returning: {}".format(name), 3)
     return name

def getSpecial(cardType,player = me):
# Functions takes as argument the name of a special card, and the player to whom it belongs, and returns the card object.
     debugNotify(">>> getSpecial() for player: {}".format(me.name)) #Debug
     specialCards = eval(player.getGlobalVariable('specialCards'))
     cardID = specialCards.get(cardType,None)
     if not cardID: 
           debugNotify("No special card of type {} found".format(cardType),2)
           card = None
     else:
           card = Card(specialCards[cardType])
     debugNotify("<<< getSpecial() by returning: {}".format(card), 3)
     return card


def storeAttachment(card, attachee, forced = False, resource = False):
     mute()
     try:
           Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
           Stored_Name = eval(getGlobalVariable('Stored_Name'))
           Stored_Resource = eval(getGlobalVariable('Stored_Resource'))
           if (card.Name == '?' and Stored_Name.get(card._id,'?') == '?') or forced:
                 if not card.isFaceUp and card.group == table and (card.owner == me or forced):
                       debugNotify("Peeking Card at storeAttachment()",2)
                       card.peek()
                       loopChk(card)
           if (Stored_Name.get(card._id,'?') == '?' and card.Name != '?') or (Stored_Name.get(card._id,'?') != card.Name and card.Name != '?') or forced:
                 debugNotify("{} not stored.  Storing...".format(card),4)
                 Stored_Name[card._id] = card.Name
                 setGlobalVariable('Stored_Name',str(Stored_Name))
                 # debugNotify(">>> Step 1",4)
                 if resource: 
                       Stored_Resource[card._id] = card.properties["Resource Icon"]
                       setGlobalVariable('Stored_Resource',str(Stored_Resource))
                 # debugNotify(">>> Step 2",4)
                 Stored_Attachments[card._id] = attachee._id
                 setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
                 # debugNotify("Storing: {} - {} - {}".format(Stored_Name.get(card._id, '?'),Stored_Resource.get(card._id,'?'),Stored_Attachments.get(card._id,'?')),4)
           elif card.Name == '?':
                 debugNotify("Could not store attachment because it is hidden from us")
                 return 'ABORT'
     except: notify("!!!ERROR!!! In storeAttachment()")

def removeAttachment(card):
    mute()
    debugNotify(">>> removeAttachment")
    Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
    Stored_Resource = eval(getGlobalVariable('Stored_Resource'))
    if Stored_Attachments.get(card._id,'?') != '?':
        del Stored_Attachments[card._id]
        setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
    if Stored_Resource.get(card._id,'?') != '?':
        del Stored_Resource[card._id]
        setGlobalVariable('Stored_Resource',str(Stored_Resource))
def getAttachments(card):
     Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
     att = [c for c in table if c._id in Stored_Attachments and Stored_Attachments.get(c._id,'?') == card._id]
     attachments = []
     for c in att:
        attachments.append(c._id)
     debugNotify(">>> Attachments: {}".format(attachments))
     return attachments

def getAttached(card):
     Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
     debugNotify(">>> Checking for attachment host - {}".format(card._id),4)
     if (card._id in Stored_Attachments and not Stored_Attachments.get(card._id,'?') == '?'):
           debugNotify(">>> Returning {}".format(Stored_Attachments.get(card._id,'?')),4)
           return Card(Stored_Attachments.get(card._id,'?'))
     else:
           return None
     
def getCommitted(card):
     commList = eval(card.owner.getGlobalVariable('committedCharacters'))
     for key,value in commList.iteritems():
           if card._id in value: 
               notify("{} committed to: {}".format(card.name,key))
               return key
     return None
       
def resetAll(): # Clears all the global variables in order to start a new game.
     global debugVerbosity, newturn, endofturn
     debugNotify(">>> resetAll(){}".format(extraASDebug())) #Debug
     mute()
     for key in storyPositions:
          me.counters[key].value = 0
     me.counters['Stories Won'].value = 0
     if int(me.getGlobalVariable('playerside')) == 1:
           setGlobalVariable('activeStories',"{}")
           setGlobalVariable('Stored_Name',"{}")
           setGlobalVariable('Stored_Resource',"{}")
           setGlobalVariable('Stored_Attachments',"{}")
           setGlobalVariable('Current Story',"None")
           setGlobalVariable('Committed Stories',"[]")
           setGlobalVariable('Story Phase',"-1")
     me.setGlobalVariable('storyScores',"{}")    
     me.setGlobalVariable('commitedCharacters',"{}")
     me.setGlobalVariable('restoredInsane',"0")    
     me.setGlobalVariable('unpaidCard',"None")    
     me.setGlobalVariable('activeDomains',"{}")
     me.handSize = 5
     newturn = False 
     endofturn = False
     selectedAbility = eval(getGlobalVariable('Stored Effects'))
     selectedAbility.clear()
     setGlobalVariable('Stored Effects',str(selectedAbility))
     me.setGlobalVariable('freePositions',str([]))
     me.setGlobalVariable('resourcesToPlay',3)
     
     # if len(getPlayers()) > 1: debugVerbosity = -1 # Reset means normal game.
     # elif debugVerbosity != -1 and confirm("Reset Debug Verbosity?"): debugVerbosity = -1    
     debugNotify("<<< resetAll()") #Debug   

  
def addResource(domainCard,resourceCard):
     debugNotify(">>> remResource\nAmount: {}".format(len(resourceCard.properties['Resource Icon'])),3)
     amount = len(resourceCard.properties['Resource Icon'])
     addRemResource(domainCard,resourceCard,amount)
def remResource(domainCard,resourceCard):
     debugNotify(">>> remResource\nAmount: {}".format(len(resourceCard.properties['Resource Icon'])),3)
     amount = len(resourceCard.properties['Resource Icon'])
     amount = amount - (amount * 2)
     addRemResource(domainCard,resourceCard,amount)

def getResources(resourceCard):
    amount = len(resourceCard.properties['Resource Icon'])
    if resourceCard.properties["Resource Icon"] == "Z": resourceType = 'Zoog'
    else: resourceType = resourceCard.Faction
    return (amount, resourceType)

def addRemResource(domainCard,resourceCard, amount=1):
     if cardStatus(domainCard) == 'Domain':
           debugNotify(">>> addRemResource()\nFaction: {}\nDomain: {}\nResource: {}\nAmount: {}".format(resourceCard.faction,domainCard.name,resourceCard.name,amount),3)
           resourceType = getResources(resourceCard)[1]
           debugNotify("Type: {}".format(resourceType))
           domainCard.markers[resdict['Resource:{}'.format(resourceType)]] += amount
     else:
           debugNotify("### Tried to add resources to a non-domain target.")
           return
           
def countResources(card,faction = 'All'):
     debugNotify(">>> Count Resources - {}".format(faction),1)
     resources = 0
     keys = resdict.viewkeys()
     for key in keys:
           if re.search('Resource', key) and (re.search(faction, key) or faction == 'All'):
                 debugNotify("Key: {}".format(key),1)
                 resources += card.markers[resdict[key]]
                 debugNotify("Resource Count: {}".format(resources),1)
     return resources
def countAllResources(faction = 'All'):
     domainList = [c for c in table if c.controller == me and cardStatus(c) == 'Domain']
     resources = 0
     for c in domainList:
           resources += countResources(c,faction)
     return resources
def arrangeAttachments(card):
     debugNotify(">>> arrangeAttachments: {}".format(card.name),3)
     x,y = card.position
     attachments = getAttachments(card)
     debugNotify("Returned: {}".format(attachments),4)
     for attachment in attachments:
           debugNotify("Attachment: {}".format(attachment),3)
           exists = False
           targetCard = None
           for c in table:
                 debugNotify("{} | {}".format(c._id, attachment),4)
                 if c._id == attachment: 
                       exists = True
                       targetCard = c
           if exists:
                 if targetCard.controller != me: targetCard.setController(me)
                 debugNotify("Does Exist",4)
                 if targetCard.name == "Drain Token":
                       debugNotify("Drain Token",4)
                       targetCard.moveToTable(x,y)
                       targetCard.sendToFront()
                 elif cardStatus(targetCard) == "Resource":
                       debugNotify("Resource",4)
                       if me.hasInvertedTable() == True: x += -8
                       else: x += 8
                       targetCard.moveToTable(x,y)
                       targetCard.sendToBack()
                 else:
                       if me.hasInvertedTable() == True: y += 8
                       else: y -= 8
                       targetCard.moveToTable(x,y)
                       targetCard.sendToBack()
           else: 
                 Stored_Attachments = eval(getGlobalVariable('Stored_Attachments'))
                 del Stored_Attachments[attachment]
                 setGlobalVariable('Stored_Attachments',str(Stored_Attachments))
           
           
def verifyAttachment(attached, attachee):
     attacheeExists = False
     attachedExists = False
     for c in table:
           if c._id == attached: attachedExists = True
           if c._id == attachee: attacheeExists = True
     if attacheeExists and attachedExists: return True
     else: return False
                 
def gameReady():
     gR = True
     for player in getPlayers():
           if not eval(player.getGlobalVariable('gameReady')): gR = False
     return gR
     
def gameStarted():
     if turnNumber() > 0: return True
     else: return False
     

def parseIcons(STRING, dictReturn = False):
     debugNotify(">>> parseIcons() with STRING: {}".format(STRING)) #Debug
     Terror = STRING.count('@')
     Combat = STRING.count('#')
     Arcane = STRING.count('$')
     Investigation = STRING.count('$')
     if not dictReturn:
           parsedIcons = ''
           if Terror: parsedIcons += 'Terror:{}. '.format(Terror)
           if Combat: parsedIcons += 'Combat:{}. '.format(Combat)
           if Arcane: parsedIcons += 'Arcane:{}. '.format(Arcane)
           if Investigation: parsedIcons += 'Investigation:{}. '.format(Investigation)
           debugNotify("<<< parseIcons() with return: {}".format(parsedIcons)) # Debug
     else:
           parsedIcons = {}
           parsedIcons[Terror] = Terror
           parsedIcons[Combat] = Combat
           parsedIcons[Arcane] = Arcane
           parsedIcons[Investigation] = Investigation
           debugNotify("<<< parseIcons() with dictReturn: {}".format(parsedIcons)) # Debug
     return parsedIcons
def chkDummy(Autoscript, card): # Checks if a card's effect is only supposed to be triggered for a (non) Dummy card
     debugNotify(">>> chkDummy()") #Debug
     if re.search(r'onlyforDummy',Autoscript) and card.highlight != DummyColor: return False
     if re.search(r'excludeDummy', Autoscript) and card.highlight == DummyColor: return False
     return True

def reduceCost(card, action = 'PLAY', fullCost = 0, dryRun = False):
# A Functiona that scours the table for cards which reduce the cost of other cards.
# if dryRun is set to True, it means we're just checking what the total reduction is going to be and are not actually removing or adding any counters.
     type = action.capitalize()
     debugNotify(">>> reduceCost(). Action is: {}. FullCost = {}. dryRyn = {}".format(type,fullCost,dryRun)) #Debug
     fullCost = abs(fullCost)
     reduction = 0
     costReducers = []
     ### First we check if the card has an innate reduction. 
     Autoscripts = []
     if card.AutoScript != '': Autoscripts = card.AutoScript.split('||') 
     debugNotify("### About to check if there's any onPay triggers on the card")
     if len(Autoscripts): 
           for autoS in Autoscripts:
                 if not re.search(r'onPay', autoS): 
                       debugNotify("### No onPay trigger found in {}!".format(autoS))
                       continue
                 else: debugNotify("### onPay trigger found in {}!".format(autoS))
                 reductionSearch = re.search(r'Reduce([0-9]+)Cost({}|All)'.format(type), autoS)
                 if debugVerbosity >= 2: #Debug
                       if reductionSearch: debugNotify("!!! self-reduce regex groups: {}".format(reductionSearch.groups()))
                       else: debugNotify("!!! No self-reduce regex Match!")
                 count = num(reductionSearch.group(1))
                 targetCards = findTarget(autoS,card = card)
                 multiplier = per(autoS, card, 0, targetCards)
                 reduction += (count * multiplier)
                 maxRegex = re.search(r'-maxReduce([1-9])', autoS) # We check if the card will only reduce its cast by a specific maximum (e.g. Weequay Elite)
                 if maxRegex and reduction > num(maxRegex.group(1)): reduction = num(maxRegex.group(1))
                 fullCost -= reduction
                 if reduction > 0 and not dryRun: notify("-- {}'s full cost is reduced by {}".format(card,reduction))
     debugNotify("### About to gather cards on the table")
     ### Now we check if any card on the table has an ability that reduces costs
     if not eval(me.getGlobalVariable('gatheredCardList')): # A global variable that stores if we've scanned the tables for cards which reduce costs, so that we don't have to do it again.
           global costModifiers
           del costModifiers[:]
           RC_cardList = sortPriority([c for c in table if c.isFaceUp and c.orientation != Rot270 and c.highlight != UnpaidColor])
           debugNotify("Cardlist: {}".format(RC_cardList))
           reductionRegex = re.compile(r'(Reduce|Increase)([0-9#X]+)Cost({}|All)-affects([A-Z][A-Za-z ]+)(-not[A-Za-z_& ]+)?'.format(type)) # Doing this now, to reduce load.
           for c in RC_cardList: # Then check if there's other cards in the table that reduce its costs.
                 Autoscripts = c.AutoScript.split('||')
                 if len(Autoscripts) == 0: continue
                 for autoS in Autoscripts:
                       debugNotify("### Checking {} with AS: {}".format(c, autoS)) #Debug
                       if not chkPlayer(autoS, c.controller, False): continue
                       reductionSearch = reductionRegex.search(autoS) 
                       if debugVerbosity >= 2: #Debug
                            if reductionSearch: debugNotify("!!! Regex is {}".format(reductionSearch.groups()))
                            else: debugNotify("!!! No reduceCost regex Match!") 
                       #if re.search(r'ifInstalled',autoS) and (card.group != table or card.highlight == RevealedColor): continue
                       if reductionSearch: # If the above search matches (i.e. we have a card with reduction for Rez and a condition we continue to check if our card matches the condition)
                            debugNotify("### Possible Match found in {}".format(c),3) # Debug         
                            if not chkDummy(autoS, c): continue   
                            if not checkOriginatorRestrictions(autoS,c): continue  
                            if not chkSuperiority(autoS, c): continue
                            if reductionSearch.group(1) == 'Reduce': 
                                  debugNotify("Adding card to cost Reducers list")
                                  costReducers.append((c,reductionSearch,autoS)) # We put the costReducers in a different list, as we want it to be checked after all the increasers are checked
                            else:
                                  debugNotify("Adding card to cost Modifiers list")
                                  costModifiers.append((c,reductionSearch,autoS)) # Cost increasing cards go into the main list we'll check in a bit, as we need to check them first. 
                                                                                                                             # In each entry we store a tuple of the card object and the search result for its cost modifying abilities, so that we don't regex again later. 
           if len(costReducers) > 0: costModifiers.extend(costReducers)
     for cTuple in costModifiers: # Now we check what kind of cost modification each card provides. First we check for cost increasers and then for cost reducers
           debugNotify("### Checking next cTuple",4) #Debug
           c = cTuple[0]
           reductionSearch = cTuple[1]
           autoS = cTuple[2]
           debugNotify("### cTuple[0] (i.e. card) is: {}".format(c)) #Debug
           debugNotify("### cTuple[2] (i.e. autoS) is: {}".format(autoS),4) #Debug
           if reductionSearch.group(4) == 'All' or checkCardRestrictions(gatherCardProperties(card), prepareRestrictions(autoS,seek = 'reduce')):
                 debugNotify(" ### Search match! Reduction Value is {}".format(reductionSearch.group(2)),3) # Debug
                 if re.search(r'onlyOnce',autoS):
                       if dryRun: # For dry Runs we do not want to add the "Activated" token on the card. 
                            if oncePerTurn(c, act = 'dryRun') == 'ABORT': continue 
                       else:
                            if oncePerTurn(c, act = 'automatic') == 'ABORT': continue # if the card's effect has already been used, check the next one
                 if reductionSearch.group(2) == '#': 
                       markersCount = c.markers[mdict['Credits']]
                       markersRemoved = 0
                       while markersCount > 0:
                            debugNotify("### Reducing Cost with and Markers from {}".format(c)) # Debug
                            if reductionSearch.group(1) == 'Reduce':
                                  if fullCost > 0: 
                                        reduction += 1
                                        fullCost -= 1
                                        markersCount -= 1
                                        markersRemoved += 1
                                  else: break
                            else: # If it's not a reduction, it's an increase in the cost.
                                  reduction -= 1
                                  fullCost += 1                     
                                  markersCount -= 1
                                  markersRemoved += 1
                       if not dryRun and markersRemoved != 0: 
                            c.markers[mdict['Credits']] -= markersRemoved # If we have a dryRun, we don't remove any tokens.
                            notify(" -- {} credits are used from {}".format(markersRemoved,c))
                 elif reductionSearch.group(2) == 'X':
                       markerName = re.search(r'-perMarker{([\w ]+)}', autoS)
                       try: 
                            marker = findMarker(c, markerName.group(1))
                            if marker:
                                  for iter in range(c.markers[marker]):
                                        if reductionSearch.group(1) == 'Reduce':
                                             if fullCost > 0:
                                                    reduction += 1
                                                    fullCost -= 1
                                        else: 
                                             reduction -= 1
                                             fullCost += 1
                       except: notify("!!!ERROR!!! ReduceXCost - Bad Script")
                 else:
                       orig_reduction = reduction
                       for iter in range(num(reductionSearch.group(2))):  # if there is a match, the total reduction for this card's cost is increased.
                            if reductionSearch.group(1) == 'Reduce': 
                                  if fullCost > 0: 
                                        reduction += 1
                                        fullCost -= 1
                            else: 
                                  reduction -= 1
                                  fullCost += 1
                       if orig_reduction != reduction: # If the current card actually reduced or increased the cost, we want to announce it
                            if reduction > 0 and not dryRun: notify(" -- {} reduces cost by {}".format(c,reduction - orig_reduction))
                            elif reduction < 0 and dryRun: notify(" -- {} increases cost by {}".format(c,abs(reduction - orig_reduction)))
     debugNotify("<<< reduceCost(). final reduction = {}".format(reduction)) #Debug
     return reduction

def chkSuperiority(Autoscript, card):
     debugNotify(">>> chkSuperiority()") #Debug
     debugNotify("### AS = {}. Card = {}".format(Autoscript, card),3) #Debug
     haveSuperiority = True # The default is True, which means that if we do not have a relevant autoscript, it's always True
     supRegex = re.search(r'-ifSuperiority([\w ]+)',Autoscript)
     if supRegex:
           supPlayers = compareObjectiveTraits(supRegex.group(1))
           if len(supPlayers) > 1 or supPlayers[0] != card.controller: haveSuperiority = False # If the controller of the card requiring superiority does not have the most objectives with that trait, we return False
     debugNotify("<<< chkSuperiority(). Return: {}".format(haveSuperiority)) #Debug
     return haveSuperiority
#------------------------------------------------------------------------------
#  Card Effects
#------------------------------------------------------------------------------

def clearStoredEffects(card, silent = False,continuePath = True): # A function which clears a card's waiting-to-be-activated scripts
     debugNotify(">>> clearStoredEffects with card: {}".format(card))
     selectedAbility = eval(getGlobalVariable('Stored Effects'))
     forcedTrigger = False
     if selectedAbility.has_key(card._id):
           debugNotify("Card's selectedAbility: {}".format(selectedAbility))
           if re.search(r'-isForced',selectedAbility[card._id][0]):
                 if not silent and not confirm("This units effect is forced which means you have to use it if possible. Are you sure you want to ignore it?"): return
                 else: forcedTrigger = True
     else: debugNotify("Card has no selectedAbility entry")
     debugNotify("Clearing Highlight",3)
     if card.highlight == ReadyEffectColor or card.highlight == OverpaidEffectColor or card.highlight == UnpaidAbilityColor: 
           if not selectedAbility.has_key(card._id): card.highlight = None
           else: card.highlight = selectedAbility[card._id][2]  # We don't want to change highlight if it was changed already by another effect.
     debugNotify("Sending card to its final destination if it has any")
     if continuePath: continueOriginalEvent(card,selectedAbility)
     debugNotify("Deleting selectedAbility tuple",3)
     if selectedAbility.has_key(card._id): del selectedAbility[card._id]
     debugNotify("Uploading selectedAbility tuple",3)
     setGlobalVariable('Stored Effects',str(selectedAbility))
     cardsLeaving(card,'remove')
     if not silent: 
           if forcedTrigger: notify(":::WARNING::: {} has chosen to ignore the FORCED trigger of {}.".format(me,card))
           else: notify("{} chose not to activate {}'s ability".format(me,card))
     debugNotify("<<< clearStoredEffects")

def clearAllEffects(silent = False): # A function which clears all card's waiting-to-be-activated scripts. This is not looping clearStoredEffects() to avoid too many setGlobalVariable calls
     debugNotify(">>> clearAllEffects")
     selectedAbility = eval(getGlobalVariable('Stored Effects'))   
     for cID in selectedAbility:
           debugNotify("Clearing Effects for {}".format(Card(cID)),3)
           debugNotify("selectedAbility[cID] = {}".format(selectedAbility[cID]),3)
           if not re.search(r'-isForced',selectedAbility[cID][0]):
                 if Card(cID).highlight == ReadyEffectColor or Card(cID).highlight == OverpaidEffectColor or Card(cID).highlight == UnpaidAbilityColor: Card(cID).highlight = selectedAbility[cID][2] # We do not clear Forced Triggers so that they're not forgotten.
                 debugNotify("Sending card to its final destination if it has any",3)
                 continueOriginalEvent(Card(cID),selectedAbility)
                 debugNotify("Now Deleting card's dictionary entry",4)
                 del selectedAbility[cID]
                 cardsLeaving(Card(cID),'remove')
           elif Card(cID).group != table:
                 debugNotify("Card was not in table. Assuming player monkeyed around and clearing",3)
                 del selectedAbility[cID]
                 cardsLeaving(Card(cID),'remove')         
           else: 
                 notify(":::WARNING::: {}'s FORCED Trigger is still remaining.".format(Card(cID)))
     debugNotify("Clearing all highlights from cards not waiting for their abilities")
     for card in table:
           if (card.highlight == ReadyEffectColor or card.highlight == OverpaidEffectColor) and not selectedAbility.has_key(card._id): card.highlight = None # If the card is still in the selectedAbility, it means it has a forced effect we don't want to clear.
     setGlobalVariable('Stored Effects',str(selectedAbility))
     if not silent: notify(":> All existing card effect triggers were ignored.".format(card))
     debugNotify("<<< clearAllEffects")

def continueOriginalEvent(card,selectedAbility):
     debugNotify(">>> continueOriginalEvent with card: {}".format(card))
     if selectedAbility.has_key(card._id):
           debugNotify("selectedAbility action = {}".format(selectedAbility[card._id][3]),2)
           if selectedAbility[card._id][3] == 'STRIKE': # If the action is a strike, it means we interrupted a strike for this effect, in which case we want to continue with the strike effects now.
                 strike(card, Continuing = True)
           if re.search(r'LEAVING',selectedAbility[card._id][3]) or selectedAbility[card._id][3] == 'THWART': 
                 if re.search(r'-DISCARD',selectedAbility[card._id][3]) or selectedAbility[card._id][3] == 'THWART': discard(card,Continuing = True)
                 elif re.search(r'-HAND',selectedAbility[card._id][3]): returnToHand(card,Continuing = True) 
                 elif re.search(r'-DECKBOTTOM',selectedAbility[card._id][3]): sendToBottom(Continuing = True) # This is not passed a specific card as it uses a card list, which we've stored in a global variable already
                 elif re.search(r'-EXILE',selectedAbility[card._id][3]): exileCard(card, Continuing = True)
                 elif re.search(r'-CAPTURE',selectedAbility[card._id][3]): capture(targetC = card, Continuing = True)
     else: debugNotify("No selectedAbility entry")
     debugNotify("<<< continueOriginalEvent with card: {} and selectedAbility {}".format(card,selectedAbility))  

     
def storeCardEffects(card,Autoscript,cost,previousHighlight,actionType,preTargetCard,count = 0):
     debugNotify(">>> storeCardEffects()")
     # A function which store's a bunch of variables inside a shared dictionary
     # These variables are recalled later on, when the player clicks on a triggered card, to recall the script to execute and it's peripheral variables.
     selectedAbility = eval(getGlobalVariable('Stored Effects'))   
     selectedAbility[card._id] = (Autoscript,cost,previousHighlight,actionType,preTargetCard,count)
     # We set a tuple of variables for when we come back to executre the scripts
     # The first variable is tracking which script is going to be used
     # The Second is the amount of resource payment 
     # The third entry in the tuple is the card's previous highlight if it had any.
     # The fourth entry in the tuple is the type of autoscript this is. In this case it's a 'USE' script, which means it was manually triggered by the player
     # The fifth is used to parse pre-selected targets for the card effects. Primarily used in autoscriptOtherPlayers()
     # The sixth entry is used to pass an amount some scripts require (e.g. the difference in edge ranks for Bounty)
     setGlobalVariable('Stored Effects',str(selectedAbility))
     debugNotify("<<< storeCardEffects()")
     


def placeCard(card): 
     mute()
     try:
           debugNotify(">>> placeCard() for card: {}".format(card)) #Debug
           if Automations['Placement']:
                 debugNotify("We have placement automations",2) #Debug
                 cardType = fetchProperty(card,'Type')
                 if cardType == 'Character': # For now we only place Units
                       unitAmount = len([c for c in table if fetchProperty(c,'Type') == 'Character' and c.controller == me and c.highlight != UnpaidColor and c.highlight != DummyColor and c.orientation != Rot270]) - 1 # we reduce by 1, because it will always count the unit we're currently putting in the game
                       debugNotify("my unitAmount is: {}.".format(unitAmount)) #Debug
                       freePositions = eval(me.getGlobalVariable('freePositions')) # We store the currently released position
                       debugNotify(" my freePositions is: {}.".format(freePositions),2) #Debug
                       if freePositions != []: # We use this variable to see if there were any discarded units and we use their positions first.
                            positionC = freePositions.pop() # This returns the last position in the list of positions and deletes it from the list.
                            debugNotify("### positionC is: {}.".format(positionC)) #Debug
                            card.moveToTable(positionC[0],positionC[1])
                            me.setGlobalVariable('freePositions',str(freePositions))
                       else:
                            loopsNR = unitAmount / 7
                            loopback = 7 * loopsNR                  
                            xoffset = 175 - (cheight(card,0) * (unitAmount - loopback))
                            # xoffset = (playerside * (100 + cheight(card,0))) - (playerside * cheight(card,0) * (unitAmount - loopback)) - 25
                            debugNotify("xoffset: {} - cheight: {} - unitamount: {} - loopback: {}".format(xoffset,cheight(card,0),unitAmount,loopback))
                            yoffset = (cheight(card,3) * (loopsNR)) + 80                  
                            newx,newy = positionOffset(card,xoffset,yoffset)
                            card.moveToTable(newx,newy)
                 elif cardType == 'Support':
                       hostType = re.search(r'Placement:([A-Za-z1-9:_ ]+)', card.AutoScript)
                       if hostType:
                            debugNotify("### hostType: {}.".format(hostType.group(1))) #Debug
                            host = findTarget('Targeted-at{}'.format(hostType.group(1)))
                            if host == []: 
                                  whisper("ABORTING!")
                                  return
                            else:
                                  debugNotify("### We have a host") #Debug
                                  storeAttachment(card,host[0],forced=True)
                                  debugNotify("### About to move into position") #Debug
                                  arrangeAttachments(host[0])
                                  host[0].target(False)
                       else:
                            supportAmount = len([c for c in table if fetchProperty(c,'Type') == 'Support' and c.controller == me and c.highlight != UnpaidColor and c.highlight != DummyColor and c.orientation != Rot270 and not hasSubType(c,'Attachment.')]) - 1
                            debugNotify("my supportAmount is: {}.".format(supportAmount)) #Debug
                            freePositions = eval(me.getGlobalVariable('freeSupportPositions')) # We store the currently released position
                            debugNotify(" my freeSupportPositions is: {}.".format(freePositions),2) #Debug
                            if freePositions != []: # We use this variable to see if there were any discarded units and we use their positions first.
                                  positionC = freePositions.pop() # This returns the last position in the list of positions and deletes it from the list.
                                  debugNotify("### positionC is: {}.".format(positionC)) #Debug
                                  card.moveToTable(positionC[0],positionC[1])
                                  me.setGlobalVariable('freeSupportPositions',str(freePositions))
                            else:
                                  loopsNR = supportAmount / 7
                                  loopback = 7 * loopsNR                  
                                  # xoffset = (playerside * (-550 + cheight(card,0))) + (playerside * cheight(card,0) * (supportAmount - loopback)) - 25
                                  xoffset = 175 - (cheight(card,0) * (supportAmount - loopback))
                                  debugNotify("xoffset: {} - cheight: {} - supportamount: {} - loopback: {}".format(xoffset,cheight(card,0),supportAmount,loopback))
                                  yoffset = 174 + (cheight(card,3) * (loopsNR))
                                  # yoffset = yaxisMove(card) + (cheight(card,3) * (loopsNR) * playerside) + (18 * playerside)                  
                                  newx, newy = positionOffset(card, xoffset, yoffset)
                                  card.moveToTable(newx,newy)
                 elif cardType == 'Conspiracy':
                       debugNotify(">>> Conspiracy")
                       cardPlaced = False
                       activeStories = eval(getGlobalVariable('activeStories'))
                       for key in storyPositions:
                            debugNotify(">>> Key: {}".format(key))
                            if cardPlaced: continue
                            if re.search('Conspiracy',key):
                                  story = activeStories.get(key,'?')
                                  if story != '?':
                                        debugNotify("Checking for {}".format(story))
                                        cardOnTable = [c for c in table if c._id == story]
                                        debugNotify("Found: {}".format(cardOnTable))
                                        if len(cardOnTable) == 0: 
                                             story = '?'
                                             del activeStories[key]
                                             setGlobalVariable('activeStories',str(activeStories))
                                  if story == '?':
                                        debugNotify(">>> Playing Story Card")
                                        playStoryCard(key, card)
                                        cardPlaced = True
           else: debugNotify("No Placement Automations. Doing Nothing",2)
           debugNotify("<<< placeCard()") #Debug
     except: notify("!!! ERROR !!! in placeCard()")

def freeCardPlacement(card): # A function which stores a unit's position when it leaves play, so that it can be re-used by a different unit
    cardType = fetchProperty(card,'Type')
    if Automations['Placement'] and (cardType == 'Character' or cardType == "Support") and card.orientation != Rot270:
        if card.owner == me and card.highlight != DummyColor and card.highlight != UnpaidColor :
            cardType = fetchProperty(card,'Type')
            freePositions = []
            if cardType == 'Character':
                freePositions = eval(me.getGlobalVariable('freePositions')) # We store the currently released position
                freePositions.append(card.position)
                me.setGlobalVariable('freePositions',str(freePositions))
            elif cardType == 'Support' and not hasSubType(card, 'Attachment.'):
                freePositions = eval(me.getGlobalVariable('freeSupportPositions'))
                freePositions.append(card.position)
                me.setGlobalVariable('freeSupportPositions',str(freePositions))
            debugNotify("Positions: {}".format(str(freePositions)))

def peek(card):
       mute()
       card.peek()
def readyEffect(card,forced = False, overPaid = False):
    # This function prepares an event for being activated and puts the initial warning out if necessary.
    debugNotify(">>> readyEffect()") #Debug
    if overPaid: card.highlight = OverPaidEffectColor
    else: card.highlight = ReadyEffectColor
    notify(":::NOTICE::: {}'s {} is about to take effect...".format(card.controller,card))
    warnImminentEffects = getSetting('warnEffect', "An effect is ready to trigger but has not been done automatically in order to allow your opponent to react.\
                                                 \nOnce your opponent had the chance to play any interrupts, double click on the green-highlighted card to finalize it and resolve any effects (remember to target any relevant cards if required).\
                                               \n\n(This message will not appear again)") # Warning about playing events. Only displayed once.
    if (not hardcoreMode or card.type == 'Event' or forced) and card.owner == me and warnImminentEffects != 'Done':
        information(warnImminentEffects)
        setSetting('warnEffect', 'Done')
    debugNotify("<<< readyEffect()") #Debug    
#------------------------------------------------------------------------------
#  Card Information
#------------------------------------------------------------------------------
def hasSubType(card,matchType):
     debugNotify("hasSubtype({}) - {}".format(matchType,card.Subtypes))
     if re.search(r'{}'.format(matchType),card.Subtypes):
           debugNotify(">> Has Subtype: {}".format(matchType))
           return True
     else: return False

def hasKeyword(card,matchType):
     debugNotify("hasKeyword({}) - {}".format(matchType,card.Keyword),1)
     cardKeywords = getKeywords(card)
     return cardKeywords.count(matchType)

def getSkill(card, printedOnly = False):
     debugNotify(">>> getSkill()")
     skill = -1
     if card.Skill: skill = num(card.Skill)
     if printedOnly: return skill
     else:  
           wipeSkill = False
           attRegex = re.compile(r'(Bonus|Subtract)([0-9X#])Skill')
           for att in getAttachments(card):
                 c = Card(att)
                 AS = c.Autoscript
                 if AS == '': continue
                 Autoscripts = AS.split('||')
                 for autoS in Autoscripts:
                       debugNotify("### Checking {} with AS: {}".format(c,autoS))
                       if not chkPlayer(autoS,c.controller, False): continue
                       attSearch = attRegex.search(autoS)
                       if attSearch:
                            debugNotify("### Possible Match found in {}".format(c),3)
                            if not chkDummy(autoS, c): continue
                            if not checkOriginatorRestrictions(autoS,c): continue
                            if not chkSuperiority(autoS, c): continue
                            if attSearch.group(1) == 'Bonus':
                                  debugNotify("::: Adding {} :::".format(attSearch.group(2)))
                                  if attSearch.group(2) == 'X':
                                        skill += num(card.Skill)
                                  elif attSearch.group(2) == '#':
                                        notify("::: Warning ::: Invalid skill modifier on {}.".format(c.name))
                                  else:
                                        skill += num(attSearch.group(2))
                            else:
                                  debugNotify("::: Subtracting {} :::".format(attSearch.group(2)))
                                  if attSearch.group(2) == 'X':
                                        skill -= num(card.Skill)
                                  elif attSearch.group(2) == '#':
                                        debugNotify("{} will remove all skill from {}".format(c.name,card.name))
                                        wipeSkill = True
                                  else:
                                        skill -= num(attSearch.group(2))
           cardList = [c for c in table if c.isFaceUp and c.orientation != Rot270]
           skillRegex = re.compile(r'(Add|Remove)([0-9])Skill-affects([A-Z][A-Za-z ]+)(-not[A-Za-z_& ]+)?') 
           for c in cardList:
                 AS = c.AutoScript
                 if AS == '': continue
                 Autoscripts = AS.split('||')
                 debugNotify("### {} Scripts: {}".format(card.name, len(Autoscripts)))
                 for autoS in Autoscripts:
                       debugNotify("### Checking {} with AS: {}".format(c,autoS)) #debug
                       if not chkPlayer(autoS, c.controller, False): continue
                       skillSearch = skillRegex.search(autoS)
                       if skillSearch: debugNotify("!!! Regex is {}".format(keywordSearch.groups()))
                       else: debugNotify("!!! No Skill Modifier regex Match!")
                       if skillSearch:
                            debugNotify("### Possible Match found in {}".format(c),3)
                            if not chkDummy(autoS, c): continue
                            if not checkOriginatorRestrictions(autoS,c): continue
                            if not chkSuperiority(autoS, c): continue
                            if skillSearch.group(1) == 'Add':
                                  debugNotify("::: Adding {} :::".format(attSearch.group(2)))
                                  if skillSearch.group(2) == 'X':
                                        skill += num(card.Skill)
                                  elif skillSearch.group(2) == '#':
                                        notify("::: Warning ::: Invalid skill modifier on {}.".format(c.name))
                                  else:
                                        skill += num(skillSearch.group(2))
                            else:
                                  debugNotify("::: Subtracting {} :::".format(skillSearch.group(2)))
                                  if skillSearch.group(2) == 'X':
                                        skill -= num(card.Skill)
                                  elif skillSearch.group(2) == '#':
                                        debugNotify("{} will remove all skill from {}".format(c.name,card.name))
                                        wipeSkill = True
                                  else:
                                        skill -= num(skillSearch.group(2)) 

           if wipeSkill: skill = 0
           return skill
           
 
def cardStatus(card):
     debugNotify(">>> cardStatus() - {} - {} - {} - {}".format(card.type, card.name, card.orientation, card.isFaceUp),4)
     cS = "InPlay"
     cardType = fetchProperty(card,'Type')
     if (cardType == "Token" and re.search(r'\bDomain\b',card.name)): cS = "Domain"
     elif (card.orientation == Rot270 and not card.isFaceUp): cS = "Domain"
     elif (card.orientation == Rot90 and not card.isFaceUp): cS = "Insane"
     elif (card.orientation == Rot90 and card.isFaceUp): cS = "Exhausted"
     elif (card.orientation == Rot270 and card.isFaceUp): cS = "Resource"
     elif (cardType == "Story"): cS = "Story"
     elif (cardType == "Conspiracy"): cS = "Conspiracy"
     debugNotify("<<< cardStatus() returned {}".format(cS))
     return cS
       
def getIcons(card, type, printedOnly = False, verbose = False):
     iconSearch = ''
     if type == 'Terror': iconSearch = '@'
     elif type == 'Combat': iconSearch = '#'
     elif type == 'Arcane': iconSearch = '$'
     elif type == 'Investigation': iconSearch = '%'
     cardIcons = fetchProperty(card,'Icons')
     count = cardIcons.count(iconSearch)
     cardCount = count
     if printedOnly: return count
     else:
           attRegex = re.compile(r'(Bonus|Subtract)({}|All)Icon'.format(type))
           for att in getAttachments(card): # Check attachments
                 c = Card(att)
                 debugNotify("Card: {}".format(c.name))
                 AS = c.AutoScript
                 if AS == '': continue
                 Autoscripts = AS.split('||')
                 debugNotify("Scripts: {}".format(Autoscripts))
                 for autoS in Autoscripts:
                       debugNotify("### Checking {} with AS: {}".format(c,autoS))
                       if not chkPlayer(autoS,c.controller, False): continue
                       attSearch = attRegex.search(autoS)
                       if attSearch:
                            debugNotify("### Possible Match found in {}".format(c),3)
                            if not chkDummy(autoS, c): continue
                            if not checkOriginatorRestrictions(autoS,c): continue
                            if not chkSuperiority(autoS, c): continue
                            if attSearch.group(1) == 'Bonus':
                                  count += 1
                            elif count > 0: count -= 1
           iconIncreasers = []
           iconModifiers = []
           cardList = [c for c in table if c.isFaceUp and c.orientation != Rot270]
           iconRegex = re.compile(r'(Add|Remove)([0-9#X]+)({}|All)Icon-affects([A-Z][A-Za-z ]+)(-not[A-Za-z_& ]+)?'.format(type))
           for c in cardList:
                 AS = c.AutoScript
                 if AS == '': continue
                 Autoscripts = AS.split('||')
                 debugNotify("### {} Scripts: {}".format(card.name, len(Autoscripts)))
                 for autoS in Autoscripts:
                       debugNotify("### Checking {} with AS: {}".format(c,autoS)) #debug
                       if not chkPlayer(autoS, c.controller, False): continue
                       iconSearch = iconRegex.search(autoS)
                       if iconSearch: debugNotify("!!! Regex is {}".format(iconSearch.groups()))
                       else: debugNotify("!!! No Icon Modifier regex Match!")
                       if iconSearch:
                            debugNotify("### Possible Match found in {}".format(c),3)
                            if not chkDummy(autoS, c): continue
                            if not checkOriginatorRestrictions(autoS,c): continue
                            if not chkSuperiority(autoS, c): continue
                            if iconSearch.group(1) == 'Add':
                                  debugNotify("Adding card to Icon Increasers list")
                                  iconIncreasers.append((c,iconSearch,autoS))
                            else:
                                  debugNotify("adding card to Icon Modifiers list")
                                  iconModifiers.append((c,iconSearch,autoS))
           if len(iconIncreasers) > 0: iconModifiers.extend(iconIncreasers)
           debugNotify(str(iconModifiers))
           for cTuple in iconModifiers:
                debugNotify("### Checking next cTuple",4)
                c = cTuple[0]
                iconSearch = cTuple[1]
                autoS = cTuple[2]
                debugNotify("### cTuple[0] (i.e. card) is: {}".format(c),2)
                debugNotify("### cTuple[2] (i.e. autoS) is: {}".format(autoS))
                if (iconSearch.group(4) == 'Self' and c == card) or iconSearch.group(4) == 'All' or checkCardRestrictions(gatherCardProperties(card, printedOnly = True), prepareRestrictions(autoS, seek = 'reduce')):
                    if not checkSpecialRestrictions(autoS,card): continue
                    debugNotify(" ### Search match! Modifier value is {}".format(iconSearch.group(2)),3)
                    if iconSearch.group(2) == '#' and iconSearch.group(1) == 'Remove':
                        count -= cardCount
                        cardCount = 0
                    elif iconSearch.group(2) == '#' and iconSearch.group(1) == 'Add':
                        count += cardCount
                        cardCount += cardCount
                    elif iconSearch.group(2) == 'X':
                        markerName = re.search(r'-perMarker{([\w ]+)}', autoS)
                        try: 
                              marker = findMarker(c, markerName.group(1))
                              if marker:
                                    for iter in range(c.markers[marker]):
                                         if reductionSearch.group(1) == 'Remove':
                                                if count > 0:
                                                    count -= 1
                                         else: count += 1
                        except: notify("!!!ERROR!!! ReduceXCost - Bad Script")
                    else:
                        orig_count = count
                        for iter in range(num(iconSearch.group(2))):
                              if iconSearch.group(1) == 'Remove':
                                    if count > 0: count -= 1
                              else: count += 1
                        if orig_count != count:
                              diff = count - orig_count
                              if diff > 0 and verbose: notify(" -- {} increases {}'s {} icons by {}".format(c,card,type,diff))
                              elif verbose: notify("-- {} decreases {}'s {} icons by {}".format(c,card,type,abs(diff))) 
     return count

def getKeywords(card, keyword = 'All', printedOnly = False, verbose = False):
     debugNotify(">>> getKeywords()")
     cKeywords = card.Keyword
     keywordsList = []
     keywordRemovers = []
     debugNotify("Card Keywords: {}".format(cKeywords))
     strippedKeywordsList = cKeywords.split('.')
     debugNotify("Stripped Keywords: {}".format(strippedKeywordsList))
     if len(strippedKeywordsList) > 0:
        for cardKW in strippedKeywordsList:
            strippedKW = cardKW.strip() # Remove any leading/trailing spaces between traits. We need to use a new variable, because we can't modify the loop iterator.
            if strippedKW and (keyword == 'All' or re.search(r'{}'.format(keyword),strippedKW)):
                debugNotify("Stripped Keyword: {}".format(strippedKW))
                getToughness = re.compile(r'(Toughness) \+([0-9])')
                checkToughness = getToughness.search(strippedKW)
                getFated = re.compile(r'(Fated) ([0-9])')
                checkFated = getFated.search(strippedKW)
                if checkToughness:
                    for x in xrange(0,num(checkToughness.group(2))):
                        keywordsList.append(checkToughness.group(1))
                if checkFated:
                    for x in xrange(0,num(checkFated.group(2))):
                        keywordsList.append(checkFated.group(1))
                else: keywordsList.append(strippedKW) 
     debugNotify("Keywords: {}".format(keywordsList))
     if printedOnly: return keywordList
     else:
           attRegex = re.compile(r'(Bonus|Subtract)([0-9])([A-Z][A-Za-z ]+)Keyword')
           for att in getAttachments(card):
                 c = Card(att)
                 AS = c.Autoscript
                 if AS == '': continue
                 Autoscripts = AS.split('||')
                 for autoS in Autoscripts:
                       debugNotify("### Checking {} with AS: {}".format(c,autoS))
                       if not chkPlayer(autoS,c.controller, False): continue
                       attSearch = attRegex.search(autoS)
                       if attSearch:
                            debugNotify("### Possible Match found in {}".format(c),3)
                            if not chkDummy(autoS, c): continue
                            if not checkOriginatorRestrictions(autoS,c): continue
                            if not chkSuperiority(autoS, c): continue
                            if attSearch.group(1) == 'Bonus':
                                  debugNotify("::: Adding {} :::".format(attSearch.group(3)))
                                  if attSearch.group(3) == 'Toughness':
                                        for x in xrange(0,num(attSearch.group(2))):
                                             keywordsList.append(attSearch.group(3))
                                  else: keywordsList.append(attSearch.group(3))
                            else:
                                  debugNotify("::: Adding {} to removal list :::".format(attSearch.group(3)))
                                  keywordRemovers.append(attSearch.group(3))               
           cardList = [c for c in table if c.isFaceUp and c.orientation != Rot270]
           keywordRegex = re.compile(r'(Add|Remove)([0-9])([A-Z][A-Za-z ]+)Keyword-affects([A-Z][A-Za-z ]+)(-not[A-Za-z_& ]+)?') 
           for c in cardList:
                 AS = c.AutoScript
                 if AS == '': continue
                 Autoscripts = AS.split('||')
                 debugNotify("### {} Scripts: {}".format(card.name, len(Autoscripts)))
                 for autoS in Autoscripts:
                       debugNotify("### Checking {} with AS: {}".format(c,autoS)) #debug
                       if not chkPlayer(autoS, c.controller, False): continue
                       keywordSearch = keywordRegex.search(autoS)
                       if keywordSearch: debugNotify("!!! Regex is {}".format(keywordSearch.groups()))
                       else: debugNotify("!!! No Keyword Modifier regex Match!")
                       if keywordSearch:
                            debugNotify("### Possible Match found in {}".format(c),3)
                            if not chkDummy(autoS, c): continue
                            if not checkOriginatorRestrictions(autoS,c): continue
                            if not chkSuperiority(autoS, c): continue
                            if (keywordSearch.group(4) == 'Self' and c == card) or keywordSearch.group(4) == 'All' or checkCardRestrictions(gatherCardProperties(card), prepareRestrictions(autoS,seek = 'reduce')):
                                if keywordSearch.group(1) == 'Add':
                                      debugNotify("::: Adding {} :::".format(keywordSearch.group(3)))
                                      if keywordSearch.group(3) == 'Toughness':
                                            for x in xrange(0,num(keywordSearch.group(2))):
                                                 keywordsList.append(keywordSearch.group(3))
                                      else: keywordsList.append(keywordSearch.group(3))
                                else:
                                      debugNotify("::: Adding {} to removal list :::".format(keywordSearch.group(3)))
                                      keywordRemovers.append(keywordSearch.group(3))
           if len(keywordRemovers) > 0:
                 for remover in keywordRemovers:
                       while remover in keywordsList:
                            debugNotify("::: {} exists, removing. :::".format(remover)) 
                            keywordsList.remove(remover)
           return keywordsList
     

def getStoryIcons(card, printedOnly = False):
     struggleIcons = eval(getGlobalVariable('struggleIcons'))
     if len(struggleIcons) > 0:
           return struggleIcons
     else:
           tmpTerror = []
           tmpCombat = []
           tmpArcane = []
           tmpInvestigation = []
           icons = card.properties['Struggle Icons']
           tmpIcons = icons.split(' ')
           attachments  = getAttachments(card)
           if not printedOnly:
               if len(attachments) > 0:
                     for a in attachments:
                           att = Card(a)
                           tmpIcons.extend(att.properties['Struggle Icons'].split(' '))
               if getGlobalVariable('Current Story') == card._id:
                     for player in getPlayers():
                           currentStory = Card(num(getGlobalVariable('Current Story')))
                           committedCharacters = eval(me.getGlobalVariable('committedCharacters')).get(currentStory._id,[])
                           if len(committedCharacters) > 0:
                                for charid in committedCharacters:
                                      char = Card(charid)
                                      tmpIcons.extend(att.properties['Struggle Icons'].split(' '))
           for icon in tmpIcons:
                 if icon == '@': tmpTerror.append('Terror')
                 elif icon == '#':tmpCombat.append('Combat')
                 elif icon == '$':tmpArcane.append('Arcane')
                 elif icon == '%':tmpInvestigation.append('Investigation')
           struggleIcons.extend(tmpTerror)
           struggleIcons.extend(tmpCombat)
           struggleIcons.extend(tmpArcane)
           struggleIcons.extend(tmpInvestigation)
           debugNotify("Struggle Icons: {}".format(struggleIcons))
           return struggleIcons
     
     
def getAvailableResources(card, type = 'All'):
    debugNotify(">>> getAvailableResources() {}".format(card.name))
    cStatus = cardStatus(card)
    if cStatus != 'Domain': return 0
    isDrained = False
    resources = 0
    for att in getAttachments(card):
        attCard = Card(att)
        debugNotify("Attachment: {}".format(attCard.name),4)
        if attCard.Name == 'Drain Token': isDrained = True
        elif cardStatus(attCard) == 'Resource':
            cardResources = getResources(attCard)
            if type == 'All' or type == cardResources[1]:
                resources += cardResources[0]
    if isDrained: resources = 0
    debugNotify("<<<< getAvailableResources() {}".format(resources),3)
    return resources
            
#------------------------------------------------------------------------------
#  Online Functions
#------------------------------------------------------------------------------


def versionCheck():
     debugNotify(">>> versionCheck()", 3) #Debug
     global startupMsg
     me.setGlobalVariable('gameVersion',gameVersion)
     if not startupMsg: MOTD() # If we didn't give out any other message , we give out the MOTD instead.
     startupMsg = True
     debugNotify("<<< versionCheck()", 3) #Debug
           
           
def MOTD():
     debugNotify(">>> MOTD()") #Debug
     if me.name == 'DarkSir23' or me.name == 'darksir23' : return #I can't be bollocksed
     (MOTDurl, MOTDcode) = webRead('https://raw.github.com/DarkSir23/CAll-of-Cthulhu-OCTGN/master/MOTD.txt')
     (DYKurl, DYKcode) = webRead('https://raw.github.com/DarkSir23/Call-of-Cthulhu-OCTGN/master/DidYouKnow.txt')
     if (MOTDcode != 200 or not MOTDurl) or (DYKcode !=200 or not DYKurl):
           whisper(":::WARNING::: Cannot fetch MOTD or DYK info at the moment.")
           return
     DYKlist = DYKurl.split('||')
     DYKrnd = rnd(0,len(DYKlist)-1)
     while MOTDdisplay(MOTDurl,DYKlist[DYKrnd]) == 'MORE': 
           MOTDurl = '' # We don't want to spam the MOTD for the further notifications
           DYKrnd += 1
           if DYKrnd == len(DYKlist): DYKrnd = 0
     debugNotify("<<< MOTD()", 3) #Debug
     
def MOTDdisplay(MOTD,DYK):
     debugNotify(">>> MOTDdisplay()") #Debug
     if re.search(r'http',MOTD): # If the MOTD has a link, then we do not sho DYKs, so that they have a chance to follow the URL
           MOTDweb = MOTD.split('&&')      
           if confirm("{}".format(MOTDweb[0])): openUrl(MOTDweb[1].strip())
     elif re.search(r'http',DYK):
           DYKweb = DYK.split('&&')
           if confirm("{}\
                          \n\nDid You Know?:\
                              \n------------------\
                              \n{}".format(MOTD,DYKweb[0])):
                 openUrl(DYKweb[1].strip())
     elif confirm("{}\
                          \n\nDid You Know?:\
                              \n-------------------\
                              \n{}\
                              \n-------------------\
                          \n\nWould you like to see the next tip?".format(MOTD,DYK)): return 'MORE'
     return 'STOP'



def concede(group=table,x=0,y=0):
     mute()
     if confirm("Are you sure you want to concede this game?"): 
           notify("{} has conceded the game".format(me))
     else: 
           notify("{} was about to concede the game, but thought better of it...".format(me))
#------------------------------------------------------------------------------
# Debugging
#------------------------------------------------------------------------------
     
def TrialError(group, x=0, y=0): # Debugging
     global debugVerbosity
     if debugVerbosity == None: debugVerbosity = int(me.getGlobalVariable('debugVerbosity'))
     mute()
     delayed_whisper("## Checking Debug Verbosity")
     if debugVerbosity >=0 and (me.name == 'DarkSir23' or me.name == 'darksir23'): 
           if debugVerbosity == 0: debugVerbosity = 1
           elif debugVerbosity == 1: debugVerbosity = 2
           elif debugVerbosity == 2: debugVerbosity = 3
           elif debugVerbosity == 3: debugVerbosity = 4
           else: debugVerbosity = 0
           me.setGlobalVariable('debugVerbosity',str(debugVerbosity))
           delayed_whisper("Debug verbosity is now: {}".format(debugVerbosity))
           return
     else:
           debugVerbosity = 0
           me.setGlobalVariable('debugVerbosity',str(debugVerbosity))
     ######## Testing Corner ########
     ###### End Testing Corner ######

     
def extraASDebug(Autoscript = None):
     if Autoscript and debugVerbosity >= 3: return ". Autoscript:{}".format(Autoscript)
     else: return ''

def ShowPos(group, x=0,y=0):
    debugNotify('x={}, y={}'.format(x,y),1)
           
def ShowPosC(card, x=0,y=0):
     if debugVerbosity >= 1: 
           debugNotify(">>> ShowPosC(){}".format(extraASDebug())) #Debug
           x,y = card.position
           debugNotify('card x={}, y={}'.format(x,y),1)      
           
def controlChange(card,x,y):
     if card.controller != me: card.setController(me)
     else: card.setController(findOpponent())
     
def DebugCard(card, x=0, y=0):
     whisper("Position: {}".format(card.position))
     if getAttached(card): tmp = getAttached(card).name
     else: tmp = "None"
     whisper("Attached to: {}".format(tmp))
     whisper("Attachments: {}".format(getAttachments(card)))
     whisper("Terror Icons: {}".format(getIcons(card, "Terror")))
     whisper("Combat Icons: {}".format(getIcons(card, "Combat")))
     whisper("Arcane Icons: {}".format(getIcons(card, "Arcane")))
     whisper("Investigation Icons: {}".format(getIcons(card, "Investigation")))
     whisper("Keywords: {}".format(getKeywords(card)))
     whisper("AutoAction: {}".format(fetchProperty(card,'AutoAction')))
     whisper("AutoScript: {}".format(fetchProperty(card,'AutoScript')))
def clrResourceMarkers(card):
     for cMarkerKey in card.markers: 
           debugNotify("### Checking marker {}.".format(cMarkerKey[0]),3)
           for resdictKey in resdict:
                 if resdict[resdictKey] == cMarkerKey or cMarkerKey[0] == 'Ignores Affiliation Match': 
                       card.markers[cMarkerKey] = 0
                       break
def cardSteadfast(card):
    steadfast = card.Name.count(card.properties['Resource Icon'])
    return steadfast

#-------------------------------------------
#  Scoring Functions
#-------------------------------------------
def addSuccess(card, x=0, y=0, verbose=False):
    mute()
    debugNotify(">>> addSuccess()")
    if cardStatus(card) == 'Story' or cardStatus(card) == 'Conspiracy':
        storyScores = eval(me.getGlobalVariable('storyScores'))
        if storyScores.get(card._id,'?') == '?':
             storyScores[card._id] = 1
        else: storyScores[card._id] += 1
        me.setGlobalVariable('storyScores', str(storyScores))
        checkStory(card)
        updateScores()
    else:
        card.markers[mdict['Success']] += 1
        markerEffects('afterSuccessAdd')
    notify("{} adds one success to {}.".format(me,card.name))
    checkMarkers(card)
    debugNotify("<<< addSuccess()")
    
def remSuccess(card, x=0, y=0):
    mute()
    debugNotify(">>> remSuccess()")
    if cardStatus(card) == 'Story':
       storyScores = eval(me.getGlobalVariable('storyScores'))
       if storyScores.get(card._id,'?') != '?' and storyScores.get(card._id,'?') >= 1:
          storyScores[card._id] -= 1
       me.setGlobalVariable('storyScores', str(storyScores))
       checkStory(card)
    else:
       card.markers[mdict['Success']] -= 1
       markerEffects('afterSuccessAdd')
    notify("{} removes one success from {}.".format(me,card.name))
    checkMarkers(card)
    debugNotify("<<< remSuccess()")

def checkStory(card):
     mute()
     debugNotify(">>> checkStory()")
     if not Automations['Damage/Scoring']: return
     storyScores = eval(me.getGlobalVariable('storyScores'))
     debugNotify("Checking story: {}".format(storyScores))
     if storyScores[card._id] >= 5:
           if card.controller != me: card.setController(me)
           notify("{} has won the {}: {}".format(me,card.type,card.name))
           attachments = getAttachments(card)
           attList = [c for c in table if c._id in attachments]
           for c in attList:
                 destroyCard(c,auto=True)
           runAutoScripts('StoryWon', card)
           card.moveTo(me.piles['ScoringPile'])
           finishStory()
           checkForWinner()
           replenishStoryCards()
           for player in getPlayers():
               remoteCall(player,'updateScores',[])
     debugNotify("<<< checkStory()")
           
def replenishStoryCards(group = table, x = 0, y =0):
     activeStories = eval(getGlobalVariable('activeStories'))
     # notify("Stories: {}".format(activeStories))
     for key in storyPositions:
           # notify('Key: {}'.format(key))
           if re.search('Story',key):
                 story = activeStories.get(key,'?')
                 # notify('Story: {}'.format(story))
                 if story != '?':
                       cardOnTable = [c for c in table if c._id == story]
                       if len(cardOnTable) == 0: 
                            story = '?'
                            del activeStories[key]
                            setGlobalVariable('activeStories',str(activeStories))
                 if story == '?':
                       # notify('Playing Story Card')
                       playStoryCard(key)

def updateScores():
    mute()
    debugNotify(">>> updateScores()")
    activeStories = eval(getGlobalVariable('activeStories'))
    for key in storyPositions:
        debugNotify("Key: {}".format(key))
        score = num(eval(me.getGlobalVariable('storyScores')).get(activeStories.get(key,0),0))
        debugNotify("Score: {}".format(score))
        me.counters[key].value = score
    count = 0
    for card in me.piles['ScoringPile']:
        cardType = fetchProperty(card,'Type')
        if cardType == 'Story' or cardType == 'Conspiracy':  count += 1
    me.counters['Stories won'].value = count
    debugNotify("<<< updateScores()")

def playStoryCard(location, card = None):
     activeStories = eval(getGlobalVariable('activeStories'))
     story = activeStories.get(location,'?')
     # notify('>>> playStoryCard: {} - {}'.format(location,story))
     if story != '?':
           cardOnTable = [c for c in table if c._id == story]
           if len(cardOnTable) == 0: story = '?'
     if story != '?':
           debugNotify("WARNING: Tried to place a story card while a story is still active in that position.")
           return
     else: 
           # notify("Story Positions: {}".format(storyPositions))
           pos = storyPositions.get(location,'?')
           # notify("Position: {}".format(pos))
           if pos == '?': 
                 debugNotify("WARNING: Invalid Story position.")
                 return
           else:
                 if card != None:
                       if card.controller != me: card.setController(me)
                       activeStories[location] = card._id
                       card.moveToTable(pos[0],pos[1])
                 else:
                       card = shared.piles['Story Deck'].top()
                       if card.controller != me: card.setController(me)
                       card.moveToTable(pos[0],pos[1])
                       activeStories[location] = card._id
                 setGlobalVariable('activeStories',str(activeStories))
def checkForWinner():
    debugNotify(">>> checkForWinner()")
    winners = []
    for player in getPlayers():
        if len(player.piles['ScoringPile']) >= 3:
            count = 0
            for card in player.piles['ScoringPile']:
                cardType = fetchProperty(card,'Type')
                if cardType == 'Story' or cardType == 'Conspiracy':  count += 1
            if count >= 3: winners.append(player)
    if len(winners) == 1:
       notify('::: GAME WON ::: {} has scored {} Story cards.'.format(winners[0].name,len(winners[0].piles['ScoringPile'])))
       return True
    elif len(winners) > 1:
       notify('::: MULTIPLE WINNERS :::')
       for player in winners:
             notify('{} has scored {} Story cards.'.format(player.name,len(player.piles['ScoringPile'])))
       return True
    else: return False
#-------------------------------------------
#  Event Handlers
#-------------------------------------------

def triggerMoveCard(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove):
    if card.controller == me and not isScriptMove:
        arrangeAttachments(card)
           
def triggerTableLoad():
    chooseSide()
    versionCheck()
    setGlobalVariable('firstPlayer',"-1")

def triggerNewTurn(player, turnNumber):
    me.setGlobalVariable('committedCharacters','{}')
    if player == me:
        clearTargets()
        debugNotify("New Turn - Player: {}".format(player.name),4)
        nextPhase()
def loadDeck(player,groups):    
    if player == me:
        chooseSide()
        firstPlayer = num(getGlobalVariable('firstPlayer'))
        if (int(me.getGlobalVariable('playerside')) == -1 and firstPlayer == -1): 
            whisper("Once first player has been determined.  Please run setup (Ctrl-Shift-S).")
            return
        if  len(me.piles['Deck']) >= 50 and ((me.getGlobalVariable('playerside')) == -1 or len(shared.piles['Story Deck']) > 0 or confirm("Do you want to set up the table now?  Select No only if you want to load a custom Story Deck.")): intSetup(table)
#-------------------------------------------
#  Other Stuff
#-------------------------------------------

def restorableCharacters():
    # Add code to this to check the table for cards that allow you to restore more insane characters.
    debugNotify("Restorable: {}".format(1),4)
    return 1
     
#-------------------------------------------
# Switches
#-------------------------------------------
def setAutomation(type, bool = False):
    Automations[type] = bool
    
def switchAutomation(type,command = 'Off', warn = ''):
    mute()
    debugNotify(">>> switchAutomation(){}".format(extraASDebug())) #Debug
    global Automations
    if (Automations[type] and command == 'Off') or (not Automations[type] and command == 'Announce'):
        notify ("--> {} turned {} automations OFF.".format(me,type))
        if command != 'Announce': 
            for player in getPlayers(): remoteCall(player,'setAutomation'[type, False])
    else:
        if warn != '' and not confirm(warn): return
        notify ("--> {} turned {} automations ON.".format(me,type))
        if command != 'Announce': 
            for player in getPlayers(): remoteCall(player,'setAutomation',[type, True])
    
def switchPlayAutomation(group,x=0,y=0):
    msg = "Play automations are still in beta, and may not work the way you intend.  Continue?"
    debugNotify(">>> switchPlayAutomation(){}".format(extraASDebug())) #Debug
    switchAutomation('Play/Resolve', warn = msg)
    
def switchTriggersAutomation(group,x=0,y=0):
    msg = "Automatic script triggers are still in beta, and many card effects will not trigger.  Continue?"
    debugNotify(">>> switchTriggersAutomation(){}".format(extraASDebug())) #Debug
    switchAutomation('Triggers', warn = msg)

def switchDamageAutomation(group, x=0, y=0):
    msg = "Automatic damage and scoring is still in beta.  It SHOULD work, but no guarantees.  Continue?"
    debugNotify(">>> switchDamageAutomation(){}".format(extraASDebug())) #Debug
    switchAutomation('Damage/Scoring', warn = msg)

def switchPaymentAutomation(group, x=0, y=0):
    msg = "Card payment calculation is in beta.  It works, but costs may not be properly reduced or raised by other cards.  Continue?"
    debugNotify(">>> switchPaymentAutomation(){}".format(extraASDebug())) #Debug
    switchAutomation('Payment', warn = msg)

def switchStartEndAutomation(group,x=0,y=0):
    msg = "Timing based automations is still in beta.  Many card effects will not trigger.  Continue?"
    debugNotify(">>> switchStartEndAutomation(){}".format(extraASDebug())) #Debug
    if Automations['Start/End-of-Turn/Phase'] and not confirm(":::WARNING::: Disabling these automations means that you'll have to do each phase's effects manually.\
                                                                                     \nThis means removing a focus from each card, increasing the dial and refreshing your hand.\
                                                                                     \nThis can add a significant amount of time to each turn's busywork.\
                                                                                     \nAre you sure you want to disable? (You can re-enable again by using the same menu option)"): return
    switchAutomation('Start/End-of-Turn/Phase', warn = msg)
    
def switchPlacement(group,x=0,y=0):
    msg = "Automatic card placement is still in beta.  Most placements will work correctly, but no guarantees.  Continue?"
    debugNotify(">>> switchPlacement(){}".format(extraASDebug())) #Debug
    switchAutomation('Placement', warn = msg)
    
def switchAll(group,x=0,y=0):
    msg = "Most of the automations are still in beta.  Card effects may not trigger, cost reductions may not work, icons totals may not be modified.  Proceed at your own risk.  This warning will go away when the system is out of beta."
    debugNotify(">>> switchAll(){}".format(extraASDebug())) #Debug
    switchAutomation('Play/Resolve', warn = msg)
    switchAutomation('Triggers')
    switchAutomation('Damage/Scoring')
    switchAutomation('Start/End-of-Turn/Phase')
    switchAutomation('Placement')
    switchAutomation('Payment')
    
