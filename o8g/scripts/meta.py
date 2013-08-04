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
               'Start/End-of-Turn'      : True, # If True, game will automatically trigger effects happening at the start of the player's turn, from cards they control.
               'Damage Prevention'      : True, # If True, game will automatically use damage prevention counters from card they control.
               'Triggers'               : True, # If True, game will search the table for triggers based on player's actions, such as installing a card, or trashing one.
               'WinForms'               : True, # If True, game will use the custom Windows Forms for displaying multiple-choice menus and information pop-ups
               'Damage'                 : True}

UniCode = True # If True, game will display credits, clicks, trash, memory as unicode characters

debugVerbosity = -1 # At -1, means no debugging messages display

startupMsg = False # Used to check if the player has checked for the latest version of the game.

gameGUID = None # A Unique Game ID that is fetched during game launch.
#totalInfluence = 0 # Used when reporting online
#gameEnded = False # A variable keeping track if the players have submitted the results of the current game already.
turn = 0 # used during game reporting to report how many turns the game lasted

CardsAA = {} # Dictionary holding all the AutoAction scripts for all cards
CardsAS = {} # Dictionary holding all the AutoScript scripts for all cards

#---------------------------------------------------------------------------
# Generic Netrunner functions
#---------------------------------------------------------------------------
def resetAll(): # Clears all the global variables in order to start a new game.
   global Stored_Name, Stored_Type, Stored_Cost, Stored_Skill, Stored_Subtypes, Stored_Icons, Stored_Keyword, Stored_AutoActions, Stored_AutoScripts
   global debugVerbosity, newturn, endofturn, turn
   debugNotify(">>> resetAll(){}".format(extraASDebug())) #Debug
   mute()
   me.counters['Success Story 1'].value = 0
   me.counters['Success Story 2'].value = 0
   me.counters['Success Story 3'].value = 0
   me.counters['Stories won'].value = 0
   Stored_Name.clear()
   Stored_Type.clear()
   Stored_Cost.clear()
   Stored_Keyword.clear()
   Stored_Skill.clear()
   Stored_Subtypes.clear()
   Stored_Icons.clear()
   Stored_AutoActions.clear()
   Stored_AutoScripts.clear()
   installedCount.clear()
   newturn = False 
   endofturn = False
   turn = 0
   ShowDicts()
   if len(players) > 1: debugVerbosity = -1 # Reset means normal game.
   elif debugVerbosity != -1 and confirm("Reset Debug Verbosity?"): debugVerbosity = -1    
   debugNotify("<<< resetAll()") #Debug   


#------------------------------------------------------------------------------
#  Online Functions
#------------------------------------------------------------------------------

def versionCheck():
   debugNotify(">>> versionCheck()") #Debug
   global startupMsg
   me.setGlobalVariable('gameVersion',gameVersion)
   if not startupMsg: MOTD() # If we didn't give out any other message , we give out the MOTD instead.
   startupMsg = True
   debugNotify("<<< versionCheck()", 3) #Debug
      
      
def MOTD():
   debugNotify(">>> MOTD()") #Debug
   if me.name == 'DarkSir23' : return #I can't be bollocksed
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

