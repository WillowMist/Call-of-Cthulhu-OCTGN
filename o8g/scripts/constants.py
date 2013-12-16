###==================================================File Contents==================================================###
# This file contains global variables in CoC. They should not be modified by the scripts at all.
###=================================================================================================================###

import re
#---------------------------------------------------------------------------
# These are constant global variables in CoC: They should not be modified by the scripts at all.
#---------------------------------------------------------------------------
phases = [
    "Opponent's Turn",
    "=== Refresh Phase: {} ===".format(me),
    "=== Draw Phase: {} ===".format(me),
    "=== Resource Phase: {} ===".format(me),
    "=== Operations Phase: {} ===".format(me),
    "=== Story Phase: {} ===".format(me)]
    
storyPhases = [
    "+++ Story: Active Player Commits +++",
    "+++ Story: Opponent Commits +++",
    "+++ Story: Active Player Selects Story To Resolve +++",
    "+++ Story: Resolve Icon Struggles +++",
    "+++ Story: Determine Success +++",
    "+++ Story: Finish Story +++"]

    
mdict = dict( # A dictionary which holds all the hard coded markers (in the markers file)
	     Wound = ("Wound", "4a247d69-b2cc-4de9-b4d1-c447bea01f61"),
	     Success = ("Success", "4a247d69-b2cc-4de9-b4d1-c447bea01f62"),
	     Drain = ("Drain", "4a247d69-b2cc-4de9-b4d1-c447bea01f63"),
	     Activation = ("Activation", "ea7418bc-6847-4e8a-9cc3-0230dc27d19b"),
         WoundPrevention = ("Wound Prevention","2396ca41-2ddd-4d7b-92de-7a182968209b")
         )
	     
resdict = {
		'Resource:Cthulhu':						("Cthulhu Resource", "a5173cd9-bafe-4be2-ae6f-11464f7260cf"),
		'Resource:Hastur':						("Hastur Resource", "3911052d-c25b-471d-92af-8aae4a18cce1"),
		'Resource:Shub-Niggurath':				("Shub-Niggurath Resource", "c9e080cd-fa2e-4397-a054-031945af4d8e"),
		'Resource:Yog-Sothoth':					("Yog-Sothoth Resource", "807d0966-15d7-4e45-88b3-87c77fc25288"),
		'Resource:The Agency':					("Agency Resource", "590456bb-17bc-4831-a08c-380def83486f"),
		'Resource:Miskatonic University':			("Miskatonic Resource", "93ec59f4-0a91-43bc-92da-210a16f20274"),
		'Resource:The Syndicate':					("Syndicate Resource", "d5ff5bee-09cc-44bb-b78c-c1c19b586028"),
		'Resource:The Order of the Silver Twilight':	("Silver Twilight Resource", "f5cfe322-21a4-4427-91ff-cd5b880c5848"),
		'Resource:Neutral':						("Neutral Resource", "e6d100e4-f79b-4b91-9853-16974ea47fb0"),
		'Resource:Zoog':						("Zoog Resource", "94dc59b3-409e-419d-be97-cb4877cdd507")}

regexHooks = dict( # A dictionary which holds the regex that then trigger each core command. 
                   # This is so that I can modify these "hooks" only in one place as I add core commands and modulators.
                   # We use "[:\$\|]" before all hooks, because we want to make sure the script is a core command, and nor part of a modulator (e.g -traceEffects)
                  GainX =              re.compile(r'(?<![<,+-])(Gain|Lose|SetTo)([0-9]+)'), 
                  CreateDummy =        re.compile(r'(?<![<,+-])CreateDummy'),
                  ReshuffleX =         re.compile(r'(?<![<,+-])Reshuffle([A-Za-z& ]+)'),
                  RollX =              re.compile(r'(?<![<,+-])Roll([0-9]+)'),
                  RequestInt =         re.compile(r'(?<![<,+-])RequestInt'),
                  DrainX =              re.compile(r'(?<![<,+-])Drain[0-9]+'),
                  DiscardX =           re.compile(r'(?<![<,+-])Discard[0-9]+'),
                  TokensX =            re.compile(r'(?<![<,+-])(Put|Remove|Refill|Use|Deal|Transfer)([0-9]+)'),
                  TransferX =          re.compile(r'(?<![<,+-])Transfer([0-9]+)'),
                  DrawX =              re.compile(r'(?<![<,+-])Draw([0-9]+)'),
                  ShuffleX =           re.compile(r'(?<![<,+-])Shuffle([A-Za-z& ]+)'),
                  RunX =               re.compile(r'(?<![<,+-])Run([A-Za-z& ]+)'),
                  TraceX =             re.compile(r'(?<![<,+-])Trace([0-9]+)'),
                  InflictX =           re.compile(r'(?<![<,+-])Inflict([0-9]+)'),
                  RetrieveX =          re.compile(r'(?<![<,+-])Retrieve([0-9]+)'),
                  ModifyStatus =       re.compile(r'(?<![<,+-])(Destroy|BringToPlay|SendToBottom|Commit|Uncommit|Sacrifice|Takeover|Score|Insane|Restore)(Target|Host|Multi|Myself)'),
                  ModifyProperty =      re.compile(r'(?<![<,+-])(Add|Remove|Replace)|([A-Za-z0-9 @#$%]+)|([A-Za-z ]+)-until([A-Za-z0-9]+)'),
                  SimplyAnnounce =     re.compile(r'(?<![<,+-])SimplyAnnounce'),
                  ChooseKeyword =      re.compile(r'(?<![<,+-])ChooseKeyword'),
                  CustomScript =       re.compile(r'(?<![<,+-])CustomScript'),
                  GameX =              re.compile(r'(?<![<,+-])(Lose|Win)Game'),
                  UseCustomAbility =   re.compile(r'(?<![<,+-])UseCustomAbility'))
				  
