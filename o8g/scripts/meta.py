    # Python Scripts for the Call of Cthulhu LCG definition for OCTGN
    # Copyright (C) 2013  Jason Cline
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

Automations = {'Play, Score and Rez'    : True, # If True, game will automatically trigger card effects when playing or double-clicking on cards. Requires specific preparation in the sets.
		'Start/End-of-Turn/Phase'      : True, # If True, game will automatically trigger effects happening at the start of the player's turn, from cards they control.
		'Damage Prevention'      : True, # If True, game will automatically use damage prevention counters from card they control.
		'Triggers'               : True, # If True, game will search the table for triggers based on player's actions, such as installing a card, or trashing one.
		'WinForms'               : True, # If True, game will use the custom Windows Forms for displaying multiple-choice menus and information pop-ups
		'Damage'                 : True,
		'Placement'		:True}

UniCode = True # If True, game will display credits, clicks, trash, memory as unicode characters

debugVerbosity = 0 # At -1, means no debugging messages display

startupMsg = False # Used to check if the player has checked for the latest version of the game.

gameGUID = None # A Unique Game ID that is fetched during game launch.
#totalInfluence = 0 # Used when reporting online
#gameEnded = False # A variable keeping track if the players have submitted the results of the current game already.
turn = 0 # used during game reporting to report how many turns the game lasted
Stored_Name = {}
Stored_Attachments = {}
Stored_Resource = {}
gatheredCardList = False
costModifiers = []

#---------------------------------------------------------------------------
# Generic functions
#---------------------------------------------------------------------------

def ofwhom(Autoscript, controller = me): 
   if debugVerbosity >= 1: notify(">>> ofwhom(){}".format(extraASDebug(Autoscript))) #Debug
   targetPL = None
   if re.search(r'o[fn]Opponent', Autoscript):
      if len(players) > 1:
         if controller == me: # If we're the current controller of the card who's scripts are being checked, then we look for our opponent
            for player in players:
               if player.getGlobalVariable('Side') == '': continue # This is a spectator 
               elif player != me and player.getGlobalVariable('Side') != Side:
                  targetPL = player # Opponent needs to be not us, and of a different type. 
                                    # In the future I'll also be checking for teams by using a global player variable for it and having players select their team on startup.
         else: targetPL = me # if we're not the controller of the card we're using, then we're the opponent of the player (i.e. we're trashing their card)
      else: 
         if debugVerbosity >= 1: whisper("There's no valid Opponents! Selecting myself.")
         targetPL = me
   else: 
      if len(players) > 1:
         if controller != me: targetPL = controller         
         else: targetPL = me
      else: targetPL = me
   if debugVerbosity >= 3: notify("<<< ofwhom() returns {}".format(targetPL))
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
   
def getKeywords(card): # A function which combines the existing card keywords, with markers which give it extra ones. - REMOVE POSSIBLY
   debugNotify(">>> getKeywords(){}".format(extraASDebug())) #Debug
  #confirm("getKeywords") # Debug
   keywordsList = []
   cKeywords = card.Keyword # First we try a normal grab, if the card properties cannot be read, then we flip face up.
   if cKeywords == '?': cKeywords = fetchProperty(card, 'Keywords')
   strippedKeywordsList = cKeywords.split('-')
   for cardKW in strippedKeywordsList:
      strippedKW = cardKW.strip() # Remove any leading/trailing spaces between traits. We need to use a new variable, because we can't modify the loop iterator.
      if strippedKW: keywordsList.append(strippedKW) # If there's anything left after the stip (i.e. it's not an empty string anymrore) add it to the list.   
   if card.markers:
      for key in card.markers:
         markerKeyword = re.search('Keyword:([\w ]+)',key[0])
         if markerKeyword:
            #confirm("marker found: {}\n key: {}".format(markerKeyword.groups(),key[0])) # Debug
            #if markerKeyword.group(1) == 'Barrier' or markerKeyword.group(1) == 'Sentry' or markerKeyword.group(1) == 'Code Gate': #These keywords are mutually exclusive. An Ice can't be more than 1 of these
               #if 'Barrier' in keywordsList: keywordsList.remove('Barrier') # It seems in ANR, they are not so mutually exclusive. See: Tinkering
               #if 'Sentry' in keywordsList: keywordsList.remove('Sentry') 
               #if 'Code Gate' in keywordsList: keywordsList.remove('Code Gate')
            #if re.search(r'Breaker',markerKeyword.group(1)):
               #if 'Barrier Breaker' in keywordsList: keywordsList.remove('Barrier Breaker')
               #if 'Sentry Breaker' in keywordsList: keywordsList.remove('Sentry Breaker')
               #if 'Code Gate Breaker' in keywordsList: keywordsList.remove('Code Gate Breaker')
            keywordsList.append(markerKeyword.group(1))
   keywords = ''
   for KW in keywordsList:
      keywords += '{}-'.format(KW)
   debugNotify("<<< getKeywords() by returning: {}.".format(keywords[:-1]), 3)
   return keywords[:-1] # We need to remove the trailing dash '-'
   
