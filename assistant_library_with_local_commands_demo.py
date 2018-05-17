#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Some code from Stack Overflow

"""Run a recognizer using the Google Assistant Library.

The Google Assistant Library has direct access to the audio API, so this Python
code doesn't need to record audio. Hot word detection "OK, Google" is supported.

It is available for Raspberry Pi 2/3 only; Pi Zero is not supported.
"""

import logging
import platform
import subprocess
import sys

import aiy.assistant.auth_helpers
from aiy.assistant.library import Assistant
import aiy.audio
import aiy.voicehat
from google.assistant.library.event import EventType

import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(26,GPIO.OUT)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
)

def testfunction(function):
    function()


def power_off_pi():
    aiy.audio.say('Powering off')
    subprocess.call('sudo shutdown now', shell=True)


def reboot_pi():
    aiy.audio.say('Rebooting')
    subprocess.call('sudo reboot', shell=True)


def say_ip():
    ip_address = subprocess.check_output("hostname -I | cut -d' ' -f1", shell=True)
    aiy.audio.say('My IP address is %s' % ip_address.decode('utf-8'))

def l_sinclair_probability(players):
    if players == 1:
        aiy.audio.say('Light blue. Orange.')
    if players == 2:
        aiy.audio.say('Orange. Red.')
    if players == 3:
        aiy.audio.say('Green.')
        
aiy.audio.set_tts_volume(20)

