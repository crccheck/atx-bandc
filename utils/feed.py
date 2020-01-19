import os

from bottle import request
from pyga.requests import Tracker, Page, Session, Visitor


ga_account = os.environ.get("GA_ACCOUNT")
ga_domain = os.environ.get("GA_DOMAIN")


def ping():
    """ping back to ga"""
    if not ga_account:
        return

    tracker = Tracker(ga_account, ga_domain)
    visitor = Visitor()
    visitor.ip_address = request.remote_addr
    session = Session()
    page = Page(request.path)
    if "referer" in request.headers:
        page.referrer = request.headers["referer"]
    tracker.track_pageview(page, session, visitor)
