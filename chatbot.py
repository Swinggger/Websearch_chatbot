#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Sept  10 11:42:20 2021

@author: yuxinyin
"""
import telegram

"""
A chat robot that can provide billions of webpages, images and news. 
"""

"""
Usage: 
Send /start to initiate the conversation.
Run "updater.stop()" to stop the bot.
"""

# Import necessary modules
import logging
import re
import random
import ast
import http.client
from telegram import ReplyKeyboardMarkup
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, ConversationHandler)
from rasa_nlu.training_data import load_data
from rasa_nlu.model import Trainer
from rasa_nlu import config
import simplejson

# 11111111111111****************************************
# 连接api
conn = http.client.HTTPSConnection("contextualwebsearch-websearch-v1.p.rapidapi.com")

headers = {
    'x-rapidapi-host': "contextualwebsearch-websearch-v1.p.rapidapi.com",
    'x-rapidapi-key': "e1149d6436mshebefc1e89896db1p109ed1jsn4b0acd2bee3f"
    }

# 训练rasa解释器
trainer = Trainer(config.load("config_spacy.yml"))
# Load the training data
training_data = load_data('emma_rasa.md')
# Create an interpreter by training the model
interpreter = trainer.train(training_data)

# 2222222222222****************************************
# 全局变量声明
params = []
# 不懂回复
default = "Sorry, I don't understand what you mean. ε(┬┬﹏┬┬)3"
# 闲聊回复
rules = {'i wish (.*)': ['What would it mean if {0}',
                         'Why do you wish {0}',
                         "What's stopping you from realising {0}"
                         ],
         'do you remember (.*)': ['Did you think I would forget {0}',
                                  "Why haven't you been able to forget {0}",
                                  'What about {0}',
                                  'Yes .. and?'
                                  ],
         'do you think (.*)': ['if {0}? Absolutely.',
                               'No chance.'
                               ],
         'if (.*)': ["Do you really think it's likely that {0}",
                     'Do you wish that {0}',
                     'What do you think about {0}',
                     'Really--if {0}'
                     ]
         }
# 定义回复规则
response = [
    "I'm sorry, I couldn't find anything like that. ╮(๑•́ ₃•̀๑)╭",
    "Great! Here are some brief information about {}:",
    "Bingo! I found the following items: ",
]
# ****************************************
updater = Updater(token='1974232577:AAGK8pZuvFYWQMV8d17a4QilH_M7BBuWs10',
                  request_kwargs={'proxy_url': 'https://127.0.0.1:7890'})

dispatcher = updater.dispatcher

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


# start命令
def start(update, context):
    update.message.reply_text(
        "Hi! My name is Emma. I can help you find billions of webpages, images and news.\n\n"
        "Remember that the keywords should be capitalized.\n"
        "For example 'show me the top news in US'.\n\n"
        "You can also search any celebrity if you want like 'search Taylor Swift for me'.\n"
        "You can also ask specific information of certain news and knowledge, "
        "including politics, entertainment, sports, economic, music.\n"
        "For example 'who is Donald Trump', 'anything new about Jay Chou'.\n\n"
        "Welcome to chat with me! (๑•ᴗ•๑)♡ "
    )


start_handler = CommandHandler('start', start)
dispatcher.add_handler(start_handler)


# 大小写转换命令
def caps(update, context):
    print(type(context.args))
    text_caps = ' '.join(context.args).upper()
    return text_caps


caps_handler = CommandHandler('caps', caps)
dispatcher.add_handler(caps_handler)


# 未知命令
def unknown(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=default)


unknown_handler = MessageHandler(Filters.command, unknown)
dispatcher.add_handler(unknown_handler)


# ****************************************
# 替换人称
def replace_pronouns(message):
    message = message.lower()

    if 'me' in message:
        # Replace 'me' with 'you'
        return re.sub('me', 'you', message)
    if 'my' in message:
        # Replace 'my' with 'your'
        return re.sub('my', 'your', message)
    if 'your' in message:
        # Replace 'your' with 'my'
        return re.sub('your', 'my', message)
    if 'you' in message:
        # Replace 'you' with 'me'
        return re.sub('you', 'me', message)

    return message


# 匹配回复规则
def match_rule(update, context, message):
    for pattern, value in rules.items():
        # Create a match object
        match = re.search(pattern, message)
        # 如果匹配成功
        if match is not None:
            # Choose a random response
            response = random.choice(rules[pattern])
            # 如果需要人称替换
            if '{0}' in response:
                phrase = re.search(pattern, message).group(1)
                phrase = replace_pronouns(phrase)
                # 回复消息
                update.message.reply_text(response.format(phrase))
            else:
                # 回复消息
                update.message.reply_text(response)
            return True

    return False


# 提取
def find_name(message):
    name = None
    name_words = []

    # Create a pattern for finding capitalized words
    name_pattern = re.compile("[A-Z]{1}[a-z]*")

    # Get the matching words in the string
    name_words += name_pattern.findall(message)

    # Create a pattern for checking if the keywords occur
    name_keyword = re.compile("name|call|news|trending|in|image", re.I)

    if name_keyword.search(message) or name_words:
        name_new_pattern = re.compile("[0-9]{1}[0-9]*")
        name_words += name_new_pattern.findall(message)

    if len(name_words) > 0:
        # Return the name if the keywords are present
        name = '%20'.join(name_words)

    return name


# 自动将电影名转换大写
def turn_name(message):
    if "name*" in message:
        index = message.index("name*") + len("name*")
        name = message[index:].upper()
        name_list = name.split(' ')

        for i in range(len(name_list)):
            if name_list[i] == '':
                continue
            else:
                index = i
                break

        newname = '%20'.join(name_list[index:])
        return newname


def trendingnews(update, context, name):
    if name == None:
        update.message.reply_text(default)
        return name

    # 获得api数据
    conn.request("GET", "/api/search/TrendingNewsAPI?pageNumber=1&pageSize=10&withThumbnails=false&location=" + name,
                 headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    print(data)
    # 将字符串转换为字典格式
    data = simplejson.loads(data)

    # 搜索错误时返回
    if len(data) <= 2:
        update.message.reply_text(response[0])
        return []

    # params存放搜索结果
    params = data['value']
    print(params)
    # rename存放搜索结果名
    rename = [r['title'] for r in params]
    print(rename)

    # 根据检索到的数目选择回复
    n = min(data['totalCount'], 2)
    update.message.reply_text(response[n].format(*rename))

    # 检索到两条以上回复请求索引
    if n == 2:
        # 得到检索到信息的长度
        lenth = len(rename)
        for i in range(lenth):
            update.message.reply_text("{}. {}".format(i + 1, rename[i]))
        update.message.reply_text("Tell me the index of which to view specific information.\n"
                                  "For example 'the third one', '5'"
                                  )

    # 仅检索到一条时打印website
    else:
        for key in params[0]:
            if key == "id":
                continue
            # 打印海报需要特殊处理
            if key == "image":
                update.message.reply_text("Image:")
                # 打印海报
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=params[0][key]["url"])
                continue
            update.message.reply_text("{}: {}".format(key, params[0][key]["url"]))

    # 更新params
    return params

def web_search(update, context, name):
    if name == None:
        update.message.reply_text(default)
        return name

    #get api
    conn.request("GET", "/api/Search/WebSearchAPI?pageNumber=1&pageSize=10&autoCorrect=true&q=" + name,
                 headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    data = simplejson.loads(data)
    params = data['value']
    rename = [r['title'] for r in params]

    n = min(data['totalCount'], 2)
    update.message.reply_text(response[n].format(*rename))

    # 检索到两条以上回复请求索引
    if n == 2:
        # 得到检索到信息的长度
        lenth = len(rename)
        for i in range(lenth):
            update.message.reply_text("{}. {}".format(i + 1, rename[i]))
        update.message.reply_text("Tell me the index of which to view specific information.\n"
                                  "For example 'the third one', '5'"
                                  )
    # 仅检索到一条时打印website
    else:
        for key in params[0]:
            if key == "id":
                continue
            # 打印海报需要特殊处理
            if key == "image":
                update.message.reply_text("Image:")
                # 打印海报
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=params[0][key]["url"])
                continue
            update.message.reply_text("{}: {}".format(key, params[0][key]["url"]))

    # 更新params
    return params



# number_work
def number_work(update, context, message, params):
    name = message

    if "1" in name:
        if name.find("0") < 0:
            id = 1
        else:
            id = 10
    elif "one" in name or "first" in name:
        id = 1
    elif "2" in name or "two" in name or "second" in name:
        id = 2
    elif "3" in name or "three" in name or "third" in name:
        id = 3
    elif "4" in name or "four" in name or "fourth" in name:
        id = 4
    elif "5" in name or "five" in name or "fifth" in name:
        id = 5
    elif "6" in name or "six" in name or "sixth" in name:
        id = 6
    elif "7" in name or "seven" in name or "seventh" in name:
        id = 7
    elif "8" in name or "eight" in name or "eighth" in name:
        id = 8
    elif "9" in name or "nine" in name or "ninth" in name:
        id = 9
    elif "10" in name or "ten" in name or "tenth" in name:
        id = 10
    else:
        id = 15

    # 索引错误时返回
    if id > len(params):
        update.message.reply_text("Please give me right index. (๑• . •๑)")
        return params

    # 索引正确时更新params并给出电影信息
    params = [params[id - 1]]
    update.message.reply_text("Here are some brief information about {}:".format(params[0]["title"]))

    for key in params[0]:
        if key == "snippet":
            break

        # 打印海报需要特殊处理
        if key == "image":
            update.message.reply_text("Image:")
            #############################################################
            update.message.reply_photo(params[0][key]['url'])
            continue
        update.message.reply_text("{}: {}".format(key, params[0][key]))

    return params


# poster_work
def poster_work(update, context, name, params):
    # name已经在params中
    for i in range(len(params)):
        if name == params[i]["title"] or name == None:
            update.message.reply_text("Here is a image of {}:".format(params[i]["title"]))
            update.message.reply_photo(params[i]["image"]["url"])
            return params

    # name不在则检索

    # 获得api数据
    conn.request("GET", "/api/search/TrendingNewsAPI?pageNumber=1&pageSize=10&withThumbnails=false&location=" + name,
                 headers=headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")

    # 将字符串转换为字典格式
    data = ast.literal_eval(data)

    # 没有检索到
    if len(data) <= 2:
        update.message.reply_text(default)
        # 返回空params
        return []

    # 更新params
    params = data["value"]

    # 打印海报
    update.message.reply_text("Here is a image of {}:".format(params[0]["title"]))
    update.message.reply_photo(params[0]["image"]["url"])

    return params


# 理解消息并回复
def respond(update, context, message):
    target = interpreter.parse(message)
    global params

    # 去掉消息中所有标点
    r = '[’!"#$%&\'()+,-./:;<=>?@[\\]^_`{|}~]+'
    message = re.sub(r, '', message)
    print(message)
    # params test
    print(params)

    # name存放用户消息中的电影名
    name = None
    if (target['entities'] is not None):
        name = find_name(message)
        if name == None:
            name = turn_name(message)
    print(name)

    message = message.lower()

    print(target['intent']['name'])
    # 判断意图进行检索
    if target['intent']['name'] == 'news_trending':
        params = trendingnews(update, context, name)

    elif target['intent']['name'] == 'search_web':
        params = web_search(update, context, name)

    elif target['intent']['name'] == 'work_number':
        params = number_work(update, context, message, params)

    elif target['intent']['name'] == 'work_image':
        params = poster_work(update, context, name, params)

    elif target['intent']['name'] == 'greet':
        # greet消息
        greet = [
            "Hello~",
            "Hey!",
            "Hi~",
            "Hey there~"
        ]
        update.message.reply_text(random.choice(greet))

    elif target['intent']['name'] == 'bot_challenge':
        # bot challenge消息
        bot = [
            "I'm Robot Emma. I can help you find billions of webpages, images and news. (๑•ᴗ•๑)♡",
            "My name is Robot Emma. I can help you find billions of webpages, images and news. (๑•ᴗ•๑)♡",
            "My name is Robot Emma, you can call me Emma. I can help you find billions of webpages, images and news. (๑•ᴗ•๑)♡"
        ]
        update.message.reply_text(random.choice(bot))

    elif target['intent']['name'] == 'mood_great':
        # mood great消息
        great = [
            "Great! o(^▽^)o",
            "Yeah! o(^▽^)o",
            "Cheers! o(^▽^)o"
        ]
        update.message.reply_text(random.choice(great))

    elif target['intent']['name'] == 'thanks':
        # thank消息
        thank = [
            "I am glad I can help. (ฅ◑ω◑ฅ)",
            "You are welcome. (ฅ◑ω◑ฅ)",
            "So kind of you. (ฅ◑ω◑ฅ)",
            "It is my pleasure. (ฅ◑ω◑ฅ)"
        ]
        update.message.reply_text(random.choice(thank))

    elif target['intent']['name'] == 'goodbye':
        # goodbye消息
        bye = [
            "bye ~",
            "goodbye ~",
            "see you around ~",
            "see you later ~",
            "see you ~"
        ]
        update.message.reply_text(random.choice(bye))

    else:
        update.message.reply_text(default)
        print("?")


# 消息回复功能
def msg(update, context):
    message = update.message.text

    result = match_rule(update, context, message)

    if result == False:
        respond(update, context, message)


msg_handler = MessageHandler(Filters.text, msg)
dispatcher.add_handler(msg_handler)
# ****************************************

# 启停
updater.start_polling()
# updater.idle()

# inline
from telegram import InlineQueryResultArticle, InputTextMessageContent


def inline_caps(update, context):
    query = update.inline_query.query
    if not query:
        return
    results = list()
    results.append(
        InlineQueryResultArticle(
            id=query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    context.bot.answer_inline_query(update.inline_query.id, results)


from telegram.ext import InlineQueryHandler

inline_caps_handler = InlineQueryHandler(inline_caps)
dispatcher.add_handler(inline_caps_handler)

