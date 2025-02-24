`App.py` is the main script for MacroPlus, containing several commonly used functions and all HTTP routes.

## process_cue_number()
---

## initialize_config()
---

## run_macro()
---
### Home Page ("/" Route)
---
[[osc_server.py]] sends incoming OSC messages to this route in JSON format. Upon receiving a message, the script checks if the message is an `/eos/out/ping=macroPlus` message, which is the standard connection validation.

If the message is not a validation ping, it checks the OSC address and arguments against the triggers for all [[Internal Macro|internal macros]], [[User Macro|user macros]], and [[Dynamic Variable|dynamic variables]]. If the trigger for a macro matches, and the cooldown for that macro is over, it starts [[app.py#run_macro()|run_macro()]].

### Network Config Page ("/network_config" Route)
---

### Variable Console Page ("/variable_console" Route)
---

### "/osc" Route
---