def fetchCardScripts(group = table, x=0, y=0): # Creates 2 dictionaries with all scripts for all cards stored, based on a web URL or the local version if that doesn't exist.
   debugNotify(">>> fetchCardScripts()") #Debug
   global CardsAA, CardsAS # Global dictionaries holding Card AutoActions and Card AutoScripts for all cards.
   whisper("+++ Fetching fresh scripts. Please Wait...")
   if (len(players) > 1 or debugVerbosity == 0) and me.name != 'dbzer0': # I put my debug account to always use local scripts.
      try: (ScriptsDownload, code) = webRead('https://raw.github.com/DarkSir23/Call-of-Cthulhu-OCTGN/master/o8g/Scripts/CardScripts.py',5000)
      except: 
         debugNotify("Timeout Error when trying to download scripts", 0)
         code = ScriptsDownload = None
   else: # If we have only one player, we assume it's a debug game and load scripts from local to save time.
      debugNotify("Skipping Scripts Download for faster debug", 0)
      code = 0
      ScriptsDownload = None
   debugNotify("code:{}, text: {}".format(code, ScriptsDownload), 4) #Debug
   if code != 200 or not ScriptsDownload or (ScriptsDownload and not re.search(r'COC CARD SCRIPTS', ScriptsDownload)) or debugVerbosity >= 0: 
      whisper(":::WARNING::: Cannot download card scripts at the moment. Will use localy stored ones.")
      Split_Main = ScriptsLocal.split('=====') # Split_Main is separating the file description from the rest of the code
   else: 
      #WHAT THE FUUUUUCK? Why does it gives me a "value cannot be null" when it doesn't even come into this path with a broken connection?!
      #WHY DOES IT WORK IF I COMMENT THE NEXT LINE. THIS MAKES NO SENSE AAAARGH!
      #ScriptsLocal = ScriptsDownload #If we found the scripts online, then we use those for our scripts
      Split_Main = ScriptsDownload.split('=====')
   if debugVerbosity >= 5:  #Debug
      notify(Split_Main[1])
      notify('=====')
   Split_Cards = Split_Main[1].split('.....') # Split Cards is making a list of a different cards
   if debugVerbosity >= 5: #Debug
      notify(Split_Cards[0]) 
      notify('.....')
   for Full_Card_String in Split_Cards:
      if re.search(r'ENDSCRIPTS',Full_Card_String): break # If we have this string in the Card Details, it means we have no more scripts to load.
      Split_Details = Full_Card_String.split('-----') # Split Details is splitting the card name from its scripts
      if debugVerbosity >= 5:  #Debug
         notify(Split_Details[0])
         notify('-----')
      # A split from the Full_Card_String always should result in a list with 2 entries.
      debugNotify(Split_Details[0].strip(), 2) # If it's the card name, notify us of it.
      Split_Scripts = Split_Details[2].split('+++++') # List item [1] always holds the two scripts. AutoScripts and AutoActions.
      CardsAS[Split_Details[1].strip()] = Split_Scripts[0].strip()
      CardsAA[Split_Details[1].strip()] = Split_Scripts[1].strip()
   if turn > 0: whisper("+++ All card scripts refreshed!")
   if debugVerbosity >= 4: # Debug
      notify("CardsAS Dict:\n{}".format(str(CardsAS)))
      notify("CardsAA Dict:\n{}".format(str(CardsAA))) 
   debugNotify("<<< fetchCardScripts()", 3) #Debug

def concede(group=table,x=0,y=0):
   mute()
   if confirm("Are you sure you want to concede this game?"): 
      reportGame('Conceded')
      notify("{} has conceded the game".format(me))
   else: 
      notify("{} was about to concede the game, but thought better of it...".format(me))
#------------------------------------------------------------------------------
# Debugging
#------------------------------------------------------------------------------
   
