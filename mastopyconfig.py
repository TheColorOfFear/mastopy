##feature toggle
images = True
#   enable or disable image support
quotes = True
#   enable or disable quote posts
scrolling = True
# enable or disable scrolling
scroll_type = 'ansi'
#   if 'pager', uses pydoc pager. !!!DOES NOT WORK WITH TELNET!!!
#   'old' uses an older pager I wrote. !!!prints a LOT of stuff!!!
#   'ansi' uses one made with ansi.
telnet = False

##account settings
default_account = 'default'
#   set to None for the multi-user menu
forcelogin = False
#   set to True for a forced login every time

##img features
imgcolour = "ascii_colour"
#   best : "colour"
#   "256" for some terminals
#   "bw" for ascii-only
#   "ascii_colour" for "256" with ascii chars underneath
imgwidth  = 60
#   best: "original"
#   "max" to stretch to terminal size
#   any int to specify width
imgwidthcrunch = "max"
#   used instead of imgwidth if imgwidth is larger than terminal width
askimages = True
#   if True, ask to set per-session image prefs