#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import os

from subprocess import check_call

from fastapi import FastAPI, Depends, HTTPException, Request
from peewee import fn

import model
import parser

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates



__dir__ = os.path.abspath(os.path.dirname(__file__))

app = FastAPI()

origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=os.path.join(__dir__, "dist/spa")), name="static")
templates = Jinja2Templates(directory=os.path.join(__dir__, "dist"))

model.db.connect()
model.db.create_tables([model.LogsDB])
model.db.close()


security = HTTPBasic()


def get_current_username(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = credentials.username == "admin"
    correct_password = credentials.password == "admin"
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


async def reset_db_state():
    model.db._state._state.set(model.db_state_default.copy())
    model.db._state.reset()


def get_db(db_state=Depends(reset_db_state)):
    try:
        model.db.connect()
        yield
    finally:
        if not model.db.is_closed():
            model.db.close()


@app.get("/", dependencies=[Depends(get_current_username)])
async def root(request: Request):
    return templates.TemplateResponse("spa/index.html", {"request": request})


@app.get("/fileds/")
async def fields(group_by: bool = False):
    if not group_by:
        return list(model.LogsColumns.keys())
    else:
        return ["ip", "url", "date", "refer", "country", "city"]


@app.get("/query/", response_model=model.AjaxLogs, dependencies=[Depends(get_db), Depends(get_current_username)])
async def get_item(
    start: int=1, length: int=10, 
    sort_by: str="time", desc: bool = True
):

    query = model.LogsDB.select()

    if desc:
        query = query.order_by(model.LogsColumns[sort_by].desc())
    else:
        query = query.order_by(model.LogsColumns[sort_by])

    data = model.AjaxLogs(
        data=list(query.offset((start - 1) * length).limit(length)),
        start=start, length=length, total=query.count()
    )

    return data


@app.get("/count/", dependencies=[Depends(get_db)])
async def get_item(by: str):
    if by not in model.LogsColumns.keys():
        raise HTTPException(status_code=302, detail=by + ": is not supported")

    col = model.LogsColumns[by]

    data = (model.LogsDB
        .select(col, fn.Count().alias('count'))
        .group_by(col).tuples())
    return data


@app.get("/bytes/", response_model=model.AjaxBytes, dependencies=[Depends(get_db),Depends(get_current_username)])
async def get_item(
    by: str, start: int = 1, 
    length: int = 10, with_date: bool = False,
    sort_by: str = "bytes", desc: bool = True
):
    if by not in model.LogsColumns.keys():
        raise HTTPException(status_code=302, detail=by + ": is not supported")

    if sort_by != "bytes" and sort_by not in model.LogsColumns.keys():
        raise HTTPException(status_code=302, detail=sort_by + ": is not supported")

    sel = [
        model.LogsColumns[by].alias('group'),
        fn.SUM(model.LogsDB.byte).alias('bytes'), 
        fn.Count().alias('counts')
    ]
    group_by = [model.LogsColumns[by]]
    header = ["group", "bytes", "counts"]

    if with_date:
        sel.append(model.LogsDB.date)
        group_by.append(model.LogsDB.date)
        header.insert(1, "date")
    
    if by == "ip":
        sel += [model.LogsDB.country, model.LogsDB.city]
        header.insert(2, "country")
        header.insert(3, "city")

    query = (model.LogsDB.select(*sel).group_by(*group_by))

    if sort_by == "bytes":
        if desc:
            query = query.order_by(fn.SUM(model.LogsDB.byte).desc())
        else:
            query = query.order_by(fn.SUM(model.LogsDB.byte).asc())

    elif sort_by == "counts":
        if desc:
            query = query.order_by(fn.Count().desc())
        else:
            query = query.order_by(fn.Count().asc())
    else:
        col = model.LogsColumns[sort_by]
        if desc:
            query = query.order_by(col.desc())
        else:
            query = query.order_by(col.asc())
    
    return model.AjaxBytes(
        data=list(query.offset((start - 1) * length).limit(length)),
        start=start, length=length, total=query.count(),
        header=header
    )


@app.get("/update", dependencies=[Depends(get_db),Depends(get_current_username)])
async def update():
    check_call(parser.parse, os.path.join(__dir__, "access.log"))
    return "success"


@app.get("/goaccess", dependencies=[Depends(get_current_username)])
async def goaccess(request: Request):
    try:
        check_call(f"goaccess {os.path.join(__dir__, 'access.log')} -a > {os.path.join(__dir__, 'dist/spa/access.html')}", shell=True)
    except Exception as err:
        print(err)
    finally:
        return RedirectResponse('static/access.html')


if __name__ == '__main__':
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=2020, log_level="info")