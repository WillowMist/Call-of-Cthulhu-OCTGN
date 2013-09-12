import re

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




