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
import re
import img2txt as image

##feature toggle
images = True
quotes = True

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
    s.feed(html.replace("<br>", "\n").replace("</p><p>", "\n\n"))
    return s.get_data()

def escape_ansi(line):
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', line)

def hr(char='-', minus=0, length=-1) :
    if length == -1:
        for i in range(os.get_terminal_size()[0]-minus):
            print(char, end='')
    else:
        for i in range(length):
            print(char, end='')
    print('')

def display_post(post) :
    show = True
    account = post['account']
    print(account['display_name'] + ' | ' + account['acct'])
    print('posted on',  post['created_at'])
    if not(post['url'] == None):
        print(post['url'])
    if post['sensitive']:
        show = yn_prompt('sensitive content labeled "' + post['spoiler_text'] + '", display? (y/n) ')
    if show and (post['reblog'] == None):
        print('')
        print(strip_tags(post['content']))
    if show and (len(post['media_attachments']) != 0):
        print('')
        print('Post has media')
        if post['sensitive']:
            print('Media for this post marked as sensitive')
        for attachment in post['media_attachments']:
            print('')
            print(attachment['url'])
            print(attachment['description'])
            if images and yn_prompt('show image? (y/n) '):
                try:
                    imgname = attachment['url'].split('/')[-1]
                    if imgname == 'original':
                        imgname = 'original.png' # just assume PNG idk
                    urllib.request.urlretrieve(attachment['url'], './mastopy/resources/images/' + str(post['id']) + '_' + imgname)
                    image.print_img('./mastopy/resources/images/' + str(post['id']) + '_' + imgname)
                except:
                    print('Something went wrong displaying the image.')
                print('\033[0m', end='')
    if show and (post['poll'] != None):
        print('\nPost has poll.')
    if (post['reblog']):
        print('')
        print('reposted :')
        display_post(post['reblog'])
    print('')

def display_pfp(account, request='avatar_static', width = 10, deco = True):
    urllib.request.urlretrieve(account[request], './mastopy/resources/pfps/' + str(account['id']) + request +'.png')
    pfp = image.print_img('./mastopy/resources/pfps/' + str(account['id']) +  request +'.png', wid=width, ret=True).split('\n')
    out = ''
    if deco:
        out += ' '
        for i in range(len(escape_ansi(pfp[1]))):
            out += '-'
    for line in pfp[1:-1]:
        if len(escape_ansi(line)) > 0:
            #print(len(escape_ansi(line)), [line], [escape_ansi(line)])
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
        print(' ', end='')
        for i in range(wid):
            print('-', end='')
        for i in range(len(pfp)):
            print('\n|' + pfp[i] + '\033[0m|' + banner[i] + '\033[0m|', end='')
        print('\n ', end='')
        for i in range(wid):
            print('-', end='')
        print('')
    print(account['display_name'] + ' | ' + account['acct'])
    print(account['url'])
    if account['bot']:
        print('Automated Account')
    print('Created: ', account['created_at'])
    if relation['following']:
        print('Following')
    hr(length=wid + 2)
    print(strip_tags(account['note']))
    hr(length=wid + 2)
    for field in account['fields']:
        print(field['name'] + ' | ', end='')
        if not(field['verified_at'] == None):
            print('\033[32m', end='')
        print(strip_tags(str(field['value'])) + '\033[0m')
    print('')

get_input_key = []
def get_input() :
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

def yn_prompt(prompt) :
    key = do_menu(['y','n'], prompt)
    print(key)
    if key == 'y':
        return True
    else:
        return False

def do_menu(valid_keys, prompt='') : 
    print('', end='\033[F\n' + prompt)
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
            print('Unfollow')
            if yn_prompt('Are you sure? (y/n) : '):
                mastodon.account_unfollow(account['id'])
        else:
            if account['locked']:
                print('Send Follow Request')
                if yn_prompt('Are you sure? (y/n)'):
                    mastodon.account_follow(account['id'])
            else:
                print('Follow')
                if yn_prompt('Are you sure? (y/n)'):
                    mastodon.account_follow(account['id'])
    elif key == 'v':
        print('View Posts')
        posts = mastodon.account_statuses(account['id'], limit=int(input("how many posts to load? ")))
        return posts
    return None
    

