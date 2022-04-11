from flask import Flask, request, abort

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        print(request.json)
        try:
            users = Database().get_all_users()
            for user in users:
                if user[7]==0:
                    checkinvoice = requests.get("https://legend.lnbits.com/api/v1/payments/"+str(user[3]), headers = {"X-Api-Key": config.api_key,"Content-type": "application/json"})
                    #print(checkinvoice.text)
                    kk=checkinvoice.json()
                    if kk["paid"]==True:
                        Database().set_ispaid(1, user[0])
                        auth = tweepy.OAuth1UserHandler(config.consumer_key, config.consumer_secret, config.access_token, config.access_token_secret)
                        api = tweepy.API(auth)
                        if user[9]==1:
                            api.unretweet(user[2])
                            print(user[0],"unretweeted!")
                        else:
                            api.retweet(user[2])
                            print(user[0],"retweeted")
                    elif ((time.time()-user[8])>1200):
                        Database().delete_row(user[0])
        except Exception as e:
            print(e)
        return 'success', 200
    else:
        abort(400)

if __name__ == '__main__':
    app.run()