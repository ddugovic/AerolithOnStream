import sys
import re
import pyautogui
import socket
import threading
import string
import config as cf
import PySimpleGUI as sg
import requests
import json
import datetime

def joinChat():
    loading = True
    while loading:
        readbuffer_join = irc.recv(1024).decode() #receiving 1024 bits/bytes at a time, save in readbuffer join
        for line in readbuffer_join.split("\n")[0:-1]:
            print(line)
            loading = loadingComplete(line)

def loadingComplete(line):
    if ("End of /NAMES list" in line):
        print('Bot ' + config.nick + ' has joined the channel ' + config.channel + '!')
        window['-BOTSTATUS-'].update('Bot ' + config.nick + ' has joined the channel ' + config.channel + '!')
        return False
    else:
        return True

def getUser(line):
    global user
    separate = line.split(":", 2) #split by colon, up to two times
    user = separate[1].split("!", 1)[0]
    return user

def getMessage(line):
    global message
    try:
        message = line.split(":", 2)[2] #split by colon, up to two times
    except:
        message = ""
    return message

def sendMessage(irc, message):
    messageTemp = "PRIVMSG #" + config.channel + " :" + message
    irc.send((messageTemp + "\n").encode())

def twitch():
    while True:
        try:
            received = irc.recv(1024)
            readbuffer = received.decode() #receiving 1024 bits/bytes at a time, save in readbuffer join
        except:
            readbuffer = ""
        for line in readbuffer.split("\r\n"):
            if line == "":
                continue
            if "PING" in line and not "PRIVMSG" in line: #responds to ping from server, needed to stay connected
                msg = "PONG tmi.twitch.tv\r\n".encode()
                irc.send(msg)
                print(msg)
                continue
            else:
                user = getUser(line)
                message = getMessage(line)
                print(user + ": " + message) #useful for debugging purposes
                message = ''.join(message.split()).upper() #remove spaces
                if started:
                    sortedMessage = ''.join(sorted(message))
                    if not blank:
                        if not sortedMessage in alpha: #wrong letters
                            continue
                    elif len(message) != blank_length or not any(containsAll(sortedMessage, string) for string in alpha): #blank quiz - probably slower.
                        continue
                    try:
                        pyautogui.typewrite(message)
                        pyautogui.press('enter')
                        print(message)
                        if message in words:
                            window['-MESSAGES-' + sg.WRITE_ONLY_KEY].print(user + ": " + message, background_color='green')
                            solved.append(message)
                            if message in words: words.remove(message) #if statement added to reduce crashes
                            if not user in scores:
                                scores[user] = 1
                            else:
                                scores[user]+= 1
                            window['-SCORES-' + sg.WRITE_ONLY_KEY].update('')
                            rank = 1
                            for u in sorted(scores, key=scores.get):
                                if rank > len(scores)-3:
                                    window['-SCORES-' + sg.WRITE_ONLY_KEY].print(u + ': ' + str(scores[u]), text_color=config.colours[len(scores) - rank]) #default is ["yellow", "black", "sandy brown"]
                                else:
                                    window['-SCORES-' + sg.WRITE_ONLY_KEY].print(u + ': ' + str(scores[u]))
                                rank += 1
                        elif message.upper() in solved: #guessed before
                            window['-MESSAGES-' + sg.WRITE_ONLY_KEY].print(user + ": " + message, background_color='grey')
                        else: #wrong guess
                            window['-MESSAGES-' + sg.WRITE_ONLY_KEY].print(user + ": " + message, background_color='red')
                            if not user in badguess:
                                badguess[user] = 1
                            else:
                                badguess[user]+= 1
                            window['-BADGUESS-' + sg.WRITE_ONLY_KEY].update('')
                            for u in sorted(badguess, key=badguess.get):
                                window['-BADGUESS-' + sg.WRITE_ONLY_KEY].print(u + ': ' + str(badguess[u]))
                    except:
                        print("There was some issue with this message: " + message)

def gameControl():
    while datetime.datetime.now() < endtime:
        continue    
    started = False
    if len(scores)>0:
        finalRanks = 'Leaderboard - '
        for i in range(0, min(5, len(scores))):
            user = sorted(scores, key=scores.get, reverse=True)[i]
            finalRanks += str(i+1) + '. @' + user + ': ' + str(scores[user]) + ' '
        sendMessage(irc, "Round over! " + finalRanks)
    else:
        sendMessage(irc, "Round over! No answers found.")
    window['-OUTPUT-'].update('Aerolith On Stream is not running.', text_color='white')