def display_posts(posts_in, section_name='') :
    post_num = 0
    posts = posts_in
    post_archive = []
    post_num_archive = []
    while True :
        print('\n\n',end='')
        display_post(posts[post_num])
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
            print('Stop')
            break
        elif key == '?' :
            print(posts[post_num])
            print(strip_tags(posts[post_num]['content']).split('\n')[-1])
            get_input()
        elif key == 'n' :
            print('Next')
            post_num += 1
        elif key == 'p' :
            print('Previous')
            post_num -= 1
        elif key == 'v' :
            print('View')
            
            prompt = ''
            keys = ['enter', 'a']
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
            prompt += '<A>ccount : '
            key = do_menu(keys, prompt)
            
            if key == 'a' :
                print('View Account')
                account = posts[post_num]['account']
                newposts = account_menu(account)
                if newposts != None:
                    post_archive.insert(0, posts)
                    post_num_archive.insert(0, post_num)
                    posts = newposts
                    post_num = 0
            elif key == 'b':
                print('Go Back')
                posts = post_archive.pop(0)
                post_num = post_num_archive.pop(0)
            elif key == 't' :
                print('View Thread')
                post_archive.insert(0, posts)
                post_num_archive.insert(0, post_num)
                if posts[post_num]['reblog'] != None:
                    posts = get_thread(posts[post_num]['reblog'])
                else:
                    posts = get_thread(posts[post_num])
                post_num = 0
            elif key == 'r' :
                print('View Replies')
                post_archive.insert(0, posts)
                post_num_archive.insert(0, post_num)
                if posts[post_num]['reblog'] != None:
                    posts, post_num = get_replies(posts[post_num]['reblog'])
                else:
                    posts, post_num = get_replies(posts[post_num])
            elif key == 'q' :
                print('View Quoted Post')
                quotedURL = strip_tags(posts[post_num]['content']).split('\n')[-1].split('RE: ')[1]
                newposts = mastodon.search(quotedURL, result_type='statuses')
                newposts = newposts['statuses']
                if len(posts) > 0:
                    post_archive.insert(0, posts)
                    post_num_archive.insert(0, post_num)
                    posts = newposts
                    post_num = 0
                else:
                    print('Quoted Post Not Found')
        elif key == 'i':
            print('Interact')
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
            prompt += ' Re<F>resh Post : '
            key = do_menu(['enter', 'l', 'r', 'b', 'f'], prompt)
            new_status = None
            if key == 'b':
                if posts[post_num]['bookmarked']:
                    print('Remove Bookmark')
                    new_status = mastodon.status_unbookmark(posts[post_num]['id'])
                else:
                    print('Bookmark Post')
                    new_status = mastodon.status_bookmark(posts[post_num]['id'])
            elif key == 'l':
                if posts[post_num]['favourited']:
                    print('Remove Like')
                    new_status = mastodon.status_unfavourite(posts[post_num]['id'])
                else:
                    print('Like Post')
                    new_status = mastodon.status_favourite(posts[post_num]['id'])
            elif key == 'r':
                if posts[post_num]['reblogged']:
                    print('Remove Boost')
                    mastodon.status_unreblog(posts[post_num]['id'])
                    new_status = mastodon.status(posts[post_num]['id'])
                else:
                    print('Boost Post')
                    mastodon.status_reblog(posts[post_num]['id'])
                    new_status = mastodon.status(posts[post_num]['id'])
            elif key == 'f':
                print('Refresh Post')
                try:
                    new_status = mastodon.status(posts[post_num]['id'])
                except mastodonpy.MastodonNetworkError:
                    print('Network Error, Couldn\'t refresh post.')
                    new_status = None
            if not(new_status == None):
                posts[post_num] = new_status

def main_menu():
    hr(minus=7)
    print('Timelines: <H>ome, <L>ocal, <F>ederated')
    print('Posts:     <V>iew by ID, <B>ookmarks')
    print('Search:    <S>earch, search by Hash<T>ag')
    print('User:      <M>y Account')#, <N>otifications')
    print('General:   <Q>uit')
    hr(minus=7)
    key = do_menu(['h','l','f', 'v','b', 's','t', 'm', 'q'], '>')
    try:
        if key in ['h','l','f']:
            if key == 'h':
                print('Home timeline')
                posts = mastodon.timeline_home(limit=int(input("how many posts to load? ")))
                display_posts(posts)
                return True
            elif key =='l':
                print('Local timeline')
                posts = mastodon.timeline_local(limit=int(input("how many posts to load? ")))
                display_posts(posts)
                return True
            elif key =='f':
                print('Federated timeline')
                posts = mastodon.timeline_public(limit=int(input("how many posts to load? ")))
                display_posts(posts)
                return True
        elif key in ['v','b']:
            if key == 'v':
                print('View post ID: ',end='')
                id = input('')
                if (id != ''):
                    post = [mastodon.status(id)]
                    display_posts(post)
                return True
            elif key =='b':
                print('Bookmarks')
                posts = mastodon.bookmarks(limit=int(input("how many posts to load? ")))
                display_posts(posts)
                return True
        elif key in ['s','t']:
            if key == 's':
                print('Search: ',end='')
                search_term = input('')
                if (search_term != ''):
                    posts = mastodon.search(search_term, result_type='statuses')
                    posts = posts['statuses']
                    if len(posts) > 0:
                        display_posts(posts)
                    else:
                        print('No Search Results')
                return True
            elif key == 't':
                print('View posts by Hashtag: ',end='')
                hashtag = input('')
                if (hashtag != ''):
                    posts = mastodon.timeline_hashtag(hashtag, limit=int(input("how many posts to load? ")))
                    display_posts(posts)
                return True
        elif key in ['m']:#,'n']:
            if key == 'm':
                print('My Account')
                account = mastodon.me()
                display_account(account)
                return True
        #    elif key == 'n':
        #        print('Notifications')
        #        posts = mastodon.notifications(types='status')
        #        display_posts(posts)
        #        return True
        elif key == 'q':
            print('Quit')
            return False
    except mastodonpy.MastodonNetworkError:
        print('Network Error, Exiting.')
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
.  .._. _____ _ ._  _ .  .
|\\/||_|/__ | / \\| \\/ \\|\\ |
|  || |__/ | \\_/|_/\\_/| \\|
"""

print(logo)

name = 'default' #default name

if (not(exists('./mastopy/info/' + name + '_usercred.secret'))):
    if (not(exists('./mastopy/info/' + name + '_clientcred.secret'))):
        app_create(name)
    user_login(name)

mastodon = Mastodon(access_token = './mastopy/info/' + name + '_usercred.secret')

while True:
    if not(main_menu()):
        break
