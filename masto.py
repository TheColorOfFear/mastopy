from mastodon import Mastodon
import mastodon as mastodonpy
from getpass import getpass
from os.path import exists
import datetime
from dateutil.tz import tzutc
from io import StringIO
from html.parser import HTMLParser
import os
from sshkeyboard import listen_keyboard, stop_listening
from time import sleep
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
scroll_type = 'ansi' #if 'pager', uses pydoc pager. 'old' uses an older pager I wrote, and 'ansi' uses one made with ansi.
telnet = True

##img features
imgcolour = "256" #best : "colour", "256" for some terminals
imgwidth  = 60 #best: "original", "max" to stretch to terminal size, any int to specify width
imgwidthcrunch = "max" #used instead of imgwidth if imgwidth is larger than terminal width

##create dirs
if not os.path.exists('./mastopy/info/'):
    os.makedirs('./mastopy/info')
if not os.path.exists('./mastopy/resources/'):
    os.makedirs('./mastopy/resources')
if not os.path.exists('./mastopy/resources/images'):
    os.makedirs('./mastopy/resources/images')
if not os.path.exists('./mastopy/resources/pfps'):
    os.makedirs('./mastopy/resources/pfps')
    
def app_create(name) :
    Mastodon.create_app(
        'python client',
        api_base_url = input('Server URL (with https://) : '),
        to_file = './mastopy/info/' + name + '_clientcred.secret'
    )
def user_login(name) :
    mastodon = Mastodon(client_id = './mastopy/info/' + name + '_clientcred.secret')
    mastodon.log_in(
        input('Email Address : '),
        getpass('Password : '),
        to_file = './mastopy/info/' + name +'_usercred.secret'
    )

#function for telnet compatibility
def get_terminal_size():
    if telnet:
        return([80,25])
    return os.get_terminal_size()

#function for telnet compatibility
def telprnt(*args, end='\n'):
    global telnet, tnwrite
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
                tnwrite.write(realargs[i])
                tnwrite.write(realend)
            else:
                tnwrite.write(realargs[i])
                tnwrite.write(' ')
    else:
        for i in range(len(args)):
            if i == len(args) - 1:
                print(args[i], end=end)
            else:
                print(args[i], end=' ')

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

def strip_tags(html):
    parser = HTMLParser()
    s = MLStripper()
    s.feed(html.replace("<br>", "\n").replace("<br />", "\n").replace("</p><p>", "\n\n"))
    return s.get_data()

def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)

def hr(char='-', minus=0, length=-1) :
    if length == -1:
        for i in range(get_terminal_size()[0]-minus):
            telprnt(char, end='')
    else:
        for i in range(length):
            telprnt(char, end='')
    telprnt('')

def get_post_size(post_list):
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

