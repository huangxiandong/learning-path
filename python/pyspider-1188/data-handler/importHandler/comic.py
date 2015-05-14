#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# Created on 2015-03-03 13:14:54
# Project: test

import re
from urlparse import urljoin, urlparse, urlunparse, urlsplit, urlunsplit
import sqlite3, math, time
import ast
import MySQLdb
import logging, logger
import pinyin
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from declarative import  Base, Video, VideoInfo, Category, PlaySource, Specicalty
from sqlalchemy.orm.exc import NoResultFound

myLogger = logging.getLogger('v1188ys.importer.comic')

def initSession():
    engine = create_engine('mysql+mysqldb://test:test@172.16.1.19/1188test?charset=utf8&use_unicode=0')
    Base.metadata.bind = engine
    DBSession = sessionmaker(bind=engine)
    session = DBSession()
    return session

def searchVideo(session,movie, video_type_id):
    try:
        movie = session.query(Video).filter(Video.orig_id == int(movie['orig_id'])).filter(Video.video_type_id == int(video_type_id)).one()
    except NoResultFound, e:
        raise e
    except Exception, e:
        myLogger.error('SearhVideo Error: %s' % e)
        raise e
    return movie

def saveVideo(session, movie, video_type_id):
    #处理rating和runtime
    if not movie['rating']:
        movie['rating'] = '0'
    rating = re.search('\d+(\.?\d?)*', movie['rating']).group(0)
    if not movie['year'] or not movie['year'].isdigit():
        movie['year'] = 0
    
    video = Video(name=movie['title'].decode('unicode-escape'), 
            rating= float(rating) ,
            year = int(movie['year']),
            location = movie['location'].decode('unicode-escape'),
            orig_id = int(movie['orig_id']),
            video_type_id = video_type_id,
            is_closed = int(movie['closed'])
        )
    session.add(video)
    return video

def searchAndSaveMovie(session, movie, video_type_id):
    if not movie['title']:
        return None

    try:
        movie = searchVideo(session, movie, video_type_id)
    except NoResultFound, e:
        movie = saveVideo(session, movie, video_type_id)
    except Exception, e:
        myLogger.error('unkown error: %s' % e)
        raise e
    return movie


def saveVideoInfo(session, movie, savedMovieObj):
    if savedMovieObj is None:
        return None
    try:
        # 查找是否已经存在
        videoInfoObj = session.query(VideoInfo).filter(VideoInfo.video == savedMovieObj).one()
        return videoInfoObj
    except NoResultFound, e:
        introduction = movie['introduction'].decode('unicode-escape')
        introduction = re.sub(r'\s*展开全部.*收起全部.*', '', introduction)
        videoInfoObj = VideoInfo(introduction=introduction,
                poster_image = movie['poster_image'],
                small_image = movie['small_image'],
                video = savedMovieObj,
                alias = movie['alias'].decode('unicode-escape'),
                upd_desc=movie['upd_desc'].decode('unicode-escape')
            )
        session.add(videoInfoObj)
        return videoInfoObj
    except Exception, e:
        myLogger.error(e)
        raise e
    

def searchAndLinkCategory(session, movie, savedMovieObj, video_type_id):
    if savedMovieObj is None:
        return None
    cats = movie['categories']
    for catName in cats:
        try:
            # 查找已有的
            catObj = session.query(Category).filter(Category.name == catName.decode('unicode-escape')).filter(Category.video_type_id == video_type_id).one()
            savedMovieObj.categories.append(catObj)
        except NoResultFound, e:
            # if not found, then save the cat, and associate the relations
            catObj = Category(name=catName.decode('unicode-escape'),
                    video_type_id=video_type_id,
                    url_rewrite = pinyin.get(catName.decode('unicode-escape')) or '',
                    is_hot = 0,
                    is_displayed = 0
                )
            session.add(catObj)
            savedMovieObj.categories.append(catObj)
        except Exception, e:
            myLogger.error(e)
            continue

def searchAndLinkPlaySource(session, movie, savedMovieObj, video_type_id):
    if savedMovieObj is None:
        return None
    play_sources = movie['play_source']
    for api_name in play_sources:
        for episode_num in play_sources[api_name]:
            try:
                playSource = session.query(PlaySource).filter(PlaySource.api_name == api_name).filter(PlaySource.video_id == savedMovieObj.id).filter(PlaySource.episode_num == int(episode_num.decode('unicode-escape')[:-1])).one()
            except NoResultFound, e:
                playSource = PlaySource(api_name=api_name,
                        url=play_sources[api_name][episode_num],
                        video=savedMovieObj,
                        episode_num = int(episode_num.decode('unicode-escape')[:-1])
                    )
                session.add(playSource)
            except Exception, e:
                myLogger.error(e)
                raise e

def searchAndLinkSpecialty(session, movie, savedMovieObj, video_type_id):
    if savedMovieObj is None:
        return None
    seps = movie['specialties']
    for sep in seps:
        try:
            sepObj = session.query(Specicalty).filter(Specicalty.name == sep.decode('unicode-escape')).filter(Specicalty.video_type_id == video_type_id).one()
            savedMovieObj.specialties.append(sepObj)
        except NoResultFound, e:
            # if not found, then save the sep, and associate the relations
            sepObj = Specicalty(name=sep.decode('unicode-escape'),
                    video_type_id=video_type_id
                )
            session.add(sepObj)
            savedMovieObj.specialties.append(sepObj)
        except Exception, e:
            myLogger.error(e)
            raise e

def doesVideoExist(session, video_id):
    pass

def start():
    session = initSession()
    limit = 1000.0
    with MySQLdb.connect('172.16.1.248', 'qiye_dev', 'qiye..dev', '1188ys_resultdb') as cursor:
        #cursor = db.cursor()
        cursor.execute('''SELECT count(*) from comic''')
        rowCount = cursor.fetchone()[0]
        runtimes = math.ceil(rowCount/limit)
        for x in xrange(0, int(runtimes)):
            sql = "SELECT taskid, result from comic limit %d, %d" % (int(x*limit ), int(limit))
            #print sql
            #print time.asctime( time.localtime(time.time()) )
            cursor.execute(sql)
            allRows = cursor.fetchall()
            i = 0
            for row in allRows:
                try:
                    movie = ast.literal_eval(row[1])
                    # 保存video, 如果已经存在就返回搜索到的Video对象
                    savedMovieObj = searchAndSaveMovie(session, movie, 2)
                    # 保存VideoInfo
                    saveVideoInfo(session, movie, savedMovieObj)
                    #保存并关联category
                    searchAndLinkCategory(session, movie, savedMovieObj, 2)
                    #保存并关联play source
                    searchAndLinkPlaySource(session, movie, savedMovieObj, 2)
                    # 保存并关联sepcialty
                    #searchAndLinkSpecialty(session, movie, savedMovieObj, 2)
                    
                    i += 1
                    if i % 200 == 0:
                        session.commit()
                except Exception, e:
                    myLogger.error('Error: %s - taskid : %s',e, row[0])
                    #logging.error('task id is  %s, eval error ', row[0])
            session.commit()
        