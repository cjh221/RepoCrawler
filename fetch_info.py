#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#fetch.py

#import library
import requests
import bs4
import socket
import argparse
import datetime
import whois
import zipfile
import os, time
import threading
import csv
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

dt = datetime.datetime.now()
result_now = '_'.join([str(dt.year), str(dt.month), str(dt.day), str(dt.hour), str(dt.minute)])
result_now = 'result_' + result_now
os.makedirs(result_now)

servers = []
netlocs = []

#the sources with their valid website for the server logging
ALL_SITES = ['tmdb', 'tadb', 'imdb', 'omdbapi', 'themoviedb', 'thetvdb', 'fanart']
ALL_SITES_SERVER = {'tmdb': 'tmdb.com', 'tadb': 'tadb.com', 'imdb': 'imdb.com',
    'omdbapi':'omdbapi.com', 'themoviedb':'themoviedb.org', 'thetvdb': 'thetvdb.com', 'fanart':'fanart.tv'}

#The github repository are added here.
REPOS = [#'https://github.com/xbmc/xbmc/tree/master/addons/',
         #'https://github.com/EmuZONE/xbmc.plugins/tree/master/zip',
         'https://github.com/kodil/kodil/tree/master/repo/'
         #'https://github.com/xbmc/xbmc-rbp/tree/master/addons/',
         #'https://github.com/Yaser7440/repository.MG.Arabic/tree/master/zip/']
         ]
"""
    def matches(s):
    if re.findall(r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))', s):
    print "%s matches" % (s)
    else:
    print "%s doesn't match" % (s)
    """


#r'(?i)\b((?:[a-z][\w-]+:(?:/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))'

#re.findall('https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+', url)

#https://github.com/EmuZONE/xbmc.plugins/tree/master/zip
#jso = soup.find_all('a', class_='js-navigation-open')
#bold@python::#for link in jso:
#     if 'metadata' in link.get('href'):
#         print(link.get('href'))
#


DB = ['']


def download_zip(zip_url):
    #if not a valid zip
    if zip_url[-4:] != '.zip':
        print('A valid zip file is required')
        exit(0)

    #split the file from the url
    file_name = zip_url.split("/")[-1]
    #download the file
    r = requests.get(zip_url, stream=True)
    if r.status_code == requests.codes.ok:
        #continue
        print("Downloading file ... ", zip_url, end="")
        #write the data to file
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

print("  DONE.")
#return the file name
return file_name


def extract_zip(file_name):
    zip_f = zipfile.ZipFile(file_name, 'r')
    #create a random directory
    random_dir = str(time.time())[:10]
    print("Creating Random Directory to hold content -- > ", random_dir)
    os.makedirs(random_dir)
    zip_f.extractall(random_dir)
    zip_f.close()
    #return the dir in which it was extracted.
    return random_dir



def search_links(data):
    soup = bs4.BeautifulSoup(data, 'lxml')
    links = []
    for link in soup.find_all('a'):
        link_url = link.get('href')
        if link_url is not None: # and link_url.startswith('http'):
            links.append(link_url)
    #print(link_url)

return links


def search_xml(dir_name):
    xml_files = []
    for r, d, f in os.walk(dir_name):
        for file in f:
            if file[-4:] == '.xml':
                print('Found a XML File --> ', file)
                xml_files.append(os.path.join(r, file))
    return xml_files


def xml_extract_link(xml_file):
    #parse files.
    print('Parsing ', xml_file, '...')
    xml_data = open(xml_file).read()
    soup = bs4.BeautifulSoup(xml_data, 'lxml')
    data_dir = soup.find_all('datadir')
    #extract
    links = [data.string for data in data_dir]
    return links


def is_zip_link(url):
    if url[-4:] == '.zip':
        return True
    else:
        return False


def is_repo_xml(url):
    #connect to the site, chekck for zip file, download, extract if no xml file , no repo
    links = []
    zip_count = 0
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        links = search_links(r.text)
        for link in links:
            #loop all links
            if is_zip_link(link):
                zip_name = download_zip(link)
                dir_name = extract_zip(zip_name)
                xml_files = search_xml(dir_name)
                if len(xml_files):
                    return True
                else:
                    return False
                else:
                    print('site down.')

def log_link(server, data):
    with open(server+'_log.dat', 'a+') as fp:
        fp.write(data)

