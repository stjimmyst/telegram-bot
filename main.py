import os

import telebot
import uuid
from telebot.async_telebot import AsyncTeleBot
import asyncio
import time
import requests
import json




BOT_TOKEN = os.environ.get('BOT_TOKEN')
OPENLANG_SERVER = os.environ.get('OPENLANG_SERVER')
ads_content = "\n\nTo see the results visit our website: https://openlang.one"
hello_text = """
<b>Welcome to the OpenLang IELTS AI Examiner</b>.
Please select one of the following command: 

<b>/writing</b>: Estimate your IELTS Writing
<b>/speaking</b>: Estimate your IELTS Speaking
"""
utm_link = "https://openlang.one?utm_source=telegram&utm_medium=openlangbot&utm_campaign=self&utm_id=0&utm_term=v0&utm_content=v0"

# bot = telebot.TeleBot(BOT_TOKEN)
bot = telebot.async_telebot.AsyncTeleBot(BOT_TOKEN)
stat = {}

print("Telegram bot is running")



def getuserid(message):
    return str(message.from_user.id)

def getTimeStamp():
    return time.time()

def getDiffTimestamp(dt1,dt2):
    vait_interval = 3600
    diff = dt2-dt1
    print("dt_old="+str(dt1))
    print("dt_new="+str(dt2))
    if (diff < vait_interval):
        return False,str(int(vait_interval-diff))
    else:
        return True,""
def getMessageLength(txt):
    return len(txt.split(" "))

def welcomeText(message):
    user_id = getuserid(message)
    user_status = stat.get(user_id, {})
    dt = getTimeStamp()
    txt_output = hello_text
    if (len(user_status) == 0):
        print("new user " + user_id)
        stat[user_id] = {"activity": "ready", "dt": 0}
    elif (message.text == "/start") :
        print("Existing user " + user_id)
        stat[user_id]["activity"] = "ready"
    else:
        print("Existing user " + user_id)
        dt_old = user_status['dt']
        res, txt = getDiffTimestamp(dt_old, dt)
        if (res == True):
            if (stat[user_id]["activity"] != "ready"):
                txt_output = txt
        else:
            txt_output = "Please wait for " + txt + " seconds before next IELTS estimation"
    return txt_output

def printHTMLResult(type,score,comment,is_signed):
    sign = ""
    if (is_signed):
        sign = """To see detailed results visit our website: <a href="{link}"><b>https://openlang.one</b></a>""".format(link=utm_link)
    return """
<b>IELTS {type} Estimation results</b>

Criteria: <b>Lexical Resource</b>
Score: <b>{score}</b>


{comment}

{sign}
""".format(type=type,score=score,comment=comment,sign=sign)

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    chat_id = message.chat.id
    asyncio.create_task(telegramLogin(message))
    await bot.send_message(chat_id,parse_mode="HTML",text=welcomeText(message))

@bot.message_handler(commands=['writing'])
async def send_welcome(message):
    user_id = getuserid(message)
    user_status = stat.get(user_id, {})
    chat_id = message.chat.id
    if (len(user_status) != 0):
        stat[getuserid(message)]['activity'] = 'writing'
        outp = "You are going to estimate you IELTS Writing. Please provide you IELTS Writing text below"
    else:
        outp = "Your session expired. Please use <b>/start</b> command again"
    await bot.send_message(chat_id, parse_mode="HTML", text=outp)

@bot.message_handler(commands=['speaking'])
async def send_welcome(message):
    user_id = getuserid(message)
    user_status = stat.get(user_id, {})
    chat_id = message.chat.id
    if (len(user_status) != 0):
        stat[getuserid(message)]['activity'] = 'speaking'
        outp = "You are going to estimate you IELTS Speaking. Please record your voice."
    else:
        outp = "Your session expired. Please use <b>/start</b> command again"
    await bot.send_message(chat_id, parse_mode="HTML", text=outp)


def getUserName(message):
    uid = getuserid(message)
    tmp = "telegram_" + str(uid)
    print("userid="+tmp)
    return tmp

async def telegramLogin(message: telebot.types.Message):
    uid = getuserid(message)
    inp = message.from_user.to_dict()
    inp["id"] = getUserName(message)
    inp["original_id"] = str(uid)
    bot_name = await bot.get_me()
    inp["source"] = bot_name.to_dict()
    json = {"profile": inp}
    response = requests.post(str(OPENLANG_SERVER)+'/login', json=json)
    print(response.json())



@bot.message_handler(content_types=['voice'])
async def voice_processing(message):
    outp = welcomeText(message)
    chat_id = message.chat.id
    if outp == "":
        id = getuserid(message)
        user_status = stat[id]
        dt = getTimeStamp()
        if user_status['activity'] == 'speaking':
            file_info = await bot.get_file(message.voice.file_id)
            await bot.send_message(chat_id, parse_mode="HTML", text="Please wait for results...")
            downloaded_file = await bot.download_file(file_info.file_path)
            request_uuid = str(uuid.uuid4())
            fn = id + "_" + request_uuid
            with open(fn, 'wb') as new_file:
                new_file.write(downloaded_file)

            params = {
                "question": "none",
                "user": str(getUserName(message)),
                "test": "ielts"
            };
            files = {
                'file': open(fn, 'rb'),
                'params': (None, json.dumps(params))
            }

            response = requests.post(OPENLANG_SERVER+'/SpeakingEstimation', files=files)
            res = json.loads(response.text)
            band = res['results']['estimations']['gra']['band']
            comment = res['results']['estimations']['gra']['comment']
            outp = printHTMLResult("Speaking", band, comment, True)
            stat[id] = {"activity": "ready", "dt": dt}
            os.remove(fn)
        else:
            outp = "Please provide text message when you want to estimate you IELTS Writing. Just type it and send to me."
            stat[id] = {"activity": "ready", "dt": 0}
    await bot.send_message(chat_id, parse_mode="HTML", text=outp)


@bot.message_handler(func=lambda msg: True)
async def echo_all(message):
    chat_id = message.chat.id
    outp = welcomeText(message)
    if outp == "":
        id = getuserid(message)
        user_status = stat[id]
        dt = getTimeStamp()
        if user_status['activity'] == 'writing':
            await bot.send_message(chat_id, parse_mode="HTML",
                                   text="Please wait for results...")

            params = {
                "answer": message.text,
                "question": "none",
                "user": str(getUserName(message)),
                "test": "ielts"
            };

            response = requests.post(OPENLANG_SERVER + '/WritingEstimation', json=params)
            print(response.text)
            res = json.loads(response.text)
            print(res)
            band = res['results']['estimations']['lr']['band']
            comment = res['results']['estimations']['lr']['comment']
            outp = printHTMLResult("Writing", band, comment, True)
            stat[id] = {"activity": "ready", "dt": dt}
        elif user_status['activity'] == 'speaking':
            outp = "Please provide voice message when you want to estimate you IELTS Speaking."
            stat[id] = {"activity": "ready", "dt": 0}

    await bot.send_message(chat_id, parse_mode="HTML", text=outp)

asyncio.run(bot.polling(non_stop=True))
