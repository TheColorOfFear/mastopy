from mastodon import Mastodon
import mastodon as mastodonpy
from getpass import getpass
from os.path import exists
from io import StringIO
from html.parser import HTMLParser
import os
try:
    import readchar
    doReadChar = True
except Exception as e:
    print("readchar error:",e)
    doReadChar = False
import urllib.request
import textwrap
import re
import img2txt as image
from pydoc import pager
import asyncio, telnetlib3

##feature toggle
images = True
quotes = True
scrolling = True #Warning, will clog up your terminal scrollback if scroll_type == 'old'
scroll_type = 'ansi' 
#   if 'pager', uses pydoc pager. !!!DOES NOT WORK WITH TELNET!!!
#   'old' uses an older pager I wrote. !!!prints a LOT of stuff!!!
#   'ansi' uses one made with ansi.
telnet = False

##account settings
default_account = 'default' #set to None for the multi-user menu
forcelogin = False #set to True for a forced login every time

##img features
imgcolour = "ascii_colour" #best : "colour", "256" for some terminals, "bw" for ascii-only, "ascii_colour" for "256" with ascii chars underneath
imgwidth  = 60 #best: "original", "max" to stretch to terminal size, any int to specify width
imgwidthcrunch = "max" #used instead of imgwidth if imgwidth is larger than terminal width
askimages = True #if True, ask to set per-session image prefs

##create dirs
if not os.path.exists('./mastopy/info/'):
    os.makedirs('./mastopy/info')
if not os.path.exists('./mastopy/resources/'):
    os.makedirs('./mastopy/resources')
if not os.path.exists('./mastopy/resources/images'):
    os.makedirs('./mastopy/resources/images')
if not os.path.exists('./mastopy/resources/pfps'):
    os.makedirs('./mastopy/resources/pfps')