def TrialError(group, x=0, y=0): # Debugging
   global ds, debugVerbosity
   mute()
   #test()
   delayed_whisper("## Checking Debug Verbosity")
   if debugVerbosity >=0: 
      if debugVerbosity == 0: 
         debugVerbosity = 1
         ImAProAtThis() # At debug level 1, we also disable all warnings
      elif debugVerbosity == 1: debugVerbosity = 2
      elif debugVerbosity == 2: debugVerbosity = 3
      elif debugVerbosity == 3: debugVerbosity = 4
      else: debugVerbosity = 0
      whisper("Debug verbosity is now: {}".format(debugVerbosity))
      return
   delayed_whisper("## Checking my Name")
   if me.name == 'db0' or me.name == 'dbzer0': 
      debugVerbosity = 0
      fetchCardScripts()
   delayed_whisper("## Checking players array size")
   if not (len(players) == 1 or debugVerbosity >= 0): 
      whisper("This function is only for development purposes")
      return
   ######## Testing Corner ########
   ###### End Testing Corner ######
   delayed_whisper("## Defining Test Cards")
   testcards = [
                "bc0f047c-01b1-427f-a439-d451eda03055", 
                "bc0f047c-01b1-427f-a439-d451eda03041", 
                "bc0f047c-01b1-427f-a439-d451eda03041", 
                "bc0f047c-01b1-427f-a439-d451eda03041", 
                "bc0f047c-01b1-427f-a439-d451eda01005", 
                "bc0f047c-01b1-427f-a439-d451eda02086", 
                # "bc0f047c-01b1-427f-a439-d451eda02107", 
                # "bc0f047c-01b1-427f-a439-d451eda02108", 
                # "bc0f047c-01b1-427f-a439-d451eda02109", 
                # "bc0f047c-01b1-427f-a439-d451eda02110", 
                # "bc0f047c-01b1-427f-a439-d451eda02111", 
                # "bc0f047c-01b1-427f-a439-d451eda02112", 
                # "bc0f047c-01b1-427f-a439-d451eda02113", 
                # "bc0f047c-01b1-427f-a439-d451eda02114", 
                # "bc0f047c-01b1-427f-a439-d451eda02115", 
                # "bc0f047c-01b1-427f-a439-d451eda02116", 
                # "bc0f047c-01b1-427f-a439-d451eda02117", 
                # "bc0f047c-01b1-427f-a439-d451eda02118", 
                # "bc0f047c-01b1-427f-a439-d451eda02119", 
                # "bc0f047c-01b1-427f-a439-d451eda02120"
                ] 
   if not ds: 
      if confirm("corp?"): ds = "corp"
      else: ds = "runner"
   me.setGlobalVariable('ds', ds) 
   me.counters['Credits'].value = 50
   me.counters['Hand Size'].value = 5
   me.counters['Tags'].value = 1
   me.counters['Agenda Points'].value = 0
   me.counters['Bad Publicity'].value = 10
   me.Clicks = 15
   notify("Variables Reset") #Debug   
   if not playerside:  # If we've already run this command once, don't recreate the cards.
      notify("Playerside not chosen yet. Doing now") #Debug   
      chooseSide()
      notify("About to create starting cards.") #Debug   
      createStartingCards()
   notify("<<< TrialError()") #Debug
   if confirm("Spawn Test Cards?"):
      for idx in range(len(testcards)):
         test = table.create(testcards[idx], (70 * idx) - 150, 0, 1, True)
         storeProperties(test)
         if test.Type == 'ICE' or test.Type == 'Agenda' or test.Type == 'Asset': test.isFaceUp = False

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


def ShowDicts():
   if debugVerbosity < 0: return
   notify("Stored_Names:\n {}".format(str(Stored_Name)))
   notify("Stored_Types:\n {}".format(str(Stored_Type)))
   notify("Stored_Costs:\n {}".format(str(Stored_Cost)))
   notify("Stored_Keywords: {}".format(str(Stored_Keywords)))
   debugNotify("Stored_AA: {}".format(str(Stored_AutoActions)), 4)
   debugNotify("Stored_AS: {}".format(str(Stored_AutoScripts)), 4)
   notify("installedCounts: {}".format(str(installedCount)))

def DebugCard(card, x=0, y=0):
   whisper("Stored Card Properties\
          \n----------------------\
          \nStored Name: {}\
          \nPrinted Name: {}\
          \nStored Type: {}\
          \nPrinted Type: {}\
          \nStored Keywords: {}\
          \nPrinted Keywords: {}\
          \nCost: {}\
          \nCard ID: {}\
          \n----------------------\
          ".format(Stored_Name.get(card._id,'NULL'), card.Name, Stored_Type.get(card._id,'NULL'), card.Type, Stored_Keywords.get(card._id,'NULL'), card.Keywords, Stored_Cost.get(card._id,'NULL'),card._id))
   if debugVerbosity >= 4: 
      #notify("Stored_AS: {}".format(str(Stored_AutoScripts)))
      notify("Downloaded AA: {}".format(str(CardsAA)))
      notify("Card's AA: {}".format(CardsAA.get(card.model,'???')))
   storeProperties(card, True)
   if Stored_Type.get(card._id,'?') != 'ICE': card.orientation = Rot0
   
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