def scroll(scroll_list):
    if scroll_type == 'pager':
        text_list = []
        for i in range(len(scroll_list)):
            if len(scroll_list[i]) == 0 or not(scroll_list[i][0] == '\x1b'):
                text_list.append(scroll_list[i])
        text = ''.join([(x+'\n') for x in text_list])
        text = re.sub(r'\x1b.*m', '', text)
        pager(text)
    elif scroll_type == 'ansi':
        fromTop = get_terminal_size()[1] - 1
        old_fromTop = 0
        key = ''
        while not(key in ['enter', 'esc', 's']):
            if fromTop > old_fromTop :
                for i in range(old_fromTop, fromTop):
                    telprnt(scroll_list[i])
                old_fromTop = fromTop
            elif fromTop < old_fromTop:
                telprnt('\033[;H', end='')
                for i in range((fromTop - (get_terminal_size()[1] - 1)), fromTop):
                    telprnt('\033[2K\r\033[0m', end='')
                    telprnt(scroll_list[i])
                old_fromTop = fromTop
                
            
            key = do_menu(['up','down', 'pageup','pagedown', 'enter','esc','s'], '<UP>/<DOWN> to scroll, <S> to stop :')
            telprnt('\033[2K\r\033[0m', end='')
            if key == 'up' and (fromTop > get_terminal_size()[1] - 1):
                fromTop -= 1
            elif key == 'down' and (fromTop < len(scroll_list)):
                fromTop += 1
            elif key == 'pageup':
                if (fromTop - (get_terminal_size()[1] - 2) > get_terminal_size()[1] - 1):
                    fromTop -= get_terminal_size()[1] - 2
                else:
                    fromTop = get_terminal_size()[1] - 1
            elif key == 'pagedown':
                if (fromTop + (get_terminal_size()[1] - 2) < len(scroll_list)):
                    fromTop += get_terminal_size()[1] - 2
                else:
                    fromTop = len(scroll_list)
    elif scroll_type == 'old':
        offset = 0
        scroll
        key = ''
        while not(key in ['enter', 'esc', 's']):
            for i in range(len(scroll_list) - offset):
                telprnt(scroll_list[i])
            key = do_menu(['up','down', 'pageup','pagedown', 'enter','esc','s'])
            if key == 'up' and ((len(scroll_list) - offset) >= get_terminal_size()[1]):
                offset += 1
            elif key == 'down' and offset > 0:
                offset -= 1
            elif key == 'pageup':
                if (len(scroll_list) - (offset + (get_terminal_size()[1] - 2))) >= get_terminal_size()[1]:
                    offset += get_terminal_size()[1] - 2
                else:
                    offset = len(scroll_list) - (get_terminal_size()[1] - 1)
            elif key == 'pagedown':
                if (offset - (get_terminal_size()[1] - 2)) > 0:
                    offset -= get_terminal_size()[1] - 2
                else:
                    offset = 0

def display_post(post) :
    show = True
    account = post['account']
    post_text = [
        textwrap.fill(account['display_name'] + ' | ' + account['acct'], get_terminal_size()[0]),
        textwrap.fill('posted on ' + str(post['created_at']), get_terminal_size()[0])
        ]
    telprnt(account['display_name'] + ' | ' + account['acct'])
    telprnt('posted on',  post['created_at'])
    if not(post['url'] == None):
        telprnt(post['url'])
        post_text.append(textwrap.fill(post['url'], get_terminal_size()[0]))
    if post['sensitive']:
        show = yn_prompt('sensitive content labeled "' + post['spoiler_text'] + '", display? (y/n) ')
        post_text.append(textwrap.fill('sensitive content labeled "' + post['spoiler_text'], get_terminal_size()[0]))
    if show and (post['reblog'] == None):
        telprnt('')
        telprnt(textwrap.fill(strip_tags(post['content']), get_terminal_size()[0], replace_whitespace=False))
        post_text.append('')
        post_text.append(textwrap.fill(strip_tags(post['content']), get_terminal_size()[0]))
    if show and (len(post['media_attachments']) != 0):
        telprnt('')
        telprnt('Post has media')
        post_text.append('')
        post_text.append('Post has media')
        if post['sensitive']:
            telprnt('Media for this post marked as sensitive')
            post_text.append(textwrap.fill('Media for this post marked as sensitive', get_terminal_size()[0]))
        for attachment in post['media_attachments']:
            telprnt('')
            telprnt(attachment['url'])
            telprnt(textwrap.fill(str(attachment['description']), get_terminal_size()[0]))
            post_text.append('')
            post_text.append(textwrap.fill(attachment['url'], get_terminal_size()[0]))
            post_text.append(textwrap.fill(str(attachment['description']), get_terminal_size()[0]))

            if images and yn_prompt('show image? (y/n) '):
                try:
                    imgname = attachment['url'].split('/')[-1]
                    if imgname == 'original':
                        imgname = 'original.png' # just assume PNG idk
                    urllib.request.urlretrieve(attachment['url'], './mastopy/resources/images/' + str(post['id']) + '_' + imgname)
                    if imgwidth > get_terminal_size()[0]:
                        img_text = image.print_img('./mastopy/resources/images/' + str(post['id']) + '_' + imgname, printType=imgcolour, wid=imgwidthcrunch, ret=True)
                    else:
                        img_text = image.print_img('./mastopy/resources/images/' + str(post['id']) + '_' + imgname, printType=imgcolour, wid=imgwidth, ret=True)
                    post_text += img_text.split('\n')[:-1]
                    telprnt(img_text)
                except:
                    telprnt('Something went wrong displaying the image.')
                telprnt('\033[0m', end='')
                post_text.append('\033[0m')
    if show and (post['poll'] != None):
        telprnt('\nPost has poll.')
        post_text.append('Post has poll')
    if (post['reblog']):
        telprnt('')
        telprnt('Reposted :')
        post_text.append('')
        post_text.append('Reposted:')
        post_text += display_post(post['reblog'])
    #telprnt('')
    post_text_final = []
    for i in range(len(post_text)):
        post_text_final += post_text[i].split('\n')
    return(post_text_final)

