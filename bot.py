import ast
import base64
import html
import json
import os
import re
import urllib.request

import logger
import requests
import urllib3.request
from bs4 import BeautifulSoup
from mutagen.mp4 import MP4, MP4Cover
from pySmartDL import SmartDL
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from pyDes import *
import logging
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)
###############################################################
welcome = "Hey {} I Am Saavn Downloader \n Please Send Me Saavn Link \n Report At  @aryanvikash "



###############################################################

#Bot config

bot_token ='864583141:AAH6pozC45wEZx6VTlGE7zNiL5IpKMGot4Y'
updater = Updater(bot_token, use_context=True)
dp = updater.dispatcher

# Pre Configurations
urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
unicode = str
raw_input = input


def addtags(filename, json_data, playlist_name):
    audio = MP4(filename)
    audio['\xa9nam'] = unicode(json_data['song'])
    audio['\xa9ART'] = unicode(json_data['primary_artists'])
    audio['\xa9alb'] = unicode(json_data['album'])
    audio['aART'] = unicode(json_data['singers'])
    audio['\xa9wrt'] = unicode(json_data['music'])
    audio['desc'] = unicode(json_data['starring'])
    audio['\xa9gen'] = unicode(playlist_name)
    # audio['cprt'] = track['copyright'].encode('utf-8')
    # audio['disk'] = [(1, 1)]
    # audio['trkn'] = [(int(track['track']), int(track['maxtracks']))]
    audio['\xa9day'] = unicode(json_data['year'])
    audio['cprt'] = unicode(json_data['label'])
    # if track['explicit']:
    #    audio['rtng'] = [(str(4))]
    cover_url = json_data['image'][:-11] + '500x500.jpg'
    fd = urllib.request.urlopen(cover_url)
    cover = MP4Cover(fd.read(), getattr(MP4Cover, 'FORMAT_PNG' if cover_url.endswith('png') else 'FORMAT_JPEG'))
    fd.close()
    audio['covr'] = [cover]
    audio.save()


def setProxy():
    base_url = 'http://h.saavncdn.com'
    proxy_ip = ''
    if ('http_proxy' in os.environ):
        proxy_ip = os.environ['http_proxy']
    proxies = {
        'http': proxy_ip,
        'https': proxy_ip,
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:49.0) Gecko/20100101 Firefox/49.0'
    }
    return proxies, headers


def setDecipher():
    return des(b"38346591", ECB, b"\0\0\0\0\0\0\0\0", pad=None, padmode=PAD_PKCS5)


def searchSongs(query):
    songs_json = []
    albums_json = []
    playLists_json = []
    topQuery_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?_format=json&query={0}&__call=autocomplete.get'.format(query))
    if respone.status_code == 200:
        respone_json = json.loads(respone.text.splitlines()[6])
        albums_json = respone_json['albums']['data']
        songs_json = respone_json['songs']['data']
        playLists_json = respone_json['playlists']['data']
        topQuery_json = respone_json['topquery']['data']
    return {"albums_json": albums_json,
            "songs_json": songs_json,
            "playLists_json": playLists_json,
            "topQuery_json": topQuery_json}


def getPlayList(listId):
    songs_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?listid={0}&_format=json&__call=playlist.getDetails'.format(listId), verify=False)
    if respone.status_code == 200:
        songs_json = list(filter(lambda x: x.startswith("{"), respone.text.splitlines()))[0]
        songs_json = json.loads(songs_json)
    return songs_json


def getAlbum(albumId):
   songs_json = []
   respone = requests.get(
       'https://www.saavn.com/api.php?_format=json&__call=content.getAlbumDetails&albumid={0}'.format(albumId),
       verify=False)
   if respone.status_code == 200:
       songs_json = list(filter(lambda x: x.startswith("{"), respone.text.splitlines()))[0]
       songs_json = json.loads(songs_json)
   return songs_json


def getSong(songId):
    songs_json = []
    respone = requests.get(
        'http://www.saavn.com/api.php?songid={0}&_format=json&__call=song.getDetails'.format(songId), verify=False)
    if respone.status_code == 200:
        print(respone.text)
        songs_json = json.loads(respone.text.splitlines()[5])
    return songs_json


def getHomePage():
    playlists_json = []
    respone = requests.get(
        'https://www.saavn.com/api.php?__call=playlist.getFeaturedPlaylists&_marker=false&language=tamil&offset=1&size=250&_format=json',
        verify=False)
    if respone.status_code == 200:
        playlists_json = json.loads(respone.text.splitlines()[2])
        playlists_json = playlists_json['featuredPlaylists']
    return playlists_json

try:
   def downloadSongs(songs_json,update,context):
    global filename
    global location
    des_cipher = setDecipher()
    context.bot.send_message(chat_id = update.message.chat_id,text ="Uploading Your songs...")
    for song in songs_json['songs']:
        try:
            enc_url = base64.b64decode(song['encrypted_media_url'].strip())
            dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
            dec_url = dec_url.replace('_96.mp4', '_320.mp4')
            filename = html.unescape(song['song']) + '.m4a'
            filename = filename.replace("\"", "'")
        except Exception as e:
            logger.error('Download Error' + str(e))
        try:
            location = os.path.join(os.path.sep, os.getcwd(), "songs", filename)
            if os.path.isfile(location):
               print("Downloaded %s" % filename)

               print("1x :",location)
               

               #ALREADY DOWNLOADED FILE SENT
               context.bot.send_document(chat_id =update.message.chat_id,document=open(location, 'rb'),caption =filename)
               os.remove(location)
               print("file removed")
            else :
                ### IF SOME FILE IS MISSING or REMOVED THAN THIS ELSE PART WILL RUN    ###

                print("Downloading %s" % filename)
                obj = SmartDL(dec_url, location)
                obj.start()
                name = songs_json['name'] if ('name' in songs_json) else songs_json['listname']
                addtags(location, song, name)
                print('\n')
                print("ENTER 2x2 :" ,location)
                # context.bot.send_message(chat_id = update.message.chat_id,text ="Uploading Your Songs ....")
                context.bot.send_document(chat_id =update.message.chat_id,document=open(location, 'rb'),caption =filename)
                os.remove(location)
                print("Files Removed successfully")
        except Exception as e:
             logger.error('Download Error' + str(e))
