# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs
from datetime import datetime, timedelta
import sqlite3
import time

ADDON_ID = "plugin.video.iplayerwww"
ADDON = xbmcaddon.Addon(id=ADDON_ID)
CACHE_PATH = xbmc.translatePath(ADDON.getAddonInfo("profile"))


class Cache(object):

    def __init__(self, name):
        self.enabled = True
        self.memcache = True
        self._window = xbmcgui.Window(10000)
        self._name = name
        if not self._name:
            self._name = "data"
        self._initdb()

    def __del__(self):
        try:
            if self._conn:
                self_conn.close()
        except:
            pass

    def Get(self, key):
        if not key:
            self._log("Get: invalid parameters: key=%s" % key)
            return None
        data = None
        if self.enabled:
            now = int(time.mktime(datetime.utcnow().timetuple()))
            if self.memcache:
                data = self._getmem(key, now)
                if data:
                    self._log("Get: retrieved from memcache: key=%s" % key)
            if not data:
                try:
                    sql = "SELECT value, expires FROM data WHERE key = ? and expires > ?"
                    row = self._conn.execute(sql, (key, now)).fetchone()
                    if row:
                        value = row[0]
                        expires = row[1]
                        if value:
                            data = eval(value)
                        if data:
                            self._log("Get: retrieved from database: key=%s" % key)
                        if self.memcache and data and expires > now :
                            self._setmem(key, data, expires)
                        else:
                            self._delmem(key)
                except Exception as err:
                    self._log("Get: database error: err=%s" % err)
        return data

    def Set(self, key, data, ttl=1):
        if not key or not data or not isinstance(ttl, int):
            self._log("Set: invalid parameters: key=%s ttl=%s data=%s" % (key, ttl, data))
            return
        if self.enabled:
            value = repr(data)
            expires = int(time.mktime((datetime.utcnow() + timedelta(hours=ttl)).timetuple()))
            try:
                sql = "REPLACE INTO data (key, value, expires) VALUES (?, ?, ?)"
                self._conn.execute(sql, (key, value, expires))
                if self.memcache:
                    self._setmem(key, data, expires)
                else:
                    self._delmem(key)
            except Exception as err:
                self._log("Set: database error: err=%s" % err)

    def Trim(self, clear=False):
        now = int(time.mktime(datetime.utcnow().timetuple()))
        try:
            sql = "SELECT key FROM data"
            params = ()
            if not clear:
                sql += " WHERE expires <= ?"
                params = (now,)
            for row in self._conn.execute(sql, params).fetchall():
                key = row[0]
                self._delmem(key)
            sql = "DELETE FROM data"
            params = ()
            if not clear:
                sql += " WHERE expires <= ?"
                params = (now,)
            self._conn.execute(sql, params)
            self._conn.execute("VACUUM")
        except Exception as err:
            self._log("Trim: database error: err=%s" % err)

    def Clear(self):
        self.Trim(clear=True)

    def _getmem(self, key, now):
        value = self._window.getProperty(key)
        if value:
            data, expires = eval(value)
            if expires > now:
                return data
            else:
                self._delmem(key)
        else:
            self._delmem(key)
        return None

    def _setmem(self, key, data, expires):
        value = repr((data, expires))
        self._window.setProperty(key, value)

    def _delmem(self, key):
        self._window.clearProperty(key)

    def _initdb(self):
        if not xbmcvfs.exists(CACHE_PATH):
            xbmcvfs.mkdirs(CACHE_PATH)
        try:
            cache_db = os.path.join(CACHE_PATH, "%s_cache.db" % self._name)
            self._conn = sqlite3.connect(cache_db, timeout=15, isolation_level=None)
            sql = "CREATE TABLE IF NOT EXISTS data (key TEXT PRIMARY KEY, expires INTEGER, value TEXT)"
            self._conn.execute(sql)
        except Exception as err:
            self._log("_initdb: database error: err=%s" % err)

    def _log(self, msg, lvl=xbmc.LOGWARNING):
        if isinstance(msg, unicode):
            msg = msg.encode("utf-8", "replace")
        xbmc.log("%s: %s: %s: %s" % (ADDON_ID, __name__, self._name, msg), level=lvl)