def start_url(url):
    print('Scraping {}'.format(url), end="    ")
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        links = search_links(r.text)
        for link in links:
            #loop all links
            if is_zip_link(link):
                zip_name = download_zip(link)
                dir_name = extract_zip(zip_name)
                xml_files = search_xml(dir_name)
                if len(xml_files):
                    for xml_file in xml_files:
                        xml_links = xml_extract_link(xml_file)
                        for l in xml_links:
                            print("Checking {} if a repository site ... ".format(l), end="")
                            if is_repo_xml(l):
                                print("It's a REPO site, will continue.")
                            else:
                                print("NOT A REPO site, probably valuable, logging ...")
                                log_link(l)


def loop_xml(xml_list):
    """what does this do ?
        """
    pass

def get_api_key_from_xml(xml_file):
    apis = []
    api_len = 32
    hay = 'api_key='
    hay_len = len(hay)
    data = open(xml_file, 'r', encoding="UTF-8").read()
    soup = bs4.BeautifulSoup(data, 'lxml')
    regexp = soup.find_all('regexp')
    for r in regexp:
        output = r.get('output')
        if hay in output:
            i = output.index(hay)
            api_key = output[i+hay_len:i+hay_len+api_len]
            if api_key not in apis:
                apis.append(api_key)
    return apis

def get_api_key_from_xml2(xml_file):
    apis = []
    api_len = 32
    hay = 'api_key='
    hay_len = len(hay)
    start = 0
    xml_data = open(xml_file, encoding="UTF-8").read()
    end = len(xml_data)
    cont = False
    if hay in xml_data:
        while 1:
            if cont:
                break
            #let's further, there's an api key available
            i = xml_data.find(hay, start)
            #print("DEbug: i +> ", i)
            if i ==  -1:
                break
            api_key = xml_data[i+hay_len:i+hay_len+api_len]
            #print("APIKEY: ", api_key)
            #api_key = output[i+hay_len:i+hay_len+api_len]
            if api_key not in apis:
                apis.append(api_key)
            start = i + hay_len + api_len + 1
    return apis

def get_description_data(xml_file):
    """ This extact description datas from
        xml file found in the zip repo
        """
    soup = bs4.BeautifulSoup(xml_file, 'lxml')
    descs = soup.find_all('description')
    for desc in descs:
        desc_data = str(desc.string)
        #if '.com' in desc_data:
        desc_arr.append(desc_data)

def get_sites(data):
    """pull out sites from data it's actually data from xml file,
        data gotten from get_description_data
        """
    sites = []
    for site in ALL_SITES:
        if site in data:
            sites.append(site)
    return sites

def download_github_zip(url):
    #before making the request, get it raw
    #file_name = ''
    url = url.replace('tree', 'raw')
    
    file_name = download_zip(url)
    
    #return the file name
    return file_name


def download_github_xml(url):
    """ Will return the name of the file downloaded
        """
    #before making the request, get it raw
    print("Downloading ", url.split("/")[-1])
    #o = urlparse(url)
    #netloc = o.netloc
    
    file_name = ''
    """
        if netloc.startswith('raw.'):
        #it's already raw, no change to make
        pass
        elif netloc.startswith('github.'):
        netloc = 'raw.' + netloc
        url = o.scheme + '://' + netloc + o.path
        """
    url = url.replace('blob', 'raw')
    #print('using ', url)
    r = requests.get(url)
    try:
        r.raise_for_status()
    except:
        #catch exception
        pass
    else:
        #no exception occured, continue
        if r.status_code == 200:
            #split the file from the url
            file_name = url.split("/")[-1]
            with open(file_name, 'wb') as fp:
                fp.write(r.text.encode('utf-8'))

#return the file name
return file_name


def get_github_dir(url):
    dirs = []
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        soup = bs4.BeautifulSoup(r.text, 'lxml')
        jso = soup.find_all('a', class_='js-navigation-open')
        if jso:
            for link in jso:
                if 'metadata' in link.get('href'):
                    file_name = link.get('href')
                    file_name = file_name.split("/")[-1]
                    if file_name.startswith('metadata'):
                        dirs.append(file_name)
    return dirs

def get_github_ls(url):
    dirs = []
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        soup = bs4.BeautifulSoup(r.text, 'lxml')
        jso = soup.find_all('a', class_='js-navigation-open')
        if jso:
            for link in jso:
                file_name = link.get('href')
                file_name = file_name.split("/")[-1]
                dirs.append(file_name)
    return dirs


