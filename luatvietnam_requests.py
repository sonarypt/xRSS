#!/usr/bin/env python3

import re
import os
import pytz
import time
import random
import requests
import datetime
from lxml import html
import xml.etree.cElementTree as ET
from xml.etree.ElementTree import fromstring

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

options = Options()
options.headless = True
mummy = webdriver.Firefox(executable_path='/usr/bin/geckodriver', options=options)
user_agent = mummy.execute_script("return navigator.userAgent;")
mummy.close()

main_d = "/data/user/code_scripts/python/xRSS"
rss_d = main_d + "/rss"
rssc_d = main_d + "/rss_conf"

def check_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

check_dir(rss_d)
check_dir(rssc_d)

pn = 2 # by default, get the newest 40 documents

host = 'luatvietnam.vn'
main_url = 'https://' + host

def line_prepender(filename, line): # prepend, use later
    with open(filename, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write(line.rstrip('\r\n') + '\n' + content)
        f.close()

def line_appender(filename, line): # append, use later
    with open(filename, 'a') as f:
        f.write(line)
        f.close()

def check_exist(filename, line): # check existence of line in file
    with open(filename, 'r') as f:
        if line not in f.read():
            return 1
        else:
            return 0

class Cat: # object for each section, link and rss xml file features
    def __init__(self, link, name, alias): # define name and link for shorter convention
        global main_url
        self.link = main_url + link
        self.name = name
        self.alias = alias
    
    self.xfile = rss_d + "/luatvietnam-" + self.alias + ".rss" # destination for RSS file XML
    self.xfile_conf = rssc_d + "/luatvietnam-" + self.alias + ".txt" # destination for RSS config file XML

    def xml_gen(self): # still work with object, not file parsing
        self.rss = ET.Element("rss", version="2.0") # default header for RSS file XML from here
        self.channel = ET.SubElement(self.rss, "channel") 
        ET.SubElement(self.channel, "title").text = "Luật Việt Nam - " + self.name
        ET.SubElement(self.channel, "description").text = "Luật Việt Nam RSS " + self.name
        self.image = ET.SubElement(channel, "image") # add favicon to XML file
        ET.SubElement(self.image, "url").text = "https://luatvietnam.vn/favicon.ico"
        ET.SubElement(self.image, "title").text = "Luật Việt Nam RSS - " + self.name
        ET.SubElement(self.image, "link").text = "https://luatvietnam.vn/"
        ET.SubElement(self.channel, "pubDate").text = cur_time # add published date
        ET.SubElement(self.channel, "generator").text = "xRSS project"
        ET.SubElement(self.channel, "link").text = "https://xrss.gotdns.ch/luatvietnam.rss"
    
    def add_item(self, doc, pos): # add item from doc object # still working with object, not file parsing
        if pos == 0: # put to the beginning
            nd = ET.Element("item")
            self.channel.insert(0, item)
        else: # just add as a SubElement
            item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = doc.name
        ET.SubElement(item, "description").text = d.description
        ET.SubElement(item, "pubDate").text = doc.d_publish
        ET.SubElement(item, "link").text = doc.link

    def log_item(self, doc, pos):
        if pos == 0: # prepend to beginning of file
            line_prepender(self.xfile_conf, doc.link)
        else: # normal append
            line_appender(self.xfile_conf, doc.link)

    def xml_write(self): # write RSS file in XML format
        tree = ET.ElementTree(self.rss)
        tree.write(self.xfile)
        line_prepender(self.xfile, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>") # only work for first time create file

# specify the regex for name searching
nr = re.compile(r"(\w| )*\d/(\w|-)*")

class Doc: # object document information
    def __init__(self, description, link, d_publish):
        global nr
        self.link = link                            # link of the document
        self.description = desc                     # description of the document
        self.d_publish = d_publish                  # date of publish
        self.name = nr.search(description).group    # name of documents need to be regexed

# write this single script, to generate 3 different RSS (van-ban-moi, van-ban-UBND, cong-van)
vbm = Cat('/van-ban-moi.html', 'Van Ban Moi', 'vbm')
ubnd = Cat('/van-ban-uy-ban-nhan-dan.html', 'Van Ban UBND', 'ubnd')
cv = Cat('/cong-van.html', 'Cong Van', 'cv')

vnm = pytz.timezone('Asia/Ho_Chi_Minh')
sgp = pytz.timezone('Asia/Singapore')   # run from Singapore server. Match timezone by yourself.
n = datetime.datetime.now()
n = sgp.localize(n)
cur_time = n.astimezone(vnm).strftime("%a, %d %b %Y %H:%M:23 %z")

headers = { # specify headers for requests
      'Host': host,
      'Connection': 'keep-alive',
      'User-Agent': user_agent,
      'Accept': '*/*',
      'Referer': main_url + '/',
      'Accept-Language': 'en-US,en;q=0.9'
      }

# work with RSS file XML format from each instances
# scrape requests with xml https://docs.python-guide.org/scenarios/scrape/
# do not need beautifulsoup anymore

for cat in [vbm, ubnd, cv]: # loop through all instances of Cat class
    xml_gen(cat)
    if not os.path.exists(cat.xfile): # check if RSS file XML exists first
        url = cat.link # continue to crawl
        for i in range(1, pn+1):
            url = cat.link + "?page=" + str(i)
            r = requests.get(url, headers=headers)
            h = html.fromstring(r.content)
            for d in h.xpath("//div[@class='boxs-content']//tbody/tr"):
                dd1 = d.xpath("/td[@class='col_news']/h3[@class='title_post']/a")
                dl = dd1.attrib['href']
                desc = dd.attrib['title']
                dp = d.xpath("/td[@class='col_time']/div[1]/span[@class='color2-cn']/text()")
                doc = Doc(desc, dl, dp)
                cat.add_item(doc, 1)
                cat.log_item(doc, 1)
    else: # when RSS file XML exists, process log file
        url = cat.link
        r = requests.get(url, headers=headers)
        h = html.fromstring(r.content)
        cat.rss = ET(fromstring(open(cat.xfile, 'r'))).getroot() # dont forget to parse old RSS file
        cat.channel = cat.rss.find('channel')
        # do not need to count for new documents
        # just check the first documents and reverse the list to check more
        first_a = h.xpath("//tbody/tr[1]/td[@class='col_news']/h3[@class='title_post']/a") # first link
        first_link = first_a.attrib['href']
        if check_exist(cat.xfile_conf, first_link): # first link is known
            quit()
        else: # first link is new
            for d in h.xpath("//div[@class='boxs-content']//tbody/tr").reverse(): # reverse the list so as to append 
                dd1 = d.xpath("/td[@class='col_news']/h3[@class='title_post']/a")
                dl = dd1.attrib['href']
                if check_exist(cat.xfile_conf, dl):
                    continue # continue search for new document(s)
                else:
                    desc = dd.attrib['title']
                    dp = d.xpath("/td[@class='col_time']/div[1]/span[@class='color2-cn']/text()")
                    doc = Doc(desc, dl, dp)
                    cat.add_item(doc, 0)
                    cat.log_item(doc, 0) # append to head of item list
                    # remove last item from item list
        # remove documents having index larger than 20*pn
    cat.xml_write()

# TODO
# how to check for new files, how to record, and check if there is old documents (need databases to handle)
# problem in working between files and objects.
# need to find optimal time to check for update (hourly or daily, due to frequency of web owners)
