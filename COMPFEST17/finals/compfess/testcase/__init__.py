import requests
from pathlib import Path
import zipfile, tarfile, io
from typing import List, TypedDict, Dict, Tuple, Any
import datetime
from multiprocessing import TimeoutError
from multiprocessing.pool import ThreadPool
import os
import re

class ServiceType(TypedDict):
    id: int
    team_id: int
    challenge_id: int
    order: int
    secret: str
    detail: Dict[str, Any]
    time_created: datetime.datetime

class FlagType(TypedDict):
    id: int
    team_id: int
    challenge_id: int
    round: int
    tick: int
    value: str
    order: int

class CheckerAgentReportType(TypedDict):
    id: int
    team_id: int
    challenge_id: int
    source_ip: str
    time_created: datetime.datetime
    report: Dict[Any, Any]
    
def create_result(stt):
    verdict = True
    if stt != "valid": verdict = False

    return verdict, {
        "status_detail": stt,
        "time_finished": datetime.datetime.now().isoformat(),
    }

def get_csrf_token(session, BASE, path="/register/"):
    r = session.get(BASE + path)
    r.raise_for_status()
    token_match = re.search(r'name="csrfmiddlewaretoken"[^>]*value="([^"]*)"', r.text)
    if token_match:
        return token_match.group(1)
    raise Exception("CSRF token not found")

s = requests.Session()

def test_case(username,password,admin_password,service_address):
    BASE = f"http://{service_address}"
    csrf = get_csrf_token(s, BASE,"/login/")
    resp = s.post(BASE + "/login/", data={
        "csrfmiddlewaretoken": csrf,
        "username": username,
        "password": password,
    }, headers={"Referer": BASE + "/login/"})
    if (username not in resp.text):
        return False

    csrf = get_csrf_token(s, BASE,"/u/me/edit/")
    resp = s.post(BASE + "/u/me/edit/", data={
        "csrfmiddlewaretoken": csrf,
        "bio": "The quick brown fox jumps over the lazy dog",
    }, headers={"Referer": BASE + "/u/me/edit/"})
    if ("The quick brown fox jumps over the lazy dog" not in resp.text):
        return False

    resp = s.get(BASE + f"/feed/by-sender/?sender=guest")
    if ("Hello admin" not in resp.text):
        return False

    resp = s.get(BASE + "/logout/")

    s_admin = requests.Session()

    csrf = get_csrf_token(s_admin, BASE,"/login/")
    resp = s_admin.post(BASE + "/login/", data={
        "csrfmiddlewaretoken": csrf,
        "username": "haiakuadmintcompfess",
        "password": admin_password,
    }, headers={"Referer": BASE + "/login/"})

    csrf = get_csrf_token(s_admin, BASE,"/admin/reports/")
    resp = s_admin.post(BASE + "/admin/reports/new", data={
        "csrfmiddlewaretoken": csrf,
        "content": "This is a test report",
    }, headers={"Referer": BASE + "/admin/reports/"})
    
    if ("haiakuadmintcompfess" not in resp.text):
        return False

    if resp.status_code == 302 or resp.history:
        report_uuid = resp.url.strip("/").split("/")[-1]

        csrf = get_csrf_token(s_admin, BASE,f"/admin/reports/{report_uuid}/")
        resp = s_admin.post(BASE + f"/admin/reports/download", data={
            "csrfmiddlewaretoken": csrf,
            "url": f"file:///upload/reports/{report_uuid}.txt"
        })
        Path("downloaded_report.txt").write_bytes(resp.content)
        content = open("downloaded_report.txt","rb").read()
        if "This is a test report" not in content.decode():
            return False
    else:
        return False
    
    csrf = get_csrf_token(s_admin, BASE, "/admin/reports/")
    files = {
        "file": ("db041bdf-35f5-461a-b818-6193e3d8d3f6.txt", b"Hello from txt", "text/plain")
    }
    data = {
        "csrfmiddlewaretoken": csrf
    }
    resp = s_admin.post(
        BASE + "/admin/reports/new",
        data=data,
        files=files,
        headers={"Referer": BASE + "/admin/reports/"}
    )

    csrf = get_csrf_token(s_admin, BASE,f"/admin/reports/")
    resp = s_admin.post(BASE + f"/admin/reports/download", data={
            "csrfmiddlewaretoken": csrf,
            "url": f"file:///upload/reports/db041bdf-35f5-461a-b818-6193e3d8d3f6.txt"
        })

    Path("notes.txt").write_bytes(resp.content)
    content = open("notes.txt","rb").read()
    if "Hello from txt" not in content.decode():
        return False

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("441c31f4-2bd2-465e-bd98-57c24ffb150c.txt", "Hello inside zip")
    buf.seek(0)
    csrf = get_csrf_token(s_admin, BASE,"/admin/reports/")
    files = {"file": ("note.zip", buf.read(), "application/zip")}
    data = {"csrfmiddlewaretoken": csrf}
    resp = s_admin.post(BASE + "/admin/reports/new", files=files, data=data, headers={"Referer": BASE + "/admin/reports/"})
    if "haiakuadmintcompfess" not in resp.text:
        return False
    csrf = get_csrf_token(s_admin, BASE,f"/admin/reports/")
    resp = s_admin.post(BASE + f"/admin/reports/download", data={
            "csrfmiddlewaretoken" : csrf,    
            "url": f"file:///upload/reports/441c31f4-2bd2-465e-bd98-57c24ffb150c.txt"
        })
    Path("inside.txt").write_bytes(resp.content)
    content = open("inside.txt","rb").read()
    if "Hello inside zip" not in content.decode():
        return False

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        data = b"Hello inside tar"
        ti = tarfile.TarInfo("6e7db14e-0be8-48c4-93b7-9b348e3e61f8.txt")
        ti.size = len(data)
        tf.addfile(ti, io.BytesIO(data))
    buf.seek(0)
    csrf = get_csrf_token(s_admin, BASE,"/admin/reports/")
    files = {"file": ("note.tar", buf.read(), "application/x-tar")}
    data = {"csrfmiddlewaretoken": csrf}
    resp = s_admin.post(BASE + "/admin/reports/new", files=files, data=data, headers={"Referer": BASE + "/admin/reports/"})
    if "haiakuadmintcompfess" not in resp.text:
        return False
    csrf = get_csrf_token(s_admin, BASE,f"/admin/reports/")
    resp = s_admin.post(BASE + f"/admin/reports/download", data={
            "csrfmiddlewaretoken" : csrf,
            "url": f"file:///upload/reports/6e7db14e-0be8-48c4-93b7-9b348e3e61f8.txt"
        })
    Path("inside_tar.txt").write_bytes(resp.content)
    content = open("inside_tar.txt","rb").read()
    if "Hello inside tar" not in content.decode():
        return False
    
    for f in ["downloaded_report.txt", "notes.txt", "inside.txt", "inside_tar.txt"]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass
    
    return True

