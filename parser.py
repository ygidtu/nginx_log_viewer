#!/usr/bin/env python3
# -*- coding:utf-8 -*-
u"""
Parse the nginx log
"""
import os
import re

from datetime import datetime

import user_agents as ua
import geoip2.database

import model


__author__ = 'ygidtu@gmail.com'
__date__ = '2020.07.02'
__dir__ = os.path.abspath(os.path.dirname(__file__))


GEOIP_ID = "349719"
GEOIP_LICENCE = "YqoAIa2jLT6LJ8qm"
client = geoip2.database.Reader(os.path.join(
    __dir__, 
    "GeoLite2-City_20200630/GeoLite2-City.mmdb"
))

lineformat = re.compile(r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""", re.IGNORECASE)


def parse(path: str):
    u"""
    Decode nginx log into data struct
    """
    with open(path) as r:
        for log in r:
            log = log.strip()
            if not log:
                continue

            if model.LogsDB.select().where(model.LogsDB.text == log).exists():
                continue
            
            
            data = re.search(lineformat, log)
            
            if data:
                datadict = data.groupdict()
                ip = datadict["ipaddress"]
                datetimestring = datadict["dateandtime"]
                url = datadict["url"]
                bytessent = datadict["bytessent"]
                referrer = datadict["refferer"]
                useragent = datadict["useragent"]
                status = datadict["statuscode"]
                method = data.group(6)
                

                response = client.city(ip)

                agents = ua.parse(useragent)
                model.LogsDB.create(
                    text = log.strip(),
                    ip = ip, country = response.country.name, city=response.city.name,
                    time = datetime.strptime(datetimestring, '%d/%b/%Y:%H:%M:%S %z'),
                    date = datetime.strptime(datetimestring, '%d/%b/%Y:%H:%M:%S %z').date(),
                    method = method,
                    url = url,
                    refer = referrer,
                    status = int(status),
                    byte = int(bytessent),
                    browser = agents.browser.family,
                    browser_version = agents.browser.version_string,
                    platform = agents.os.family,
                    platform_version = agents.os.version_string,
                    device = agents.device.family,
                    brand = agents.device.brand
                )
        

if __name__ == '__main__':

    # model.create_table(model.LogsDB)

    # with open("nginx/access.log") as r:
    #     for line in r:
    #         print(parse(line))            
    from peewee import fn
    data = (model.LogsDB.select(
                model.LogsDB.ip, 
                fn.Count().alias('count')).group_by(model.LogsDB.ip))

    for d in data:
        print(d.ip, d.count)