config = cf.config()
SERVER = "irc.twitch.tv"
PORT = 6667

scores = {}
badguess = {}
started = False
endtime = datetime.datetime.now()

#Enter your twitch username and oauth-key below, and the app connects to twitch with the details.
irc = socket.socket()
irc.connect((SERVER, PORT))
irc.send(("PASS " + config.irc_token + "\n" +
        "NICK " + config.nick + "\n" +
        "JOIN #" + config.channel + "\n").encode())

sg.theme(config.theme) #default is Dark Black

# Define the window's contents
layout = [[sg.Text('Bot has not joined the channel.',size=(40,1), key='-BOTSTATUS-', font=config.font)], #default font is Arial
    [sg.Text('Aerolith On Stream is not running.', size=(40,2), key='-OUTPUT-', font = config.font)],
    [sg.Text('Guesses:', font = config.font)],
    [sg.MLine(size=(40,config.box_height[0]+1), disabled=True, key='-MESSAGES-' + sg.WRITE_ONLY_KEY, font = config.font)], #+1 to height because there is an empty line at the end
    [sg.Text('Scoreboard:', font = config.font)],
    [sg.MLine(size=(40,config.box_height[1]+1), disabled=True, key='-SCORES-'+ sg.WRITE_ONLY_KEY, font = config.font)], #+1 to height because there is an empty line at the end
    [sg.Text('Nopeboard:', font = config.font)],
    [sg.MLine(size=(40,config.box_height[2]+1), disabled=True, key='-BADGUESS-'+ sg.WRITE_ONLY_KEY, font = config.font)], #+1 to height because there is an empty line at the end
    [sg.Text('Room Number', font = config.font), sg.InputText(key='-ROOM-', size=(8,1), font = config.font)], 
    [sg.Checkbox('Retain scores across rounds', key='-SAVESCORE-', default=True, font = config.font)], 
    [sg.Button('Start', font = config.font), sg.Button('End', font = config.font)]]

# Create the window
global window
window = sg.Window('Aerolith On Stream', layout, finalize=True)
joinChat()
irc.setblocking(False)

t1 = threading.Thread(target = twitch)
t1.start()

# Display and interact with the Window using an Event Loop
while True:
    global event, values
    event, values = window.read()
    # See if user wants to quit or window was closed
    if event == sg.WINDOW_CLOSED:
        islive=False
        print("window closed!")
        break
    elif event == 'Start':
        try:
            room = int(values['-ROOM-'])
        except ValueError:
            sg.popup('Key in your Aerolith room number!')
            
        client = requests.session()
        r = client.get('https://aerolith.org/wordwalls/api/answers/?tablenum=' + values['-ROOM-'])
        if r.status_code == 400:
            sg.popup('Invalid or inactive Aerolith room number!')
            continue
        elif r.status_code != 200:
            sg.popup('Error!')
            continue
        data = json.loads(r.content)
        time = data['time_remaining']
        alpha = []
        words = []
        for question in data['questions']:
            alpha.append(question['a'])
            words.extend(question['ws'])
        blank = any('?' in string for string in alpha) #checks if this is a blank quiz
        blank_length = len(alpha[0]) #get length of first alphagram for blank quizzes
        alpha = [s.replace('?', '') for s in alpha]
        endtime = datetime.datetime.now() + datetime.timedelta(seconds = float(time))
        window['-OUTPUT-'].update('Aerolith On Stream has started!', text_color = 'red')
        sendMessage(irc, "Starting Aerolith On Stream!")
        solved = []
        started = True
        window['-MESSAGES-' + sg.WRITE_ONLY_KEY].update('')
        if values['-SAVESCORE-'] == False:
            scores = {}
            badguess = {}
            window['-SCORES-' + sg.WRITE_ONLY_KEY].update('')
            window['-BADGUESS-' + sg.WRITE_ONLY_KEY].update('')
        t2 = threading.Thread(target = gameControl)
        t2.start()
    elif event == 'End':
        started = False
        sendMessage(irc, "Ending Aerolith On Stream!")
        window['-OUTPUT-'].update('Aerolith On Stream is not running.', text_color='white')
# Finish up by removing from the screen
window.close()