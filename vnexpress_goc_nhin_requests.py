#!/usr/bin/env python3
###############################################################################
# author        : Hoang Nguyen 
# email         : nvhhnvn@gmail.com
# script name   : vnexpress_goc_nhin_requests.py
# description   : make RSS xml file from vnexpress.net goc_nhin column
###############################################################################

import re
import os
import pytz
import time
import random
import requests
import datetime
from bs4 import BeautifulSoup
import xml.etree.cElementTree as ET

if not os.path.exists('/home/user/scripts/python/rss'):
   os.makedirs('/home/user/scripts/python/rss')
if not os.path.exists('/home/user/scripts/python/rss_conf'):
   os.makedirs('/home/user/scripts/python/rss_conf')

url = 'https://vnexpress.net/goc-nhin'

headers = {
      'Host': 'vnexpress.net',
      'Connection': 'keep-alive',
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36',
      'Accept': '*/*',
      'Referer': 'https://vnexpress.net/',
      'Accept-Language': 'en-US,en;q=0.9'
      }

r = requests.get(url, headers=headers)
html = BeautifulSoup(r.text, "html.parser")

vnm = pytz.timezone('Asia/Ho_Chi_Minh')
sgp = pytz.timezone('Asia/Singapore')
n = datetime.datetime.now()
n = sgp.localize(n)
cur_time = n.astimezone(vnm).strftime("%a, %d %b %Y %H:%M:23 %z")

title = []
author = []
link = []
pub = []
description = []

def get_time(link):
    time.sleep(random.randint(1,20))
    link_r = requests.get(link, headers=headers)
    link_html = BeautifulSoup(link_r.text, "html.parser")
    their_time = link_html.find("span", {"class": "time"}).getText().strip()
    our_time = (their_time.rsplit(',', 2)[1] + their_time.rsplit(',', 2)[2]).strip()
    ttime = our_time.rsplit(' ', 2)[0] + " " + our_time.rsplit(' ', 2)[1]
    final_time = datetime.datetime.strptime(
            ttime, '%d/%m/%Y %H:%M'
            ).strftime('%a, %d %b %Y %H:%M:23 +0700')
    return final_time

def time2file(file, time):
    with open(file, 'a') as stat:
        stat.write(time + "\n")
        stat.close()

# information from featured article
featured_header = html.find("h1", {"class": "title_featured"})
tt = featured_header.getText().strip()
title.append(tt)
if os.path.exists("/home/user/scripts/python/rss_conf/vnexpress_fh.txt"):
    with open("/home/user/scripts/python/rss_conf/vnexpress_fh.txt", 'r+') as fheader:
        fh = fheader.read()
        if fh == tt:
            print("Already Updated")
            time2file("/home/user/scripts/python/rss_conf/check_stat.txt", cur_time)
            exit()
        else:
            fheader.seek(0,0)
            fheader.write(tt)
            fheader.close()
else:
    with open("/home/user/scripts/python/rss_conf/vnexpress_fh.txt", 'w') as fheader:
        fheader.write(tt)
        fheader.close()

featured_link = featured_header.find("a")['href']
link.append(str(featured_link))
pub.append(get_time(featured_link))
featured_author = html.find("p", {"class": "author"}).getText().strip()
author.append(featured_author)

featured_description = html.find("h2", {"class": "description"}).getText().strip()
description.append(featured_description)

# work with side_featured title
for side_featured in html.find_all("article", {"class": "list_side_featured exclude"}):
    for h3 in side_featured.find_all("h3", {"class": "title_side_featured"}):
        title.append(h3.getText().strip())
        l = h3.find("a")['href']
        link.append(l)
        pub.append(get_time(l))
    for au in side_featured.find_all("span", {"class": "meta_author"}):
        author.append(au.getText().strip())
    for dsc in side_featured.find_all("p", {"class": "description"}):
        description.append(dsc.getText().strip())

# work with all article in class "list_item clearfix"
for article in html.find_all("section", {"class": "sidebar_2"}):
    # find all remaining articles's titles
    for h2 in article.find_all("h2", {"class": "title_item"}):
        title.append(h2.getText().strip())
        l = h2.find("a")['href']
        link.append(l)
        pub.append(get_time(l))
    # find all remaining authors's names
    for au in article.find_all("span", {"class": "meta_author"}):
        author.append(au.getText().strip())
    for dsc in article.find_all("p", {"class": "description"}):
        description.append(dsc.getText().strip())

num = len(title)

rss = ET.Element("rss", version="2.0")
channel = ET.SubElement(rss, "channel")
ET.SubElement(channel, "title").text = "Góc nhìn - VnExpress RSS"
ET.SubElement(channel, "description").text = "VnExpress RSS"

image = ET.SubElement(channel, "image")
ET.SubElement(image, "url").text = "https://s.vnecdn.net/vnexpress/i/v20/logos/vne_logo_rss.png"
ET.SubElement(image, "title").text = "Góc nhìn - VnExpress RSS"
ET.SubElement(image, "link").text = "https://vnexpress.net"

ET.SubElement(channel, "pubDate").text = cur_time
ET.SubElement(channel, "generator").text = "RSS.GOTDNS.CH"
ET.SubElement(channel, "link").text = "https://rss.gotdns.ch/goc_nhin.rss"

for i in range(0, num):
    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title[i]
    ET.SubElement(item, "description").text = description[i]
    ET.SubElement(item, "pubDate").text = pub[i]
    ET.SubElement(item, "link").text = link[i]
    ET.SubElement(item, "author").text = author[i]

tree = ET.ElementTree(rss)
tree.write("/home/user/scripts/python/rss/goc_nhin.rss")

with open("/home/user/scripts/python/rss/goc_nhin.rss", 'r+') as f:
    content = f.read()
    f.seek(0,0)
    f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>" + content)
    f.close()

time2file("/home/user/scripts/python/rss_conf/check_stat.txt", cur_time)