def display_pfp(account, request='avatar_static', width = 10, deco = True):
    urllib.request.urlretrieve(account[request], './mastopy/resources/pfps/' + str(account['id']) + request +'.png')
    pfp = image.print_img('./mastopy/resources/pfps/' + str(account['id']) +  request +'.png', wid=width, ret=True, printType=imgcolour).split('\n')
    out = ''
    if deco:
        out += ' '
        for i in range(len(escape_ansi(pfp[1]))):
            out += '-'
    for line in pfp[1:-1]:
        if len(escape_ansi(line)) > 0:
            #telprnt(len(escape_ansi(line)), [line], [escape_ansi(line)])
            if deco:
                out += '\n|' + line + '\033[0m|'
            else:
                out += '\n' + line + '\033[0m'
    out += '\n '
    if deco:
        for i in range(len(escape_ansi(pfp[1]))):
            out += '-'
    out += '\033[0m'
    return out

def display_account(account, relationship=None, show_pfp = True, show_banner = True):
    if relationship == None:
        relation = mastodon.account_relationships(account['id'])[0]
    else:
        relation = relationship
    wid = 10
    if show_pfp and images:
        hei = 5
        i = 0
        banner = []
        while len(banner) < hei:
            banner = display_pfp(account, request='header_static', width=30+i, deco=False).split('\n')[1:-1]
            wid = 41 + i
            i += 1
        pfp    = display_pfp(account, request='avatar_static', deco=False).split('\n')[1:-1]
        telprnt(' ', end='')
        for i in range(wid):
            telprnt('-', end='')
        for i in range(len(pfp)):
            telprnt('\n|' + pfp[i] + '\033[0m|' + banner[i] + '\033[0m|', end='')
        telprnt('\n ', end='')
        for i in range(wid):
            telprnt('-', end='')
        telprnt('')
    telprnt(account['display_name'] + ' | ' + account['acct'])
    telprnt(account['url'])
    if account['bot']:
        telprnt('Automated Account')
    telprnt('Created: ', account['created_at'])
    if relation['following']:
        telprnt('Following')
    hr(length=wid + 2)
    telprnt(strip_tags(account['note']))
    hr(length=wid + 2)
    for field in account['fields']:
        telprnt(field['name'] + ' | ', end='')
        if not(field['verified_at'] == None):
            telprnt('\033[32m', end='')
        telprnt(strip_tags(str(field['value'])) + '\033[0m')
    telprnt('')

get_input_key = []
def get_input() :
    #TODO: catch specific error
    if telnet:
        key = input().lower()
        if key == "":
            key = "enter"
        return key
    else:
        try:
            global get_input_key
            get_input_key = []
            def press(key) :
                global get_input_key
                get_input_key.append(key)
                stop_listening()
            listen_keyboard(on_press=press)
            if len(get_input_key) == 0 :
                get_input_key.append('esc')
            return(get_input_key[0])
        except:
            key = input().lower()
            if key == "":
                key = "enter"
            return key

