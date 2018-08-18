import discord
import asyncio

async def main():
    client = discord.Client()
    print("x")
   
    await client.login("yrwvqkij@sharklasers.com","password12345")
    await client.wait_until_login()
    print("y")
    if client.is_logged_in:
        print("True")
   # await client.connect()

    print(client.is_closed)
    print(list(client.servers))
    
    for server in client.servers:
        for member in server.members:
            print(member)

    async for emoji in emojis:
        print(emoji)


loop = asyncio.get_event_loop()
task = loop.create_task(main())
loop.run_until_complete(task)
