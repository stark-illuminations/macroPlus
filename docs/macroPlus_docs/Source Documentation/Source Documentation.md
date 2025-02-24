MacroPlus' source code is written in Python, with persistent data being stored in XML files, and macro scripts saved in plaintext. Its structure is described below. Information on each type of data, as well as overall processes can be found on the relevant pages.

## Project Structure
---
```
/src
	/config
		/macros
			# Macro action scripts
		macros.xml
		network_settings.xml
		variables.xml
	/static
		/css
			main.css
		/js
			main.js
	/templates
		base.html
		index.html
		network_config.html
		variable_console.html
	/tests
		test_osc.py
		test_osc_server.py
		test_scripting.py
		test_value.py
	app.py
	eos_query.py
	macros.py
	osc.py
	osc_server.py
	scripting.py
	value.py
	variables.py
```

## Data Types
---
MacroPlus data can be organized into several data types. See the pages below for more information.

| Data Type             | Function                                                                                                                                                                                                                                            |
| --------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [[User Macro]]        | Persistent macros created by the user, which can be triggered manually, via a pre-defined OSC command, or when a pre-defined cue fires.                                                                                                             |
| [[Internal Macro]]    | Temporary macros created by MacroPlus, only used by internal code. Their main function is to fetch, receive, and store [[Eos Query]] data.                                                                                                          |
| [[User Variable]]     | Persistent variables defined by the user, intended to store re-usable data such as strings of text, numbers, or boolean values. These can be accessed and written by all types of macros.                                                           |
| [[Internal Variable]] | Temporary variables created by [[Internal Macro\|internal macros]] in the course of running [[User Macro\|user macros]]. These typically hold Eos query data before it is inserted into a user macro. These are only accessible by internal macros. |
| [[Dynamic Variable]]  | Automatically updated variables holding oft-used Eos data, such as the filename, the current cue and list numbers, and the current selection. These are writeable and accessible by all macros.                                                     |
| [[Eos Query]]         | A request for some data from the console, such as a palette's label or a fixture's intensity. These can be used like variables in [[User Macro\|user macros]].                                                                                      |

## Scripting Language
---
See the main [[Scripting Language]] page for information about how MacroPlus' custom scripting language works.

## Run Loop Overview
---
On launch, MacroPlus needs two scripts to run: [[app.py]] and [[osc_server.py]]. `App.py` handles all main functionality, while `osc_server.py` directs incoming OSC from Eos to the "/osc" HTTP route, thus allowing MacroPlus to process it.

When [[app.py]] starts, it runs [[app.py#initialize_config()|initialize_config()]], loading all persistent data, including network settings, [[User Macro|user macros]], and [[User Variable|user variables]], as well as [[osc.py#start_osc_client()|starting the OSC server]].

Once initialized, app.py listens for incoming HTTP requests for each of its routes, including the Home/Macro page, the Network Setup page, the Variable Console page, and the "/osc" route, which handles incoming OSC messages. When the user presses a button on one of the main pages, the main runloop checks the type of action that was triggered, then completes the appropriate action. See the [[app.py]] page for more information.