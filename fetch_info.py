#!/usr/bin/env python

# fetch.py
# import library
import requests
import bs4
import socket
import argparse
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import whois
import zipfile
import os, time
import random
import shutil
servers = []
netlocs = []
# sample request
#  https://www.ultratools.com/tools/asnInfoResult?domainName=google
#  https://www.ultratools.com/tools/geoIpResult


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


def download_zip(zip_url):
    if zip_url[-4:] != '.zip':
        print('A valid zip file is required')
        exit(0)
    file_name = zip_url.split("/")[-1]
    r = requests.get(zip_url, stream=True)
    if r.status_code == requests.codes.ok:
        # continue
        print("Downloading file ... ", zip_url, "")
        with open(file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        print("\nDONE ##")
        return file_name


def extract_zip(file_name):
    zip_f = zipfile.ZipFile(file_name, 'r')
    # maybe i should create a random directory
    random_dir = str(random.randrange(int(time.time())))[:10]
    print("Creating Random Directory to hold content -- > ", random_dir)
    os.makedirs(random_dir)
    zip_f.extractall(random_dir)
    zip_f.close()
    return random_dir


def get_hosting_info(domain):
    try:
        w = whois.whois(domain)
        return w.get('registrar')
    except whois.parser.PywhoisError:
        print("No hosting information available.")
        return 'NOT AVAILABLE'

    
def get_ipaddress(domain):
    o = urlparse(domain)
    return socket.gethostbyname(o.netloc)


def get_geo_info(ip_address):
    tool_url = 'https://www.ultratools.com/tools/geoIpResult'
    final_res = []

    r = requests.post(tool_url, data={'ipAddress': ip_address})
    if r.status_code == requests.codes.ok:
        # parse the result
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
    # print('Debug: Making request to ', tool_url_dup)
    reform = []
    final_res = []
    r = requests.get(tool_url_dup)
    if r.status_code == requests.codes.ok:
        markup = r.text
        soup = bs4.BeautifulSoup(markup, 'lxml')
        result_container = soup.find('div', class_='tool-results-container')
        result_heading = result_container.find_all('div', class_="tool-results-heading")
        result_body = result_container.find_all('div', class_="tool-results")
        for field in zip(result_heading, result_body):
            #reform.append(i)
            final_res.append(field[0].string)

    return final_res


def get_links(url):
    response = requests.get(url)
    data = response.text
    soup = bs4.BeautifulSoup(data, 'lxml')
    links = []
    for link in soup.find_all('a'):
        link_url = link.get('href')
        if link_url is not None:  # and link_url.startswith('http'):
            links.append(link_url)
            # print(link_url)
    
    return links


def get_servers(links):
    global servers
    global netlocs

    for link in links:
        o = urlparse(link)
        netloc = o.netloc
        if netloc in netlocs and netloc != '':
            # print('neloc: ', netloc, "in netlocs")
            # print('Debug: netlocs is .. ', netlocs)
            pass
        else:
            # if not link in servers:
            netlocs.append(netloc)
            servers.append("".join([o.scheme, "://", netloc]))


def print_info(domain):
    # General information
    print(" General Information ".center(50, "="), "\n")
    ip_addr = get_ipaddress(domain)
    host_company = get_hosting_info(domain)
    print("Site Name:".ljust(20), domain.ljust(20))
    print("IP Address:".ljust(20), ip_addr.ljust(20))
    print("Hosting Provider:".ljust(20), host_company.ljust(20))
    print("")

    # GEO information
    print(" Geographical Information ".center(50, "="))
    print("")
    for tpl in get_geo_info(ip_addr):
        print(tpl[0].rjust(20), tpl[1].ljust(20))
    print("")

    # ASN information
    print(" ASN ".center(50, "="))
    asns = get_asn(ip_addr)
    for x in asns:
        print(x)


def hunt_zip(downloaded, zip_url):
    # have we downloaded the file
    if downloaded:
        zip_file = zip_url
    else:
        zip_file = download_zip(zip_url)

    xml_files = []
    print('Extracting zip file :: ', zip_file)
    dir_name = extract_zip(zip_file)

    print('Hunting for XML File')
    for r, d, f in os.walk(dir_name):
        # print(r, d, f)
        for file in f:
            if file[-4:] == '.xml':
                print('Found a XML File --> ', file)
                xml_files.append(os.path.join(r, file))
    print(xml_files)

    for xml_file in xml_files:
        # lets parse our files.
        print('Parsing ', xml_file, '...')
        xml_data = open(xml_file).read()
        soup = bs4.BeautifulSoup(xml_data, 'lxml')
        data_dir = soup.find_all('datadir')
        # extract
        links = []
        for data in data_dir:
            links.append(data.string)

        get_servers(links)
        # print summary
        print('Found ', len(servers), ' Servers')
        print(servers)

    print("Starting to gather informations on servers.\n\n")
    for server in servers:
        if server.startswith('http'):
            print("\n\nGAthering INFO FOR ", server)
            print_info(server)
    # remove the dir created earlier
    destroy_dir(dir_name)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Get Information about site")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--domain", dest="domain", help="Domain name to be looked up")
    group.add_argument("-z", "--zipfile", dest="zip_url", help="The Zip file to be downloaded and scraped")
    group.add_argument("-r", "--zipdir", dest="zip_dir", help="The directory in which the zip files are contained")
    args = parser.parse_args()

    if args.domain and args.zip_url:
        print("You can only supply one of zip URL or domain to scrape")
        exit()
    if args.domain:
        domain = args.domain
        links = get_links(domain)
        # print(links)
        get_servers(links)

        print(servers)

        for server in servers:
            if server.startswith('http'):
                print("\n\nGAthering INFO FOR ", server)
                print_info(server)

    elif args.zip_url:
        hunt_zip(False, args.zip_url)

    elif args.zip_dir:
        # does the file even exits
        zip_dir = args.zip_dir
        zip_files = []
        if os.path.exists(zip_dir):
            # walk the dir for zip files
            if os.path.isdir(zip_dir):
                for r, d, f in os.walk(zip_dir):
                    # print(r, d, f)
                    for file in f:
                        if file[-4:] == '.zip':
                            zip_files.append(os.path.join(r, file))
                    # let's deal with the zip files found
                    print('Found {} zip files'.format(len(zip_files)))
                    if len(zip_files) == 0:
                        print("No zip files to work with, exiting ...")
                        exit()
                    for zip_file in zip_files:
                        hunt_zip(True, zip_file)
                else:
                    print('The directory provided in not a valid directory')
                    exit()
            else:
                # file does not exists
                print('The Directory supplied does not exist')
                exit()


