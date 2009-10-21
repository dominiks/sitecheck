#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib, urllib2, re, cookielib, os, hashlib, sendmail
from BeautifulSoup import BeautifulSoup
from threading import Thread
from time import strftime


def getResponse(url, postData = None):
    header = { 'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0',
                'Accept-Language': 'de',
                'Accept-Encoding': 'utf-8'                                   
            } 
    if(postData is not None):
        postData = urllib.urlencode(postData)
    req = urllib2.Request(url, postData, header)
    try:
        return urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print 'Error Code:', e.code
        return None

class Course(Thread):
    def __init__ (self, url, CourseName):
        Thread.__init__(self)
        self.url = url
        self.CourseName = CourseName

    def run(self):
        self.newFiles = []
        if not os.path.exists(self.CourseName):
            os.mkdir(self.CourseName)
        soup = BeautifulSoup(getResponse(self.url).read())
        links = soup.findAll(attrs={'href' : re.compile("resource/view.php")})
        for link in links:
            if not(link.span is None):
                new = self.download(link['href'], link.span.next, self.CourseName)
                for n in new:
                    self.newFiles.append(n)
    
    def download(self, url, folder, CourseName):
        newFiles, savedFile = [], []
        response = getResponse(url)
        if(response is not None):
            # Direkter Download
            if(response.info().get("Content-Type").find('audio/x-pn-realaudio') == 0):
                d="" #print "Real Player Moodle Page"
            elif(response.info().get("Content-Type").find('text/html') != 0):
                fileUrl = response.geturl()
                savedFile = self.saveFile(fileUrl)
                if(len(savedFile) > 0):
                    newFiles.append(savedFile)
            # Moodle indirekter Download
            else:
                data = response.read()
                soup = BeautifulSoup(data)
                # entweder frames oder files und dirs
                frames = soup.findAll(attrs={'src' : re.compile("http://moodle.uni-duisburg-essen.de/file.php")})
                files = soup.findAll(attrs={'href' : re.compile("http://moodle.uni-duisburg-essen.de/file.php")})
                dirs = soup.findAll(attrs={'href' : re.compile("subdir")})
    
                folder = re.sub(u"[^a-zA-Z0-9_()äÄöÖüÜ ]", "", folder).strip()
                for f in files:
                    savedFile = self.saveFile(f['href'], folder)
                    if(len(savedFile) > 0):
                        newFiles.append(savedFile)
                # Folders
                for d in dirs:
                    folder = os.path.basename(d['href'])                
                    href = "http://moodle.uni-duisburg-essen.de/mod/resource/" + d['href']
                    self.download(href, folder, CourseName)
                # Frame
                for f in frames:
                    savedFile = self.saveFile(f['src'])
                    if(len(savedFile) > 0):
                        newFiles.append(savedFile)
        return newFiles
    
    def saveFile(self, url, folder = ""):
        if(folder != ""):
            folder = "/" + folder
        isFileNew = False
        fileChanged = False
        newPath = ""
        c = 0
        splitUrl = url.split("/")
        for p in splitUrl:
            c = c + 1
            if c > 5:
                newPath = newPath + "/" + p
                if not(os.path.isdir(self.CourseName + newPath)) and c < len(splitUrl): # len because of filename
                    os.mkdir(self.CourseName + newPath)   
        fullFileName = self.CourseName + newPath

        response = getResponse(url)
        if(os.path.isfile(fullFileName)):
            with open(fullFileName, 'r') as f:
                read_data = f.read()
                f.closed
            check_md5 = False
            # if no Content-Length in header
            if(response.info().get("Content-Length") is None or check_md5 == True):
                data = response.read()
                m1 = hashlib.md5()
                m2 = hashlib.md5()
                m1.update(data)
                m2.update(read_data)
                #print "Lokal:", m1.hexdigest(), "Online:", m2.hexdigest()
                if (m1.hexdigest() == m2.hexdigest()):
                    return []
                else:
                    isFileNew = True
                    fileChanged = True
            else:
                #print filename, "check:", "Length"
                length = response.info().get("Content-Length")
                if (int(length) == len(read_data)):
                    return []
                else:
                    isFileNew = True
                    fileChanged = True
        else:
            isFileNew = True
        if(isFileNew == True):
            data = response.read()
            with open(fullFileName, "w") as f:
                f.write(data)
                f.close()
            return [fullFileName, url, fileChanged]
        else:
            return []
        
def finish(newFiles):
    """
    Moved from Monitor class. Sends an email containing all new files.
    """
    if(len(newFiles) > 0):
        text = ""
        subject = "Moodle Report - "
        for course in newFiles:
	    text += "~"*5 + course + "~"*5 + "\n"
            if(len(newFiles[course]) > 0):
                subject += course + " "
            for file in newFiles[course]:
                if file[2]:
                    suffix = "Changed"
                else:
                    suffix = "New"
                text += file[0] + " - " + suffix + "\n"
                text += "Link: " + file[1] + "\n\n"
            text += "\n\n"
        text += "MoodleCheck.py - 1.1"
        subject += strftime("%d.%m.%Y")
        # Send the mail to every address in mails.txt
        mails = open("mails.txt", "r").readlines()
        sendmail.connectToServer()
        for mail in mails:
            mail = mail.strip()
            if len(mail) > 0 and not mail.startswith("#"):
                sendmail.sendmail(mail, subject, text)
        sendmail.closeConnection()

#
#
# Benutzerdaten
password = "" # PASSWORD
user = ""
# CAS Daten
casUrl = 'https://cas.uni-duisburg-essen.de/cas/login'
casService = "http://moodle.uni-duisburg-essen.de/login/index.php?authCAS=CAS"

# Setup
jar = cookielib.CookieJar()
handler = urllib2.HTTPCookieProcessor(jar)
opener = urllib2.build_opener(handler)
urllib2.install_opener(opener)
    
# Get token
data = getResponse(casUrl).read()
rawstr = '<input type="hidden" name="lt" value="([A-Za-z0-9_\-]*)" />'
token = re.search(rawstr, data, re.MULTILINE).group(1)

# Login
postData = {'username': user, 'password': password, 'lt': token, '_eventId': 'submit'}
dummy = getResponse(casUrl + '?service=' + casService, postData)
dummy = None

# Use the Service
url = 'http://moodle.uni-duisburg-essen.de/index.php'
# verueckt, erst muss ich einen kurs aufrufen um in der hauptseite eingeloggt zu sein
dummy = getResponse("http://moodle.uni-duisburg-essen.de/course/view.php?id=1574")

html = getResponse(url).read()
soup = BeautifulSoup(html)
# Nicht allzu sauber mit den regexp
links = soup.findAll(attrs={'href' : re.compile("course/view.php"), 'title' : re.compile("Hier klicken"), })

courses = []

newFiles = {}

for link in links:
    CourseName = link.string.replace("&amp;", "&")
    CourseName = re.sub(u"[^a-zA-Z0-9_() ]", "", CourseName).strip()
    #print u"Kurs: " + CourseName
    current = Course(link['href'], CourseName)
    courses.append(current)
    current.start()
    
for course in courses:
    course.join()
    new_files_of_course = course.newFiles
    if new_files_of_course:
        newFiles[course.CourseName] = course.newFiles
    
finish(newFiles)