except Excption as e :
 print("ERROR DOWNLOAD FUNCTION :" + e)
 def downloadSongs(songs_json):
    global filename
    global location
    print("0x")
    # context.bot.send_message(chat_id = update.message.chat_id,text ="TEST")
    des_cipher = setDecipher()
    for song in songs_json['songs']:
        try:
            enc_url = base64.b64decode(song['encrypted_media_url'].strip())
            dec_url = des_cipher.decrypt(enc_url, padmode=PAD_PKCS5).decode('utf-8')
            dec_url = dec_url.replace('_96.mp4', '_320.mp4')
            filename = html.unescape(song['song']) + '.m4a'
            filename = filename.replace("\"", "'")
        except Exception as e:
            logger.error('Download Error' + str(e))
        try:
            location = os.path.join(os.path.sep, os.getcwd(), "songs", filename)
            if os.path.isfile(location):
               print("Downloaded %s" % filename)
               print("1x :",location)
            #    context.bot.send_document(chat_id =update.message.chat_id,document=open(location, 'rb'),caption =filename+ )
            else :
                print("Downloading %s" % filename)
                obj = SmartDL(dec_url, location)
                obj.start()
                name = songs_json['name'] if ('name' in songs_json) else songs_json['listname']
                addtags(location, song, name)
                print('\n')
                print("ENTER 2x :" ,location)
                # context.bot.send_document(chat_id =update.message.chat_id,document=open(location, 'rb'),caption =filename)
        except Exception as e:
             logger.error('Download Error' + str(e))

# if __name__ == '__main__':
def savndl(update,context):
    global res
    global input_url
    update.message.reply_text( text ="Processing url... Please Wait.")
    # context.bot.send_message(chat_id= update.message.chat_id,text= 'Processing url... Please Wait.')

    rawurl = update.message.text.strip()
    rawurl =rawurl.split()
    input_url = rawurl[-1]
    try:
        proxies, headers = setProxy()
        res = requests.get(input_url, proxies=proxies, headers=headers)
        # context.bot.send_message(chat_id= update.message.chat_id,text= 'Enter req Try .')
    except Exception as e:
        logger.error('Error accessing website error: ' + e)

    soup = BeautifulSoup(res.text, "lxml")

    try:
        getPlayListID = soup.select(".flip-layout")[0]["data-listid"]
        if getPlayListID is not None:
            print("Initiating PlayList Downloading")
            context.bot.send_message(chat_id= update.message.chat_id,text= 'Initiating PlayList Downloading')
            downloadSongs(getPlayList(getPlayListID))
            try:
                context.bot.send_message(chat_id= update.message.chat_id,text= 'Uploading Your File.....')
                context.bot.send_document(chat_id =update.message.chat_id,document=open(location, 'rb'),caption =filename)
                print("Trying To Remove File...")
                # try:
                #     os.remove(location)
                #     print("Playlist  cleaned")
                # except Excption as e:
                #     print("ERROR REMOVING : ",e)
                
            except Exception as e:
                context.bot.send_message(chat_id=update.message.chat_id,text ="Uploaing Fail : \n"+e)
                
        print("done",filename)   
        context.bot.send_message(chat_id=update.message.chat_id,text =filename)     
    except Exception as e:
        print('...')
    try:
        getAlbumID = soup.select(".play")[0]["onclick"]
        getAlbumID = ast.literal_eval(re.search("\[(.*?)\]", getAlbumID).group())[1]
        if getAlbumID is not None:
            print("Initiating Album Downloading")
            # context.bot.send_message(chat_id= update.message.chat_id,text= 'entered playlist 1 if X2.')
            try:
                downloadSongs(getAlbum(getAlbumID),update,context)
            except Excption as e :
                print("ENTING DOWNLOADING Fun :" + e)
                downloadSongs(getAlbum(getAlbumID))
            # context.bot.send_message(chat_id=update.message.chat_id,text ="Downloading YoUr file : "+location+filename)
            try:
                ####uploading single file (now this uploading moved to download function)######

                # context.bot.send_message(chat_id = update.message.chat_id,message ="Uploading your Song")
                # context.bot.send_document(chat_id =update.message.chat_id,document=open(location, 'rb'),caption = filename)
                try:
                    os.remove(location)
                    print("File Clean")
                except Excption as e:
                    print("ERROR REMOVING : ",e)
            except Exception as e:
                print("UPLOADING ERROR : ",e)
                print(location)
                context.bot.send_message(chat_id=update.message.chat_id,text =e)
            # sys.exit()
        # context.bot.send_message(chat_id= update.message.chat_id,text= 'entered playlist 1 if DONE PART.')
    except Exception as e:
        print('Retrying...')

    print("Please paste link of album or playlist")
    
def start(update,context):
    context.bot.send_message(chat_id=update.message.chat_id, text=welcome.format(update.message.from_user.first_name))

http_handler = MessageHandler(Filters.regex(r'http' ), savndl)
dp.add_handler(http_handler)

conv_handler = CommandHandler('start'or 'hello'or 'Hello' or 'Start', start)
dp.add_handler(conv_handler)


#polling bot 
updater.start_polling()
updater.idle()