automatedMarkers = [] #Used in the Inspect() command to let the player know if the card has automations based on the markers it puts out.

ScoredColor = "#00ff44"
SelectColor = "#009900"
EmergencyColor = "#fff600"
DummyColor = "#9370db" # Marks cards which are supposed to be out of play, so that players can tell them apart.
RevealedColor = "#ffffff"
PriorityColor = "#ffd700"
InactiveColor = "#888888" # Cards which are in play but not active yer (e.g. see the shell traders)
StealthColor = "#000000" # Cards which are in play but not active yer (e.g. see the shell traders)
UnpaidColor = "#ffd700"
UnpaidAbilityColor = "#40e0d0"
ReadyEffectColor = "#eeeeee"
OverpaidEffectColor = "#efefef"
EngagedColor = "#0000aa"

Xaxis = 'x'
Yaxis = 'y'

storyDecks = {
	'Core Story Deck':[
		'45f006f4-02ed-4b8d-b095-eb5efe58d156',
		'45f006f4-02ed-4b8d-b095-eb5efe58d157',
		'45f006f4-02ed-4b8d-b095-eb5efe58d158',
		'45f006f4-02ed-4b8d-b095-eb5efe58d159',
		'45f006f4-02ed-4b8d-b095-eb5efe58d160',
		'45f006f4-02ed-4b8d-b095-eb5efe58d161',
		'45f006f4-02ed-4b8d-b095-eb5efe58d162',
		'45f006f4-02ed-4b8d-b095-eb5efe58d163',
		'45f006f4-02ed-4b8d-b095-eb5efe58d164',
		'45f006f4-02ed-4b8d-b095-eb5efe58d165'],
	'Ancient Relics Story Deck':[
		'f26280d4-6260-4475-9f94-e496394af001',
		'f26280d4-6260-4475-9f94-e496394af002',
		'f26280d4-6260-4475-9f94-e496394af003',
		'f26280d4-6260-4475-9f94-e496394af004',
		'f26280d4-6260-4475-9f94-e496394af005',
		'f26280d4-6260-4475-9f94-e496394af006',
		'f26280d4-6260-4475-9f94-e496394af007',
		'f26280d4-6260-4475-9f94-e496394af008',
		'f26280d4-6260-4475-9f94-e496394af009',
		'f26280d4-6260-4475-9f94-e496394af010',
		'f26280d4-6260-4475-9f94-e496394af011',
		'f26280d4-6260-4475-9f94-e496394af012'],
	'Secrets of Arkham Story Deck':[
		'ff1087a7-9c94-463e-8359-8e0483f99e51',
		'ff1087a7-9c94-463e-8359-8e0483f99e52',
		'ff1087a7-9c94-463e-8359-8e0483f99e53',
		'ff1087a7-9c94-463e-8359-8e0483f99e54',
		'ff1087a7-9c94-463e-8359-8e0483f99e55',
		'ff1087a7-9c94-463e-8359-8e0483f99e56',
		'ff1087a7-9c94-463e-8359-8e0483f99e57',
		'ff1087a7-9c94-463e-8359-8e0483f99e58',
		'ff1087a7-9c94-463e-8359-8e0483f99e59',
		'ff1087a7-9c94-463e-8359-8e0483f99e60']
	}

storyPositions = {	'Story 1':[-131,-43],
				'Story 2':[-31,-43],
				'Story 3': [68,-43],
				'Conspiracy 1':[-231,-43],
				'Conspiracy 2':[168,-43]}
				
domainPositions = {	'Domain 1':["f22ee55c-8f47-4174-a7a4-985731a74d30",-528,20],
				'Domain 2':["a8cec1b8-1121-4612-80c4-c66a437cc2e0",-528,94],
				'Domain 3':["d8a151e4-28c8-4653-b826-ebda237b776b",-528,168],
				'SpareDom 1':['None',-528,242],
				'SpareDom 2':['None',-528,316]}
				
