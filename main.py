'''
This is a script for analyzing information about stock changes on the Pennystocks Discord Server.
Author: Akul Arora
Date: 08/16/2018
'''

import discord
import asyncio
import sys

def main(argv):
    CHANNEL_ID = '308090934099181571'
    loop = asyncio.get_event_loop()
    
    # Connection. Creates asynchronous task
    connect_task = loop.create_task(connect_discord(argv))
    client = loop.run_until_complete(connect_task)

    # Get messages from #trades channel
    trade_channel = client.get_channel(CHANNEL_ID)

    # Get the generator for retrieving messages on #trades.
    generator = channel.logs_from(trade_channel, limit=100) # TODO error handling
    
    # Get a list of percentages. Creates asynchronous task
    get_task = loop.create_task(get_percentages(generator))
    percentages = loop.run_until_complete(get_task)

    # add percentages
    sum_percents = 0
    for percent in percentages:
        sum_percents += percent

    print("Total sum of percentages: %d " % (sum_percents))

    # Close connection
    close_task = loop.create_task(client.close())
    loop.run_until_complete(close_task)

async def connect_discord(argv):
    client = discord.Client()

    await client.login(argv[0],argv[1])
    #try:
        
    #except LoginFailure: # TODO NameError cannot find LoginFailure
    #    print("Incorrect login")
    #except HTTPException:
     #   print("HTTP Error")
    #except Exception as e:
     #   print(e)

    client.connect() # TODO error handling
    for x in client.servers:
        print(x)
    return client
    
async def get_percentages(logs_generator):
    percentages = []

    async for message in logs_generator:
        contents = message.content
        if "sold" in contents and "%" in contents:
            # using rfind() to avoid potential % or spaces before the intended one
            str_percent = contents[0:contents.rfind("%")] # string from 0 to (non-inclusive) % symbol
            str_percent = str_percent[str_percent.rfind(" ")+1:len(str_percent)]
            print("Done")
            percentages.append(int(str_percent))

    percentages.get_type()
    return percentages

if __name__ == "__main__":
    main(sys.argv[1:]) # pass username and password
