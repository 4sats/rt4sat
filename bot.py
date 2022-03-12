import tweepy,asyncio,json,requests,qrcode,os,time,config
from tweepy.asynchronous import AsyncStream
from database import Database

consumer_key = config.consumer_key
consumer_secret = config.consumer_secret
access_token = config.access_token
access_token_secret = config.access_token_secret
api_key = config.api_key
min_amount=config.min_amount

async def main():
    printer = IDPrinter(consumer_key, consumer_secret,access_token, access_token_secret)
    await printer.filter(track=[config.username])


class IDPrinter(AsyncStream):
    async def on_status(self, status):
      try:
        if hasattr(status, "_json"):
          print(status._json)
          ismentioned = False
          for mention in status.entities["user_mentions"]:
            if mention["screen_name"] == config.username:
              ismentioned = True
              break
          if ismentioned and (status.in_reply_to_status_id_str is not None):
            id = status.id_str
            amount = min_amount
            text = status.text.lower()
            cmd = text[text.rfind('@'+config.username):]
            s = cmd.split(" ")
            auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
            api = tweepy.API(auth)
            
            if len(s)>1:
                if s[1]=="unretweet":
                    real_status = api.get_status(status.in_reply_to_status_id_str)
                    if real_status.retweeted:
                        print("unretweet")
                        amount=Database().get_total_amount(status.in_reply_to_status_id_str)
                        create_transaction(id,status.in_reply_to_status_id_str,amount,1,"to unretweet this tweet")
                    else:
                        api.update_status("This tweet hasn't been retweeted yet!",in_reply_to_status_id=id,auto_populate_reply_metadata=True)
                        print("can't unretweet")
                elif int(s[1]) >= min_amount:
                    amount = int(s[1])
                    create_transaction(id,status.in_reply_to_status_id_str,amount,0,"to retweet this tweet")
                else:
                    create_transaction(id,status.in_reply_to_status_id_str,amount,0,"to retweet this tweet")
            else:
                create_transaction(id,status.in_reply_to_status_id_str,amount,0,"to retweet this tweet")
          return True
        else:
          # returning False disconnects the stream
          return False
      except:
        print("fucked")

def create_transaction(tweet_id,retweet_id,amount,unretweet,reason):
    print(amount)
    if amount > 4000000:
        amount = 4000000
    print("replied to",retweet_id)
    invoice = requests.post("https://legend.lnbits.com/api/v1/payments", data = '{"out": false,"amount":'+str(amount)+'}', headers = {"X-Api-Key": api_key,"Content-type": "application/json"})
    print(invoice.text)
    auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
    api = tweepy.API(auth)
    kk = invoice.json()
    img = qrcode.make(kk["payment_request"])
    type(img)  # qrcode.image.pil.PilImage
    img.save(str(tweet_id)+".png")
    api.update_status_with_media("Pay "+str(amount)+"sat with lightning "+reason,filename=str(tweet_id)+".png",in_reply_to_status_id=tweet_id,auto_populate_reply_metadata=True)
    os.remove(str(tweet_id)+".png")
    Database().add_user(tweet_id,retweet_id,kk["payment_hash"],kk["payment_request"],kk["checking_id"],amount,0,time.time(),unretweet)


asyncio.run(main())

