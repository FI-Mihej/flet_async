__all__ = ['app']

import argparse
import json
import logging
import os
import signal
import socket
import subprocess
import tarfile
import tempfile
import threading
import time
import traceback
import urllib.request
import zipfile
from pathlib import Path
from time import sleep
from typing import Sequence

from watchdog.events import FileSystemEventHandler, PatternMatchingEventHandler
from watchdog.observers import Observer

from flet import constants, version
from flet.connection import Connection
from flet.event import Event
from flet.page import Page
from flet.reconnecting_websocket import ReconnectingWebSocket
from flet.utils import *

try:
    from typing import Literal
except:
    from typing_extensions import Literal

from flet.flet import _connect_internal, AppViewer, FLET_APP, FLET_APP_HIDDEN, _open_flet_view, WEB_BROWSER
from cengal.code_flow_control.smart_values import ValueExistence


def app(
    name="",
    host=None,
    port=0,
    target=None,
    permissions=None,
    view: AppViewer = FLET_APP,
    assets_dir=None,
    web_renderer="canvaskit",
    route_url_strategy="hash",
    window_pid_holder: ValueExistence = None
):

    if target == None:
        raise Exception("target argument is not specified")

    conn = _connect_internal(
        page_name=name,
        host=host,
        port=port,
        is_app=True,
        permissions=permissions,
        session_handler=target,
        assets_dir=assets_dir,
        web_renderer=web_renderer,
        route_url_strategy=route_url_strategy,
    )

    target._original_on_event = conn.on_event
    conn.on_event = target.on_event

    url_prefix = os.getenv("FLET_DISPLAY_URL_PREFIX")
    print("App URL:" if url_prefix == None else url_prefix, conn.page_url)

    terminate = threading.Event()

    def exit_gracefully(signum, frame):
        logging.debug("Gracefully terminating Flet app...")
        terminate.set()

    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    print("Connected to Flet app and handling user sessions...")

    fvp = None
    window_pid_holder.existence = False

    if (
        (view == FLET_APP or view == FLET_APP_HIDDEN)
        and not is_linux_server()
        and url_prefix == None
    ):
        fvp = _open_flet_view(conn.page_url, view == FLET_APP_HIDDEN)
        try:
            window_pid_holder.value = fvp.pid
            fvp.wait()
        except (Exception) as e:
            pass
    else:
        if view == WEB_BROWSER and url_prefix == None:
            open_in_browser(conn.page_url)
        try:
            if is_windows():
                input()
            else:
                terminate.wait()
        except (Exception) as e:
            pass

    conn.close()

    if fvp != None and not is_windows():
        try:
            logging.debug(f"Flet View process {fvp.pid}")
            os.kill(fvp.pid + 1, signal.SIGKILL)
        except:
            pass