def pileName(group):
   debugNotify(">>> pileName()") #Debug
   debugNotify("pile name {}".format(group.name), 2) #Debug   
   debugNotify("pile player: {}".format(group.player), 2) #Debug
   name = group.name
   debugNotify("<<< pileName() by returning: {}".format(name), 3)
   return name

def storeSpecial(card): 
# Function stores into a shared variable some special cards that other players might look up.
   try:
      debugNotify(">>> storeSpecial(){}".format(extraASDebug())) #Debug
      specialCards = eval(me.getGlobalVariable('specialCards'))
      if card.name == 'HQ' or card.name == 'R&D' or card.name == 'Archives':
         specialCards[card.name] = card._id # The central servers we find via name
      else: specialCards[card.Type] = card._id
      me.setGlobalVariable('specialCards', str(specialCards))
   except: notify("!!!ERROR!!! In storeSpecial()")

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
		global Stored_Attachments, Stored_Name, Stored_Resource
		if (card.Name == '?' and Stored_Name.get(card._id,'?') == '?') or forced:
			if not card.isFaceUp and card.group == table and (card.owner == me or forced):
				debugNotify("Peeking Card at storeAttachment()",2)
				card.peek()
				loopChk(card)
		if (Stored_Name.get(card._id,'?') == '?' and card.Name != '?') or (Stored_Name.get(card._id,'?') != card.Name and card.Name != '?') or forced:
			debugNotify("{} not stored.  Storing...".format(card),4)
			Stored_Name[card._id] = card.Name
			# debugNotify(">>> Step 1",4)
			if resource: Stored_Resource[card._id] = card.properties["Resource Icon"]
			# debugNotify(">>> Step 2",4)
			Stored_Attachments[card._id] = attachee._id
			# debugNotify("Storing: {} - {} - {}".format(Stored_Name.get(card._id, '?'),Stored_Resource.get(card._id,'?'),Stored_Attachments.get(card._id,'?')),4)
		elif card.Name == '?':
			debugNotify("Could not store attachment because it is hidden from us")
			return 'ABORT'
	except: notify("!!!ERROR!!! In storeAttachment()")
			
def getAttachments(card):
	global Stored_Attachments
	att = [c for c in table if c._id in Stored_Attachments and Stored_Attachments.get(c._id,'?') == card._id]
	attachments = []
	for c in att:
		
		attachments.append(c._id)
	debugNotify(">>> Attachments: {}".format(attachments))
	return attachments

def getAttached(card):
	global Stored_Attachments
	debugNotify(">>> Checking for attachment host - {}".format(card._id),4)
	if (card._id in Stored_Attachments and not Stored_Attachments.get(card._id,'?') == '?'):
		debugNotify(">>> Returning {}".format(Stored_Attachments.get(card._id,'?')),4)
		return Card(Stored_Attachments.get(card._id,'?'))
	else:
		return 
	
