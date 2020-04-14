# -*- coding: utf-8 -*-
"""
Created on Sat Apr  4 13:12:30 2020

@author: michaeltrent
"""

# This code will be a function to scrap the NY times politics
#health and wellness, science and

import requests
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
from collections import defaultdict
from heapq import nlargest
import os

#%% Define the function to download the NYT articles
##############################################################################
def getArticle(url, token='article', func='getWP'):
    if func == 'NYT': #if the site is NYT use this function
        try:
            webPage = urllib.request.urlopen(url).read().decode('utf8')
        except:
            return None, None, None
        soup = BeautifulSoup(webPage)
        if soup is None:
            return None, None, None
        # If there is no soup, we want to return nothing
        text = ""
        title = soup.find('title').text
        divs = soup.findAll('p', {'class':'story-body-text story-content'})
        text = text.join(map(lambda p:p.text, divs))
        # for sec in range(0,10):
        #         print('sleeping for: ' + str(sec) + ' seconds')
        #         time.sleep(1)
        return text, title, webPage
    else: # this is the original getWPT function that seems to work well
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
            # for sec in range(0,10):
            #     print('sleeping for   :' + str(sec) + ' seconds')
            #     time.sleep(1)
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


#%% This bit will grab all urls from for a given subject
##############################################################################

def urlScrape(siteUrl, years, category):
    errorURL = {}
    request = urllib.request.Request(siteUrl)
    response = urllib.request.urlopen(request)
    soup = BeautifulSoup(response, 'lxml')
    content = {}   
    articles = pd.DataFrame(columns = ['site', 'category', 'title', 'url', 'text', 'processedText','webPage'])
    counter = 0
    errorCounter = 0
    
    for a in soup.findAll('a'):
        try:
            url = a['href']
            for year in years:
                if years is not None and year in url or year is None: 
                    text, title, html = getArticle(url) #Grab the article
                    if text == None or text == '':
                        next
                    else:
                        processedText = cleanText(text) #clean the text for ML
                        site = siteUrl.split('https://')[-1].split('/')[0] # parse the url for the site name
                        article = [site, category, title, url, text, processedText, html]
                        print(len(articles))
                        articles.loc[counter] = article
                        #Add the data to the dataframe
                        counter += 1 #iterate the counter
                        print(site +' - article ' + str(counter))
                        if site not in content.keys():
                            content[site] = {}
                        if title not in content[site][category].keys():
                            content[site][category][title] = processedText
        except:
            errorCounter +=1
            errorURL[errorCounter] = a
    return articles, content, errorURL

#%% define a function to determine the frequency of words in an article
    
def wordFrequency(article, normalize=True):
    wordFreq = defaultdict(int)
    wordFreqNorm = {}
    
    wordFreq = {}
    for word in article:
        if word in wordFreq.keys():
            wordFreq[word] +=1
        else:
            wordFreq[word] = 1
        
    if normalize==True:
        highFreq = float(max(wordFreq.values()))
        for word in wordFreq.keys():
            wordFreqNorm[word] = wordFreq[word]/highFreq
        return wordFreqNorm
    else:
        return wordFreq

#%%The csv 

#%% Define a function to extract pertinent k features
###############################################################################

def extractFeatures(freq, n=5):
    
    if n < 0: # if n is negative just return all the frequencies in order
        return nlargest(len(freq.keys()), freq, key=freq.get)
    else: 
        return nlargest(n,freq, key=freq.get)


#test the wordFrequency function using some sample data. 

urls = ['https://www.washingtonpost.com/politics/courts_law/supreme-court-says-federal-workers-are-entitled-to-a-personnel-process-untainted-by-age-discrimination/2020/04/06/80977c9e-7813-11ea-9bee-c5bf9d2e3288_story.html', 'https://www.washingtonpost.com/news/powerpost/paloma/daily-202/2020/04/06/daily-202-british-canadian-and-u-s-leaders-cite-world-war-ii-to-make-very-different-points-about-coronavirus/5e8abef088e0fa101a75b5a8/']

#%% load some test data

os.chdir('D:/Python Stuff')
#wps = pd.read_csv('WP Sports data 2015')
#content = wps.to_dict()
# the test data was saved as a string rather than a list. So I need to clean that up
from ast import literal_eval

wps = pd.read_pickle('article_data.pkl')
wps = wps[['site','title','text']]
#wps1[['site','title','processedText']] = wps[['site','title','processedText']].apply(literal_eval)


content = {}
for entry in range(len(wps)):
    if wps.iloc[entry, 0] not in content.keys():
        content[wps.iloc[entry,0]]={}
        #print('Adding new site: ' + wps.iloc[entry,0])
    for site in content.keys():
        for article in range(len(wps)):
            if wps.iloc[article, 1] not in content[site].keys():
                print('Adding article: ' + str(wps.iloc[article,1]) + ' to site: ', str(site))
                content[site][wps.iloc[article,1]] = {}
                content[site][wps.iloc[article,1]] = wps.iloc[article,2]


#%%

                

freq = {}
for site in content.keys():
    for article in content[site].keys():
        freq[article] = wordFrequency(content[site][article], True)
#%%
#Try extracting some features

features = {}
for article in freq.keys():
    features[article] = extractFeatures(freq[article])


#%% Testing scraper...
    
testSports = "https://www.washingtonpost.com/sports"

category = 'Sports'

year = '2019'

#textWParticles, content, errs = urlScrape(testSports, year, category)

#textWParticles.to_csv('WP_' + category + '_' + year + '.csv')


#%% Define the K-nearest neighbors algorithm
#########################################################################

#First we will need to read in our training data/testing data



                            
                        
                    
                    
                
    


