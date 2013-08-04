###==================================================File Contents==================================================###
# This file contains global variables in ANR. They should not be modified by the scripts at all.
###=================================================================================================================###

import re
#---------------------------------------------------------------------------
# These are constant global variables in ANR: They should not be modified by the scripts at all.
#---------------------------------------------------------------------------

mdict = dict( # A dictionary which holds all the hard coded markers (in the markers file)
             Wound =            ("Wound", "4a247d69-b2cc-4de9-b4d1-c447bea01f61"),
             Success =                  ("Success", "4a247d69-b2cc-4de9-b4d1-c447bea01f62"),
             Drain =                   ("Drain", "4a247d69-b2cc-4de9-b4d1-c447bea01f63"))

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

