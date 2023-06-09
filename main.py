#  @rondevv
#  FARMSTACK Tutorial - Sunday 13.06.2021

# import asyncio
import asyncio
from datetime import date
import http
import time
from typing import Union
from fastapi import FastAPI, Body, Depends, HTTPException, Security, status
import httpx
from pydantic import BaseModel
from fastapi.security import APIKeyHeader, APIKeyQuery
from dataclasses import dataclass
from typing import List
import json
import os
import openai
import pydantic
import regex
import pandas as pd
from bson import ObjectId
pydantic.json.ENCODERS_BY_TYPE[ObjectId]=str


import requests

from model import Article, Todo
# from send import run

# azure imports and variables
# import asyncio
# from azure.servicebus.aio import ServiceBusClient
# from azure.servicebus import ServiceBusMessage
# from azure.identity.aio import DefaultAzureCredential

# FULLY_QUALIFIED_NAMESPACE = "dayInHistory.servicebus.windows.net"
# ARTICLE_QUEUE_NAME = "articlequeue"
# HEADLINE_QUEUE_NAME = "headlinequeue"
# credential = DefaultAzureCredential()


# OPEN AI TO DO SEPARATE

OAI_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"

# @dataclass
# class Message:
#     role: str
#     content: str

# @dataclass
# class OpenAiHeadlines(BaseModel):
#     model: str
#     messages: List[Message]

    # Define a list of valid API keys
OPENAI_API_KEY = "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"

# # Define the name of query param to retrieve an API key from
# api_key_query = APIKeyQuery(name="api-key", auto_error=False)
# # Define the name of HTTP header to retrieve an API key from
# api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


# def get_api_key(
#     api_key_query: str = Security(api_key_query),
#     api_key_header: str = Security(api_key_header),
# ):
#     """Retrieve & validate an API key from the query parameters or HTTP header"""
#     # If the API Key is present as a query param & is valid, return it
#     if api_key_query in API_KEYS:
#         return api_key_query

#     # If the API Key is present in the header of the request & is valid, return it
#     if api_key_header in API_KEYS:
#         return api_key_header

#     # Otherwise, we can raise a 401
#     raise HTTPException(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         detail="Invalid or missing API Key",
#     )
# 

from database import (
    create_article,
    fetch_all_articles,
    fetch_config,
    fetch_one_article,
    fetch_one_todo,
    fetch_all_todos,
    create_todo,
    remove_article,
    update_article,
    update_todo,
    remove_todo,
)

# an HTTP-specific exception class  to generate exception information

from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

origins = [
    "http://localhost:3000",
]

# what is a middleware? 
# software that acts as a bridge between an operating system or database and applications, especially on a network.

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/api/todo")
async def get_todo():
    response = await fetch_all_todos()
    return response

@app.get("/api/todo/{title}", response_model=Todo)
async def get_todo_by_title(title):
    response = await fetch_one_todo(title)
    if response:
        return response
    raise HTTPException(404, f"There is no todo with the title {title}")

@app.post("/api/todo/", response_model=Todo)
async def post_todo(todo: Todo):
    response = await create_todo(todo.dict())
    if response:
        return response
    raise HTTPException(400, "Something went wrong")

@app.put("/api/todo/{title}/", response_model=Todo)
async def put_todo(title: str, desc: str):
    response = await update_todo(title, desc)
    if response:
        return response
    raise HTTPException(404, f"There is no todo with the title {title}")

@app.delete("/api/todo/{title}")
async def delete_todo(title):
    response = await remove_todo(title)
    if response:
        return "Successfully deleted todo"
    raise HTTPException(404, f"There is no todo with the title {title}")

#open ai api SECOND FUNCTION