def resetAll(): # Clears all the global variables in order to start a new game.
   global debugVerbosity, newturn, endofturn, turn, firstTurn
   debugNotify(">>> resetAll(){}".format(extraASDebug())) #Debug
   mute()
   me.counters['Success Story 1'].value = 0
   me.counters['Success Story 2'].value = 0
   me.counters['Success Story 3'].value = 0
   me.counters['Stories won'].value = 0
   me.handSize = 5
   newturn = False 
   endofturn = False
   firstTurn = True
   turn = 0
   selectedAbility = eval(getGlobalVariable('Stored Effects'))
   selectedAbility.clear()
   setGlobalVariable('Stored Effects',str(selectedAbility))
   me.setGlobalVariable('freePositions',str([]))
   me.setGlobalVariable('resourcesToPlay',3)
   if len(players) > 1: debugVerbosity = -1 # Reset means normal game.
   elif debugVerbosity != -1 and confirm("Reset Debug Verbosity?"): debugVerbosity = -1    
   debugNotify("<<< resetAll()") #Debug   

def cardStatus(card):
	debugNotify(">>> cardStatus() - {} - {} - {} - {}".format(card.type, card.name, card.orientation, card.isFaceUp),4)
	cS = "InPlay"
	if (card.type == "Token" and re.search(r'\bDomain\b',card.name)): cS = "Domain"
	if (card.orientation == Rot0 and not card.isFaceUp): cS = "Domain"
	if (card.orientation == Rot90 and not card.isFaceUp): cS = "Insane"
	if (card.orientation == Rot90 and card.isFaceUp): cS = "Exhausted"
	return cS
	
def addResource(domainCard,resourceCard):
	debugNotify(">>> remResource\nAmount: {}".format(len(resourceCard.properties['Resource Icon'])),3)
	amount = len(resourceCard.properties['Resource Icon'])
	addRemResource(domainCard,resourceCard,amount)
def remResource(domainCard,resourceCard):
	debugNotify(">>> remResource\nAmount: {}".format(len(resourceCard.properties['Resource Icon'])),3)
	amount = len(resourceCard.properties['Resource Icon'])
	amount = amount - (amount * 2)
	addRemResource(domainCard,resourceCard,amount)	
def addRemResource(domainCard,resourceCard, amount=1):
	if cardStatus(domainCard):
		debugNotify(">>> addRemResource()\nFaction: {}\nDomain: {}\nResource: {}\nAmount: {}".format(resourceCard.faction,domainCard.name,resourceCard.name,amount),3)
		if resourceCard.Faction=="Yog-Sothoth":domainCard.markers[resdict['Resource:Yog-Sothoth']] += amount
		elif resourceCard.Faction=="Cthulhu":domainCard.markers[resdict['Resource:Cthulhu']] += amount
		elif resourceCard.Faction=="Hastur":domainCard.markers[resdict['Resource:Hastur']] += amount
		elif resourceCard.Faction=="Shub-Niggurath":domainCard.markers[resdict['Resource:Shub-Niggurath']] += amount
		elif resourceCard.Faction=="The Agency":domainCard.markers[resdict['Resource:The Agency']] += amount
		elif resourceCard.Faction=="Miskatonic University":domainCard.markers[resdict['Resource:Miskatonic University']] += amount
		elif resourceCard.Faction=="The Syndicate":domainCard.markers[resdict['Resource:The Syndicate']] += amount
		elif resourceCard.Faction=="The Order of the Silver Twilight":domainCard.markers[resdict['Resource:The Order of the Silver Twilight']] += amount
		elif resourceCard.properties["Resource Icon"] =="Z":domainCard.markers[resdict['Resource:Zoog']] += amount
		else: domainCard.markers[resdict['Resource:Neutral']] += amount
	else:
		debugNotify("### Tried to add resources to a non-domain target.")
		return
