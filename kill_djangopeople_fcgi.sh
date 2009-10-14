#!/bin/bash
PIDFILE="/tmp/djangopeoplenet.pid"
kill `cat -- $PIDFILE`
rm -f -- $PIDFILE