@app.post("/api/article/OpenAI_custom", tags=["Article"])
async def post_article_custom(category: str, start_date: date):
       

    try:
        config = await fetch_config()

        #Get date range and iterate
        articleList = []
        
        #OG
        phrase = config.get_headlines_phrase.replace("REPLACE_CATEGORY", category)
        phrase = phrase.replace("REPLACE_HEADLINE_COUNT", str(config.headlines_per_category_count))
        #1978-01-21
        phrase = phrase.replace("REPLACE_DATE", str(start_date.strftime("%B %d, %Y")))
        print(phrase)

        openai.api_key = OPENAI_API_KEY
        
        # list models
        models = openai.Model.list()

        # print the first model's id
        print(models.data[0].id)

        rawHeadlines = ""
        number = 0
        
        # create a chat completion
        print("*openai.ChatCompletion.create*")
        chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": phrase}])
        # print the chat completion
        print("print the chat completion: ")
        print(chat_completion.choices[0].message.content)
        rawHeadlines = chat_completion.choices[0].message.content

        # ### uhhh
            
        print("rawHeadlines is: " + rawHeadlines)
        startIndex = str(rawHeadlines).index('1.')
        OpenAiMessage = rawHeadlines[0:startIndex]
        print("OpenAiMessage is: " + OpenAiMessage)
        headlines_String = rawHeadlines[startIndex-1:len(rawHeadlines)]
        print("headlines_String is: " + headlines_String)
        # print("index is: " + str(startIndex))
        
        #FIXME split the headlines by numbers list 1. 2. 3. ...
        # headlines = regex.split("\d+(?:\.\d+)*[\s\S]*?\w+\.", headlines_String)
        headline_list =  regex.split("\d+\.", str(headlines_String))
        print("test test test")
        print("headline_list: ")
        print(headline_list)


        # CUSTOM HEADLINES TEST
        # headline_list = {"red sparrow", "blue bird"}

        # creating list
        list = []
        today = date.today()

        #for every single headline in the list, create headlines
        for headline in headline_list:
            print("foreach headline isCUSTOM: " + headline)
            
            d1 = today.strftime("%d/%m/%Y")

            #TODO RETRY 5 TIMES UNTIL ARTICLE IS NOT EMPTY
            essay = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Write a " + str(config.article_body_character_limit) + " character essay about the topic of" + headline}])
            
            article = Article(title=headline, body=essay.choices[0].message.content, datecreated=date.today().strftime("%Y-%m-%d"), dayOfTheYear=start_date.strftime("%Y-%m-%d"), Category=category)
            
            try:
                
                # doc = vars(article)
                #add to mongo
                result = await create_article(article.dict())
                #FIXME RETURNS JUST FOR ONE ARTICLE / ONE DAY / do for every day in date range
                # return result
        
            except Exception as error:
            
                return ('An exception occurred: {}'.format(error))
            # appending instances to list
            # list.append(Article(title=headline, body=essay.choices[0].message.content, date=date.today()))
            articleList.append(Article(title=headline, body=essay.choices[0].message.content, date=date.today()))

            # if list:
            #     return list
            # raise HTTPException(400, "Something went wrong")
            
        if articleList:
                return articleList
        raise HTTPException(400, "Something went wrong")
    
    except Exception as error:
        return ('An exception occurred: {}'.format(error))


##open ai api

@app.post("/api/article/OpenAI", tags=["Article"])
async def post_article(start_date: date, end_date: date):
       

    try:
        config = await fetch_config()

        #Get date range and iterate
        daterange = pd.date_range(str(start_date), end_date)
        articleList = []
        #creating articles between a date range vs a single day
        for single_date in daterange:

            #TODO refactor each_category
            #creating articles for every single category in the config file
            #**********************************************************************
            #run using async
            run_each_category = each_category(single_date)
            # asyncio.run(run_create_articles)
            articleList += await run_each_category
            #**********************************************************************

            
            # return articleList
        if articleList:
                return articleList
        raise HTTPException(400, "Something went wrong")
    
    except Exception as error:
        return ('An exception occurred: {}'.format(error))