def get_github_file_names(url, type_):
    #the type, is it zip or xml.
    all_files = []
    files = get_github_ls(url)
    for file in files:
        if file.endswith(type_):
            #we found our type
            all_files.append(file)

return all_files


def github_path(url, fd_name):
    if url.endswith('/'):
        return url + fd_name
    else:
        return url + '/' + fd_name

def log_apis(apis, site_name):
    with open(os.path.join(result_now, site_name+'_keys.csv'), 'a') as fp:
        writer = csv.writer(fp)
        for api in apis:
            writer.writerow([api])

def ls_repo():
    pass


def get_servers(links):
    global servers
    global netlocs
    
    for link in links:
        o = urlparse(link)
        netloc = o.netloc
        if netloc in netlocs and netloc != '':
            #print('neloc: ', netloc, "in netlocs")
            #print('Debug: netlocs is .. ', netlocs)
            pass
        else:
            #if not link in servers:
            netlocs.append(netloc)
            servers.append("".join([o.scheme, "://", netloc]))

def get_hosting_info(domain):
    try:
        w = whois.whois(domain)
        return w.get('registrar')
    except whois.parser.PywhoisError:
        print("No hosting information available.")
        return 'NOT AVAILABLE'

def get_ipaddress(domain):
    #o = urlparse(domain)
    return socket.gethostbyname(domain)

def get_geo_info(ip_address):
    tool_url = 'https://www.ultratools.com/tools/geoIpResult'
    final_res = []
    
    r = requests.post(tool_url, data={'ipAddress':ip_address})
    if r.status_code == requests.codes.ok:
        #parse the result
        markup = r.text
        soup = bs4.BeautifulSoup(markup, 'lxml')
        result = soup.find('div', class_="tool-results")
        label = result.find_all('span', class_="label")
        value = result.find_all('span', class_="value")
        for v in zip(label, value):
            if v[1] is None or v[0] is None:
                continue
            else:
                if v[1].string and v[0].string:
                    final_res.append((v[0].string.strip(), v[1].string.strip()))
        return final_res


def get_asn(query):
    tool_url = 'https://www.ultratools.com/tools/asnInfoResult?domainName=xxxx'
    query = query.strip()
    tool_url_dup = tool_url.replace('xxxx', query)
    #print('Debug: Making request to ', tool_url_dup)
    reform = []
    final_res = [];
    r = requests.get(tool_url_dup)
    if r.status_code == requests.codes.ok:
        markup = r.text
        soup = bs4.BeautifulSoup(markup, 'lxml')
        result_container = soup.find('div', class_='tool-results-container')
        result_heading = result_container.find_all('div', class_="tool-results-heading")
        result_body = result_container.find_all('div', class_="tool-results")
        for field in zip(result_heading, result_body):
            ##reform.append(i)
            final_res.append(field[0].string)
    
    return final_res


def print_info(domain):
    #General information
    #we will be printing two times, one for log and one for stdout
    file = os.path.join(result_now, domain + '_log.dat')
    with open(file) as f:
        print(" General Information ".center(50, "="), file=f, end="\n")
        print(" General Information ".center(50, "="), end="\n")
        
        ip_addr = get_ipaddress(domain)
        host_company = get_hosting_info(domain)
        
        print("Site Name:".ljust(20), domain.ljust(20));
        print("Site Name:".ljust(20), domain.ljust(20), file=f);
        
        print("IP Address:".ljust(20), ip_addr.ljust(20))
        print("IP Address:".ljust(20), ip_addr.ljust(20), file=f)
        
        print("Hosting Provider:".ljust(20), str(host_company).ljust(20))
        print("Hosting Provider:".ljust(20), str(host_company).ljust(20), file=f)
        print("")
        
        #GEO information
        print(" Geographical Information ".center(50, "="))
        print(" Geographical Information ".center(50, "="), file=f)
        print("")
        
        for tpl in get_geo_info(ip_addr):
            print(tpl[0].rjust(20), tpl[1].ljust(20))
            print(tpl[0].rjust(20), tpl[1].ljust(20), file=f)
        print("")
        
        #ASN information
        print(" ASN ".center(50, "="))
        asns = get_asn(ip_addr)
        for x in asns:
            print(x)
            print(x, file=f)

