### Marker Constants ###
Wound = ("Wound", "4a247d69-b2cc-4de9-b4d1-c447bea01f61")
Success = ("Success", "4a247d69-b2cc-4de9-b4d1-c447bea01f62")
Resource = ("Resource", "880d8ceb-4be1-4c18-8676-0bd3bd333aa4")

phases = [
    'It is currently in the Pre-game Setup Phase',
    "It is now {}'s Refresh Phase",
    "It is now {}'s Draw Phase",
    "It is now {}'s Resource Phase",
    "It is now {}'s Operations Phase",
    "It is now {}'s Story Phase",
    "{} finished his/her turn."]

phaseIdx = 0

def nextPhase(group, x = 0, y = 0):
    global phaseIdx
    phaseIdx += 1
    showCurrentPhase(group)

def showCurrentPhase(group, x = 0, y = 0):
    notify(phases[phaseIdx].format(me))

def goToRefreshPhase(group, x = 0, y = 0):
    global phaseIdx
    phaseIdx = 1
    showCurrentPhase(group)

#---------------------------------------------------------------------------
# Table group actions
#---------------------------------------------------------------------------

def flipCoin(group, x = 0, y = 0):
    mute()
    n = rnd(1, 2)
    if n == 1:
        notify("{} flips heads.".format(me))
    else:
        notify("{} flips tails.".format(me))

def createDomain(group, x = 0, y = 0):
	if me.hasInvertedTable() == True:
		table.create("33dd6531-5aa0-45f7-a752-56e1029c5de1", -350, 50, 1)
	else:
		table.create("33dd6531-5aa0-45f7-a752-56e1029c5de1", -400, 170, 1)
		
def createDomains(group, x = 0, y = 0):
    if me.hasInvertedTable() == True: 
		table.create("a8cec1b8-1121-4612-80c4-c66a437cc2e0", -50, 50, 1)
		table.create("f22ee55c-8f47-4174-a7a4-985731a74d30", -150, 50, 1)
		table.create("d8a151e4-28c8-4653-b826-ebda237b776b", -250, 50, 1)
    else: 
		table.create("0054c047-1887-4a5d-b11b-b70f3cff3a0a", -300, 170, 1)
		table.create("593da3cb-290b-426e-9eec-1b3fd3465a2d", -200, 170, 1)
		table.create("46cfc241-12ea-4d15-91f5-0facf26a9d82", -100, 170, 1)


#---------------------------------------------------------------------------
# Table card actions
#---------------------------------------------------------------------------

def exhaust(card, x = 0, y = 0):
    mute()
    if card.Type == 'Token' or card.markers[Resource] == 1: return
    card.orientation ^= Rot90
    if card.orientation & Rot90 == Rot90:
        notify('{} exhausts {}'.format(me, card))
    else:
        notify('{} readies {}'.format(me, card))

def commit(card, x = 0, y = 0):
    mute()
    if card.Type == 'Token' or card.markers[Resource] == 1: return
    card.orientation ^= Rot90
    if card.orientation & Rot90 == Rot90:
        notify('{} commits {} to a story'.format(me, card))
    else:
        notify('{} readies {}'.format(me, card))

def drain(card, x = 0, y = 0):
  mute()
  # if card.highlight == "#008000":
  if card.name == "Drain Token":
    card.moveTo(me.piles['Discard Pile'])
    notify('{} refreshes Domain'.format(me))
  else:
    if "Domain" in card.name:
        xp, yp = card.position
        DrainToken = table.create("d42706b4-2721-439e-a41f-0611d6beb449", xp , yp , 1)
        notify('{} drains {}'.format(me, card)) 

def turnInsane(card, x = 0, y = 0):
    mute()
    if card.Type == 'Token' or card.markers[Resource] == 1: return
    if card.isFaceUp:
        notify("{} turns {} insane.".format(me, card))
        card.isFaceUp = False
    else:
        card.isFaceUp = True
        card.orientation = Rot90
        notify("{} restores {} to sanity.".format(me, card))

def restore(card, x = 0, y = 0): 
    mute()
    if card.Type != 'Token' and card.Type != 'Story' and card.markers[Resource] == 0: 
        card.orientation = Rot0
    if card.name == "Drain Token": card.moveTo(me.piles['Discard Pile'])
    card.highlight = None
    
def restoreAll(group, x = 0, y = 0): 
   mute()
   if not confirm("Are you sure you want to refresh all your cards?"): return
   cards = (card for card in table
                 if card.controller == me)
   for card in cards: restore(card)
   notify("{} Refreshes all their cards.".format(me))    

def addWound(card, x = 0, y = 0):
    mute()
    notify("{} wounds {}.".format(me, card))
    card.markers[Wound] += 1

def subWound(card, x = 0, y = 0):
    mute()
    notify("{} removes a Wound token from {}.".format(me, card))
    card.markers[Wound] -= 1

def addSuccess(card, x = 0, y = 0):
    mute()
    notify("{} adds a Success token to {}.".format(me, card))
    card.markers[Success] += 1

def subSuccess(card, x = 0, y = 0):
    mute()
    notify("{} removes a Success token from {}.".format(me, card))
    card.markers[Success] -= 1


#------------------------------------------------------------------------------
# Hand Actions
#------------------------------------------------------------------------------

def randomDiscard(group):
 mute()
 card = group.random()
 if card == None: return
 card.moveTo(me.piles['Discard pile'])
 notify("{} randomly discards {}.".format(me, card))
 
def mulligan(group, x = 0, y = 0):
    mute()
    for card in group:
        card.moveToBottom(me.deck)
        me.deck.shuffle()
    for card in me.deck.top(8):
        card.moveTo(me.hand)
    notify("{} mulligans.".format(me))

def playresource(card, x = 0, y = 0):
    mute()
    src = card.group
    if me.hasInvertedTable() == True: card.moveToTable(0, -90)
    else: card.moveToTable(0, 90)
    card.orientation ^= Rot180
    card.sendToBack()	
    card.markers[Resource] = 1
    notify("{} brings in a {} resource from his hand.".format(me, card.Faction))

def play(card, x = 0, y = 0):
    mute()
    src = card.group
    card.moveToTable(0, 0)
    notify("{} plays {} from his {}.".format(me, card, src.name))

#------------------------------------------------------------------------------
# Pile Actions
#------------------------------------------------------------------------------

def draw(group, x = 0, y = 0):
    if len(group) == 0: return
    mute()
    group[0].moveTo(me.hand)
    notify("{} draws a card.".format(me))

def shuffle(group):
  group.shuffle()

def drawMany(group, count = None):
    if len(group) == 0: return
    mute()
    if count == None: count = askInteger("Draw how many cards?", 8)
    for c in group.top(count): c.moveTo(me.hand)
    notify("{} draws {} cards.".format(me, count))