async def each_category( single_date: date):
    articleList = []
    #
    try:
        config = await fetch_config()
        # for each category in Config.categories 
        for category in config.categories:

                #Sleep
                time.sleep(config.open_ai_request_sleep_mls)

                phrase = config.get_headlines_phrase.replace("REPLACE_CATEGORY", category)
                phrase = phrase.replace("REPLACE_HEADLINE_COUNT", str(config.headlines_per_category_count))
                #1978-01-21
                phrase = phrase.replace("REPLACE_DATE", str(single_date.strftime("%B %d, %Y")))
                print(phrase)

                openai.api_key = OPENAI_API_KEY
                
                # list models
                models = openai.Model.list()

                # print the first model's id
                print(models.data[0].id)

                rawHeadlines = ""
                number = 0
                hasHeadlines = False
                print("hasHeadlines is " + str(hasHeadlines))
                #keep creating headlines if openAI fails to generate headlines the first time
                while hasHeadlines==False & number < config.headline_retry_count:
                    print("WHILE hasHeadlines is " + str(hasHeadlines))
                    print("WHILE retryCount is " + str(config.headline_retry_count))
                    
                    # create a chat completion
                    print("*openai.ChatCompletion.create*")
                    chat_completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": phrase}])
                    # print the chat completion
                    print("print the chat completion: ")
                    print(chat_completion.choices[0].message.content)
                    rawHeadlines = chat_completion.choices[0].message.content
                    number = number + 1

                    if "1." in rawHeadlines: 
                        hasHeadlines=True
                        print("*hasHeadlines = " + str(hasHeadlines))

                if hasHeadlines:
                    
                    print("rawHeadlines is: " + rawHeadlines)
                    startIndex = str(rawHeadlines).index('1.')
                    OpenAiMessage = rawHeadlines[0:startIndex]
                    print("OpenAiMessage is: " + OpenAiMessage)

                    # headlines_String = rawHeadlines[startIndex-1:len(rawHeadlines)]
                    # print("headlines_String is: " + headlines_String)
                    # print("index is: " + str(startIndex))
                    
                    #FIXME split the headlines by numbers list 1. 2. 3. ...
                    # headlines = regex.split("\d+(?:\.\d+)*[\s\S]*?\w+\.", headlines_String)
                    # headline_list =  regex.split("\d+\. ", str(headlines_String))
                    if "1) " in rawHeadlines:
                        headline_list =  regex.split("\d+\) ", str(rawHeadlines))
                    else:
                        headline_list =  regex.split("\d+\. ", str(rawHeadlines))

                    print("headline_list: ")
                    print(headline_list)

                    # creating list
                    list = []
                    today = date.today()

                    #TODO refacted "create_articles"... 
                    #**********************************************************************
                    category_string = str(category)
                    single_date_string = single_date.strftime("%Y-%m-%d")
                    #run using async
                    run_create_articles = create_articles_from_headlineList(headline_list, single_date_string, category_string)
                    # asyncio.run(run_create_articles)
                    articleList += await run_create_articles
                    #**********************************************************************
                    
                else:
                    return ('No Headlines were received')
            # return....
    except Exception as error:
        return ('An exception occurred: {} in each_category'.format(error))
    return articleList