def hunt_zip(zip_file_name, site_name):
    print("\nHunting {} ...".format(zip_file_name))
    xml_files = []
    #print('Extracting zip file :: ', zip_file)
    dir_name = extract_zip(zip_file_name)
    
    print("\tSearching for XML Files in  {}".format(zip_file_name))
    for r, d, f in os.walk(dir_name):
        #print(r, d, f)
        for file in f:
            if file[-4:] == '.xml':
                print("\tFound a XML File --> ", file)
                xml_files.append(os.path.join(r, file))
    #print(xml_files)

for xml_file_name in xml_files:
    #lets parse our files.
    apis = get_api_key_from_xml2(xml_file_name)
    if len(apis):
        log_apis(apis, site_name)
        print("DEBUG: APIS +> ", apis)
        print("Found {0} in {1}".format(len(apis), xml_file_name))
        #delete the xml file
        os.unlink(xml_file_name)
        time.sleep(1)
    
    
    destroy_dir(dir_name)

def destroy_dir(dirs):
    for fd in os.listdir(dirs):
        file_path = os.path.join(dirs, fd)
        try:
            if o.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except:
            print('could not remove directory, proceeding...')

def start(start_zip):
    START_ZIP = start_zip
    zip_name = download_zip(START_ZIP)
    dir_name = extract_zip(zip_name)
    xml_files = search_xml(dir_name)
    if len(xml_files):
        for xml_file in xml_files:
            xml_links = xml_extract_link(xml_file)
            for l in xml_links:
                #start a thread for each url
                #enter the url and extact sites.
                l = l + "addons.xml"
                print("Following ", l)
                #check if the xml exists
                r = requests.get(l)
                if r.status_code == requests.codes.ok:
                    print("XML File is alive, ... scraping ...");
                    #search for the sites.
                    data = r.text
                    #get the server from the file ...
                    sites = get_sites(data)
                    
                    print('Source Servers found:')
                    for site in sites:
                        print(site)
                    
                    print('Logging server information:')
                    for site in sites:
                        print_info(ALL_SITES_SERVER[site])
                
                    print("Fetching keys ...")
                    
                    for repo in REPOS:
                        print("Looking up ", repo, "...")
                        metas = get_github_dir(repo)
                        print("Metadata found")
                        for meta in metas:
                            print(meta)
                            for site in sites:
                                if site in meta:
                                    print("Checking keys for {} in {}".format(site, meta))
                                    print('searching xml files ...')
                                    #get xml files in the metadata
                                    xml_files = get_github_file_names(repo + meta + "/", 'xml')
                                        time.sleep(1)
                                        for xml_file in xml_files:
                                            print("Looking in ", xml_file)
                                            xml_file_name = download_github_xml(repo + meta + "/" + xml_file)
                                            time.sleep(0.5)
                                            apis = get_api_key_from_xml2(xml_file_name)
                                            if len(apis):
                                                log_apis(apis, site)
                                                print("DEBUG: APIS +> ", apis)
                                            print("Found {0} in {1}".format(len(apis), xml_file_name))
                                            #delete the xml file
                                            os.unlink(xml_file_name)
                                        time.sleep(1)
                                        print('searching zip files ...')
                                        zip_files = get_github_file_names(repo + meta + "/", "zip")
                                        if len(zip_files):
                                            for zip_file in zip_files:
                                                print("Looking in ", zip_file)
                                                zip_file_name = download_github_zip(repo + meta + "/" + zip_file)
                                                hunt_zip(zip_file_name, site)
                                    
                                        else:
                                            pass



#sites will contain what to lookup in the git repo.

#START_ZIP = 'http://repo.mrblamo.xyz/repository.universalscrapers-1.0.0.zip'
#START_ZIP = 'Http://www.tantrumtv.com/download/repository.tantrumtv-1.2.3.zip'
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get Information about site")
    #group = parser.add_mutually_exclusive_group()
    #group.add_argument("-d", "--domain", dest="domain", help="Domain name to be looked up")
    parser.add_argument("-z", "--zipfile", dest="zip_url", help="The Zip file to be downloaded and scraped")
    #group.add_argument("-r", "--zipdir", dest="zip_dir", help="The directory in which the zip files are contained")
    args = parser.parse_args()

if args.zip_url:
    START_ZIP = args.zip_url
    start(START_ZIP)