def countResources(card,faction = 'All'):
	# debugNotify(">>> Count Resources",3)
	resources = 0
	keys = resdict.viewkeys()
	for key in keys:
		if re.search('Resource', key) and (re.search(faction, key) or faction == 'All'):
			# debugNotify("Key: {}".format(key),4)
			resources += card.markers[resdict[key]]
			# debugNotify("Resource Count: {}".format(resources),4)
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
			debugNotify("Does Exist",4)
			
			if targetCard.name == "Drain Token":
				debugNotify("Drain Token",4)
				targetCard.moveToTable(x,y)
				targetCard.sendToFront()
			else:
				if me.hasInvertedTable() == True: y += 8
				else: y -= 8
				targetCard.moveToTable(x,y)
				targetCard.sendToBack()
		else: del Stored_Attachments[attachment]
		
		
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
	for player in players:
		if not eval(player.getGlobalVariable('gameReady')): gR = False
	return gR
	
def gameStarted():
	if turnNumber() > 0: return True
	else: return False
	
def hasSubType(card,matchType):
	debugNotify("hasSubtype({}) - {}".format(matchType,card.Subtypes))
	if re.search(r'{}'.format(matchType),card.Subtypes):
		debugNotify(">> Has Subtype: {}".format(matchType))
		return True
	else: return False
def hasKeyword(card,matchType):
   debugNotify("hasKeyword({}) - {}".format(matchType,card.Keywords))
   if re.search(r'{}'.format(matchType),card.Keywords):
      debugNotify(">> Has Keyword: {}".format(matchType))
      return True
   else: return False
def parseIcons(STRING, dictReturn = False):
	if debugVerbosity >= 1: notify(">>> parseIcons() with STRING: {}".format(STRING)) #Debug
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
		if debugVerbosity >= 3: notify("<<< parseIcons() with return: {}".format(parsedIcons)) # Debug
	else:
		parsedIcons = {}
		parsedIcons[Terror] = Terror
		parsedIcons[Combat] = Combat
		parsedIcons[Arcane] = Arcane
		parsedIcons[Investigation] = Investigation
		if debugVerbosity >= 3: notify("<<< parseIcons() with dictReturn: {}".format(parsedIcons)) # Debug
	return parsedIcons
def chkDummy(Autoscript, card): # Checks if a card's effect is only supposed to be triggered for a (non) Dummy card
   if debugVerbosity >= 4: notify(">>> chkDummy()") #Debug
   if re.search(r'onlyforDummy',Autoscript) and card.highlight != DummyColor: return False
   if re.search(r'excludeDummy', Autoscript) and card.highlight == DummyColor: return False
   return True