async def create_articles_from_headlineList(headlines_list: list, single_date: str, category_string: str):
    articlesList = []
    articleCounter = 0
    today = date.today()
    print("****ENTERED create_articles...****")
    #
    try:
        config = await fetch_config()
        for headline in headlines_list:

            if headline !="":

                print("foreach headline is (CREATE): " + headline)
                
                d1 = today.strftime("%d/%m/%Y")

                #TODO RETRY 5 TIMES UNTIL ARTICLE IS NOT EMPTY
                essay = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": "Write a " + str(config.article_body_character_limit) + "minimum word essay about the topic of" + headline}])
                # print("essay: " + str(essay.choices[0].message.content))
                articleRetryCount=0
                hasArticle=False

                if essay.choices[0].message.content !="":
                    while hasArticle==False & articleRetryCount < config.headline_retry_count:
                        time.sleep(config.open_ai_request_sleep_mls)

                        article = Article(title=headline, body=essay.choices[0].message.content, datecreated=date.today().strftime("%Y-%m-%d"), dayOfTheYear=single_date, Category=category_string, readcount=0)
                        articleRetryCount+1
                        if essay.choices[0].message.content!="":
                            hasArticle=True
                            print("article: " + str(article.body))
                            try:
                                
                                # doc = vars(article)
                                #add to mongo
                                result = await create_article(article.dict())
                                #FIXME RETURNS JUST FOR ONE ARTICLE / ONE DAY / do for every day in date range
                                # return result
                                articleCounter+=1
                                print("FINISHED ARTICLE #" + str(articleCounter) + " FOR CATEGORY: ::::::::::::::::::::::::" + category_string)
                            except Exception as error:
                                return ('An exception occurred: {}'.format(error))
                            # appending instances to list
                            # list.append(Article(title=headline, body=essay.choices[0].message.content, date=date.today()))
                            articlesList.append(Article(title=headline, body=essay.choices[0].message.content, date=date.today()))
                else:
                    print("essay machine broke. ")
    except Exception as error:
        return ('An exception occurred: {} in create_articles_from_headlineList'.format(error))
    return articlesList

#######################  get / post for article###########################################################################
@app.get("/api/article", tags=["Article"])
async def get_article():
    response = await fetch_all_articles()
    return response

@app.get("/api/article/{title}", response_model=Article, tags=["Article"])
async def get_article_by_title(title):
    response = await fetch_one_article(title)
    if response:
        return response
    raise HTTPException(404, f"There is no todo with the title {title}")

@app.post("/api/article/", response_model=Article, tags=["Article"])
async def post_article(article: Article):
    response = await create_article(article.dict())
    if response:
        return response
    raise HTTPException(400, "Something went wrong")

@app.put("/api/article/{title}/", response_model=Article, tags=["Article"])
async def put_article(title: str, body: str):
    response = await update_article(title, body)
    if response:
        return response
    raise HTTPException(404, f"There is no todo with the title {title}")


@app.delete("/api/article/{title}", tags=["Article"])
async def delete_article(title):
    response = await remove_article(title)
    if response:
        return "Successfully deleted todo"
    raise HTTPException(404, f"There is no todo with the title {title}")

#####################################################################################################












#azure
# async def send_single_message(sender):
#     # Create a Service Bus message and send it to the queue
#     message = ServiceBusMessage("Single Message")
#     await sender.send_messages(message)
#     print("Sent a single message")

# async def send_a_list_of_messages(sender):
#     # Create a list of messages and send it to the queue
#     messages = [ServiceBusMessage("Message in list") for _ in range(5)]
#     await sender.send_messages(messages)
#     print("Sent a list of 5 messages")

# async def send_batch_message(sender):
#     # Create a batch of messages
#     async with sender:
#         batch_message = await sender.create_message_batch()
#         for _ in range(10):
#             try:
#                 # Add a message to the batch
#                 batch_message.add_message(ServiceBusMessage("Message inside a ServiceBusMessageBatch"))
#             except ValueError:
#                 # ServiceBusMessageBatch object reaches max_size.
#                 # New ServiceBusMessageBatch object can be created here to send more data.
#                 break
#         # Send the batch of messages to the queue
#         await sender.send_messages(batch_message)
#     print("Sent a batch of 10 messages")

# async def run():
#     # create a Service Bus client using the credential
#     async with ServiceBusClient(
#         fully_qualified_namespace=FULLY_QUALIFIED_NAMESPACE,
#         credential=credential,
#         logging_enable=True) as servicebus_client:
#         # get a Queue Sender object to send messages to the queue
#         sender = servicebus_client.get_queue_sender(queue_name=HEADLINE_QUEUE_NAME)
#         async with sender:
#             # send one message
#             await send_single_message(sender)
#             # send a list of messages
#             #await send_a_list_of_messages(sender)
#             # send a batch of messages
#             #await send_batch_message(sender)

#         # Close credential when no longer needed.
#         await credential.close()
# define a custom coroutine

 
# asyncio.run(run())
# print("Done sending messages")
# print("-----------------------")


    