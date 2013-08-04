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
   (MOTDurl, MOTDcode) = webRead('https://raw.github.com/db0/Android-Netrunner-OCTGN/master/MOTD.txt')
   (DYKurl, DYKcode) = webRead('https://raw.github.com/db0/Android-Netrunner-OCTGN/master/DidYouKnow.txt')
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

def initGame(): # A function which prepares the game for online submition
   debugNotify(">>> initGame()") #Debug
   if getGlobalVariable('gameGUID') != 'None': return #If we've already grabbed a GUID, then just use that.
   (gameInit, initCode) = webRead('http://84.205.248.92/slaghund/init.slag')
   if initCode != 200:
      #whisper("Cannot grab GameGUID at the moment!") # Maybe no need to inform players yet.
      return
   debugNotify("{}".format(gameInit), 2) #Debug
   GUIDregex = re.search(r'([0-9a-f-]{36}).*?',gameInit)
   if GUIDregex: setGlobalVariable('gameGUID',GUIDregex.group(1))
   else: setGlobalVariable('gameGUID','None') #If for some reason the page does not return a propert GUID, we won't record this game.
   setGlobalVariable('gameEnded','False')
   debugNotify("<<< initGame()", 3) #Debug
   
def reportGame(result = 'AgendaVictory'): # This submits the game results online.
   delayed_whisper("Please wait. Submitting Game Stats...")     
   debugNotify(">>> reportGame()") #Debug
   GUID = getGlobalVariable('gameGUID')
   if GUID == 'None' and debugVerbosity < 0: return # If we don't have a GUID, we can't submit. But if we're debugging, we go through.
   gameEnded = getGlobalVariable('gameEnded')
   if gameEnded == 'True':
     if not confirm("Your game already seems to have finished once before. Do you want to change the results to '{}' for {}?".format(result,me.name)): return
   #LEAGUE = fetchLeagues()
   LEAGUE = '' #Disabled as I don't think I need this part of the code anymore.
   PLAYER = me.name # Seeting some variables for readability in the URL
   id = getSpecial('Identity',me)
   IDENTITY = id.Subtitle
   RESULT = result
   GNAME = currentGameName()
   if result == 'Flatlined' or result == 'Conceded' or result == 'DeckDefeat': WIN = 0
   else: WIN = 1
   SCORE = me.counters['Agenda Points'].value
   deckStats = eval(me.getGlobalVariable('Deck Stats'))
   debugNotify("Retrieved deckStats ", 2) #Debug
   debugNotify("deckStats = {}".format(deckStats), 2) #Debug
   INFLUENCE = deckStats[0]
   CARDSNR = deckStats[1]
   AGENDASNR = deckStats[2]
   TURNS = turn
   VERSION = gameVersion
   debugNotify("About to report player results online.", 2) #Debug
   if (turn < 1 or len(players) == 1) and debugVerbosity < 1:
      notify(":::ATTENTION:::Game stats submit aborted due to number of players ( less than 2 ) or turns played (less than 1)")
      return # You can never win before the first turn is finished and we don't want to submit stats when there's only one player.
   if debugVerbosity < 1: # We only submit stats if we're not in debug mode
      (reportTXT, reportCode) = webRead('http://84.205.248.92/slaghund/game.slag?g={}&u={}&id={}&r={}&s={}&i={}&t={}&cnr={}&anr={}&v={}&w={}&lid={}&gname={}'.format(GUID,PLAYER,IDENTITY,RESULT,SCORE,INFLUENCE,TURNS,CARDSNR,AGENDASNR,VERSION,WIN,LEAGUE,GNAME),10000)
   else: 
      if confirm('Report URL: http://84.205.248.92/slaghund/game.slag?g={}&u={}&id={}&r={}&s={}&i={}&t={}&cnr={}&anr={}&v={}&w={}&lid={}&gname={}\n\nSubmit?'.format(GUID,PLAYER,IDENTITY,RESULT,SCORE,INFLUENCE,TURNS,CARDSNR,AGENDASNR,VERSION,WIN,LEAGUE,GNAME)):
         (reportTXT, reportCode) = webRead('http://84.205.248.92/slaghund/game.slag?g={}&u={}&id={}&r={}&s={}&i={}&t={}&cnr={}&anr={}&v={}&w={}&lid={}&gname={}'.format(GUID,PLAYER,IDENTITY,RESULT,SCORE,INFLUENCE,TURNS,CARDSNR,AGENDASNR,VERSION,WIN,LEAGUE,GNAME),10000)
         notify('Report URL: http://84.205.248.92/slaghund/game.slag?g={}&u={}&id={}&r={}&s={}&i={}&t={}&cnr={}&anr={}&v={}&w={}&lid={}&gname={}\n\nSubmit?'.format(GUID,PLAYER,IDENTITY,RESULT,SCORE,INFLUENCE,TURNS,CARDSNR,AGENDASNR,VERSION,WIN,LEAGUE,GNAME))
   try:
      if reportTXT != "Updating result...Ok!" and debugVerbosity >=0: whisper("Failed to submit match results") 
   except: pass
   # The victorious player also reports for their enemy
   enemyPL = ofwhom('-ofOpponent')
   ENEMY = enemyPL.name
   enemyIdent = getSpecial('Identity',enemyPL)
   E_IDENTITY = enemyIdent.Subtitle
   debugNotify("Enemy Identity Name: {}".format(E_IDENTITY), 2) #Debug
   if result == 'FlatlineVictory': 
      E_RESULT = 'Flatlined'
      E_WIN = 0
   elif result == 'Flatlined': 
      E_RESULT = 'FlatlineVictory'
      E_WIN = 1
   elif result == 'Conceded': 
      E_RESULT = 'ConcedeVictory'
      E_WIN = 1  
   elif result == 'DeckDefeat': 
      E_RESULT = 'DeckVictory'
      E_WIN = 1  
   elif result == 'AgendaVictory': 
      E_RESULT = 'AgendaDefeat'
      E_WIN = 0
   else: 
      E_RESULT = 'Unknown'
      E_WIN = 0
   E_SCORE = enemyPL.counters['Agenda Points'].value
   debugNotify("About to retrieve E_deckStats", 2) #Debug
   E_deckStats = eval(enemyPL.getGlobalVariable('Deck Stats'))
   debugNotify("E_deckStats = {}".format(E_deckStats), 2) #Debug
   E_INFLUENCE = E_deckStats[0]
   E_CARDSNR = E_deckStats[1]
   E_AGENDASNR = E_deckStats[2]
   if ds == 'corp': E_TURNS = turn - 1 # If we're a corp, the opponent has played one less turn than we have.
   else: E_TURNS = turn # If we're the runner, the opponent has played one more turn than we have.
   E_VERSION = enemyPL.getGlobalVariable('gameVersion')
   debugNotify("About to report enemy results online.", 2) #Debug
   if debugVerbosity < 1: # We only submit stats if we're not debugging
      (EreportTXT, EreportCode) = webRead('http://84.205.248.92/slaghund/game.slag?g={}&u={}&id={}&r={}&s={}&i={}&t={}&cnr={}&anr={}&v={}&w={}&lid={}&gname={}'.format(GUID,ENEMY,E_IDENTITY,E_RESULT,E_SCORE,E_INFLUENCE,E_TURNS,E_CARDSNR,E_AGENDASNR,E_VERSION,E_WIN,LEAGUE,GNAME),10000)
   setGlobalVariable('gameEnded','True')
   notify("Thanks for playing. Please submit any bugs or feature requests on github.\n-- https://github.com/db0/Android-Netrunner-OCTGN/issues")
   debugNotify("<<< reportGame()", 3) #Debug