class mastopy:
    # create the app
    # `name` : the local account name (if none, no local account: don't save)
    # `api_base_url` : the server URL (if none, will ask)
    async def app_create(self, name, api_base_url = None) :
        if (api_base_url == None):
            # get base url if it wasn't passed
            api_base_url = await self.telinput('Server URL : ')
            self.telprnt("")
        if name == None:
            # make the app, but don't save the creds
            return Mastodon.create_app(
                'python client',
                api_base_url = api_base_url
            )
        else:
            # make the app and DO save the creds
            # don't return anything, because we'll read the clientcred from a file later
            Mastodon.create_app(
                'python client',
                api_base_url = api_base_url,
                to_file = './mastopy/info/' + name + '_clientcred.secret'
            )
    
    # Login the user
    # `name` : the local account name
    async def user_login(self, name) :
        if name == None:
            # if `name` isn't anything, then log in from scratch
            # (also don't save the user info for relog)
            
            # establish our mastodon link
            api_base_url = await self.telinput('Server URL : ')
            self.telprnt("")
            # make the app
            appinfo = await self.app_create(None, api_base_url)
            mastodon = Mastodon(api_base_url = api_base_url, client_id = appinfo[0], client_secret = appinfo[1])
            
            
            ## Old code for email/pw login
            """
            #email = await self.telinput('Email Address : ')
            #self.telprnt("")
            #password = await self.telgetpass('Password : ')
            #self.telprnt("")
            #mastodon.log_in(
            #    email,
            #    password,
            #)
            """
            
            ## New code for OAuth login
            self.telprnt("Go to the following URL in a browser where you're logged into mastodon, and save the code : ")
            self.telprnt("")
            self.telprnt(mastodon.auth_request_url())
            self.telprnt("")
            code = await self.telinput('OAuth code : ')
            self.telprnt("")
            mastodon.log_in(
                code=code,
            )
            # return the mastodon object
            return mastodon
        else:
            mastodon = Mastodon(client_id = './mastopy/info/' + name + '_clientcred.secret')
            ## Old code for email/pw login
            """
            #email = await self.telinput('Email Address : ')
            #self.telprnt("")
            #password = await self.telgetpass('Password : ')
            #self.telprnt("")
            #mastodon.log_in(
            #    email,
            #    password,
            #    to_file = './mastopy/info/' + name +'_usercred.secret'
            #)
            """
            
            ## New code for OAuth login
            self.telprnt("Go to the following URL in a browser where you're logged into mastodon to log in : ")
            self.telprnt("")
            self.telprnt(mastodon.auth_request_url())
            self.telprnt("")
            code = await self.telinput('OAuth code : ')
            self.telprnt("")
            # DON'T return the mastodon object, put the info in the usercred file
            mastodon.log_in(
                code=code,
                to_file = './mastopy/info/' + name +'_usercred.secret'
            )
    
    # Establish mastodon connection
    # returns `None` if user chooses to quit, returns a mastodon variable otherwise.
    async def usermenu(self):
        global forcelogin, default_account
        if forcelogin:
            # if config'd for forcelogin, make the user login from scratch,
            # return value of `user_login(None)` is the mastodon client so we return that.
            return await self.user_login(None)
        else:
            # if not config'd for forcelogin, do account shenanigans
            if default_account == None:
                # if we don't have a default_account config'd, do the menu.
                ##TODO this is scuffed, we only support 10 accounts,
                #   but can add more than 10?
                ##TODO furthermore, because we're messing with files, this has 
                #   potential to be MAJORLY screwy if connected to multiple telnet clients?
                options = [
                    '<Q>uit\n'
                    '<N>ew User'
                ]
                validkeys = ['q','n']
                
                if (not(exists('./mastopy/info/userlist'))):
                    # make a userlist if we don't have one
                    with open('./mastopy/info/userlist', "wt") as userlist:
                        userlist.write("")
                else:
                    # if we do have a userlist, read that info to make our account menu.
                    with open('./mastopy/info/userlist') as userlist:
                        userlisttxt = userlist.read()
                    userlist = userlisttxt.splitlines()
                    for i in range(len(userlist)):
                        # add to the options, and to the validkeys
                        user = str(str((i + 1) % 10) + ".) " + userlist[i])
                        options.append(user)
                        validkeys.append(str((i + 1) % 10))
                # do the menu
                output = await self.do_menu(validkeys, '\n'.join(options) + '\n> ')
                # menu results : 
                if output.lower() == 'n':
                    # make our new user
                    name = input("New User Name? ")
                    if (not(exists('./mastopy/info/' + name + '_usercred.secret'))):
                        # if we don't have a usercred, check if we have a clientcred
                        if (not(exists('./mastopy/info/' + name + '_clientcred.secret'))):
                            # if we don't have a clientcred, make one
                            await self.app_create(name)
                        # make a usercred
                        await self.user_login(name)
                    # get a list of users, append to it, then write it back to the file.
                    with open('./mastopy/info/userlist') as userlist:
                        listcontent = userlist.read()
                    with open('./mastopy/info/userlist', "wt") as userlist:
                        userlist.write(listcontent + name + '\n')
                    # return the result of another `usermenu()`
                    return await self.usermenu()
                elif output.isdigit():
                    # if it's a digit, then we chose an account.
                    if output == "0":
                        # account 0 is the same as account 10, which is the 11th option
                        # in the options list.
                        name = options[11][4:]
                    else:
                        # otherwise, it's just our chosen number minus 2 in the options list.
                        name = options[int(output) - 2][4:]
                    # return our mastodon client!
                    ##TODO should probably add error checking here, to make sure that:
                    #   1.) the file exists
                    #   2.) the file is a valid mastodon client
                    return Mastodon(access_token = './mastopy/info/' + name + '_usercred.secret')
                elif output.lower() == "q":
                    # user chose to quit, so return None
                    return None
                else:
                    # this shouldn't be needed but with how scuffed the `usermenu()` func is,
                    # better safe than sorry.
                    self.telprnt("Invalid Option")
                    return await self.usermenu()
            else:
                # if we DO have a default account, use that!
                if (not(exists('./mastopy/info/' + default_account + '_usercred.secret'))):
                    # if we don't have a usercred,
                    if (not(exists('./mastopy/info/' + default_account + '_clientcred.secret'))):
                        # make sure we have a clientcred
                        await self.app_create(default_account)
                    # then make said usercred
                    await self.user_login(default_account)
                # return our mastodon client!
                ##TODO should probably add error checking here, to make sure that:
                #   1.) the file exists
                #   2.) the file is a valid mastodon client
                return Mastodon(access_token = './mastopy/info/' + default_account + '_usercred.secret')
    
    # equivilant of `input()`, but with telnet support.
    async def telinput(self, prompt=""):
        global telnet
        # print the prompt
        self.telprnt(prompt, end='')
        if telnet:
            # do fancy telnet stuff if we're in telnet mode : 
            out = ''
            key = ''
            while not(key in ['\r', '\n']):
                # while we haven't recieved a newline (those will count as "submit"):
                if key == self.backspace:
                    # if we get the backspace key we detected in `mastopy.begin()`, 
                    # we remove the last character in our output
                    out = out[:-1]
                else:
                    # otherwise we add the key we just got to the output
                    out += key
                # print the input key
                self.tnwrite.write(''.join(i for i in key if ord(i)<128))
                # and get the next input key
                key = str(await self.tnread.read(1))
            # once we're done, print a newline and return our out
            self.telprnt('')
            return out
        else:
            # because this func is basically just `input()`, if we aren't in telnet mode 
            # we do just use regular input
            out = input()
            return out
    
    # like `telinput()` but without printing the characters input so that passwords aren't 
    #   visible in plaintext in the terminal history.
    async def telgetpass(self, prompt=""):
        global telnet
        if telnet:
            self.telprnt(prompt, end='')
            out = ''
            key = ''
            while not(key in ['\r', '\n']):
                if key == self.backspace:
                    out = out[:-1]
                else:
                    out += key
                #self.tnwrite.write(''.join(i for i in key if ord(i)<128)) #just don't write the text back, obvs
                key = str(await self.tnread.read(1))
            self.telprnt('')
            return out
        else:
            # for non-telnet, use the `getpass()` function from the getpass module
            out = getpass(prompt)
            return out

    # os.get_terminal_size() but with a telnet fallback
    telnetSize = None
    def get_terminal_size(self):
        global telnet
        if telnet:
            if self.telnetSize != None:
                return self.telnetSize
            return([80,25])
        return os.get_terminal_size()

    # like "print()" but with extra special telnet stuff
    def telprnt(self, *args, end='\n'):
        global telnet
        if telnet:
            # if we're a telnet client, jump through a bunch of hoops to print stuff
            realargs = []
            for item in args:
                realitem = str(item)
                endwithnewline = (len(realitem) > 0) and (realitem[-1] == '\n')
                realitem = '\r\n'.join(realitem.splitlines())
                if endwithnewline:
                    realitem = realitem + '\r\n'
                realargs.append(realitem)
            endwithnewline = (len(end) > 0) and (end[-1] == '\n')
            realend = '\r\n'.join(end.splitlines())
            if endwithnewline:
                realend = realend + '\r\n'
            for i in range(len(realargs)):
                if i == len(realargs) - 1:
                    self.tnwrite.write(''.join(r for r in realargs[i] if ord(r)<128))
                    self.tnwrite.write(''.join(r for r in realend if ord(r)<128))
                else:
                    self.tnwrite.write(''.join(r for r in realargs[i] if ord(r)<128))
                    self.tnwrite.write(' ')
        else:
            # if we aren't a telnet client we can just print things normally
            for i in range(len(args)):
                if i == len(args) - 1:
                    print(args[i], end=end)
                else:
                    print(args[i], end=' ')

    # wrapper for `image.print_img()`
    def print_img(self, imgName, printType="colour", imgres="high", wid=80, ret=False):
        out = image.print_img(imgName, printType=printType, imgres=imgres, wid=wid, ret=ret)

        if telnet:
            # replace some non-ascii chars for telnet purposes
            out = out.replace('█', '@').replace('▀', '=')
        return out
    
    # Needed for `mastopy.strip_tags()`
    class MLStripper(HTMLParser):
        def __init__(self):
            super().__init__()
            self.reset()
            self.strict = False
            self.convert_charrefs= True
            self.text = StringIO()
        def handle_data(self, d):
            self.text.write(d)
        def get_data(self):
            return self.text.getvalue()
    
    # takes HTML input and (very shoddily) clears out all the tags
    # `html`    : html data to strip
    def strip_tags(self, html):
        # make the parser
        parser = HTMLParser()
        s = self.MLStripper()
        # strip the tags, first replacing a few kinds of newline with actual newlines
        s.feed(html.replace("<br>", "\n").replace("<br />", "\n").replace("</p><p>", "\n\n"))
        return s.get_data()
    
    # remove ansi escape sequences from a string
    # `line`    : ansi line to strip escape sequences from
    def escape_ansi(self, line):
        # regex from https://stackoverflow.com/questions/14693701/how-can-i-remove-the-ansi-escape-sequences-from-a-string-in-python#14693789
        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', line)
    
    # print a horizontal line
    # `char`    : content of the line (---- or ==== or whatever )
    # `minus`   : offset from the end of the line
    # `length`  : if set, make the line exactly that long.
    def hr(self, char='-', minus=0, length=-1) :
        if length == -1:
            # if `length` is unset then we do the width minus `minus`
            for i in range(self.get_terminal_size()[0]-minus):
                self.telprnt(char, end='')
        else:
            # if `length` is set then make a hr that long
            for i in range(length):
                self.telprnt(char, end='')
        # newline!
        self.telprnt('')
    
    # Get the length, in lines, of a given post
    # `post_list`   : the post, passed as a list of strings representing lines
    def get_post_size(self, post_list):
        global scroll_type
        if scroll_type == 'pager':
            # if we're using the 'pager' scroll type, do some extra stuff
            text_list = []
            for i in range(len(post_list)):
                if len(post_list[i]) == 0 or not(post_list[i][0] == '\x1b'):
                    text_list.append(post_list[i])
            text = ''.join([(x+'\n') for x in post_list])
            text = re.sub(r'\x1b.*m', '', text)
            text_list = text.split('\n')
            return len(text_list)
        else:
            # otherwise just return the length of the list we were passed
            return len(post_list)
    
    # Scroll a post
    # `scroll_list` : a list of lines we're going to scroll
    async def scroll(self, scroll_list):
        global scroll_type
        # if we're using the pydoc pager !!!doesn't work over telnet!!!
        if scroll_type == 'pager':
            text_list = []
            for i in range(len(scroll_list)):
                if len(scroll_list[i]) == 0 or not(scroll_list[i][0] == '\x1b'):
                    text_list.append(scroll_list[i])
            text = ''.join([(x+'\n') for x in text_list])
            text = re.sub(r'\x1b.*m', '', text)
            pager(text)
        # otherwise, if it's the ansi pager (best one if you have ansi support)
        elif scroll_type == 'ansi':
            fromTop = self.get_terminal_size()[1] - 1
            old_fromTop = 0
            key = ''
            while not(key in ['enter', 'esc', 's']):
                if fromTop > old_fromTop :
                    for i in range(old_fromTop, fromTop):
                        self.telprnt(scroll_list[i])
                    old_fromTop = fromTop
                elif fromTop < old_fromTop:
                    self.telprnt('\033[;H', end='')
                    for i in range((fromTop - (self.get_terminal_size()[1] - 1)), fromTop):
                        self.telprnt('\033[2K\033[G\033[0m', end='')
                        self.telprnt(scroll_list[i])
                    old_fromTop = fromTop
                
                key = await self.do_menu(['up','down', 'u', 'd', 'pageup','pagedown', 'enter','esc','s'], '<U>P/<D>OWN to scroll, <S> to stop :')
                self.telprnt('\033[2K\033[G\033[0m', end='')
                if key in ['up', 'u'] and (fromTop > self.get_terminal_size()[1] - 1):
                    fromTop -= 1
                elif key in ['down', 'd'] and (fromTop < len(scroll_list)):
                    fromTop += 1
                elif key == 'pageup':
                    if (fromTop - (self.get_terminal_size()[1] - 2) > self.get_terminal_size()[1] - 1):
                        fromTop -= self.get_terminal_size()[1] - 2
                    else:
                        fromTop = self.get_terminal_size()[1] - 1
                elif key == 'pagedown':
                    if (fromTop + (self.get_terminal_size()[1] - 2) < len(scroll_list)):
                        fromTop += self.get_terminal_size()[1] - 2
                    else:
                        fromTop = len(scroll_list)
        # otherwise, if it's the older pager
        elif scroll_type == 'old':
            offset = 0
            #scroll
            key = ''
            while not(key in ['enter', 'esc', 's']):
                for i in range(len(scroll_list) - offset):
                    self.telprnt(scroll_list[i])
                key = await self.do_menu(['up','down', 'pageup','pagedown', 'enter','esc','s'])
                if key == 'up' and ((len(scroll_list) - offset) >= self.get_terminal_size()[1]):
                    offset += 1
                elif key == 'down' and offset > 0:
                    offset -= 1
                elif key == 'pageup':
                    if (len(scroll_list) - (offset + (self.get_terminal_size()[1] - 2))) >= self.get_terminal_size()[1]:
                        offset += self.get_terminal_size()[1] - 2
                    else:
                        offset = len(scroll_list) - (self.get_terminal_size()[1] - 1)
                elif key == 'pagedown':
                    if (offset - (self.get_terminal_size()[1] - 2)) > 0:
                        offset -= self.get_terminal_size()[1] - 2
                    else:
                        offset = 0
    
    # display a post
    # `post`    : a post dict
    # returns the text we printed, for paging reasons
    async def display_post(self, post) :
        ##TODO Remake this so that I'm not `telprnt`ing *and* adding to `post_text`
        #       - add everything to `post_text` and then print it?
        #       - make a subfunction to do both at once?
        global imgwidth, imgwidthcrunch
        
        # shorthand for the account dict
        account = post['account']
        
        # show the post by default
        show = True
        
        # initial info about the poster
        post_text = [
            textwrap.fill(account['display_name'] + ' | ' + account['acct'], self.get_terminal_size()[0]),
            textwrap.fill('posted on ' + str(post['created_at']), self.get_terminal_size()[0])
            ]
        self.telprnt(account['display_name'] + ' | ' + account['acct'])
        self.telprnt('posted on',  post['created_at'])
        
        # if we have a post url, print it
        if not(post['url'] == None):
            self.telprnt(post['url'])
            post_text.append(textwrap.fill(post['url'], self.get_terminal_size()[0]))
        
        # if the post is sensitive, y/n if we want to display it
        if post['sensitive']:
            show = await self.yn_prompt('sensitive content labeled "' + post['spoiler_text'] + '", display? (y/n) ')
            post_text.append(textwrap.fill('sensitive content labeled "' + post['spoiler_text'], self.get_terminal_size()[0]))
        
        # if there's no repost, print the post content
        if show and (post['reblog'] == None):
            self.telprnt('')
            self.telprnt(textwrap.fill(self.strip_tags(post['content']), self.get_terminal_size()[0], replace_whitespace=False))
            post_text.append('')
            post_text.append(textwrap.fill(self.strip_tags(post['content']), self.get_terminal_size()[0]))
        
        # if there are media attachments, go through showing them
        ##TODO seperate this out into its own function?
        if show and (len(post['media_attachments']) != 0):
            self.telprnt('')
            self.telprnt('Post has media')
            post_text.append('')
            post_text.append('Post has media')
            # remind the user that this is sensitive
            if post['sensitive']:
                self.telprnt('Media for this post marked as sensitive')
                post_text.append(textwrap.fill('Media for this post marked as sensitive', self.get_terminal_size()[0]))
            for attachment in post['media_attachments']:
                # URL and alt text
                self.telprnt('')
                self.telprnt(attachment['url'])
                self.telprnt(textwrap.fill(str(attachment['description']), self.get_terminal_size()[0]))
                post_text.append('')
                post_text.append(textwrap.fill(attachment['url'], self.get_terminal_size()[0]))
                post_text.append(textwrap.fill(str(attachment['description']), self.get_terminal_size()[0]))
                
                # confirm we want to show the image, then show the image
                if self.images and await self.yn_prompt('show image? (y/n) '):
                    try:
                        imgname = attachment['url'].split('/')[-1]
                        if imgname == 'original':
                            ##TODO don't just assume PNG
                            imgname = 'original.png' # just assume PNG idk
                        urllib.request.urlretrieve(attachment['url'], './mastopy/resources/images/' + str(post['id']) + '_' + imgname)
                        if imgwidth > self.get_terminal_size()[0]:
                            img_text = self.print_img('./mastopy/resources/images/' + str(post['id']) + '_' + imgname, printType=self.imgcolour, wid=imgwidthcrunch, ret=True)
                        else:
                            img_text = self.print_img('./mastopy/resources/images/' + str(post['id']) + '_' + imgname, printType=self.imgcolour, wid=imgwidth, ret=True)
                        post_text += img_text.split('\n')[:-1]
                        self.telprnt(img_text)
                    except:
                        self.telprnt('Something went wrong displaying the image.')
                    self.telprnt('\033[0m', end='')
                    post_text.append('\033[0m')
        
        # if there's a poll, show it
        if show and (post['poll'] != None):
            self.telprnt('\nPost has poll.')
            post_text.append('')
            post_text.append('Post has poll')
            votetotal = post['poll']['votes_count']
            voted = post['poll']['voted']
            # print the options
            for i in range(len(post['poll']['options'])):
                if voted or post['poll']['expired']:
                    if i in post['poll']['own_votes']:
                        self.telprnt('> ', end="")
                        itemcontent = "> "
                    else:
                        self.telprnt('- ', end="")
                        itemcontent = "- "
                    votescount = post['poll']['options'][i]['votes_count']
                    if votescount == 0:
                        votespercent = 0
                    else:
                        votespercent = int(round((votescount / votetotal) * 100, 0))
                    self.telprnt(str(votespercent).ljust(3, " ") + "% ", end='')
                    itemcontent += str(votespercent).ljust(3, " ") + "% "
                else:
                    self.telprnt('- ', end="")
                    itemcontent = "- "
                self.telprnt(post['poll']['options'][i]['title'])
                itemcontent += post['poll']['options'][i]['title']
                post_text.append(itemcontent)
            self.telprnt("Total votes : " + str(votetotal))
            post_text.append("Total votes : " + str(votetotal))
            # print some extra poll info
            if voted:
                self.telprnt("You've voted in this poll.")
                post_text.append("You've voted in this poll.")
            if post['poll']['expired']:
                self.telprnt("Poll is closed.")
                post_text.append("Poll is closed.")
            else:
                self.telprnt("Poll closes at " + str(post['poll']['expires_at']))
                post_text.append("Poll closes at " + str(post['poll']['expires_at']))
        
        # if there's a repost, call this function on that repost
        if (post['reblog']):
                self.telprnt('')
                self.telprnt('Reposted :')
                post_text.append('')
                post_text.append('Reposted:')
                post_text += await self.display_post(post['reblog'])
        
        # split `post_text` into lines
        post_text_final = []
        for i in range(len(post_text)):
            post_text_final += post_text[i].split('\n')
        return(post_text_final)
    
    # Display a profile picture (also used for account banners )
    # `account` : the account dict to get the image from
    # `request` : where in the account dict to look for the image
    # `width`   : how wide to make the image
    # `deco`    : fancy shmancy outline for our image
    def display_pfp(self, account, request='avatar_static', width = 10, deco = True):
        # request the pfp and save it to a file
        ##TODO we just assume it's a .png which isn't the best
        urllib.request.urlretrieve(account[request], './mastopy/resources/pfps/' + str(account['id']) + request +'.png')
        # convert it to text with `print_img()`
        pfp = self.print_img('./mastopy/resources/pfps/' + str(account['id']) +  request +'.png', wid=width, ret=True, printType=self.imgcolour).split('\n')
        
        # combine the deco (if any) with the image
        out = ''
        if deco:
            out += ' '
            for i in range(len(self.escape_ansi(pfp[1]))):
                out += '-'
        for line in pfp[1:-1]:
            # if the line has any printable characters in it, add the deco
            ##WHAT: why are we doing this at all when in theory this should 
            #       Just Work(tm) without it?
            if len(self.escape_ansi(line)) > 0:
                ##TODO this assumes the client supports ANSI (`\033[0m`) which 
                #       might not always be the case
                if deco:
                    out += '\n|' + line + '\033[0m|'
                else:
                    out += '\n' + line + '\033[0m'
        out += '\n '
        if deco:
            for i in range(len(self.escape_ansi(pfp[1]))):
                out += '-'
        ##TODO this assumes the client supports ANSI (`\033[0m`) which 
        #       might not always be the case
        out += '\033[0m'
        return out
    
    # Display an entire account
    # `account`         : the account dict we want to display
    # `relationship`    : The relationship dict (if you have it)
    # `show_pfp`        : Bool, do we want to show the profile picture
    # `show_banner`     : Bool, do we want to show the banner (only shows if show_pfp is `True`)
    def display_account(self, account, relationship=None, show_pfp = True, show_banner = True):
        self.telprnt('')
        # if we didn't pass the relationship, get it
        if relationship == None:
            relation = self.mastodon.account_relationships(account['id'])[0]
        else:
            relation = relationship
        
        # if we're wanting to drawing the pfp (and images are enabled)
        wid = 10
        if show_pfp and self.images:
            hei = 5
            i = 0
            banner = []
            # if we're showing the banner
            if show_banner:
                # max our banner size, but min our width (probably not efficient )
                while len(banner) < hei:
                    banner = self.display_pfp(account, request='header_static', width=30+i, deco=False).split('\n')[1:-1]
                    wid = 41 + i
                    i += 1
            # get the instructions for drawing our pfp
            pfp    = self.display_pfp(account, request='avatar_static', deco=False).split('\n')[1:-1]
            
            # print the pfp and banner
            self.telprnt(' ', end='')
            for i in range(wid):
                self.telprnt('-', end='')
            for i in range(len(pfp)):
                if show_banner:
                    self.telprnt('\n|' + pfp[i] + '\033[0m|' + banner[i] + '\033[0m|', end='')
                else:
                    self.telprnt('\n|' + pfp[i] + '\033[0m|', end='')
            self.telprnt('\n ', end='')
            for i in range(wid):
                self.telprnt('-', end='')
            self.telprnt('')
        # print the display name and @
        self.telprnt(account['display_name'] + ' | ' + account['acct'])
        # print their URL too
        self.telprnt(account['url'])
        # and a note if they're a bot account
        if account['bot']:
            self.telprnt('Automated Account')
        # print when the account was created
        self.telprnt('Created: ', account['created_at'])
        # print our relation
        if relation['following']:
            self.telprnt('Following')
        self.hr(length=wid + 2)
        # print the bio
        self.telprnt(self.strip_tags(account['note']))
        self.hr(length=wid + 2)
        # and the account fields
        for field in account['fields']:
            self.telprnt(field['name'] + ' | ', end='')
            if not(field['verified_at'] == None):
                self.telprnt('\033[32m', end='')
            self.telprnt(self.strip_tags(str(field['value'])) + '\033[0m')
        self.telprnt('')
    
    # wrapper for getting 1 key worth of input
    # returns a string
    getinput_key = []
    async def get_input(self) :
        global telnet
        #TODO: catch specific error
        ##TODO what? what error?
        if telnet:
            key = str(await self.tnread.read(1)).lower()
            if key in ['\n', '\r', '']:
                key = "enter"
            return key
        elif doReadChar:
            #readchar solution, it's okay but I'd need to add every single new key to this and make it the same as the telnet version
            key = readchar.readkey()
            if key == readchar.key.DOWN:
                key = 'down'
            elif key == readchar.key.UP:
                key = 'up'
            elif key == readchar.key.ENTER:
                key = 'enter'
            elif key == readchar.key.PAGE_DOWN:
                key = 'pagedown'
            elif key == readchar.key.PAGE_UP:
                key = 'pageup'
            elif key == readchar.key.ESC:
                key = 'esc'
            #print([key])
            return key
        else:
            #telinput solution
            key = (await self.telinput()).lower()
            if key == "":
                key = "enter"
            return key
    
    # easy shorthand for `do_menu()`, and return True/False on Y/N
    async def yn_prompt(self, prompt) :
        key = await self.do_menu(['y','n'], prompt)
        self.telprnt(key)
        if key == 'y':
            return True
        else:
            return False
    
    # do a menu, and until we have a valid result keep the user trapped in said menu
    # `valid_keys` : info about which keys we can accept
    # `prompt` : prompt to be telprnt'd
    async def do_menu(self, valid_keys, prompt='') :
        # stick a '\033[F\n' before our prompt so that it actually prints
        ##TODO: this should be modified to support non-ansi terminals
        self.telprnt('', end='\033[F\n' + prompt)
        while True :
            key = await self.get_input()
            if (key in valid_keys):
                # the returned key will ALWAYS be in the list `valid_keys`.
                return key
    
    # do an account menu
    # `account` : account dict we're doing a menu for
    # returns `None` if no posts to display, or a list of posts if we chose some
    async def account_menu(self, account):
        # get the relationship to an account
        relationship = self.mastodon.account_relationships(account['id'])[0]
        # draw the account (and pass the relationship because we just got it )
        self.display_account(account, relationship)
        self.hr(minus=7)
        # build our prompt!
        prompt = ''
        # following
        if relationship['following']:
            prompt += 'Un<F>ollow, '
        else:
            # if they're locked we have to send a request instead of just following them
            if account['locked']:
                prompt += 'Send <F>ollow Request, '
            else:
                prompt += '<F>ollow, '
        # view posts
        prompt += '<V>iew Posts : '
        
        # do the menu
        key = await self.do_menu(['enter', 'f', 'v'], prompt)
        
        # handle following
        if key == 'f':
            # yes no prompt for all of these
            if relationship['following']:
                self.telprnt('Unfollow')
                if await self.yn_prompt('Are you sure? (y/n) : '):
                    self.mastodon.account_unfollow(account['id'])
            else:
                if account['locked']:
                    self.telprnt('Send Follow Request')
                    if await self.yn_prompt('Are you sure? (y/n)'):
                        self.mastodon.account_follow(account['id'])
                else:
                    self.telprnt('Follow')
                    if await self.yn_prompt('Are you sure? (y/n)'):
                        self.mastodon.account_follow(account['id'])
        # view posts
        elif key == 'v':
            self.telprnt('View Posts')
            numposts = await self.telinput("how many posts to load? ")
            if self.valid_numposts(numposts):
                posts = self.mastodon.account_statuses(account['id'], limit=int(numposts))
                return posts
        return None
    
    # display a list of posts
    # `posts_in`    : a list of post dicts
    # `prompt`      : an optional string to display before the prompt
    async def display_posts(self, posts_in, prompt='') :
        # grab the feature toggles
        global quotes, scrolling
        
        # setup prompt
        section_name = prompt
        # start on the 0th post
        post_num = 0
        # initialize our post list to the posts we were passed
        posts = posts_in
        # setup our archive for when we need to go deeper
        post_archive = []
        post_num_archive = []
        # "do we want to display the post the next time the menu loops"? the answer right now is YES
        show_post = True
        # `while True` because we'll use a `break` to exit this function.
        while True :
            # double newline for formatting
            self.telprnt('\n\n',end='')
            # if we're showing the post, show the post (and recieve `post_text_list` as a special treat for later ;3 )
            if show_post:
                post_text_list = await self.display_post(posts[post_num])
            # reset `show_post` for next loop
            show_post = True
            # hr for formatting
            self.hr(minus=7)
            
            # - -BEGIN THE MENU- -
            #initialize menu options
            keys = []
            
            # building our prompt!
            prompt=''
            # add the `section_name`
            if section_name != '':
                prompt += (section_name + ' | ')
            # where are we
            prompt += str(post_num + 1) + '/' + str(len(posts)) + ' | '
            # interact submenu
            prompt += '<I>nteract, '
            keys += 'i'
            # only show navigation if we could possibly navigate that way
            if (post_num != 0):
                prompt += '<P>revious, '
                keys += 'p'
            if (post_num < len(posts)-1):
                prompt += '<N>ext, '
                keys += 'n'
            # full quit, view submenu, and a debug feller
            prompt += '<S>top, <V>iew : ' # <?> help 
            keys += ['s', '?', 'v']
            
            # get the selection, and do the menu: 
            key = await self.do_menu(keys, prompt)
            # set `new_status` to None for later
            new_status = None
            # stop the loop
            if key == 's' : 
                self.telprnt('Stop')
                break
            # display debug info
            elif key == '?' :
                # selected post dict
                self.telprnt(posts[post_num])
                # a stripped version of our post's content
                self.telprnt(self.strip_tags(posts[post_num]['content']).split('\n')[-1])
                # wait for a return press
                await self.get_input()
            # go to next post
            elif key == 'n' :
                self.telprnt('Next')
                post_num += 1
            # go to previous post
            elif key == 'p' :
                self.telprnt('Previous')
                post_num -= 1
            # 'view' submenu
            elif key == 'v' :
                self.telprnt('View')
                
                prompt = ''
                keys = []
                # if the post is too tall for our screen, and scrolling is enabled, give the option to scroll
                if scrolling and self.get_post_size(post_text_list) > self.get_terminal_size()[1]:
                    prompt += '<P>ost, '
                    keys += 'p'
                # if there's a thread above us, or if this is a reblogged post and there's a 
                #   thread above /that/ post, give the option for the thread.
                if (posts[post_num]['in_reply_to_id'] != None) or (posts[post_num]['reblog'] != None and posts[post_num]['reblog']['in_reply_to_id'] != None):
                    prompt += '<T>hread, '
                    keys += 't'
                # if there're replies below us, or if this is a reblogged post and there're 
                #   replies below /that/ post, give the option for the replies (and include the number of replies )
                if (posts[post_num]['replies_count'] > 0)      or (posts[post_num]['reblog'] != None and posts[post_num]['reblog']['replies_count'] > 0):
                    if posts[post_num]['reblog'] != None:
                        prompt += '<R>eplies ({replies}), '.format(replies = str(posts[post_num]['reblog']['replies_count']))
                    else:
                        prompt += '<R>eplies ({replies}), '.format(replies = str(posts[post_num]['replies_count']))
                    keys += 'r'
                # if we've incepted, give the option to go back a layer
                if len(post_archive) > 0 :
                    prompt += '<B>ack, '
                    keys += 'b'
                # if the quotes feature is enabled, and we detect a quoted post, give the option for the quote post.
                ##TODO fix up the quote post feature
                if quotes and self.strip_tags(posts[post_num]['content']).split('\n')[-1][:8] == 'RE: http':
                    prompt += '<Q>uoted Post, '
                    keys += 'q'
                # option to view the poster's account, and option to re-get the post
                prompt += '<A>ccount, Re<F>resh Post : '
                # "enter" will just leave the sub menu
                keys += ['enter', 'a', 'f']
                
                # get the selection and do the menu:
                key = await self.do_menu(keys, prompt)
                # view the account
                if key == 'a' :
                    self.telprnt('View Account')
                    # send the account to the `account_menu`, then if we get posts back, hit 'em with an "inception"
                    account = posts[post_num]['account']
                    newposts = await self.account_menu(account)
                    if newposts != None:
                        post_archive.insert(0, posts)
                        post_num_archive.insert(0, post_num)
                        posts = newposts
                        post_num = 0
                # scroll the post
                elif key == 'p':
                    self.telprnt('View Post')
                    await self.scroll(post_text_list)
                    show_post = False
                # go up an inception layer
                elif key == 'b':
                    self.telprnt('Go Back')
                    posts = post_archive.pop(0)
                    post_num = post_num_archive.pop(0)
                # view the thread
                elif key == 't' :
                    self.telprnt('View Thread')
                    post_archive.insert(0, posts)
                    post_num_archive.insert(0, post_num)
                    # get and set the thread posts
                    if posts[post_num]['reblog'] != None:
                        posts = self.get_thread(posts[post_num]['reblog'])
                    else:
                        posts = self.get_thread(posts[post_num])
                    # set position to the top of the thread
                    post_num = 0
                # view the replies
                elif key == 'r' :
                    self.telprnt('View Replies')
                    post_archive.insert(0, posts)
                    post_num_archive.insert(0, post_num)
                    # get the `posts` and the `post_num`
                    if posts[post_num]['reblog'] != None:
                        posts, post_num = self.get_replies(posts[post_num]['reblog'])
                    else:
                        posts, post_num = self.get_replies(posts[post_num])
                # view the quoted post
                elif key == 'q' :
                    ##TODO this is actually kinda borked, fixme?
                    self.telprnt('View Quoted Post')
                    quotedURL = self.strip_tags(posts[post_num]['content']).split('\n')[-1].split('RE: ')[1]
                    newposts = self.mastodon.search(quotedURL, result_type='statuses')
                    newposts = newposts['statuses']
                    if len(posts) > 0:
                        post_archive.insert(0, posts)
                        post_num_archive.insert(0, post_num)
                        posts = newposts
                        post_num = 0
                    else:
                        self.telprnt('Quoted Post Not Found')
                # refresh the post
                elif key == 'f':
                    self.telprnt('Refresh Post')
                    try:
                        new_status = self.mastodon.status(posts[post_num]['id'])
                    except mastodonpy.MastodonNetworkError:
                        self.telprnt('Network Error, Couldn\'t refresh post.')
                        new_status = None
            # 'interact' submenu
            elif key == 'i':
                self.telprnt('Interact')
                prompt = ''
                # all of our inputs are about the same EVERY SINGLE TIME so we don't have do do much of an additive list ! yippee !
                valid_keys = ['enter', 'l', 'r', 'b', 'f', 'c']
                # like prompt
                if posts[post_num]['favourited']:
                        prompt += 'Un<L>ike, '
                else:
                    prompt += '<L>ike, '
                # repost prompt
                if posts[post_num]['reblogged']:
                    prompt += 'Un<R>epost, '
                else:
                    prompt += '<R>epost, '
                #bookmark prompt
                if posts[post_num]['bookmarked']:
                    prompt += 'Un<B>ookmark, '
                else:
                    prompt += '<B>ookmark, '
                # poll prompt
                repoll = False
                try: #check the reblog for a poll, if it exists
                    repoll = posts[post_num]['reblog']['poll'] != None
                except:
                    pass
                if posts[post_num]['poll'] != None or repoll:
                    # choose the poll
                    if repoll:
                        poll = posts[post_num]['reblog']['poll']
                    else:
                        poll = posts[post_num]['poll']
                    # if poll isn't expired, give the option to interact with it
                    if not(poll['expired'] or poll['voted']):
                        prompt += '<P>oll, '
                        valid_keys.append('p')
                prompt += ' Re<F>resh Post, <C>omment : '
                
                # do the menu
                key = await self.do_menu(valid_keys, prompt)
                new_status = None
                # bookmarks
                if key == 'b':
                    if posts[post_num]['bookmarked']:
                        self.telprnt('Remove Bookmark')
                        new_status = self.mastodon.status_unbookmark(posts[post_num]['id'])
                    else:
                        self.telprnt('Bookmark Post')
                        new_status = self.mastodon.status_bookmark(posts[post_num]['id'])
                # interact with poll
                elif key == 'p':
                    self.telprnt('Vote in Poll')
                    options = ['enter']
                    # choose the poll
                    if repoll:
                        poll = posts[post_num]['reblog']['poll']
                    else:
                        poll = posts[post_num]['poll']
                    # generate and print our poll options
                    for i in range(len(poll['options'])):
                        options.append(str(i + 1)) # might break things if you can make polls with more than 9 options but I don't think you can?
                        self.telprnt(str(i + 1) + '.) ', end='')
                        self.telprnt(poll['options'][i]['title'])
                    key = await self.do_menu(options, '> ')
                    if key != 'enter':
                        self.telprnt(key)
                        new_status = posts[post_num]
                        pollresponse = self.mastodon.poll_vote(poll['id'], (int(key) - 1))
                        # replace the poll in our post with the updated poll we got from `mastodon.poll_vote`
                        if repoll:
                            poll = posts[post_num]['reblog']['poll'] = pollresponse
                        else:
                            poll = posts[post_num]['poll'] = pollresponse
                    else:
                        self.telprnt('')
                # likes
                elif key == 'l':
                    if posts[post_num]['favourited']:
                        self.telprnt('Remove Like')
                        new_status = self.mastodon.status_unfavourite(posts[post_num]['id'])
                    else:
                        self.telprnt('Like Post')
                        new_status = self.mastodon.status_favourite(posts[post_num]['id'])
                # boosts
                elif key == 'r':
                    if posts[post_num]['reblogged']:
                        self.telprnt('Remove Boost')
                        self.mastodon.status_unreblog(posts[post_num]['id'])
                        new_status = self.mastodon.status(posts[post_num]['id'])
                    else:
                        self.telprnt('Boost Post')
                        self.mastodon.status_reblog(posts[post_num]['id'])
                        new_status = self.mastodon.status(posts[post_num]['id'])
                # refresh post
                elif key == 'f':
                    self.telprnt('Refresh Post')
                    try:
                        new_status = self.mastodon.status(posts[post_num]['id'])
                    except mastodonpy.MastodonNetworkError:
                        self.telprnt('Network Error, Couldn\'t refresh post.')
                        new_status = None
                # comment on post
                elif key == 'c':
                    self.telprnt('Comment')
                    # reply to the post 
                    await self.write_status(in_reply_to = posts[post_num])
                
            # if we got a new status, set our current post to the new one
            if not(new_status == None):
                posts[post_num] = new_status
    
    # menu/loop for writing a status as the logged in user.
    # `in_reply_to` : the post, passed as a dict, that we're replying to
    async def write_status(self, in_reply_to = None):
        global telnet
        #print control info
        self.telprnt('Entering message. Pressing return will   ')
        self.telprnt('give a hard line break. Pressing return  ')
        self.telprnt('on an empty line will open the menu, but ')
        self.telprnt('will not give a second hard line break.  ')
        self.telprnt('Press S in the menu to post your status. \n')
        
        # our function to add to the post
        async def write_text(postList=[]):
            postList_tmp = postList
            lastline = 'tmp'
            while lastline != '':
                lastline = (await self.telinput())
                if lastline != '':
                    postList_tmp.append(lastline)
            post = ''.join([('\n' + line) for line in postList_tmp]).lstrip('\n')
            return postList_tmp, post
        
        # start by letting the user write a bunch
        postList, post = await write_text()
        
        # init a couple of vars to defaults (no CW, default visibility)
        cw_string = '   add content <W>arning\n'
        cw = None
        visibility = None
        # we'll use setting `in_menu` to `False` to leave the array, so set to `True` here
        in_menu = True
        while in_menu:
            # do our menu
            key = await self.do_menu(['?','a','c','s','p','w','v'], '\nEntry command (? for options) -> ')
            # if the user wanted the options, print the options
            if key == '?':
                self.telprnt('\n' +
                    'One of...\n' +
                    '   <A>bort\n' +
                    '   <C>ontinue\n' +
                    '   post <S>tatus\n' +
                    '   <P>rint post\n' +
                    cw_string +
                    '   change <V>isibility\n')
            # if the user wanted to quit, y/n prompt them and then quit if they're sure.
            elif key == 'a':
                self.telprnt('Abort')
                if await self.yn_prompt('Are you sure? '):
                    # leave the menu
                    in_menu = False
            # continue typing, this will call `write_text()` again
            elif key == 'c':
                self.telprnt('Continue')
                postList, post = await write_text(postList)
            # post the reply after a y/n "are you sure" prompt, then leave the menu
            elif key == 's':
                self.telprnt('Post status')
                if await self.yn_prompt('Are you sure? '):
                    if in_reply_to == None:
                        # if we aren't replying to anyone, post the status like normal.
                        self.mastodon.status_post(post, visibility=visibility, spoiler_text=cw)
                    else:
                        # if we are replying to someone, post the status with `in_reply_to` as an arg,
                        #   and with `mastodon.status_reply`
                        self.mastodon.status_reply(in_reply_to, post, visibility=visibility, spoiler_text=cw)
                    # leave the menu
                    in_menu = False
            # literally just print the post
            elif key == 'p':
                self.telprnt('Print post')
                self.telprnt(post)
            # change or unset the cw
            elif key == 'w':
                self.telprnt('Add CW')
                self.telprnt('Current CW is: ' + str(cw))
                cw = await self.telinput('Content warning (press enter for none) : ')
                # change the cw dialogue because we have a cw now
                cw_string = '   change content <W>arning\n'
                if cw == '':
                    # if they don't want a CW, set `cw` to `None` because the post function takes `None`
                    #   to mean "don't add a cw to this post ! !"
                    cw = None
                    # also reset the cw dialogue because we in fact do NOT have a cw
                    cw_string = '   add content <W>arning\n'
                self.telprnt('')
            # change the post's visibility
            elif key == 'v':
                self.telprnt('Change Visibility')
                self.telprnt('Current Visibility is: ', end='')
                if visibility == None:
                    # this exception is because 'default' is `None` when passed to the api function.
                    self.telprnt('default')
                else:
                    self.telprnt(visibility)
                # print and do a menu, where the options are literally just the API's options
                self.telprnt('Change to:\n  <1> Default\n  <2> Public\n  <3> Unlisted\n  <4> Private\n  <5> Direct')
                key = await self.do_menu(['1','2','3','4','5'],'> ')
                self.telprnt(key)
                if key == '1':
                    visibility = None
                if key == '2':
                    visibility = 'public'
                if key == '3':
                    visibility = 'unlisted'
                if key == '4':
                    visibility = 'private'
                if key == '5':
                    visibility = 'direct'
    
    # check for a valid number of posts for a request
    # `number`  : an int we're checking
    def valid_numposts(self, number):
        return number.isdigit() and int(number) > 0
    
    # The top-level menu, from which the user gets to a bunch of other stuff.
    # if we return `True`, we indicate that we want to keep looping
    # if we return `False`, we indicate that we want to quit
    async def main_menu(self):
        # print our menu and setup our menu options
        opts = []
        self.hr(minus=7)
        self.telprnt('Timelines: <H>ome, <L>ocal, <F>ederated');        opts += ['h','l','f']
        self.telprnt('Posts:     <V>iew by ID, <B>ookmarks, <C>reate'); opts += ['v','b','c']
        self.telprnt('Search:    <S>earch, search by Hash<T>ag');       opts += ['s','t']
        self.telprnt('User:      <M>y Account');                        opts += ['m'] #, <N>otifications')
        self.telprnt('General:   <Q>uit');                              opts += ['q']
        self.hr(minus=7)
        
        # do our menu
        key = await self.do_menu(opts, '>')
        # This is wrapped in a try/except because if a network error happens we want to be able to deal.
        try:
            # first row of the menu, various timelines
            if key in ['h','l','f']:
                if key == 'h':
                    self.telprnt('Home timeline')
                    howmany = await self.telinput("how many posts to load? ")
                    if self.valid_numposts(howmany): # validate numposts
                        # `mastodon.timeline_home` is the home timeline
                        posts = self.mastodon.timeline_home(limit=int(howmany))
                        await self.display_posts(posts)
                    return True
                elif key =='l':
                    self.telprnt('Local timeline')
                    howmany = await self.telinput("how many posts to load? ")
                    if self.valid_numposts(howmany): # validate numposts
                        # `mastodon.timeline_local` is the local timeline
                        posts = self.mastodon.timeline_local(limit=int(howmany))
                        await self.display_posts(posts)
                    return True
                elif key =='f':
                    self.telprnt('Federated timeline')
                    howmany = await self.telinput("how many posts to load? ")
                    if self.valid_numposts(howmany): # validate numposts
                        # `mastodon.timeline_public` is the public timeline
                        posts = self.mastodon.timeline_public(limit=int(howmany))
                        await self.display_posts(posts)
                    return True
            # second row of the menu, post utils
            elif key in ['v','b','c']:
                # view a specific post 
                if key == 'v':
                    self.telprnt('View post ID: ',end='')
                    id = await self.telinput('')
                    post = None
                    if (id != ''):
                        try:
                            post = [self.mastodon.status(id)]
                        except mastodonpy.MastodonNotFoundError:
                            # if we couldn't find the post:
                            self.telprnt('Err: post with that id not found')
                            post = None
                    
                    if post != None:
                        await self.display_posts(post)
                    return True
                # view your bookmarks
                elif key =='b':
                    self.telprnt('Bookmarks')
                    howmany = await self.telinput("how many posts to load? ")
                    if self.valid_numposts(howmany): # validate numposts
                        # `mastodon.bookmarks` is the ""timeline"" with the user bookmarks
                        posts = self.mastodon.bookmarks(limit=int(howmany))
                        await self.display_posts(posts)
                    return True
                # create a post
                elif key =='c':
                    self.telprnt('Post')
                    await self.write_status()
                    return True
            # third row of menu, search utils
            elif key in ['s','t']:
                # search posts normally
                if key == 's':
                    self.telprnt('Search: ',end='')
                    search_term = await self.telinput('')
                    if (search_term != ''):
                        ##TODO verify that you can't add a limit to a `mastodon.search()`
                        posts = self.mastodon.search(search_term, result_type='statuses')
                        posts = posts['statuses']
                        # make sure we have posts to display
                        if len(posts) > 0:
                            await self.display_posts(posts)
                        else:
                            self.telprnt('No Search Results')
                    return True
                # search posts by hashtag
                elif key == 't':
                    self.telprnt('View posts by Hashtag: ',end='')
                    hashtag = await self.telinput('')
                    if (hashtag != ''):
                        howmany = await self.telinput("how many posts to load? ")
                        if self.valid_numposts(howmany): # validate howmany
                            posts = self.mastodon.timeline_hashtag(hashtag, limit=int(howmany))
                            # make sure we have posts to display
                            if len(posts) > 0:
                                await self.display_posts(posts)
                            else:
                                self.telprnt('No Search Results')
                    return True
            # fourth row of menu, account utils
            elif key in ['m']:#,'n']:
                # your account info
                if key == 'm':
                    # Doesn't enter the account menu, just displays the account.
                    self.telprnt('My Account')
                    account = self.mastodon.me()
                    self.display_account(account)
                    return True
                """
                # your notifs
                ##TODO finish this
                elif key == 'n':
                    telprnt('Notifications')
                    posts = mastodon.notifications(types='status')
                    await display_posts(posts)
                    return True"""
            # fifth row, just quit for now
            elif key == 'q':
                self.telprnt('Quit')
                # return `False` to quit
                return False
        except mastodonpy.MastodonNetworkError:
            # if we encounter a network error, give the user the option to quit.
            self.telprnt('Network Error.')
            return not(await self.yn_prompt('Quit? (y/n) '));
    
    # Get the thread leading up to a post
    # `post`    : a post, passed as a dict
    def get_thread(self, post):
        # get the context and then put our post at the end of the returned thread
        thread_tmp = self.mastodon.status_context(post['id'])
        thread = thread_tmp['ancestors']
        thread.append(post)
        return thread
    
    # Get the replies of a post
    # `post`    : a post, passed as a dict
    def get_replies(self, post):
        # get the context of our post (which has the parent and replies)
        replies_tmp = self.mastodon.status_context(post['id'])
        # get the thread before our post
        thread = replies_tmp['ancestors']
        # get *all* the replies to our post
        replies = replies_tmp['descendants']
        # limit our replies to the direct children of our `post`
        for i in range(len(replies) - 1, -1, -1):
            if replies[i]['in_reply_to_id'] != post['id']:
                replies.pop(i)
        # all the posts we're going to return will be in `replies_full`
        replies_full = []
        replies_full += thread
        # the post that we want to focus on is going to be one after our thread. because
        # python is zero-indexed we can just set the focused post to the length of `replies_full`
        post_num = len(replies_full)
        replies_full.append(post)
        replies_full += replies
        return replies_full, post_num
    
    # make our telnet reader and writer
    # only really used by our low level input/output functions
    def __init__(self, reader, writer):
        self.tnread = reader
        self.tnwrite = writer
    
    # set everything up and hop into the menu
    async def begin(self):
        global telnet, imgcolour, images, askimages
        name = 'default' #default name
        
        self.telprnt(logo)
        # set default choices
        self.images = images
        self.imgcolour = imgcolour
        
        # get backspace key for telnet
        if telnet:
            self.telprnt('Press your backspace key ', end='')
            self.backspace = await self.get_input()
            self.telprnt("")
            customSize = False
            self.telprnt('What is your terminal width? ', end='')
            wid = await self.telinput()
            if wid.isdigit():
                self.telprnt('What is your terminal height? ', end='')
                hei = await self.telinput()
                if wid.isdigit() and hei.isdigit():
                    self.telnetSize = (int(wid), int(hei))
                    customSize = True
            if customSize:
                self.telprnt(f'Terminal size: {self.telnetSize[0]}x{self.telnetSize[1]}')
            else:
                self.telprnt(f'Terminal size: 80x20')
        
        # ask the user to config stuff
        if askimages:
            imgpref = await self.do_menu(['t','a','c'], 'Images: Alt <T>ext, <A>scii, <C>olour : ')
            if imgpref.lower() == 't':
                self.images = False
                self.telprnt('Alt Text')
            elif imgpref.lower() == 'a':
                self.images = True
                self.imgcolour = 'bw'
                self.telprnt('ASCII')
            elif imgpref.lower() == 'c':
                self.images = True
                self.imgcolour = '256'
                self.telprnt('Colour')
        
        # set up our mastodon link
        self.mastodon = await self.usermenu()
        
        # check that `self.mastodon` isn't `None`, because if it is, the user chose to quit 
        #   in `self.usermenu()`.
        while True and not(self.mastodon == None):
            # if `self.main_menu` ever returns False, then we quit.
            # otherwise keep calling it.
            if not(await self.main_menu()):
                break
        if telnet:
            # gotta wrap things up with the telnet client, if there is one.
            self.tnwrite.close()

logo = """\
.  .._. _____ _ ._  _ .  .
|\\/||_|/__ | / \\| \\/ \\|\\ |
|  || |__/ | \\_/|_/\\_/| \\|\n\
"""
# var to keep track of our telnet clients PURELY for logs
globalid = 0
if telnet:
    # server open
    print('ready')
    async def shell(reader, writer):
        global globalid
        # print which client we are on connect
        globalid += 1
        thisid = globalid
        print('connected', thisid)
        # init with the telnet reader and writer
        thisShell = mastopy(reader, writer)
        try:
            await thisShell.begin()
        except:
            # Close the telnet shell BEFORE we raise the error
            thisShell.telprnt('Something went wrong, disconnecting you...')
            thisShell.tnwrite.close()
            raise
        # print which client we are on d/c as well
        print('disconnected', thisid)
    
    # async + telnet stuff
    loop = asyncio.get_event_loop()
    coro = telnetlib3.create_server(port=6023, shell=shell, timeout=False)
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed()) 
else:
    # if we aren't telnet, then don't init with a reader or writer
    thisShell = mastopy(None, None)
    # async stuff
    loop = asyncio.get_event_loop()
    while True:
        if not(loop.run_until_complete(thisShell.begin())):
            break