def yn_prompt(prompt) :
    key = do_menu(['y','n'], prompt)
    telprnt(key)
    if key == 'y':
        return True
    else:
        return False

def do_menu(valid_keys, prompt='') : 
    telprnt('', end='\033[F\n' + prompt)
    while True :
        key = get_input()
        if (key in valid_keys):
            return key

def account_menu(account):
    relationship = mastodon.account_relationships(account['id'])[0]
    display_account(account, relationship)
    hr(minus=7)
    prompt = ''
    if relationship['following']:
        prompt += 'Un<F>ollow, '
    else:
        if account['locked']:
            prompt += 'Send <F>ollow Request, '
        else:
            prompt += '<F>ollow, '
    prompt += '<V>iew Posts : '
    key = do_menu(['enter', 'f', 'v'], prompt)
    
    if key == 'f':
        if relationship['following']:
            telprnt('Unfollow')
            if yn_prompt('Are you sure? (y/n) : '):
                mastodon.account_unfollow(account['id'])
        else:
            if account['locked']:
                telprnt('Send Follow Request')
                if yn_prompt('Are you sure? (y/n)'):
                    mastodon.account_follow(account['id'])
            else:
                telprnt('Follow')
                if yn_prompt('Are you sure? (y/n)'):
                    mastodon.account_follow(account['id'])
    elif key == 'v':
        telprnt('View Posts')
        posts = mastodon.account_statuses(account['id'], limit=int(input("how many posts to load? ")))
        return posts
    return None
    