def run_tests(username, password, admin_password, service_address):
    testcase_func = [
        lambda: test_case(username, password, admin_password, service_address)
    ]
    
    pool = ThreadPool(processes=3)
    tc_res = [pool.apply_async(func) for func in testcase_func]
    pool.close()
    pool.join()

    for res in tc_res:
        try:
            if not res.get(timeout=10):
                return False
        except TimeoutError:
            return False
    return True

def main(services: List[ServiceType], flags: List[FlagType], checker_agent_report: CheckerAgentReportType | None) -> Tuple[bool, Dict]:
    
    service_addresses: List[str] = services[0]["detail"]['public_addresses']
    service_address = service_addresses[0]
    admin_password = services[0]["secret"]
    if not admin_password:
        return create_result("configuration error - no password")
    
    if checker_agent_report is None:
        return create_result("agent lost")

    agent_time = datetime.datetime.fromisoformat(checker_agent_report["time_created"]).astimezone(datetime.timezone.utc)
    time_now = datetime.datetime.now(datetime.timezone.utc)
    if not (time_now - agent_time) <= datetime.timedelta(seconds=60):
        return create_result("agent lost")

    if not checker_agent_report["report"]["is_code_valid"]:
        return create_result("service faulty")

    try:
        BASE = f"http://{service_address}"
        username = "checker_user"
        password = """c=d[KkM$xs5CPalQh^9Q"""
        email = "checker@checker.com"
        csrf = get_csrf_token(s, BASE,"/register/")

        s.post(BASE + "/register/", data={
        "csrfmiddlewaretoken": csrf,
        "username": username,
        "email": email,
        "password": password,
    }, headers={"Referer": BASE + "/register/"})

        csrf = get_csrf_token(s, BASE,"/send/")
        s.post(BASE + "/send/", data={
            "csrfmiddlewaretoken": csrf,
            "recipient": "1", 
            "content": "Hello admin, this is a test menfess!"
        }, headers={"Referer": BASE + "/send/"})
        if not run_tests(username,password,admin_password,service_address):
            return create_result("service faulty")

    except Exception as e:
         return create_result("service faulty")

    return create_result("valid")