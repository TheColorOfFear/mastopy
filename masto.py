from mastodon import Mastodon
import mastodon as mastodonpy
from getpass import getpass
from os.path import exists
from io import StringIO
from html.parser import HTMLParser
import os
import readchar
import urllib.request
import textwrap
import re
import img2txt as image
from pydoc import pager
import asyncio, telnetlib3
import atproto
##feature toggle
images = True
quotes = True
scrolling = True #Warning, will clog up your terminal scrollback if scroll_type == 'old'
scroll_type = 'ansi' #if 'pager', uses pydoc pager. 'old' uses an older pager I wrote, and 'ansi' uses one made with ansi.
telnet = True
atprotoMode = True #enable atproto mode
askatproto = True #ask user if they're using the atproto

##account settings
default_account = 'default' #set to None for the multi-user menu
forcelogin = True #set to True for a forced login every time

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
    async def app_create(self, name, api_base_url = None) :
        if name == None:
            return Mastodon.create_app(
                'python client',
                api_base_url = api_base_url
            )
        else:
            api_base_url = await self.telinput('Server URL : ')
            self.telprnt("")
            Mastodon.create_app(
                'python client',
                api_base_url = api_base_url,
                to_file = './mastopy/info/' + name + '_clientcred.secret'
            )
    async def user_login(self, name) :
        if not(self.atprotoMode):
            if name == None:
                api_base_url = await self.telinput('Server URL : ')
                self.telprnt("")
                appinfo = await self.app_create(None, api_base_url)
                mastodon = Mastodon(api_base_url = api_base_url, client_id = appinfo[0], client_secret = appinfo[1])
                email = await self.telinput('Email Address : ')
                self.telprnt("")
                password = await self.telgetpass('Password : ')
                self.telprnt("")
                mastodon.log_in(
                    email,
                    password,
                )
                return mastodon
            else:
                mastodon = Mastodon(client_id = './mastopy/info/' + name + '_clientcred.secret')
                email = await self.telinput('Email Address : ')
                self.telprnt("")
                password = await self.telgetpass('Password : ')
                self.telprnt("")
                mastodon.log_in(
                    email,
                    password,
                    to_file = './mastopy/info/' + name +'_usercred.secret'
                )
        else:
            atprotoClient = atproto.Client()
            username = await self.telinput('Username : ')
            self.telprnt("")
            password = await self.telgetpass('Password : ')
            self.telprnt("")
            atprotoClient.login(
                username,
                password,
            )

    async def usermenu(self):
        global forcelogin, default_account
        if forcelogin:
            return await self.user_login(None)
        else:
            if default_account == None:
                options = [
                    '<Q>uit\n'
                    '<N>ew User'
                ]
                validkeys = ['q','n','1']

                if (not(exists('./mastopy/info/userlist'))):
                    with open('./mastopy/info/userlist', "wt") as userlist:
                        userlist.write("")
                else:
                    with open('./mastopy/info/userlist') as userlist:
                        userlisttxt = userlist.read()
                    userlist = userlisttxt.splitlines()
                    for i in range(len(userlist)):
                        user = str(str((i + 1) % 10) + ".) " + userlist[i])
                        options.append(user)
                        validkeys.append(str((i + 1) % 10))
                output = await self.do_menu(validkeys, '\n'.join(options) + '\n> ')
                
                if output.lower() == 'n':
                    name = input("New User Name? ")
                    if (not(exists('./mastopy/info/' + name + '_usercred.secret'))):
                        if (not(exists('./mastopy/info/' + name + '_clientcred.secret'))):
                            await self.app_create(name)
                        await self.user_login(name)
                    with open('./mastopy/info/userlist') as userlist:
                        listcontent = userlist.read()
                    with open('./mastopy/info/userlist', "wt") as userlist:
                        userlist.write(listcontent + name + '\n')
                    return await self.usermenu()
                elif output.isdigit():
                    if output == "0":
                        name = options[11][4:]
                    else:
                        name = options[int(output) - 2][4:]
                    return Mastodon(access_token = './mastopy/info/' + name + '_usercred.secret')
                elif output.lower() == "q":
                    return None
                else:
                    self.telprnt("Invalid Option")
                    return await self.usermenu()
            else:
                if (not(exists('./mastopy/info/' + default_account + '_usercred.secret'))):
                    if (not(exists('./mastopy/info/' + default_account + '_clientcred.secret'))):
                        await self.app_create(default_account)
                    await self.user_login(default_account)
                return Mastodon(access_token = './mastopy/info/' + default_account + '_usercred.secret')
    
    #function for telnet compatibility
    async def telinput(self, prompt=""):
        global telnet
        self.telprnt(prompt, end='')
        if telnet:
            out = ''
            key = ''
            while not(key in ['\r', '\n']):
                if key == self.backspace:
                    out = out[:-1]
                else:
                    out += key
                self.tnwrite.write(''.join(i for i in key if ord(i)<128))
                key = str(await self.tnread.read(1))
            self.telprnt('')
            return out
        else:
            key = input()
            return key
    
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
            key = getpass(prompt)
            return key

    #function for telnet compatibility
    def get_terminal_size(self):
        global telnet
        if telnet:
            return([80,25])
        return os.get_terminal_size()

    #function for telnet compatibility
    def telprnt(self, *args, end='\n'):
        global telnet
        if telnet:
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
            for i in range(len(args)):
                if i == len(args) - 1:
                    print(args[i], end=end)
                else:
                    print(args[i], end=' ')

    #wrapper for image.print_img
    def print_img(self, imgName, printType="colour", imgres="high", wid=80, ret=False):
        out = image.print_img(imgName, printType=printType, imgres=imgres, wid=wid, ret=ret)

        if telnet:
            out = out.replace('█', '@').replace('▀', '=')
        return out
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

    def strip_tags(self, html):
        parser = HTMLParser()
        s = self.MLStripper()
        s.feed(html.replace("<br>", "\n").replace("<br />", "\n").replace("</p><p>", "\n\n"))
        return s.get_data()

    def escape_ansi(self, line):
        ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
        return ansi_escape.sub('', line)

    def hr(self, char='-', minus=0, length=-1) :
        if length == -1:
            for i in range(self.get_terminal_size()[0]-minus):
                self.telprnt(char, end='')
        else:
            for i in range(length):
                self.telprnt(char, end='')
        self.telprnt('')

    def get_post_size(self, post_list):
        global scroll_type
        if scroll_type == 'pager':
            text_list = []
            for i in range(len(post_list)):
                if len(post_list[i]) == 0 or not(post_list[i][0] == '\x1b'):
                    text_list.append(post_list[i])
            text = ''.join([(x+'\n') for x in post_list])
            text = re.sub(r'\x1b.*m', '', text)
            text_list = text.split('\n')
            return len(text_list)
        else:
            return len(post_list)

    async def scroll(self, scroll_list):
        global scroll_type
        if scroll_type == 'pager':
            text_list = []
            for i in range(len(scroll_list)):
                if len(scroll_list[i]) == 0 or not(scroll_list[i][0] == '\x1b'):
                    text_list.append(scroll_list[i])
            text = ''.join([(x+'\n') for x in text_list])
            text = re.sub(r'\x1b.*m', '', text)
            pager(text)
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

    async def display_post(self, post) :
        global imgwidth, imgwidthcrunch
        show = True
        if not(self.atprotoMode):
            account = post['account']
            displayname = account['display_name']
            handle = account['acct']
            created_at = post['created_at']
            content = post['content']
        else:
            account = post.author
            displayname = account.display_name
            handle = account.handle
            created_at = post.indexed_at
            content = post.record.text
        post_text = [
            textwrap.fill(displayname + ' | ' + handle, self.get_terminal_size()[0]),
            textwrap.fill('posted on ' + str(created_at), self.get_terminal_size()[0])
            ]
        self.telprnt(displayname + ' | ' + handle)
        self.telprnt('posted on ' + str(created_at))
        if not((not(self.atprotoMode) and post['url'] == None)):
            if not(self.atprotoMode):
                url = post['url']
            else:
                url = post.uri
            self.telprnt(url)
            post_text.append(textwrap.fill(url, self.get_terminal_size()[0]))
        if not(self.atprotoMode) and post['sensitive']: #TODO ATPROTO, not sure how to do this
            show = await self.yn_prompt('sensitive content labeled "' + post['spoiler_text'] + '", display? (y/n) ')
            post_text.append(textwrap.fill('sensitive content labeled "' + post['spoiler_text'], self.get_terminal_size()[0]))
        if (not(self.atprotoMode) and show and (post['reblog'] == None)) or (self.atprotoMode): #TODO ATPROTO, not sure how to know if something is a repost yet
            self.telprnt('')
            self.telprnt(textwrap.fill(self.strip_tags(content), self.get_terminal_size()[0], replace_whitespace=False))
            post_text.append('')
            post_text.append(textwrap.fill(self.strip_tags(content), self.get_terminal_size()[0]))
        if not(self.atprotoMode) and show and (len(post['media_attachments']) != 0): #TODO ATPROTO, just want to get posts working before I dive into attachments.
            self.telprnt('')
            self.telprnt('Post has media')
            post_text.append('')
            post_text.append('Post has media')
            if post['sensitive']:
                self.telprnt('Media for this post marked as sensitive')
                post_text.append(textwrap.fill('Media for this post marked as sensitive', self.get_terminal_size()[0]))
            for attachment in post['media_attachments']:
                self.telprnt('')
                self.telprnt(attachment['url'])
                self.telprnt(textwrap.fill(str(attachment['description']), self.get_terminal_size()[0]))
                post_text.append('')
                post_text.append(textwrap.fill(attachment['url'], self.get_terminal_size()[0]))
                post_text.append(textwrap.fill(str(attachment['description']), self.get_terminal_size()[0]))

                if self.images and await self.yn_prompt('show image? (y/n) '):
                    try:
                        imgname = attachment['url'].split('/')[-1]
                        if imgname == 'original':
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
        if not(self.atprotoMode) and show and (post['poll'] != None): #TODO ATPROTO, same as with attachments I just want to get basic posting working
            self.telprnt('\nPost has poll.')
            post_text.append('')
            post_text.append('Post has poll')
            votetotal = post['poll']['votes_count']
            voted = post['poll']['voted']
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
            if voted:
                self.telprnt("You've voted in this poll.")
                post_text.append("You've voted in this poll.")
            if post['poll']['expired']:
                self.telprnt("Poll is closed.")
                post_text.append("Poll is closed.")
            else:
                self.telprnt("Poll closes at " + str(post['poll']['expires_at']))
                post_text.append("Poll closes at " + str(post['poll']['expires_at']))
        if not(self.atprotoMode) and (post['reblog']): #TODO ATPROTO not entirely sure how reposts work in ATPROTO
                self.telprnt('')
                self.telprnt('Reposted :')
                post_text.append('')
                post_text.append('Reposted:')
                post_text += await self.display_post(post['reblog'])
        #telprnt('')
        post_text_final = []
        for i in range(len(post_text)):
            post_text_final += post_text[i].split('\n')
        return(post_text_final)

    def display_pfp(self, account, request='avatar_static', width = 10, deco = True):
        if not(self.atprotoMode):
            urllib.request.urlretrieve(account[request], './mastopy/resources/pfps/' + str(account['id']) + request +'.png')
            reqpath = './mastopy/resources/pfps/' + str(account['id']) + request +'.png'
        else:
            if request == 'avatar_static':
                urllib.request.urlretrieve(account.avatar, './mastopy/resources/pfps/' + account.handle + request +'.png')
            elif request == 'banner_static' or request == 'header_static':
                urllib.request.urlretrieve(account.banner, './mastopy/resources/pfps/' + account.handle + request +'.png')
            reqpath = './mastopy/resources/pfps/' + account.handle + request +'.png'
        pfp = self.print_img(reqpath, wid=width, ret=True, printType=self.imgcolour).split('\n')
        out = ''
        if deco:
            out += ' '
            for i in range(len(self.escape_ansi(pfp[1]))):
                out += '-'
        for line in pfp[1:-1]:
            if len(self.escape_ansi(line)) > 0:
                #telprnt(len(escape_ansi(line)), [line], [escape_ansi(line)])
                if deco:
                    out += '\n|' + line + '\033[0m|'
                else:
                    out += '\n' + line + '\033[0m'
        out += '\n '
        if deco:
            for i in range(len(self.escape_ansi(pfp[1]))):
                out += '-'
        out += '\033[0m'
        return out

    def display_account(self, account, relationship=None, show_pfp = True, show_banner = True):
        self.telprnt('')
        if relationship == None:
            if not(self.atprotoMode):
                relation = self.mastodon.account_relationships(account['id'])[0]
            else:
                relation = account.viewer
        else:
            relation = relationship
        if not(self.atprotoMode):
            following = relation['following']
            created_at = account['created_at']
            bio = account['note']
        else:
            if relation.following == None:
                following = False
            else:
                following = True
            created_at = account.created_at
            bio = account.description
        wid = 10
        if show_pfp and self.images:
            hei = 5
            i = 0
            banner = []
            while len(banner) < hei:
                banner = (self.display_pfp(account, request='header_static', width=30+i, deco=False)).split('\n')[1:-1]
                wid = 41 + i
                i += 1
            pfp    = (self.display_pfp(account, request='avatar_static', deco=False)).split('\n')[1:-1]
            self.telprnt(' ', end='')
            for i in range(wid):
                self.telprnt('-', end='')
            for i in range(len(pfp)):
                self.telprnt('\n|' + pfp[i] + '\033[0m|' + banner[i] + '\033[0m|', end='')
            self.telprnt('\n ', end='')
            for i in range(wid):
                self.telprnt('-', end='')
            self.telprnt('')
        
        if not(self.atprotoMode):
            self.telprnt(account['display_name'] + ' | ' + account['acct'])
            self.telprnt(account['url'])
        else:
            self.telprnt(account.display_name + ' | ' + account.handle)
            #self.telprnt(account['url']) #TODO ATPROTO
        if (not(self.atprotoMode) and account['bot']): #not a feature in the atproto as far as I can tell?
            self.telprnt('Automated Account')
        self.telprnt('Created: ', created_at)
        if (following):
            self.telprnt('Following')
        self.hr(length=wid + 2)
        self.telprnt(self.strip_tags(bio))
        self.hr(length=wid + 2)
        if not(self.atprotoMode): #TODO ATPROTO
            for field in account['fields']: #is there something that's equivilant to this in atproto
                self.telprnt(field['name'] + ' | ', end='')
                if not(field['verified_at'] == None):
                    self.telprnt('\033[32m', end='')
                self.telprnt(self.strip_tags(str(field['value'])) + '\033[0m')
        self.telprnt('')

    getinput_key = []
    async def get_input(self) :
        global telnet
        #TODO: catch specific error
        if telnet:
            key = str(await self.tnread.read(1)).lower()
            if key in ['\n', '\r', '']:
                key = "enter"
            return key
        else:
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

            '''
            #telinput solution, worse than sshkeyboard but actually works
            key = (await self.telinput()).lower()
            if key == "":
                key = "enter"
            return key
            '''


            '''
            #sshkeyboard solution, doesn't work because async
            try:
                self.getinput_key = []
                def press(getinput_key, key) :
                    getinput_key.append(key)
                    stop_listening()
                await listen_keyboard(on_press=press) #augh you're KILLIN me shhkeyboard
                if len(self.getinput_key) == 0 :
                    self.getinput_key.append('esc')
                return(self.getinput_key[0])
            except:
                key = (await self.telinput()).lower()
                if key == "":
                    key = "enter"
                return key
            '''
            

    async def yn_prompt(self, prompt) :
        key = await self.do_menu(['y','n'], prompt)
        self.telprnt(key)
        if key == 'y':
            return True
        else:
            return False

    async def do_menu(self, valid_keys, prompt='') : 
        self.telprnt('', end='\033[F\n' + prompt)
        while True :
            key = await self.get_input()
            if (key in valid_keys):
                return key

    async def account_menu(self, account):
        relationship = None
        if not(self.atprotoMode):
            relationship = self.mastodon.account_relationships(account['id'])[0] #TODO ATPROTO
        else:
            account = self.mastodon.get_profile(account.did)
            relationship = account.viewer
        self.display_account(account, relationship)
        self.hr(minus=7)
        prompt = ''
        if not(self.atprotoMode):
            following = relationship['following']
        else:
            following = account.viewer.following
        if following:
            prompt += 'Un<F>ollow, '
        else:
            if not(self.atprotoMode) and account['locked']:
                prompt += 'Send <F>ollow Request, '
            else:
                prompt += '<F>ollow, '
        prompt += '<V>iew Posts : '
        key = await self.do_menu(['enter', 'f', 'v'], prompt)
        
        if key == 'f':
            if following:
                self.telprnt('Unfollow')
                if await self.yn_prompt('Are you sure? (y/n) : '):
                    if not(self.atprotoMode):
                        self.mastodon.account_unfollow(account['id'])
                    else:
                        self.mastodon.unfollow(following)
            else:
                if not(self.atprotoMode) and account['locked']:
                    self.telprnt('Send Follow Request')
                else:
                    self.telprnt('Follow')
                if await self.yn_prompt('Are you sure? (y/n)'):
                    if not(self.atprotoMode):
                        self.mastodon.account_follow(account['id'])
                    else:
                        self.mastodon.follow(account.did)
        elif key == 'v':
            self.telprnt('View Posts')
            if not(self.atprotoMode):
                posts = self.mastodon.account_statuses(account['id'], limit=int(await self.telinput("how many posts to load? ")))
            else:
                posts = await self.bskyFeed2post(self.mastodon.get_author_feed(account.did, limit=int(await self.telinput("how many posts to load? "))).feed)
            return posts
        return None
        

    async def display_posts(self, posts_in, section_name='') :
        global quotes, scrolling
        post_num = 0
        posts = posts_in
        post_archive = []
        post_num_archive = []
        show_post = True
        while True :
            self.telprnt('\n\n',end='')
            if show_post:
                post_text_list = await self.display_post(posts[post_num])
            show_post = True
            self.hr(minus=7)
            keys = ['s', '?', 'v']
            
            prompt=''
            if section_name != '':
                prompt += (section_name + ' | ')
            prompt += str(post_num + 1) + '/' + str(len(posts)) + ' | '
            prompt += '<I>nteract, '
            keys += 'i'
            if (post_num != 0):
                prompt += '<P>revious, '
                keys += 'p'
            if (post_num < len(posts)-1):
                prompt += '<N>ext, '
                keys += 'n'
            prompt += '<S>top, <V>iew, <?>help : '
            key = await self.do_menu(keys, prompt)
            
            if key == 's' : 
                self.telprnt('Stop')
                break
            elif key == '?' :
                self.telprnt(posts[post_num])
                await self.get_input()
            elif key == 'n' :
                self.telprnt('Next')
                post_num += 1
            elif key == 'p' :
                self.telprnt('Previous')
                post_num -= 1
            elif key == 'v' :
                self.telprnt('View')
                
                prompt = ''
                keys = ['enter', 'a', 'f']
                if scrolling and self.get_post_size(post_text_list) > self.get_terminal_size()[1]:
                    prompt += '<P>ost, '
                    keys += 'p'
                if not(self.atprotoMode):
                    if (posts[post_num]['in_reply_to_id'] != None) or (posts[post_num]['reblog'] != None and posts[post_num]['reblog']['in_reply_to_id'] != None):
                        prompt += '<T>hread, '
                        keys += 't'
                    if (posts[post_num]['replies_count'] > 0)      or (posts[post_num]['reblog'] != None and posts[post_num]['reblog']['replies_count'] > 0):
                        if posts[post_num]['reblog'] != None:
                            prompt += '<R>eplies ({replies}), '.format(replies = str(posts[post_num]['reblog']['replies_count']))
                        else:
                            prompt += '<R>eplies ({replies}), '.format(replies = str(posts[post_num]['replies_count']))
                        keys += 'r'
                else:
                    try: #wrap this in a try/except because it sends a network request
                        a = self.mastodon.get_post_thread(posts[post_num].uri, 0).thread
                        if a.parent != None:
                            prompt += '<T>hread, '
                            keys += 't'
                    except:
                        raise
                    if (posts[post_num].reply_count > 0):
                        prompt += '<R>eplies ({replies}), '.format(replies = str(posts[post_num].reply_count))
                        keys += 'r'
                if len(post_archive) > 0 :
                    prompt += '<B>ack, '
                    keys += 'b'
                if not(self.atprotoMode): #TODO ATPROTO : work on quote posts because they work differently than on mastodon
                    if quotes and self.strip_tags(posts[post_num]['content']).split('\n')[-1][:8] == 'RE: http':
                        prompt += '<Q>uoted Post, '
                        keys += 'q'
                prompt += '<A>ccount, Re<F>resh Post : '
                key = await self.do_menu(keys, prompt)
                
                if key == 'a' : #TODO ATPROTO
                    self.telprnt('View Account')
                    if not(self.atprotoMode):
                        account = posts[post_num]['account']
                    else:
                        account = posts[post_num].author
                    newposts = await self.account_menu(account)
                    if newposts != None:
                        post_archive.insert(0, posts)
                        post_num_archive.insert(0, post_num)
                        posts = newposts
                        post_num = 0
                elif key == 'p':
                    self.telprnt('View Post')
                    await self.scroll(post_text_list)
                    show_post = False
                elif key == 'b':
                    self.telprnt('Go Back')
                    posts = post_archive.pop(0)
                    post_num = post_num_archive.pop(0)
                elif key == 't' : 
                    self.telprnt('View Thread')
                    post_archive.insert(0, posts)
                    post_num_archive.insert(0, post_num)
                    if not(self.atprotoMode):
                        if posts[post_num]['reblog'] != None:
                            posts, post_num = self.get_replies(posts[post_num]['reblog'])
                        else:
                            posts, post_num = self.get_replies(posts[post_num])
                    else:
                        posts, post_num = self.get_replies(posts[post_num])
                    post_num = 0
                elif key == 'r' :
                    self.telprnt('View Replies')
                    post_archive.insert(0, posts)
                    post_num_archive.insert(0, post_num)
                    if not(self.atprotoMode):
                        if posts[post_num]['reblog'] != None:
                            posts, post_num = self.get_replies(posts[post_num]['reblog'])
                        else:
                            posts, post_num = self.get_replies(posts[post_num])
                    else:
                        posts, post_num = self.get_replies(posts[post_num])
                elif key == 'q' : #TODO ATPROTO
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
                elif key == 'f': #TODO ATPROTO
                    self.telprnt('Refresh Post')
                    try:
                        new_status = self.mastodon.status(posts[post_num]['id'])
                    except mastodonpy.MastodonNetworkError:
                        self.telprnt('Network Error, Couldn\'t refresh post.')
                        new_status = None
            elif key == 'i':
                self.telprnt('Interact')
                prompt = ''
                #prompt = '<L>ike, <R>epost, <B>ookmark :'
                valid_keys = ['enter', 'l', 'r','f']
                if not(self.atprotoMode):
                    favourited = posts[post_num]['favourited']
                    reblogged = posts[post_num]['reblogged']
                else:
                    if posts[post_num].viewer.like == None:
                        favourited = False
                    else: 
                        favourited = True
                    if posts[post_num].viewer.repost == None:
                        reblogged = False
                    else:
                        reblogged = True
                if favourited:
                        prompt += 'Un<L>ike, '
                else:
                    prompt += '<L>ike, '
                if reblogged:
                    prompt += 'Un<R>epost, '
                else:
                    prompt += '<R>epost, '
                if not(self.atprotoMode):
                    if posts[post_num]['bookmarked']: #TODO ATPROTO, see other comments on bookmarks
                        prompt += 'Un<B>ookmark, '
                    else:
                        prompt += '<B>ookmark, '
                    valid_keys.append('b')
                if not(self.atprotoMode) and posts[post_num]['poll'] != None: #TODO ATPROTO
                    if not(posts[post_num]['poll']['expired'] or posts[post_num]['poll']['voted']):
                        prompt += '<P>oll, '
                        valid_keys.append('p')
                prompt += ' Re<F>resh Post'
                if not(self.atprotoMode):
                    prompt += ', <C>omment : '
                    valid_keys.append('c')
                key = await self.do_menu(valid_keys, prompt)
                new_status = None
                if key == 'b':
                    if not(self.atprotoMode) and posts[post_num]['bookmarked']: #TODO ATPROTO, see other comments on bookmarks
                        self.telprnt('Remove Bookmark')
                        new_status = self.mastodon.status_unbookmark(posts[post_num]['id'])
                    else:
                        self.telprnt('Bookmark Post')
                        new_status = self.mastodon.status_bookmark(posts[post_num]['id'])
                elif key == 'p':
                    self.telprnt('Vote in Poll')
                    options = ['enter']
                    for i in range(len(posts[post_num]['poll']['options'])):
                        options.append(str(i + 1)) # might break things if you can make polls with more than 9 options but I don't think you can?
                        self.telprnt(str(i + 1) + '.) ', end='')
                        self.telprnt(posts[post_num]['poll']['options'][i]['title'])
                    key = await self.do_menu(options, '> ')
                    if key != 'enter':
                        self.telprnt(key)
                        new_status = posts[post_num]
                        pollresponse = self.mastodon.poll_vote(posts[post_num]['poll']['id'], (int(key) - 1))
                        #print(pollresponse) # for some reason this is always None as far as I can tell so as a quick fix, just refresh the page
                        #posts[post_num]['poll'] = pollresponse # don't do what the API says I should be able to do, instead 
                        try:
                            new_status = self.mastodon.status(posts[post_num]['id'])
                        except mastodonpy.MastodonNetworkError:
                            #print('Network Error, Couldn\'t refresh post.')
                            new_status = None
                    else:
                        self.telprnt('')
                elif key == 'l':
                    if favourited:
                        self.telprnt('Remove Like')
                        if not(self.atprotoMode):
                            new_status = self.mastodon.status_unfavourite(posts[post_num]['id'])
                        else:
                            self.mastodon.unlike(posts[post_num].viewer.like)
                            new_status = self.mastodon.get_posts([posts[post_num].uri]).posts[0]
                    else: 
                        self.telprnt('Like Post')
                        if not(self.atprotoMode):
                            new_status = self.mastodon.status_favourite(posts[post_num]['id'])
                        else:
                            self.mastodon.like(posts[post_num].uri, posts[post_num].cid)
                            new_status = self.mastodon.get_posts([posts[post_num].uri]).posts[0]
                elif key == 'r':
                    if reblogged:
                        self.telprnt('Remove Boost')
                        if not(self.atprotoMode):
                            self.mastodon.status_unreblog(posts[post_num]['id'])
                            new_status = self.mastodon.status(posts[post_num]['id'])
                        else:
                            self.mastodon.unrepost(posts[post_num].viewer.repost)
                            new_status = self.mastodon.get_posts([posts[post_num].uri]).posts[0]
                    else:
                        self.telprnt('Boost Post')
                        if not(self.atprotoMode):
                            self.mastodon.status_reblog(posts[post_num]['id'])
                            new_status = self.mastodon.status(posts[post_num]['id'])
                        else:
                            self.mastodon.repost(posts[post_num].uri, posts[post_num].cid)
                            new_status = self.mastodon.get_posts([posts[post_num].uri]).posts[0]
                elif key == 'f':
                    self.telprnt('Refresh Post')
                    try:
                        if not(self.atprotoMode):
                            new_status = self.mastodon.status(posts[post_num]['id'])
                        else:
                            new_status = self.mastodon.get_posts([posts[post_num].uri]).posts[0]
                    except mastodonpy.MastodonNetworkError:
                        self.telprnt('Network Error, Couldn\'t refresh post.')
                        new_status = None
                elif key == 'c': #TODO ATPROTO, not sure how to get a ReplyRef object??
                    self.telprnt('Comment')
                    await self.write_status(in_reply_to = posts[post_num])
                if not(new_status == None):
                    posts[post_num] = new_status

    async def write_status(self, in_reply_to = None):
        global telnet
        if telnet:
            self.telprnt('Entering message. Word wrap will give you')
            self.telprnt('soft linebreaks. Pressing the "enter" key')
            self.telprnt('will give you a hard linebreak and open  ')
            self.telprnt('the menu, from which you can press "c" to')
            self.telprnt('continue writing the message.            ')
            self.telprnt('press "enter" and then "s" when finished.\n')
        else:
            self.telprnt('Entering message. Word wrap will give you')
            self.telprnt('soft linebreaks. Pressing the "enter" key')
            self.telprnt('will give you a hard linebreak. Press')
            self.telprnt('"enter" twice when finished.\n')
        postList = []
        lastline = 'tmp'
        while lastline != '':
            lastline = (await self.telinput())
            if lastline != '':
                postList.append(lastline)
        post = ''.join(('\n' + line) for line in postList).lstrip('\n')
        cw_string = '   add content <W>arning\n'
        cw = None
        visibility = None
        in_menu = True
        while in_menu:
            key = await self.do_menu(['?','a','c','s','p','w','v'], '\nEntry command (? for options) -> ')
            if key == '?':
                self.telprnt('\n' +
                    'One of...\n' +
                    '   <A>bort\n' +
                    '   <C>ontinue\n' +
                    '   post <S>tatus\n' +
                    '   <P>rint formatted')
                if not(self.atprotoMode):
                    self.telprnt(
                        cw_string +
                        '   change <V>isibility\n')
            elif key == 'a':
                self.telprnt('Abort')
                if await self.yn_prompt('Are you sure? '):
                    in_menu = False
            elif key == 'c':
                self.telprnt('Continue')
                postList = [post]
                lastline = 'tmp'
                while lastline != '':
                    lastline = (await self.telinput())
                    if lastline != '':
                        postList.append(lastline)
                post = ''.join(('\n' + line) for line in postList).lstrip('\n')
            elif key == 's':
                self.telprnt('Post status')
                if in_reply_to == None:
                    if not(self.atprotoMode):
                        self.mastodon.status_post(post, visibility=visibility, spoiler_text=cw)
                    else:
                        self.mastodon.post(post)
                else:
                    if not(self.atprotoMode):
                        self.mastodon.status_reply(in_reply_to, post, visibility=visibility, spoiler_text=cw)
                    else:
                        self.telprnt("Replies currently don't work for the ATPROTO. Very sorry!")
                in_menu = False
            elif key == 'p':
                self.telprnt('Print formatted')
                self.telprnt(post)
            elif key == 'w':
                self.telprnt('Add CW')
                self.telprnt('Current CW is: ' + str(cw))
                cw = await self.telinput('Content warning (press enter for none) : ')
                if cw == '':
                    cw = None
                cw_string = '   change content <W>arning\n'
                self.telprnt('')
            elif key == 'v':
                self.telprnt('Change Visibility')
                self.telprnt('Current Visibility is: ', end='')
                if visibility == None:
                    self.telprnt('default')
                else:
                    self.telprnt(visibility)
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

    async def bskyLRR2post(self, ListRecordsResponse):
        outputlist = []
        for uri, post in ListRecordsResponse:
            #print(uri, post.text)
            id = [uri]
            outpost = self.mastodon.get_posts(id).posts
            outputlist += outpost
        return outputlist
    async def bskyFeed2post(self, feed):
        outputlist = []
        for post in feed:
            outputlist.append(post.post)
        return outputlist

    async def main_menu(self):
        self.hr(minus=7)
        #TODO ATPROTO : 
        #   "View by ID" should be "View by URI"
        self.telprnt('Timelines: <H>ome, <L>ocal, <F>ederated')
        self.telprnt('Posts:     <V>iew by ID, <B>ookmarks, <C>reate')
        self.telprnt('Search:    <S>earch, search by Hash<T>ag')
        self.telprnt('User:      <M>y Account')#, <N>otifications')
        self.telprnt('General:   <Q>uit')
        self.hr(minus=7)
        key = await self.do_menu(['h','l','f', 'v','b','c', 's','t', 'm', 'q'], '>')
        try:
            if key in ['h','l','f']:
                if key == 'h':
                    self.telprnt('Home timeline')
                    howmany = await self.telinput("how many posts to load? ")
                    if howmany.isdigit():
                        if not(self.atprotoMode):
                            posts = self.mastodon.timeline_home(limit=int(howmany))
                        else:
                            #the following comment gets YOUR posts
                            # posts = self.mastodon.app.bsky.feed.post.list(self.mastodon.me.did, limit=int(howmany)).records.items() #this should work?
                            # posts = await self.bskyLRR2post(posts)
                            posts = await self.bskyFeed2post(self.mastodon.get_timeline(limit=int(howmany)).feed)
                            #print(posts)
                        await self.display_posts(posts)
                    return True
                elif key =='l': #TODO ATPROTO, other timelines have no use as of yet
                    self.telprnt('Local timeline')
                    howmany = await self.telinput("how many posts to load? ")
                    if howmany.isdigit():
                        posts = self.mastodon.timeline_local(limit=int(howmany))
                        await self.display_posts(posts)
                    return True
                elif key =='f': #TODO ATPROTO, other timelines have no use as of yet
                    print('Federated timeline')
                    howmany = await self.telinput("how many posts to load? ")
                    if howmany.isdigit():
                        posts = self.mastodon.timeline_public(limit=int(howmany))
                        await self.display_posts(posts)
                    return True
            elif key in ['v','b','c']:
                if key == 'v':
                    self.telprnt('View post ID: ',end='')
                    id = await self.telinput('')
                    #id = 'at://did:plc:kvwvcn5iqfooopmyzvb4qzba/app.bsky.feed.post/3k2yihcrp6f2c'
                    if (id != ''):
                        if not(self.atprotoMode):
                            post = [self.mastodon.status(id)]
                        else:
                            id = [id]
                            post = self.mastodon.get_posts(id).posts
                        await self.display_posts(post)
                    return True
                elif key =='b':  #TODO ATPROTO, bsky doesn't have bookmarks
                    self.telprnt('Bookmarks')
                    howmany = await self.telinput("how many posts to load? ")
                    if howmany.isdigit():
                        posts = self.mastodon.bookmarks(limit=int(howmany))
                        await self.display_posts(posts)
                    return True
                elif key =='c':
                    self.telprnt('Post')
                    await self.write_status()
                    return True
            elif key in ['s','t']:
                if key == 's':  #TODO ATPROTO, learn how to use search
                    self.telprnt('Search: ',end='')
                    search_term = await self.telinput('')
                    if (search_term != ''):
                        posts = self.mastodon.search(search_term, result_type='statuses')
                        posts = posts['statuses']
                        if len(posts) > 0:
                            await self.display_posts(posts)
                        else:
                            self.telprnt('No Search Results')
                    return True
                elif key == 't':  #TODO ATPROTO, learn how to use search
                    self.telprnt('View posts by Hashtag: ',end='')
                    hashtag = await self.telinput('')
                    if (hashtag != ''):
                        howmany = await self.telinput("how many posts to load? ")
                        if howmany.isdigit():
                            posts = self.mastodon.timeline_hashtag(hashtag, limit=int(howmany))
                            await self.display_posts(posts)
                    return True
            elif key in ['m']:#,'n']:
                if key == 'm':
                    self.telprnt('My Account')
                    if not(self.atprotoMode):
                        account = self.mastodon.me()
                        await (account)
                    else:
                        account = self.mastodon.get_profile(self.mastodon.me.did)
                        self.display_account(account)
                    return True
            #    elif key == 'n':
            #        telprnt('Notifications')
            #        posts = mastodon.notifications(types='status')
            #        await display_posts(posts)
            #        return True
            elif key == 'q':
                self.telprnt('Quit')
                return False
        except mastodonpy.MastodonNetworkError:
            self.telprnt('Network Error, Exiting.')
            return False

    def get_replies(self, post):
        if not(self.atprotoMode):
            replies = []
            replies_tmp = self.mastodon.status_context(post['id'])
            thread = replies_tmp['ancestors']
            replies = replies_tmp['descendants']
            for i in range(len(replies) - 1, -1, -1):
                if replies[i]['in_reply_to_id'] != post['id']:
                    replies.pop(i)
            replies_full = []
            replies_full += thread
            post_num = len(replies_full)
            replies_full.append(post)
            replies_full += replies
        else:
            replies_tmp = self.mastodon.get_post_thread(post.uri)
            thread = replies_tmp.thread.parent
            replies = replies_tmp.thread.replies
            upthread = []
            while thread != None:
                upthread.append(thread.post)
                thread = thread.parent
            replies_full = list(reversed(upthread))
            post_num = len(replies_full)
            replies_full.append(replies_tmp.thread.post)
            for postList in replies:
                replies_full.append(postList.post)
        return replies_full, post_num
    
    def __init__(self, reader, writer):
        self.tnread = reader
        self.tnwrite = writer

    async def begin(self):
        global telnet, imgcolour, images, askimages, atprotoMode, askatproto
        name = 'default' #default name

        self.telprnt(logo)
        self.images = images
        self.imgcolour = imgcolour
        self.atprotoMode = atprotoMode

        if telnet:
            self.telprnt('Press your backspace key ', end='')
            self.backspace = await self.get_input()
            self.telprnt("")
        
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
        
        if askatproto:
            self.atprotoMode = await self.yn_prompt("AtProto account? ")
        self.mastodon = await self.usermenu()

        while True and not(self.mastodon == None):
            if not(await self.main_menu()):
                break
        if telnet:
            self.tnwrite.close()

logo = """\
.  .._. _____ _ ._  _ .  .
|\\/||_|/__ | / \\| \\/ \\|\\ |
|  || |__/ | \\_/|_/\\_/| \\|\n\
"""
globalid = 0
if telnet:
    async def shell(reader, writer):
        global globalid
        globalid += 1
        thisid = globalid
        print('connected', thisid)
        thisShell = mastopy(reader, writer)
        await thisShell.begin()
        print('disconnected', thisid)
    
    loop = asyncio.get_event_loop()
    coro = telnetlib3.create_server(port=6023, shell=shell, timeout=False)
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed()) 
else:
    thisShell = mastopy(None, None)
    loop = asyncio.get_event_loop()
    while True:
        if not(loop.run_until_complete(thisShell.begin())):
            break