def display_posts(posts_in, section_name='') :
    post_num = 0
    posts = posts_in
    post_archive = []
    post_num_archive = []
    show_post = True
    while True :
        telprnt('\n\n',end='')
        if show_post:
            post_text_list = display_post(posts[post_num])
        show_post = True
        hr(minus=7)
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
        key = do_menu(keys, prompt)
        
        if key == 's' : 
            telprnt('Stop')
            break
        elif key == '?' :
            telprnt(posts[post_num])
            telprnt(strip_tags(posts[post_num]['content']).split('\n')[-1])
            get_input()
        elif key == 'n' :
            telprnt('Next')
            post_num += 1
        elif key == 'p' :
            telprnt('Previous')
            post_num -= 1
        elif key == 'v' :
            telprnt('View')
            
            prompt = ''
            keys = ['enter', 'a', 'f']
            if scrolling and get_post_size(post_text_list) > get_terminal_size()[1]:
                prompt += '<P>ost, '
                keys += 'p'
            if (posts[post_num]['in_reply_to_id'] != None) or (posts[post_num]['reblog'] != None and posts[post_num]['reblog']['in_reply_to_id'] != None):
                prompt += '<T>hread, '
                keys += 't'
            if (posts[post_num]['replies_count'] > 0)      or (posts[post_num]['reblog'] != None and posts[post_num]['reblog']['replies_count'] > 0):
                if posts[post_num]['reblog'] != None:
                    prompt += '<R>eplies ({replies}), '.format(replies = str(posts[post_num]['reblog']['replies_count']))
                else:
                    prompt += '<R>eplies ({replies}), '.format(replies = str(posts[post_num]['replies_count']))
                keys += 'r'
            if len(post_archive) > 0 :
                prompt += '<B>ack, '
                keys += 'b'
            if quotes and strip_tags(posts[post_num]['content']).split('\n')[-1][:8] == 'RE: http':
                prompt += '<Q>uoted Post, '
                keys += 'q'
            prompt += '<A>ccount, Re<F>resh Post : '
            key = do_menu(keys, prompt)
            
            if key == 'a' :
                telprnt('View Account')
                account = posts[post_num]['account']
                newposts = account_menu(account)
                if newposts != None:
                    post_archive.insert(0, posts)
                    post_num_archive.insert(0, post_num)
                    posts = newposts
                    post_num = 0
            elif key == 'p':
                telprnt('View Post')
                scroll(post_text_list)
                show_post = False
            elif key == 'b':
                telprnt('Go Back')
                posts = post_archive.pop(0)
                post_num = post_num_archive.pop(0)
            elif key == 't' :
                telprnt('View Thread')
                post_archive.insert(0, posts)
                post_num_archive.insert(0, post_num)
                if posts[post_num]['reblog'] != None:
                    posts = get_thread(posts[post_num]['reblog'])
                else:
                    posts = get_thread(posts[post_num])
                post_num = 0
            elif key == 'r' :
                telprnt('View Replies')
                post_archive.insert(0, posts)
                post_num_archive.insert(0, post_num)
                if posts[post_num]['reblog'] != None:
                    posts, post_num = get_replies(posts[post_num]['reblog'])
                else:
                    posts, post_num = get_replies(posts[post_num])
            elif key == 'q' :
                telprnt('View Quoted Post')
                quotedURL = strip_tags(posts[post_num]['content']).split('\n')[-1].split('RE: ')[1]
                newposts = mastodon.search(quotedURL, result_type='statuses')
                newposts = newposts['statuses']
                if len(posts) > 0:
                    post_archive.insert(0, posts)
                    post_num_archive.insert(0, post_num)
                    posts = newposts
                    post_num = 0
                else:
                    telprnt('Quoted Post Not Found')
            elif key == 'f':
                telprnt('Refresh Post')
                try:
                    new_status = mastodon.status(posts[post_num]['id'])
                except mastodonpy.MastodonNetworkError:
                    telprnt('Network Error, Couldn\'t refresh post.')
                    new_status = None
        elif key == 'i':
            telprnt('Interact')
            prompt = ''
            #prompt = '<L>ike, <R>epost, <B>ookmark :'
            if posts[post_num]['favourited']:
                prompt += 'Un<L>ike, '
            else:
                prompt += '<L>ike, '
            if posts[post_num]['reblogged']:
                prompt += 'Un<R>epost, '
            else:
                prompt += '<R>epost, '
            if posts[post_num]['bookmarked']:
                prompt += 'Un<B>ookmark, '
            else:
                prompt += '<B>ookmark, '
            prompt += ' Re<F>resh Post, <C>omment : '
            key = do_menu(['enter', 'l', 'r', 'b', 'f', 'c'], prompt)
            new_status = None
            if key == 'b':
                if posts[post_num]['bookmarked']:
                    telprnt('Remove Bookmark')
                    new_status = mastodon.status_unbookmark(posts[post_num]['id'])
                else:
                    telprnt('Bookmark Post')
                    new_status = mastodon.status_bookmark(posts[post_num]['id'])
            elif key == 'l':
                if posts[post_num]['favourited']:
                    telprnt('Remove Like')
                    new_status = mastodon.status_unfavourite(posts[post_num]['id'])
                else:
                    telprnt('Like Post')
                    new_status = mastodon.status_favourite(posts[post_num]['id'])
            elif key == 'r':
                if posts[post_num]['reblogged']:
                    telprnt('Remove Boost')
                    mastodon.status_unreblog(posts[post_num]['id'])
                    new_status = mastodon.status(posts[post_num]['id'])
                else:
                    telprnt('Boost Post')
                    mastodon.status_reblog(posts[post_num]['id'])
                    new_status = mastodon.status(posts[post_num]['id'])
            elif key == 'f':
                telprnt('Refresh Post')
                try:
                    new_status = mastodon.status(posts[post_num]['id'])
                except mastodonpy.MastodonNetworkError:
                    telprnt('Network Error, Couldn\'t refresh post.')
                    new_status = None
            elif key == 'c':
                telprnt('Comment')
                write_status(in_reply_to = posts[post_num])
            if not(new_status == None):
                posts[post_num] = new_status