def reduceCost(card, action = 'PLAY', fullCost = 0, dryRun = False):
# A Functiona that scours the table for cards which reduce the cost of other cards.
# if dryRun is set to True, it means we're just checking what the total reduction is going to be and are not actually removing or adding any counters.
   type = action.capitalize()
   if debugVerbosity >= 1: notify(">>> reduceCost(). Action is: {}. FullCost = {}. dryRyn = {}".format(type,fullCost,dryRun)) #Debug
   fullCost = abs(fullCost)
   reduction = 0
   costReducers = []
   ### First we check if the card has an innate reduction. 
   Autoscripts = card.AutoScript.split('||') 
   if debugVerbosity >= 2: notify("### About to check if there's any onPay triggers on the card")
   if len(Autoscripts): 
      for autoS in Autoscripts:
         if not re.search(r'onPay', autoS): 
            if debugVerbosity >= 2: notify("### No onPay trigger found in {}!".format(autoS))
            continue
         elif debugVerbosity >= 2: notify("### onPay trigger found in {}!".format(autoS))
         reductionSearch = re.search(r'Reduce([0-9]+)Cost({}|All)'.format(type), autoS)
         if debugVerbosity >= 2: #Debug
            if reductionSearch: notify("!!! self-reduce regex groups: {}".format(reductionSearch.groups()))
            else: notify("!!! No self-reduce regex Match!")
         count = num(reductionSearch.group(1))
         targetCards = findTarget(autoS,card = card)
         multiplier = per(autoS, card, 0, targetCards)
         reduction += (count * multiplier)
         maxRegex = re.search(r'-maxReduce([1-9])', autoS) # We check if the card will only reduce its cast by a specific maximum (e.g. Weequay Elite)
         if maxRegex and reduction > num(maxRegex.group(1)): reduction = num(maxRegex.group(1))
         fullCost -= reduction
         if reduction > 0 and not dryRun: notify("-- {}'s full cost is reduced by {}".format(card,reduction))
   if debugVerbosity >= 2: notify("### About to gather cards on the table")
   ### Now we check if any card on the table has an ability that reduces costs
   if not gatheredCardList: # A global variable that stores if we've scanned the tables for cards which reduce costs, so that we don't have to do it again.
      global costModifiers
      del costModifiers[:]
      RC_cardList = sortPriority([c for c in table if c.isFaceUp])
      reductionRegex = re.compile(r'(Reduce|Increase)([0-9#X]+)Cost({}|All)-affects([A-Z][A-Za-z ]+)(-not[A-Za-z_& ]+)?'.format(type)) # Doing this now, to reduce load.
      for c in RC_cardList: # Then check if there's other cards in the table that reduce its costs.
         Autoscripts = c.AutoScript.split('||')
         if len(Autoscripts) == 0: continue
         for autoS in Autoscripts:
            if debugVerbosity >= 2: notify("### Checking {} with AS: {}".format(c, autoS)) #Debug
            if not chkPlayer(autoS, c.controller, False): continue
            reductionSearch = reductionRegex.search(autoS) 
            if debugVerbosity >= 2: #Debug
               if reductionSearch: notify("!!! Regex is {}".format(reductionSearch.groups()))
               else: notify("!!! No reduceCost regex Match!") 
            #if re.search(r'ifInstalled',autoS) and (card.group != table or card.highlight == RevealedColor): continue
            if reductionSearch: # If the above search matches (i.e. we have a card with reduction for Rez and a condition we continue to check if our card matches the condition)
               if debugVerbosity >= 3: notify("### Possible Match found in {}".format(c)) # Debug         
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
      if len(costReducers): costModifiers.extend(costReducers)
   for cTuple in costModifiers: # Now we check what kind of cost modification each card provides. First we check for cost increasers and then for cost reducers
      if debugVerbosity >= 4: notify("### Checking next cTuple") #Debug
      c = cTuple[0]
      reductionSearch = cTuple[1]
      autoS = cTuple[2]
      if debugVerbosity >= 2: notify("### cTuple[0] (i.e. card) is: {}".format(c)) #Debug
      if debugVerbosity >= 4: notify("### cTuple[2] (i.e. autoS) is: {}".format(autoS)) #Debug
      if reductionSearch.group(4) == 'All' or checkCardRestrictions(gatherCardProperties(card), prepareRestrictions(autoS,seek = 'reduce')):
         if debugVerbosity >= 3: notify(" ### Search match! Reduction Value is {}".format(reductionSearch.group(2))) # Debug
         if re.search(r'onlyOnce',autoS):
            if dryRun: # For dry Runs we do not want to add the "Activated" token on the card. 
               if oncePerTurn(c, act = 'dryRun') == 'ABORT': continue 
            else:
               if oncePerTurn(c, act = 'automatic') == 'ABORT': continue # if the card's effect has already been used, check the next one
         if reductionSearch.group(2) == '#': 
            markersCount = c.markers[mdict['Credits']]
            markersRemoved = 0
            while markersCount > 0:
               if debugVerbosity >= 2: notify("### Reducing Cost with and Markers from {}".format(c)) # Debug
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
   if debugVerbosity >= 1: notify("<<< reduceCost(). final reduction = {}".format(reduction)) #Debug
   return reduction

