#-*- coding: utf-8 -*-
import tweepy
import json
import time
import traceback
import sys
import gzip
import argparse
import codecs
import glob
import os


# This is the listener, resposible for receiving data
class StdOutListener(tweepy.StreamListener):

    def __init__(self, f_out, f_log, langs):
        tweepy.StreamListener.__init__(self)
        self.f_out=f_out
        self.f_log=f_log
        self.langs=langs

    def on_data(self, data):
        # Twitter returns data in JSON format - we need to decode it first
        decoded = json.loads(data)
        
        if "lang" in decoded and decoded["lang"] in self.langs:
            print >> self.f_log, decoded["lang"], decoded["text"].replace(u"\n",u" ").encode("utf-8")
            self.f_log.flush()
            print >> self.f_out, data
            print >> self.f_out
        else:
            pass
        return True

    def on_error(self, status):
        print "Error",status

if __name__=="__main__":
    parser = argparse.ArgumentParser(description='Train')
    parser.add_argument('--hashtags', default="hashtags.conf", help='List of hashtags. Default %(default)s')
    parser.add_argument('--outname', default="tweets", help='Name of the output file. Default %(default)s')
    parser.add_argument('--langs', default="fi,fr,en", help='Comma-seprated list of langs. Default %(default)s')
    parser.add_argument('--secrets', default="secrets.json", help='Json dictionary with consumer_key, consumer_secret, access_token, access_token_secret. Default %(default)s')
    args = parser.parse_args()
    # There are different kinds of streams: public stream, user stream, multi-user streams
    # In this example follow #programming tag
    # For more details refer to https://dev.twitter.com/docs/streaming-apis

    htags=set()
    with codecs.open(args.hashtags,"r","utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            htags.add(line)
    htags=sorted(htags)
    print >> sys.stderr, "STARTED", time.asctime(), (u", ".join(htags)).encode("utf-8")
    print >> sys.stderr

    with open(args.secrets) as f:
        secrets=json.loads(f.read())

    langs=args.langs.split(",")
    files=sorted(glob.glob(args.outname+"_*.json.gz"))
    if not files:
        f_num=0
    else:
        f_num=int(files[-1].replace(".json.gz","").split("_")[-1])
        if os.path.getsize(files[-1])>1000: #This is a real output file, make a new one
            f_num+=1

    if f_num>10000: #this should never happen
        sys.exit(1)

    f_out=gzip.open("%s_%05d.json.gz"%(args.outname,f_num),"w")
    f_log=gzip.open("%s_%05d.txt.gz"%(args.outname,f_num),"w")
    

    #stream.filter(track=[],languages=["fi"])
    while True:
        try:
            l = StdOutListener(f_out,f_log,langs)
            auth = tweepy.OAuthHandler(secrets["consumer_key"], secrets["consumer_secret"])
            auth.set_access_token(secrets["access_token"], secrets["access_token_secret"])
            stream = tweepy.Stream(auth, l)
            stream.filter(track=htags,languages=langs)
        except:
            traceback.print_exc()
            time.sleep(10)