def write_status(in_reply_to = None):
    telprnt('Entering message. Word wrap will give you')
    telprnt('soft linebreaks. Pressing the "enter" key')
    telprnt('will give you a hard linebreak. Press')
    telprnt('"enter" twice when finished.\n')
    postList = []
    lastline = 'tmp'
    while lastline != '':
        lastline = input()
        if lastline != '':
            postList.append(lastline)
    post = ''.join(('\n' + line) for line in postList).lstrip('\n')
    cw_string = '   add content <W>arning\n'
    cw = None
    visibility = None
    in_menu = True
    while in_menu:
        key = do_menu(['?','a','c','s','p','w','v'], 'Entry command (? for options) -> ')
        if key == '?':
            telprnt('\n' +
                  'One of...\n' +
                  '   <A>bort\n' +
                  '   <C>ontinue\n' +
                  '   post <S>tatus\n' +
                  '   <P>rint formatted\n' +
                  cw_string +
                  '   change <V>isibility\n')
        elif key == 'a':
            telprnt('Abort')
            if yn_prompt('Are you sure? '):
                in_menu = False
        elif key == 'c':
            telprnt('Continue')
            postList = [post]
            lastline = 'tmp'
            while lastline != '':
                lastline = input()
                if lastline != '':
                    postList.append(lastline)
            post = ''.join(('\n' + line) for line in postList).lstrip('\n')
        elif key == 's':
            telprnt('Post status')
            if in_reply_to == None:
                mastodon.status_post(post, visibility=visibility, spoiler_text=cw)
            else:
                mastodon.status_reply(in_reply_to, post, visibility=visibility, spoiler_text=cw)
            in_menu = False
        elif key == 'p':
            telprnt('Print formatted')
            telprnt(post)
        elif key == 'w':
            telprnt('Add CW')
            telprnt('Current CW is: ' + str(cw))
            cw = input('Content warning (press enter for none) : ')
            if cw == '':
                cw = None
            cw_string = '   change content <W>arning\n'
            telprnt('')
        elif key == 'v':
            telprnt('Change Visibility')
            telprnt('Current Visibility is: ', end='')
            if visibility == None:
                telprnt('default')
            else:
                telprnt(visibility)
            telprnt('Change to:\n  <1> Default\n  <2> Public\n  <3> Unlisted\n  <4> Private\n  <5> Direct')
            key = do_menu(['1','2','3','4','5'],'> ')
            telprnt(key)
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

