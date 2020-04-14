# -*- coding: utf-8 -*-
"""
Created on Sun Mar 29 20:23:54 2020

@author: micha
"""
# Requires importin BeutifulSoup and urllib
from bs4 import BeautifulSoup
import urllib
import nltk
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
import pandas as pd
import numpy as np
import re
import selenium
from selenium import webdriver
from nltk.stem import PorterStemmer

#%% Define the getArticle function to download the url and return the text
##############################################################################
def getArticle(url, token):
    try:
        page = urllib.request.urlopen(url).read().decode('utf8')
        
    except:
        return (None,None, None)
    webPage = BeautifulSoup(page, 'lxml')
    if webPage is None:
        return(None, None, None)
    
    textPage = ""
    if webPage.find_all(token) is not None:
        textPage = ''.join(map(lambda p: p.text, webPage.find_all(token)))
        webPage2 = BeautifulSoup(textPage, 'lxml')
        if webPage2.find_all('p') is not None:
            textPage = ''.join(map(lambda p: p.text, webPage2.find_all('p')))
            if textPage == None:
                textPage = ['No text in url, MOFO']
    if textPage and webPage.title.text != None:
        return textPage, webPage.title.text, webPage
    else:
        return None, None, None
    
    

#%% Define the cleanText function to process the text data
##############################################################################

def cleanText(text, customStopWords=None):
    try:
        sentances = sent_tokenize(text)
        wordSent = [word_tokenize(s.strip().lower()) for s in sentances]
        tokens = []
        for word in wordSent:
            for subWord in word:
                tokens.append(subWord)
        words = [w for w in tokens if w.isalpha()]
        if customStopWords is None:
            stop_words = set(stopwords.words('english'))
        else:
            stop_words = customStopWords
        processed = [w for w in words if w not in stop_words]
        porter = PorterStemmer()
        stemmed = [porter.stem(w) for w in processed]
        return stemmed
    except:
        return ['The article contained no text']

#%% use selenium to gather the urls from the COVID archive
#########################################################################
driver = webdriver.Chrome()
driver.get('https://www.covid19-archive.com/')
urls=[]
for page in range(0,250): 
    try:
        ids = driver.find_elements_by_xpath('//*[@href]')
        [urls.append(id.get_attribute('href')) for id in ids]
        nButton = driver.find_element_by_id('tablepress-10000_next')
        nButton.click()
    except:
        nButton = driver.find_element_by_id('tablepress-10000_next')
        nButton.click()
    
driver.quit()
urls = list(dict.fromkeys(urls))

#%% Kick the football 
###########################################################################
token = 'article'
url = ''
#text, title = getArticle(url, token)
site=[]
counter = 0
content = {}
art = pd.DataFrame(index=range(0,len(urls)), columns = ['site', 'title', 'url', 'text', 'webPage'])
for url in urls:
    if url[0:len('https://web.archive.org')] == 'https://web.archive.org' and url[0:len('https://s.w')] != 'https://s.w':
        site = url.split('/https://')[-1].split('/')[0]
        text, title, webPage = getArticle(url, token)
        if text == None or text == '':
            next
        else:
            text = cleanText(text)
            art.iloc[counter,0] = site
            art.iloc[counter,1] = title
            art.iloc[counter,2] = url
            art.iloc[counter,3] = text
            art.iloc[counter,4] = webPage
            counter += 1
            print(site +' - article ' + str(counter) + '/' + str(len(urls)))
            if site not in content.keys():
                content[site] = {}
                content[site][title] = text
            else:
                content[site][title] = text
    else:
        next

#%% Save the art data as a pickle for transport
art.to_pickle('articla_data.pkl')


    

 
