from bs4 import BeautifulSoup 
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
from selenium.webdriver import firefox
from multiprocess import Pool
import pandas as pd
import numpy as np
import time
import requests
import re
import random
import json

# Environment settings
CHROME_PATH = '/home/maituoy/project/ungoogled-chromium_90.0.4430.85_3.vaapi_linux/chromedriver'
FIREFOX_BINARY = '/home/maituoy/project/firefox/firefox'
FIREFOX_DRIVER = '/home/maituoy/project/geckodriver'

def getPage(url):
    result = requests.get(url)
    content = result.content
    return BeautifulSoup(content, features='lxml')

def getRoomClasses(listing):
    rooms = listing.findAll("div", {"class": "_8ssblpx"})
    result = []
    for room in rooms:
        result.append(room)
    return result

def getListingLink(listing):
    return "http://airbnb.com" + listing.find("a")["href"]

def findNextPage(listing):
    try:
        next_url = listing.find("a",{"aria-label":"Next"})["href"]
        return "http://airbnb.com" + next_url
    except:
        next_url = "N/A"
        
    return next_url

def getAllPages(listing):
    
    listing_list = []
    listing_list.append(listing)
    next_url = findNextPage(listing)
    while next_url != "N/A":
        next_page = getPage(next_url)
        if getRoomClasses(next_page) == []:
            break
        listing_list.append(next_page)
        next_url = findNextPage(next_page)
        
    return listing_list

def getListingId(listing):
    return listing.find("a")['target'].split('_')[1]

def getListingTitle(listing):
    return listing.find("div",{"class":"_5kaapu"}).text

def getRoomInfo(listing):
    info_dict = {"guests":0, "bedrooms":0, "beds":0, "bathroom_text":0}
    room_info = listing.find("div",{"class":"_kqh46o"}).text.split(" · ")
    for item in room_info:
        if 'guest' in item:
            info_dict['guests'] = item.split(" ")[0]
        elif 'Studio' in item:
            info_dict['bedrooms'] = 1
        elif 'bedroom' in item:
            info_dict['bedrooms'] = item.split(" ")[0]
        elif 'bed' in item:
            info_dict['beds'] = item.split(" ")[0]
        elif 'bath' in item:
            info_dict['bathroom_text'] = item
            
    return info_dict

def getPrice(listing):
    try:
        price = listing.find("span",{"class":"_olc9rf0"}).text.split(" ")[0]
    except:
        price = "-1"
    return price

def getNumReviews(listing):
    try:
        num_reviews = listing.find("div",{"class":"_1hxyyw3"}).span['aria-label'].split(' ')[-2]
    except:
        num_reviews = 0
    return num_reviews

def setupDriver(url, waiting_time=2):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.146 Safari/537.36"
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument(f'user-agent={user_agent}')
    driver = webdriver.Chrome(CHROME_PATH, chrome_options = chrome_options)
    driver.get(url)
    time.sleep(waiting_time) 
    return driver

def firefoxDriver(url, waiting_time=3):
    binary = FirefoxBinary(FIREFOX_BINARY)
    firefox_options = firefox.options.Options()
    firefox_options.add_argument('--headless')
    firefox_options.add_argument('--no-sandbox')
    driver = webdriver.Firefox(firefox_binary=binary, executable_path=FIREFOX_DRIVER,firefox_options=firefox_options)
    driver.get(url)
    time.sleep(waiting_time) 
    return driver

def getJSpage_firefox(listingUrl, waiting_time=3):
    driver = firefoxDriver(listingUrl, waiting_time)
    SCROLL_PAUSE_TIME = 1
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    html = driver.page_source
    time.sleep(2)
    driver.close()
    return BeautifulSoup(html, features='lxml') 

def getJSpage_safari(listingUrl):
    driver = safariDriver(listingUrl)
    SCROLL_PAUSE_TIME = 1
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    html = driver.page_source
    time.sleep(2)
    driver.close()
    return BeautifulSoup(html, features="lxml") 

def getJSpage(listingUrl):

    driver = setupDriver(listingUrl)
    SCROLL_PAUSE_TIME = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    read_more_buttons = driver.find_elements_by_class_name("_1d784e5")
    if read_more_buttons == []:
        read_more_buttons = driver.find_elements_by_class_name("_1di55y9")
        
    try:
        for i in range(2, len(read_more_buttons)):
            read_more_buttons[i].click()
    except:
        pass
    
    html = driver.page_source
    time.sleep(2)
    driver.close()
    return BeautifulSoup(html, features="lxml") 

def getAmenitiesPage(detailedPage):
    
    detailed_page = detailedPage.find("div",{"data-plugin-in-point-id":"AMENITIES_DEFAULT"})
    try:
        amenities_url = detailed_page.find("a",{"class":"b9v58tx vh7amno dir dir-ltr"})['href']
    except:
        amenities_url = detailed_page.find("a",{"class":"b1sec48q v7aged4 dir dir-ltr"})['href']
    amenities_url = 'https://airbnb.com' + amenities_url
    
    am_driver = firefoxDriver(amenities_url, 3)
    SCROLL_PAUSE_TIME = 1
    last_height = am_driver.execute_script("return document.body.scrollHeight")
    while True:
        am_driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = am_driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    am_html = am_driver.page_source
    time.sleep(2)
    am_driver.close()
    
    return BeautifulSoup(am_html, features="lxml")