def chkSuperiority(Autoscript, card):
   if debugVerbosity >= 1: notify(">>> chkSuperiority()") #Debug
   if debugVerbosity >= 3: notify("### AS = {}. Card = {}".format(Autoscript, card)) #Debug
   haveSuperiority = True # The default is True, which means that if we do not have a relevant autoscript, it's always True
   supRegex = re.search(r'-ifSuperiority([\w ]+)',Autoscript)
   if supRegex:
      supPlayers = compareObjectiveTraits(supRegex.group(1))
      if len(supPlayers) > 1 or supPlayers[0] != card.controller: haveSuperiority = False # If the controller of the card requiring superiority does not have the most objectives with that trait, we return False
   if debugVerbosity >= 3: notify("<<< chkSuperiority(). Return: {}".format(haveSuperiority)) #Debug
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
   if card.highlight == ReadyEffectColor or card.highlight == UnpaidAbilityColor: 
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
         if Card(cID).highlight == ReadyEffectColor or Card(cID).highlight == UnpaidAbilityColor: Card(cID).highlight = selectedAbility[cID][2] # We do not clear Forced Triggers so that they're not forgotten.
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
      if card.highlight == ReadyEffectColor and not selectedAbility.has_key(card._id): card.highlight = None # If the card is still in the selectedAbility, it means it has a forced effect we don't want to clear.
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
         if card.Type == 'Character': # For now we only place Units
            unitAmount = len([c for c in table if c.Type == 'Character' and c.controller == me and c.highlight != UnpaidColor and c.highlight != DummyColor and c.orientation != Rot180]) - 1 # we reduce by 1, because it will always count the unit we're currently putting in the game
            debugNotify("my unitAmount is: {}.".format(unitAmount)) #Debug
            freePositions = eval(me.getGlobalVariable('freePositions')) # We store the currently released position
            debugNotify(" my freePositions is: {}.".format(freePositions),2) #Debug
            if freePositions != []: # We use this variable to see if there were any discarded units and we use their positions first.
               positionC = freePositions.pop() # This returns the last position in the list of positions and deletes it from the list.
               if debugVerbosity >= 2: notify("### positionC is: {}.".format(positionC)) #Debug
               card.moveToTable(positionC[0],positionC[1])
               me.setGlobalVariable('freePositions',str(freePositions))
            else:
               loopsNR = unitAmount / 7
               loopback = 7 * loopsNR                  
               xoffset = (playerside * (100 + cheight(card,0))) - (playerside * cheight(card,0) * (unitAmount - loopback)) - 25
               # notify("xoffset: {} - cheight: {} - unitamount: {} - loopback: {}".format(xoffset,cheight(card,0),unitAmount,loopback))
               if debugVerbosity >= 2: notify("### xoffset is: {}.".format(xoffset)) #Debug
               yoffset = yaxisMove(card) + (cheight(card,3) * (loopsNR) * playerside) + (35 * playerside)                  
               card.moveToTable(xoffset,yoffset)
         elif card.Type == 'Support':
            hostType = re.search(r'Placement:([A-Za-z1-9:_ ]+)', card.AutoScript)
            if hostType:
               if debugVerbosity >= 2: notify("### hostType: {}.".format(hostType.group(1))) #Debug
               host = findTarget('Targeted-at{}'.format(hostType.group(1)))
               if host == []: 
                  whisper("ABORTING!")
                  return
               else:
                  if debugVerbosity >= 2: notify("### We have a host") #Debug
                  storeAttachment(card,host[0])
                  if debugVerbosity >= 2: notify("### About to move into position") #Debug
                  arrangeAttachments(host[0])
                  host[0].target = False
            else:
               supportAmount = len([c for c in table if c.Type == 'Support' and c.controller == me and c.orientation != Rot180 and not hasSubType(c,'Attachment.')])
               loopsNR = supportAmount / 7
               loopback = 7 * loopsNR                  
               xoffset = (playerside * (-550 + cheight(card,0))) + (playerside * cheight(card,0) * (supportAmount - loopback)) - 25
               # notify("xoffset: {} - cheight: {} - supportamount: {} - loopback: {}".format(xoffset,cheight(card,0),supportAmount,loopback))
               if debugVerbosity >= 2: notify("### xoffset is: {}.".format(xoffset)) #Debug
               yoffset = yaxisMove(card) + (cheight(card,3) * (loopsNR) * playerside) + (135 * playerside)                  
               card.moveToTable(xoffset,yoffset)

      else: debugNotify("No Placement Automations. Doing Nothing",2)
      if debugVerbosity >= 3: notify("<<< placeCard()") #Debug
   except: notify("!!! ERROR !!! in placeCard()")

