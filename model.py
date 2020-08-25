#!/usr/bin/env python3
# -*- coding:utf-8 -*-
u"""
nginx log database
"""
import os

from datetime import datetime

import peewee

from typing import Any, List, Optional, Union

from contextvars import ContextVar
from pydantic import BaseModel
from pydantic.utils import GetterDict


__author__ = 'ygidtu@gmail.com'
__date__ = '2020.07.02'


__dir__ = os.path.abspath(os.path.dirname(__file__))

DATABASE_URL = os.path.join(__dir__, "nginx.db")


class PeeweeGetterDict(GetterDict):
    def get(self, key: Any, default: Any = None):
        res = getattr(self._obj, key, default)
        if isinstance(res, peewee.ModelSelect):
            return list(res)
        return res


class PeeweeConnectionState(peewee._ConnectionState):
    def __init__(self, **kwargs):
        super().__setattr__("_state", db_state)
        super().__init__(**kwargs)

    def __setattr__(self, name, value):
        self._state.get()[name] = value

    def __getattr__(self, name):
        return self._state.get()[name]


db_state_default = {"closed": None, "conn": None, "ctx": None, "transactions": None}
db_state = ContextVar("db_state", default=db_state_default.copy())
db = peewee.SqliteDatabase(DATABASE_URL, check_same_thread=False)
db._state = PeeweeConnectionState()


class LogsDB(peewee.Model):
    text = peewee.TextField(primary_key=True)
    ip = peewee.CharField(index=True)
    country = peewee.CharField(index=True, null=True)
    city = peewee.CharField(index=True, null=True, default="Unknown")
    time = peewee.DateTimeField(index=True)
    date = peewee.DateTimeField(index=True)
    method = peewee.CharField(index=True)
    url = peewee.TextField(index=True)
    refer = peewee.TextField(index=True)
    status = peewee.IntegerField(index=True)
    byte = peewee.IntegerField(index=True)
    browser = peewee.CharField(index=True)
    browser_version = peewee.CharField(index=True)
    platform = peewee.CharField(index=True)
    platform_version = peewee.CharField(index=True)
    device = peewee.CharField(index=True)
    brand = peewee.CharField(index=True, null=True)

    class Meta:
        database = db
        table_name = "logs"

LogsColumns = {
    "ip": LogsDB.ip, "time": LogsDB.time, "date": LogsDB.date,
    "country": LogsDB.country, "city": LogsDB.city,
    "method": LogsDB.method, "url": LogsDB.url,
    "refer": LogsDB.refer, "status": LogsDB.status,
    "byte": LogsDB.byte, "browser": LogsDB.browser,
    "browser_version": LogsDB.browser_version,
    "platform": LogsDB.platform,
    "platform": LogsDB.platform_version,
    "device": LogsDB.device, "brand": LogsDB.brand,
}


class Logs(BaseModel):
    text:str
    ip:str
    country: str
    city: Optional[str]
    time: datetime
    date: datetime
    method:str
    url:str
    refer:str
    status: int
    byte:int
    browser:str
    browser_version:str
    platform:str
    platform_version: str
    device: str
    brand: Optional[str]

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class AjaxLogs(BaseModel):
    data: List[Logs]
    start: int
    length: int
    total: int


class Bytes(BaseModel):
    group: Union[str, datetime, None]
    date: Optional[datetime]
    country: Optional[str]
    city: Optional[str]
    bytes:int
    counts: int
    refer: Optional[str]

    class Config:
        orm_mode = True
        getter_dict = PeeweeGetterDict


class AjaxBytes(BaseModel):
    data: List[Bytes]
    start: int
    length: int
    total: int
    header: List[str]


def create_table(table: peewee.Model):
    if not table.table_exists():
        table.create_table()


def insert_data(table: peewee.Model, data, length: int=300):
    with db.atomic():
        for i in range(0, len(data), length):
            table.insert_many(data[i, i + length]).execute()

