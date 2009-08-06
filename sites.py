'''

'''
import os, urllib2, shutil

def processSitesInFile(sitesLines):
    sites = {}
    for site in sitesLines:
        site = site.strip()
        
	# Ignore lines starting with # as comments
        if site.startswith("#"):
            continue
        
        try:
            parts = site.split("=")
            if len(parts) == 2:
                sites[parts[0].strip()] = parts[1].strip()
            else:
                print "Unknown site format: {0}".format(site)
        except exception as err:
            print "Error: {0}".format(err)
            
    return sites

def checkSite(siteDict, site):
    diff = None
    url = siteDict[site]
    hash = url.__hash__()
    content = urllib2.urlopen(url).read()
    
    if not os.path.exists(site + ".old"):
        file = open(site + ".old", "w")
        file.write(content)
        file.close()
    else:
        oldfile = site + ".old"
        newfile = site + ".new"
        
        file = open(newfile, "w")
        file.write(content)
        file.close()
        
        diff = os.popen("diff -uw " + oldfile + " " + newfile).read()
        shutil.move(newfile, oldfile)
        
    return diff