def getAmenities(ap_link):
    
    start = time.time()
    page = getJSpage(ap_link)
    amenities = []
    try:            
        for am in page.findAll(class_ = "_vzrbjl"):
            if am.text.startswith("Unavailable"):
                continue
            else:
                amenities.append(am.contents[0])
        am = ';'.join(i for i in amenities)
        if am == '':
            raise
        print("total time taken: ", time.time() - start)
    except:
        print('Error raised')
        pass
    return am

def getDescription(detailedPage):
    
    try:
        section = detailedPage.find("div",{"data-plugin-in-point-id":"DESCRIPTION_DEFAULT"}) 
        description = section.find("div",{"class":"_1d784e5"}).text
    except:
        try:
            section = detailedPage.find("div",{"data-plugin-in-point-id":"DESCRIPTION_DEFAULT"}) 
            description = section.text
        except:
            description = 'N/A'
    return description

def getLocation(detailedPage):
    
    try:
        section = detailedPage.find("div",{"data-plugin-in-point-id":"LOCATION_DEFAULT"})
        location = section.find("div",{"class":"_152qbzi"}).text
    except:
        section = detailedPage.find("div",{"data-plugin-in-point-id":"TITLE_DEFAULT"})
        location = section.find("span",{"class":"_169len4r"}).text
        
    return location
    
def getHostInfo(detailedPage):
    
    section = detailedPage.find("div",{"data-plugin-in-point-id":"HOST_PROFILE_DEFAULT"})
    
    dateJoined = section.find("div",{"class":"_1fg5h8r"}).text
    
    try:
        total_reviews = section.findAll("div",{"class":"_5kaapu"})[0].text.split(" ")[0]
    except:
        total_reviews = 0
        
    try:
        if section.findAll("div",{"class":"_5kaapu"})[1].text == 'Identity verified':
            identityVerified = True
        else:
            identityVerified = False
    except:
        identityVerified = False
    
    responseRate = 'N/A'
    responseTime = 'N/A'
    try:
        for sec in section.find("div",{"class":"_1k8vduze"}).findAll("li"):
            if 'Response rate' in sec.text:
                responseRate = sec.text.split(": ")[1]  
            if 'Response time' in sec.text:
                responseTime = sec.text.split(": ")[1]
    except:
        for sec in section.findAll("li",{"class":"_1q2lt74"}):
            if 'Response rate' in sec.text:
                responseRate = sec.text.split(": ")[1]
            if 'Response time' in sec.text:
                responseTime = sec.text.split(": ")[1]
        
    return (dateJoined, total_reviews, identityVerified, responseRate, responseTime)

def getPolicies(detailedPage):
    
    section = detailedPage.find("div",{"data-plugin-in-point-id":"POLICIES_DEFAULT"})
    contents = section.find("div",{"class":"_1byskwn"}).contents
    
    checkinTime = 'N/A'
    checkoutTime = 'N/A'
    cancellationPolicy = 'N/A'
    for subsection in contents:
        title = subsection.find('div',{"class":"_h0dm2e"}).text
        if 'House rules' in title:
            houseRules = subsection.find("div",{"class":"_ud8a1c"}).contents
            for item in houseRules:
                if 'Check-in' in item.text:
                    checkinTime = item.text.split(": ")[1]

                if 'Checkout' in item.text:
                    checkoutTime = item.text.split(": ")[1]

        if 'Cancellation policy' in title:
            cancellationPolicy = subsection.find("div",{"class":"_1fopc40"}).text
    
    return (checkinTime, checkoutTime, cancellationPolicy)

def getLogInfo(detailedPage,waittime=4):
    url = detailedPage
    chrome_path = CHROME_PATH
    capabilities = DesiredCapabilities.CHROME
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    capabilities["goog:loggingPrefs"] = {"performance": "ALL"}
    driver = webdriver.Chrome(chrome_path,desired_capabilities=capabilities,chrome_options = chrome_options)
    driver.get(url)
    time.sleep(waittime)
    logs = driver.get_log("performance")
    
    data = []
            
    for item in logs:
        try:
                data.append(json.loads(item["message"])["message"]["params"]["request"]["postData"])
        except:
              pass
    
    for item in data:
        for subItem in json.loads(item):
            try:
                Latitude = subItem["event_data"]["listing_lat"]
                Longitude = subItem["event_data"]["listing_lng"]
                accuracy_rating =  subItem["event_data"]["accuracy_rating"]
                checkin_rating = subItem["event_data"]["checkin_rating"]
                cleanliness_rating = subItem["event_data"]["cleanliness_rating"]
                communication_rating = subItem["event_data"]["communication_rating"]
                location_rating = subItem["event_data"]["location_rating"]
                value_rating = subItem["event_data"]["value_rating"]
                guest_satisfaction_overall = subItem["event_data"]["guest_satisfaction_overall"]

                home_tier = subItem["event_data"]["home_tier"]
                room_type =  subItem["event_data"]["room_type"]
                is_superhost = subItem["event_data"]["is_superhost"]
                picture_count = subItem["event_data"]["picture_count"]
                
                return (Latitude,Longitude,accuracy_rating,checkin_rating,\
                        cleanliness_rating,communication_rating,location_rating,\
                        value_rating, guest_satisfaction_overall,home_tier,room_type, is_superhost,picture_count)
            except:
                continue 