def process_event(assistant, event):
    status_ui = aiy.voicehat.get_status_ui()
    if event.type == EventType.ON_START_FINISHED:
        status_ui.status('ready')
        if sys.stdout.isatty():
            print('Say "OK, Google" then speak, or press Ctrl+C to quit...')

    elif event.type == EventType.ON_CONVERSATION_TURN_STARTED:
        status_ui.status('listening')

    elif event.type == EventType.ON_RECOGNIZING_SPEECH_FINISHED and event.args:
        print('You said:', event.args['text'])
        text = event.args['text'].lower()
        if text == 'power off':
            assistant.stop_conversation()
            power_off_pi()
        elif text == 'reboot':
            assistant.stop_conversation()
            reboot_pi()
        elif text == 'ip address':
            assistant.stop_conversation()
            say_ip()
        elif 'tell' in text:
            assistant.stop_conversation()
            text_list = text.split()
            if 'to' in text_list:
                if text_list[0] == 'tell':
                    to_index = text_list.index('to')
                    # Make action equal to 4th element to end
                    action = ' '.join(text_list[to_index+1:])
                    if text_list[1] == 'the':
                        name = ' '.join(text_list[2:to_index])
                    else:
                        name = ' '.join(text_list[1:to_index])
                    response = name + ', ' + action
            else:
                if 'that' in text_list:
                    if text_list[0] == 'tell':
                        that_index = text_list.index('that')
                        # Make action equal to 4th element to end
                        action = ' '.join(text_list[that_index+1:])
                        if text_list[1] == 'the':
                            name = ' '.join(text_list[2:that_index])
                        else:
                            name = ' '.join(text_list[1:that_index])
                        response = name + ', ' + action
                else:
                    if text_list[1] == 'the':
                        response = ' '.join(text_list[2:])
                    else:
                        response = ' '.join(text_list[1:])
            aiy.audio.say(response)
        elif 'call' in text:
            assistant.stop_conversation()
            text_list = text.split()
            if text_list[0] == 'call':              # This makes sure that call is the first item.
                if 'open' in text_list:             # This checks if the user is going to give arguments to their function
                    if 'parentheses' in text_list or 'parenthesis' in text_list:            # This confirms the user is giving arguments.
                        parenthesis_index = text_list.index('open') # As in open parenthesis
                        and_index_count = []
                        argument_list = []
                        if 'and' in text_list[parenthesis_index + 2:]:                      # This checks if the user is giving multiple arguments.
                            for i in text_list[parenthesis_index + 2:]:
                                if i == 'and':                                              # This determines if an item in the text_list is an argument or the word 'and'.
                                    and_index_count += i
                            for element in and_index_count:
                                if and_index_count[and_index_count.index(element) + 1] != None:     # This determines if there is an item directly after 'and'.
                                    item = '_'.join(text_list[element:and_index_count[and_index_count.index(element)+1]])
                                    if item != 'close parenthesis' and item != 'close parentheses': # This determines if the last element is 'close parentheses' or 'close parenthesis.'
                                        argument_list.append(item)
                                else:
                                    item = '_'.join(text_list[element:])
                                    if item != 'close parenthesis' and item != 'close parentheses': # This does the same thing as previous commented if statement.
                                        argument_list.append(item)
                        else:                                               # if and is not text_list[parenthesis_index + 2].
                            for i in text_list[parenthesis_index + 2]:
                                if i != 'close parenthesis' and i != 'close parentheses':           # This also determines if the last element is 'close parenthesis' or close
                                    argument_list.append(i)                                         # parentheses'.
                        function = text_list[1:parenthesis_index]
                        function = '_'.join(function)
                        function = function + '(' + ','.join(argument_list) + ')'
                else:
                    function = text_list[1:]
                    function = '_'.join(function)
                    function = function + '()'
                print(function)
                try:                            # This attempts to use the eval function to run the given function.
                    eval(function)
                except NameError:               # If there is an error, 'Function not defined' will be said.
                    aiy.audio.say('Function not defined.')
        elif 'say' in text:
            assistant.stop_conversation()
            text_list = text.split()
            if text_list[0] == 'say':
                response = ' '.join(text_list[1:])
                aiy.audio.say(response)
        elif 'what books in our library are owned by' in text or 'list books in our library owned by' in text or 'what books in this library are owned by' in text or 'list books in this library owned by' in text or 'what books in the library are owned by' in text or 'list books in the library owned by' in text or 'list books in our library that are owned by' in text or 'list books in this library that are owned by' in text or 'list books in the library that are owned by' in text or 'list books owned by' in text or 'what books are owned by' in text:
            assistant.stop_conversation()
            with open('books.txt','r') as books:
                text_list = text.split()
                books_found = False
                possabilities = []
                possability_shelf_list = []
                book_shelf_list = []
                owner = text_list[text_list.index('by')+1:]
                books_list = []
                for l in books:
                    line = l.split(';')
                    for i in owner:
                        if i in line[2]:
                            possability = line[0] + ' owned by ' + line[2] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                            possability_shelf_list.append(line[3])
                            if possability not in possabilities:
                                possabilities.append(possability)
                    owner_name = ' '.join(owner)
                    if owner_name == line[2]:
                        book_shelf_list.append(line[3])
                        books_found = True
                        if len(books_list) == 0:
                            solution = line[0] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                        else:
                            solution = ' and ' + line[0] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                        books_list.append(solution)
                if books_found == False and len(possabilities) != 0:
                    aiy.audio.say('You may have been looking for ')
                    for i in possabilities:
                        aiy.audio.say(i)
                        if possability_shelf_list[possabilities.index(i)] == 'a1':                                # Add more LEDs later
                            for num in range(1,3):
                                GPIO.output(26,GPIO.HIGH)
                                time.sleep(.5)
                                GPIO.output(26,GPIO.LOW)
                                time.sleep(.5)
                        print(i)
                if books_found == True:
                    response = ' '.join(owner) + ' owns ' + str(len(books_list)) + ' books: '
                    aiy.audio.say(response)
                    for i in books_list:
                        aiy.audio.say(i)
                        if book_shelf_list[books_list.index(i)] == 'a1':                                # Add more LEDs later
                            for num in range(1,3):
                                GPIO.output(26,GPIO.HIGH)
                                time.sleep(.5)
                                GPIO.output(26,GPIO.LOW)
                                time.sleep(.5)
                    print(books_list)
                if len(possabilities) == 0:
                    aiy.audio.say('Unknown Owner.')
        elif 'what books in our library did' in text or 'list books in our library by' in text or 'what books in this library did' in text or 'list books in this library by' in text or 'what books in the library did' in text or 'list books in the library by' in text:
            assistant.stop_conversation()
            text = text.lower()
            text_list = text.split()
            possability_shelf_list = []
            book_shelf_list = []
            if len(text_list) != 1:
                with open('books.txt','r') as books:
                    text_list = text.split()
                    books_found = False
                    possabilities = []
                    if 'what books did' not in text:
                        author = text_list[6:]
                    else:
                        for item in text_list:
                            if item == 'write':
                                write_index = text_list.index(item)
                        author = text_list[6:write_index]
                    books_list = []
                    for l in books:
                        line = l.split(';')
                        for i in author:
                            if i in line[1]:
                                possability = line[0] + ' by ' + line[1] + ' is on shelf ' + line[3] + ' position ' + line[4]
                                if possability not in possabilities:
                                    possabilities.append(possability)
                                    possability_shelf_list.append(line[3])
                        author_name = ' '.join(author)  
                        if author_name == line[1]:
                            books_found = True
                            if len(books_list) == 0:
                                solution = line[0] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                            else:
                                solution = ' and ' + line[0] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                            books_list.append(solution)
                            book_shelf_list.append(line[3])
                    if books_found == False:
                        aiy.audio.say('You may have been looking for ')
                        for i in possabilities:
                            aiy.audio.say(i)
                            if possability_shelf_list[possabilities.index(i)] == 'a1':                                # Add more LEDs later
                                for num in range(1,3):
                                    GPIO.output(26,GPIO.HIGH)
                                    time.sleep(.5)
                                    GPIO.output(26,GPIO.LOW)
                                    time.sleep(.5)
                        print(possabilities)
                    if books_found == True:
                        response = ' '.join(author) + ' wrote ' + len(books_list) + ' that are in this library: '
                        aiy.audio.say(response)
                        for i in books_list:
                            aiy.audio.say(i)
                            if possability_shelf_list[possabilities.index(i)] == 'a1':                                # Add more LEDs later
                                for num in range(1,3):
                                    GPIO.output(26,GPIO.HIGH)
                                    time.sleep(.5)
                                    GPIO.output(26,GPIO.LOW)
                                    time.sleep(.5)
                        print(books_list)
        elif 'find' in text or 'locate' in text: 
            assistant.stop_conversation()
            text = text.lower()
            text_list = text.split()
            book_shelf_list = []
            possability_shelf_list = []
            if len(text_list) != 1:
                with open('books.txt','r') as books:        # This opens book.txt, which contains the list of books, authors, book owners, and book locations.
                    if text_list[1] != 'books':             # This loop checks to see if the second item in text_list is not 'books'. If the second word is 'books', the user
                        # would most likely be saying 'find' or 'locate' 'books owned by' or 'books by' a given person.
                        book = ' '.join(text_list[1:])
                        possabilities = []
                        book_found = False
                        for l in books:                     # This loop goes through each line in the books.txt file and separates the items by a semicolon.
                            line = l.split(';')
                            if book in line[0]:             # If the book the user asked to search for is in the title of the book in a line, add the book to a
                                possability = line[0] + ' which is on shelf '  + line[3] + ' position ' + line[4] + ',' # list of possabilities and add the shelf
                                possabilities.append(possability)                                                       # number into the list of shelves (so the
                                possability_shelf_list.append(line[3])                                                  # LED can be easily programmed).
                            if line[0] == book:             # If the book the user is looking for is identical to the book in the record, the book name will be stated along with
                                book_found = True           # its location (the shelf and position).
                                shelf = line[3] 
                                position = line[4]
                                response = book + ' is on shelf ' + shelf + ' position ' + position
                                print(response)
                                aiy.audio.say(response)
                                if line[3] == 'a1':                             # This lights up the LED when the book is on shelf A1. This shelf is being used as
                                    for num in range(1,3):                      # an example. I will add more LEDs later.
                                        GPIO.output(26,GPIO.HIGH)
                                        time.sleep(.5)
                                        GPIO.output(26,GPIO.LOW)
                                        time.sleep(.5)
                        if book_found == False:                                     # If the identical match to the user's search is not found, the possabilities (the
                            if len(possabilities) != 0:                             # books that contained part of the users book in their title) will be listed.
                                print(possabilities)
                                aiy.audio.say('You may have been looking for ')
                                for i in possabilities:
                                    aiy.audio.say(i)
                                    if possability_shelf_list[possabilities.index(i)] == 'a1':                      # This lights up the LED if the book being
                                        for num in range(1,5):                                                      # presented is on shelf A1. I will add more LEDs
                                            GPIO.output(26,GPIO.HIGH)                                               # later.
                                            time.sleep(.5)
                                            GPIO.output(26,GPIO.LOW)
                                            time.sleep(.5)
                    if text_list[1] == 'books':                                     # This loop determines the user is looking for an author or book owner.
                        if len(text_list) > 2:
                            if text_list[2] == 'by':                                # This loop looks specifically for an author.
                                books_found = False
                                possabilities = []
                                author = text_list[3:]
                                books_list = []
                                possability_shelf_list = []
                                book_shelf_list = []
                                for l in books:
                                    line = l.split(';')
                                    for i in author:
                                        if i in line[1]:
                                            possability = line[0] + ' wrote ' + line[1] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                                            if possability not in possabilities:                        # This makes sure something isn't added to a list multiple
                                                possabilities.append(possability)                       # times.
                                                possability_shelf_list.append(line[3])
                                    author_name = ' '.join(author)
                                    if author_name == line[1]:                                          # This determines if a book is definitely by an author and
                                        books_found = True                                              # not only possably by an author (previous loop).
                                        # ^ This sets the variable 'books_found' to true, meaning that the exact book(s) the user was looking for were found.
                                        if len(books_list) == 0:
                                            solution = line[0] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                                        else:
                                            solution = ' and ' + line[0] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                                        books_list.append(solution)
                                if books_found == False and len(possabilities) != 0:            # If no books completely match the search parameters and there
                                    aiy.audio.say('You may have been looking for ')             # possabilities.
                                    for i in possabilities:
                                        aiy.audio.say(i)
                                    print(possabilities)
                                if books_found == True:
                                    response = ' '.join(author) + ' wrote ' + len(books_list) + ' books that are in this library: ' + ' '.join(books_list)
                                    aiy.audio.say(response)
                                    print(books_list)
                                if len(possabilities) == 0:
                                    aiy.audio.say('Unknown Author.')
                            if text_list[2:4] == ['owned', 'by']:                   # This determines if the user is looking for books owned by a specific person.
                                books_found = False
                                possabilities = []
                                owner = text_list[4:]
                                books_list = []
                                for l in books:
                                    line = l.split(';')
                                    for i in owner:
                                        if i in line[2]:
                                            possability = line[0] + ' owned by ' + line[2] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                                            if possability not in possabilities:
                                                possabilities.append(possability)
                                    owner_name = ' '.join(owner)
                                    if owner_name.strip() == line[2].strip():
                                        books_found = True
                                        if len(books_list) == 0:
                                            solution = line[0] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                                        else:
                                            solution = ' and ' + line[0] + ' which is on shelf ' + line[3] + ' position ' + line[4]
                                        books_list.append(solution)
                                if books_found == False:
                                    response = 'You may have been looking for '
                                    aiy.audio.say(response)
                                    for i in possabilities:
                                        aiy.audio.say(i)
                                        item = i.split(' ')
                                        for i in item:
                                            if i == 'a1':
                                                for num in range(1,3):
                                                    GPIO.output(26,GPIO.HIGH)
                                                    time.sleep(.5)
                                                    GPIO.output(26,GPIO.LOW)
                                                    time.sleep(.5)
                                    print(possabilities)
                                if books_found == True:
                                    response = ' '.join(owner) + ' owns ' + str(len(books_list)) + 'books: '
                                    aiy.audio.say(response)
                                    for i in books_list:
                                        aiy.audio.say(i)
                                        item = i.split(' ')
                                        for i in item:
                                            if i == 'a1':                                # Lights up the LEDs. I will add more LEDs later
                                                for num in range(1,3):
                                                    GPIO.output(26,GPIO.HIGH)
                                                    time.sleep(.5)
                                                    GPIO.output(26,GPIO.LOW)
                                                    time.sleep(.5)
                                    print(books_list)
                                if len(possabilities) == 0:
                                    aiy.audio.say('Unknown Owner.')
            else:                                                               # This happens if if the user does not state a book to find.
                aiy.audio.say('Unknown Book.')
        elif 'move' in text and 'to shelf' in text and 'position' in text:
            assistant.stop_conversation()
            text_list = text.split()
            to_index = text_list.index('to')
            position_index = text_list.index('position')
            book = ' '.join(text_list[1:to_index])
            print(to_index)
            #new_shelf = text_list[to_index+1:
##            with open("books.txt", "r") as books:
##                data = books.readlines()
##                for line in books:
##                    if line[0] == book:
##                        new_line = [line[0],line[1],line[2],new_shelf
                
                

    elif event.type == EventType.ON_END_OF_UTTERANCE:
        status_ui.status('thinking')

    elif (event.type == EventType.ON_CONVERSATION_TURN_FINISHED
          or event.type == EventType.ON_CONVERSATION_TURN_TIMEOUT
          or event.type == EventType.ON_NO_RESPONSE):
        status_ui.status('ready')

    elif event.type == EventType.ON_ASSISTANT_ERROR and event.args and event.args['is_fatal']:
        sys.exit(1)


def main():
    if platform.machine() == 'armv6l':
        print('Cannot run hotword demo on Pi Zero!')
        exit(-1)

    credentials = aiy.assistant.auth_helpers.get_assistant_credentials()
    with Assistant(credentials) as assistant:
        for event in assistant.start():
            process_event(assistant, event)


if __name__ == '__main__':
    main()