def freeUnitPlacement(card): # A function which stores a unit's position when it leaves play, so that it can be re-used by a different unit
   if Automations['Placement'] and card.Type == 'Character' and card.orientation != Rot180:
      if card.owner == me and card.highlight != DummyColor and card.highlight != UnpaidColor:
         freePositions = eval(me.getGlobalVariable('freePositions')) # We store the currently released position
         freePositions.append(card.position)
         me.setGlobalVariable('freePositions',str(freePositions))
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
   if me.name == 'darksir23' : return #I can't be bollocksed
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
   mute()
   delayed_whisper("## Checking Debug Verbosity")
   if debugVerbosity >=0: 
      if debugVerbosity == 0: debugVerbosity = 1
      elif debugVerbosity == 1: debugVerbosity = 2
      elif debugVerbosity == 2: debugVerbosity = 3
      elif debugVerbosity == 3: debugVerbosity = 4
      else: debugVerbosity = 0
      delayed_whisper("Debug verbosity is now: {}".format(debugVerbosity))
      return
   delayed_whisper("## Checking my Name")
   if me.name == 'DarkSir232': 
      debugVerbosity = 0
   delayed_whisper("## Checking players array size")
   if not (len(players) == 1 or debugVerbosity >= 0): 
      whisper("This function is only for development purposes")
      return
   ######## Testing Corner ########
   ###### End Testing Corner ######

def debugChangeSides(group=table,x=0,y=0):
   global ds
   if debugVerbosity >=0:
      delayed_whisper("## Changing side")
      if ds == "corp": 
         notify("Runner now")
         ds = "runner"
         me.setGlobalVariable('ds','runner')
      else: 
         ds = "corp"
         me.setGlobalVariable('ds','corp')
         notify("Corp Now")
   else: whisper("Sorry, development purposes only")

   
def extraASDebug(Autoscript = None):
   if Autoscript and debugVerbosity >= 3: return ". Autoscript:{}".format(Autoscript)
   else: return ''

def ShowPos(group, x=0,y=0):
   if debugVerbosity >= 1: 
      notify('x={}, y={}'.format(x,y))
      
def ShowPosC(card, x=0,y=0):
   if debugVerbosity >= 1: 
      notify(">>> ShowPosC(){}".format(extraASDebug())) #Debug
      x,y = card.position
      notify('card x={}, y={}'.format(x,y))      
      
def controlChange(card,x,y):
   if card.controller != me: card.setController(me)
   else: card.setController(findOpponent())
   
def DebugCard(card, x=0, y=0):
   whisper("Position: {}".format(card.position))
   debugNotify("<<< getAttached {}".format(card.name))
   if getAttached(card): tmp = getAttached(card).name
   else: tmp = "None"
   whisper("Attached to: {}".format(tmp))
   debugNotify("<<< getAttachments {}".format(card.name))
   whisper("Attachments: {}".format(getAttachments(card)))
def clrResourceMarkers(card):
   for cMarkerKey in card.markers: 
      if debugVerbosity >= 3: notify("### Checking marker {}.".format(cMarkerKey[0]))
      for resdictKey in resdict:
         if resdict[resdictKey] == cMarkerKey or cMarkerKey[0] == 'Ignores Affiliation Match': 
            card.markers[cMarkerKey] = 0
            break
def cardSteadfast(card):
   steadfast = card.Name.count(card.properties['Resource Icon'])
   return steadfast
#-------------------------------------------
#  Event Handlers
#-------------------------------------------

def triggerMoveCard(player, card, fromGroup, toGroup, oldIndex, index, oldX, oldY, x, y, isScriptMove):
	if card.controller == me and not isScriptMove:
		arrangeAttachments(card)
		
	