def getTotalListings(listingPage):
    page_list = []
    pages = getAllPages(listingPage)
    page_list.extend(pages)

    total_listings = []
    for p in page_list:
        total_listings.extend(getRoomClasses(p))
    return total_listings

def urlGenerator(city, state, country, checkinDate, checkoutDate, priceMin, priceMax):
    listing_url = "https://www.airbnb.com/s/{}--{}--{}/homes?".format(city, state, country)

    if checkinDate != None:
        listing_url += 'checkin={}'.format(checkinDate)

    if checkoutDate != None:
        listing_url += '&checkout={}'.format(checkoutDate)

    if priceMin != None:
        listing_url += '&price_min={}'.format(priceMin)

    if priceMax != None:
        listing_url += '&price_max={}'.format(priceMax)

    return listing_url

def priceDistribution(city, state, country, checkinDate, checkoutDate):
    start_price = 10
    step_size = 9
    dist = {}
    total_listings = []

    while start_price <= 1000:
        price_max = start_price + step_size
        url = urlGenerator(city=city,
                     state=state,
                     country=country,
                     checkinDate=checkinDate,
                     checkoutDate=checkoutDate,
                     priceMin=start_price,
                     priceMax=price_max)
        page = getPage(url)
        count_in_range = page.find("div",{"class":"_1snxcqc"}).text.split(' ')[0]

        m = 1
        while count_in_range == "300+":
            price_max = start_price + step_size//(2*m)
            url = urlGenerator(city=city,
                    state=state,
                    country=country,
                    checkinDate=checkinDate,
                    checkoutDate=checkoutDate,
                    priceMin=start_price,
                    priceMax=price_max)
            page = getPage(url)
            count_in_range = page.find("div",{"class":"_1snxcqc"}).text.split(' ')[0]
            m += 1

        n = 1
        while int(count_in_range) < 30 and price_max < 1000:
            price_max += 10*n
            url = urlGenerator(city=city,
                    state=state,
                    country=country,
                    checkinDate=checkinDate,
                    checkoutDate=checkoutDate,
                    priceMin=start_price,
                    priceMax=price_max)
            page = getPage(url)
            count_in_range = page.find("div",{"class":"_1snxcqc"}).text.split(' ')[0]
            n += 1

        print("price range {} - {}: {}".format(start_price, price_max, count_in_range))
        dist[(start_price, price_max)] = int(count_in_range)

        # Collect listings
        total_listings.extend(getTotalListings(page))

        start_price = price_max + 1

    url = urlGenerator(city=city,
                     state=state,
                     country=country,
                     checkinDate=checkinDate,
                     checkoutDate=checkoutDate,
                     priceMin=start_price,
                     priceMax=None)
    page = getPage(url)
    # Collect listings
    total_listings.extend(getTotalListings(page))
    count_in_range = page.find("div",{"class":"_1snxcqc"}).text.split(' ')[0]
    print("price range {}+: {}".format(start_price,count_in_range))
    dist[(start_price, )] = int(count_in_range)

    return dist, total_listings

def scrapeAllPages(listing):
        start = time.time()
        listing_bs = BeautifulSoup(listing, features="lxml")
        listing_url = getListingLink(listing_bs)
        try:
                detailed_page = getJSpage(listing_url)
                dp_raw = str(detailed_page)
                amenities_page = getAmenitiesPage(detailed_page)
                ap_raw = str(amenities_page)
                check_content = detailed_page.find("div",{"data-plugin-in-point-id":"AMENITIES_DEFAULT"})
                if check_content == None:
                        dp_raw = 'N/A'
                elif detailed_page.find('title').contents == ['503 Service Unavailable - Airbnb']:
                        dp_raw = 'N/A'
                elif detailed_page.find('title').contents == ['Access Denied']:
                        dp_raw = 'N/A'
                elif dp_raw.startswith('<html><head><title>429'):
                        dp_raw = 'N/A'

                if dp_raw == 'N/A':
                        print("page not found")
                else:
                        print("total time taken: ", time.time() - start)
                return [listing, listing_url, dp_raw, ap_raw]
        except:
                print("page not found")
                return [listing, listing_url, 'N/A', 'N/A']

def chunks(lst, n):
        for i in range(0, len(lst), n):
                yield lst[i:i + n]