def main_menu():
    hr(minus=7)
    telprnt('Timelines: <H>ome, <L>ocal, <F>ederated')
    telprnt('Posts:     <V>iew by ID, <B>ookmarks, <C>reate')
    telprnt('Search:    <S>earch, search by Hash<T>ag')
    telprnt('User:      <M>y Account')#, <N>otifications')
    telprnt('General:   <Q>uit')
    hr(minus=7)
    key = do_menu(['h','l','f', 'v','b','c', 's','t', 'm', 'q'], '>')
    try:
        if key in ['h','l','f']:
            if key == 'h':
                telprnt('Home timeline')
                posts = mastodon.timeline_home(limit=int(input("how many posts to load? ")))
                display_posts(posts)
                return True
            elif key =='l':
                telprnt('Local timeline')
                posts = mastodon.timeline_local(limit=int(input("how many posts to load? ")))
                display_posts(posts)
                return True
            elif key =='f':
                telprnt('Federated timeline')
                posts = mastodon.timeline_public(limit=int(input("how many posts to load? ")))
                display_posts(posts)
                return True
        elif key in ['v','b','c']:
            if key == 'v':
                telprnt('View post ID: ',end='')
                id = input('')
                if (id != ''):
                    post = [mastodon.status(id)]
                    display_posts(post)
                return True
            elif key =='b':
                telprnt('Bookmarks')
                posts = mastodon.bookmarks(limit=int(input("how many posts to load? ")))
                display_posts(posts)
                return True
            elif key =='c':
                telprnt('Post')
                write_status()
                return True
        elif key in ['s','t']:
            if key == 's':
                telprnt('Search: ',end='')
                search_term = input('')
                if (search_term != ''):
                    posts = mastodon.search(search_term, result_type='statuses')
                    posts = posts['statuses']
                    if len(posts) > 0:
                        display_posts(posts)
                    else:
                        telprnt('No Search Results')
                return True
            elif key == 't':
                telprnt('View posts by Hashtag: ',end='')
                hashtag = input('')
                if (hashtag != ''):
                    posts = mastodon.timeline_hashtag(hashtag, limit=int(input("how many posts to load? ")))
                    display_posts(posts)
                return True
        elif key in ['m']:#,'n']:
            if key == 'm':
                telprnt('My Account')
                account = mastodon.me()
                display_account(account)
                return True
        #    elif key == 'n':
        #        telprnt('Notifications')
        #        posts = mastodon.notifications(types='status')
        #        display_posts(posts)
        #        return True
        elif key == 'q':
            telprnt('Quit')
            return False
    except mastodonpy.MastodonNetworkError:
        telprnt('Network Error, Exiting.')
        return False

def get_thread(post):
    thread = []
    #this_post = post
    #while (this_post['in_reply_to_id'] != None):
    #    thread.insert(0,this_post)
    #    this_post = mastodon.status(this_post['in_reply_to_id'])
    #thread.insert(0,this_post)
    thread_tmp = mastodon.status_context(post['id'])
    thread = thread_tmp['ancestors']
    thread.append(post)
    #thread += thread_tmp['descendants']
    return thread

def get_replies(post):
    replies = []
    replies_tmp = mastodon.status_context(post['id'])
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
    return replies_full, post_num

#logo = """\
#      _______
#    _/       \\_
#   /           \\
#  ]             [
#  ]             [
#  ]             [
#  ]           _/
#   \\  _______/
#   /_/
#  --
#"""
#logo = """\
#    ____ 
#___/ __ \\___.  . _  _____ _ __  _ .  .
#    /  \\/   |\\/|/_\\/__ | / \\| \\/ \\|\\ |
#___/\\__/ ___|  || |__/ | \\_/|_/\\_/| \\|
#   \\____/\
#"""
logo = """
.  .._. _____ _ ._  _ .  .\n|\\/||_|/__ | / \\| \\/ \\|\\ |\n|  || |__/ | \\_/|_/\\_/| \\|\n
"""
tnread = ''
tnwrite = ''
mastodon = ''
if telnet:
    async def shell(reader, writer):
        global tnread, tnwrite, mastodon
        tnread = reader
        tnwrite = writer
        name = 'default' #default name

        if (not(exists('./mastopy/info/' + name + '_usercred.secret'))):
            if (not(exists('./mastopy/info/' + name + '_clientcred.secret'))):
                app_create(name)
            user_login(name)

        mastodon = Mastodon(access_token = './mastopy/info/' + name + '_usercred.secret')

        while True:
            if not(main_menu()):
                break
    
    loop = asyncio.get_event_loop()
    coro = telnetlib3.create_server(port=6023, shell=shell)
    server = loop.run_until_complete(coro)
    loop.run_until_complete(server.wait_closed()) 
else:
    telprnt(logo)
    name = 'default' #default name

    if (not(exists('./mastopy/info/' + name + '_usercred.secret'))):
        if (not(exists('./mastopy/info/' + name + '_clientcred.secret'))):
            app_create(name)
        user_login(name)

    mastodon = Mastodon(access_token = './mastopy/info/' + name + '_usercred.secret')

    while True:
        if not(main_menu()):
            break
