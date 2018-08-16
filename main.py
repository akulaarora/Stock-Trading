'''
This is a script for analyzing information about stock changes on the Pennystocks Discord Server.
Author: Akul Arora
Date: 08/16/2018
'''

import discord
import asyncio

def main(argv):
    # Connection
    client = discord.Client()
    try:
        await client.login(argv[0],argv[1])
    except LoginFailure:
        print("Incorrect login")
    except HTTPException:
        print("HTTP Error")
    except Exception as e:
        print(e)

    # Get messages from #trades channel
    trade_channel = client.get_channel(TODO)
    try:
        messages_generator = client.logs_from(trade_channel)
    except Forbidden:
        print("Cannot access #trades channel")
    except NotFound:
        print("Channel does not exist")
    except HTTPException:
        print("Could not connect to the server")
        
    # Get a list of percentages
    percentages = get_percentages(messages_generator)

    # add percentages
    sum_percents = 0
    for percent in percentages:
        sum_percents += percent

    print("Total sum of percentages: %d " % (sum_percents))
    
def get_percentages(generator):
    percentages = []
    
    async for message in generator:
        contents = message.contents
        if "sold" in contents and "%" in contents:
            # using rfind() to avoid potential % or spaces before the intended one
            str_percent = contents[0:contents.rfind("%")] # string from 0 to (non-inclusive) % symbol
            str_percent = str_percent[str_percent.rfind(" ")+1:len(str_percent)]

            percentages.append(int(str_percent))

    return percentages

if __name__ == "__main__":
    main(sys.argv[1:]) # pass username and password
