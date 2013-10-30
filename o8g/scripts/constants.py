###==================================================File Contents==================================================###
# This file contains global variables in ANR. They should not be modified by the scripts at all.
###=================================================================================================================###

import re
#---------------------------------------------------------------------------
# These are constant global variables in ANR: They should not be modified by the scripts at all.
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
    "+++ Story: Resolve Icon Struggles +++",
    "+++ Story: Determine Success +++",
    "+++ Story: Reward Unopposed +++",
    "+++ Story: Resolve Completed Stories +++"]

    
mdict = dict( # A dictionary which holds all the hard coded markers (in the markers file)
	     Wound = ("Wound", "4a247d69-b2cc-4de9-b4d1-c447bea01f61"),
	     Success = ("Success", "4a247d69-b2cc-4de9-b4d1-c447bea01f62"),
	     Drain = ("Drain", "4a247d69-b2cc-4de9-b4d1-c447bea01f63"),
	     Activation = ("Activation", "ea7418bc-6847-4e8a-9cc3-0230dc27d19b")
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
                  DiscardX =           re.compile(r'(?<![<,+-])Discard[0-9]+'),
                  TokensX =            re.compile(r'(?<![<,+-])(Put|Remove|Refill|Use|Infect)([0-9]+)'),
                  TransferX =          re.compile(r'(?<![<,+-])Transfer([0-9]+)'),
                  DrawX =              re.compile(r'(?<![<,+-])Draw([0-9]+)'),
                  ShuffleX =           re.compile(r'(?<![<,+-])Shuffle([A-Za-z& ]+)'),
                  RunX =               re.compile(r'(?<![<,+-])Run([A-Za-z& ]+)'),
                  TraceX =             re.compile(r'(?<![<,+-])Trace([0-9]+)'),
                  InflictX =           re.compile(r'(?<![<,+-])Inflict([0-9]+)'),
                  RetrieveX =          re.compile(r'(?<![<,+-])Retrieve([0-9]+)'),
                  ModifyStatus =       re.compile(r'(?<![<,+-])(Rez|Derez|Expose|Trash|Uninstall|Possess|Exile|Rework|Install|Score)(Target|Host|Multi|Myself)'),
                  SimplyAnnounce =     re.compile(r'(?<![<,+-])SimplyAnnounce'),
                  ChooseKeyword =      re.compile(r'(?<![<,+-])ChooseKeyword'),
                  CustomScript =       re.compile(r'(?<![<,+-])CustomScript'),
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

Xaxis = 'x'
Yaxis = 'y'