def fetchLeagues():
   debugNotify(">>> fetchLeagues()") #Debug
   #return '' ### Code still WiP! Remove this at 1.1.16
   (LeagueTXT, LeagueCode) = webRead('https://raw.github.com/db0/Android-Netrunner-OCTGN/master/Leagues.txt')
   if LeagueCode != 200 or not LeagueTXT:
      whisper(":::WARNING::: Cannot check League Details online.")
      return ''
   if LeagueTXT == "No Leagues Ongoing": return
   leaguesSplit = LeagueTXT.split('-----') # Five dashes separate on league from another
   opponent = ofwhom('onOpponent')
   for league in leaguesSplit:
      leagueMatches = league.split('\n')
      debugNotify("League Linebreak Splits: {}".format(leagueMatches), 4)
      for matchup in leagueMatches:
         if re.search(r'{}'.format(me.name),matchup, re.IGNORECASE) and re.search(r'{}'.format(opponent.name),matchup, re.IGNORECASE): #Check if the player's name exists in the league
            leagueDetails = league.split('=====') # Five equals separate the league name from its participants
            timeDetails = leagueDetails[1].strip() # We grab the time after which the matchup are not valid anymore.
            endTimes = timeDetails.split('.')
            currenttime = time.gmtime(time.time())
            debugNotify("Current Time:{}\n### End Times:{}".format(currenttime,endTimes), 2) #Debug
            if endTimes[0] >= currenttime[0] and endTimes[1] >= currenttime[1] and endTimes[2] >= currenttime[2] and endTimes[3] >= currenttime[3] and endTimes[4] >= currenttime[4]:          
               if confirm("Was this a match for the {} League?".format(leagueDetails[0])):
                  return leagueDetails[0] # If we matched a league, the return the first entry in the list, which is the league name.
   return '' # If we still haven't found a league name, it means the player is not listed as taking part in a league.
   
def fetchCardScripts(group = table, x=0, y=0): # Creates 2 dictionaries with all scripts for all cards stored, based on a web URL or the local version if that doesn't exist.
   debugNotify(">>> fetchCardScripts()") #Debug
   global CardsAA, CardsAS # Global dictionaries holding Card AutoActions and Card AutoScripts for all cards.
   whisper("+++ Fetching fresh scripts. Please Wait...")
   if (len(players) > 1 or debugVerbosity == 0) and me.name != 'dbzer0': # I put my debug account to always use local scripts.
      try: (ScriptsDownload, code) = webRead('https://raw.github.com/db0/Android-Netrunner-OCTGN/master/o8g/Scripts/CardScripts.py',5000)
      except: 
         debugNotify("Timeout Error when trying to download scripts", 0)
         code = ScriptsDownload = None
   else: # If we have only one player, we assume it's a debug game and load scripts from local to save time.
      debugNotify("Skipping Scripts Download for faster debug", 0)
      code = 0
      ScriptsDownload = None
   debugNotify("code:{}, text: {}".format(code, ScriptsDownload), 4) #Debug
   if code != 200 or not ScriptsDownload or (ScriptsDownload and not re.search(r'ANR CARD SCRIPTS', ScriptsDownload)) or debugVerbosity >= 0: 
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