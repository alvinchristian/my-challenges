import os
import time
import logging
import hashlib
import datetime
from typing import Any, Mapping

import requests

logging.basicConfig(format="[%(asctime)s] %(message)s")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

FILES = [('src/manage.py', '951e4e0919a7d03870eedc6652435b9f83a012f5f00c8dafa22412c8f6661ffb'), ('src/compfess/asgi.py', '57915b0a23f38b12800cfe176f84561b274421837aa47c4edef646a2d4528dc5'), ('src/compfess/jinja2.py', '72fcdbedd752cdde4c75362dddfc053d14c6ae5a7bd1cfe7c1ce97ae0debd03d'), ('src/compfess/settings.py', '58f1393c0f98fba2234e201d56ee5bdd42133db158c2e53eee342c5d671ebdb8'), ('src/compfess/urls.py', '1685c85b4f04c642417a02194a4b7c15323d374ddb31961841e71185189f403b'), ('src/compfess/wsgi.py', '3b5bfd6fcee0b058ddc98c5a132754227b7fbf64337d1b606346525434217e8f'), ('src/compfess/__init__.py', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'), ('src/main/admin.py', 'c8fb5b88f1a8d63befc88e45a2f0f5e2864f8f2590d96cdcc99f0056fc4f02bd'), ('src/main/apps.py', '3fe796e074975aa2db7433a72ed8de5881b87ef46ccf4e9a8a513b836d839165'), ('src/main/auth.py', 'ac7652e5d41bd005912668b3415467f12005efb358d8e9a36b7abfce1f0e4b46'), ('src/main/middleware.py', '39499391253961e4e1306bb4c738187e14b1e79fcdaa76365dab8f863f06337a'), ('src/main/models.py', '9a6951cdcb1b76418097dea0e6cd28c63caef1e91949d44cafd30df7af795456'), ('src/main/urls.py', 'a2a5b2a308e917ec28567f21260f8e0ab10ce499436c36e25c59a4c9ef3000f2'), ('src/main/views.py', 'c8f6c06ad4ab9cc411105ec8175882122fc076ded7a775ab5bdf7be375bf1bbd'), ('src/main/__init__.py', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'), ('src/main/management/__init__.py', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'), ('src/main/management/commands/generate_admin.py', 'c353eef7b53c47abdbfdf46e3134a597c8205fbf9c5f6d45c39ffd890f638fcc'), ('src/main/management/commands/__init__.py', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'), ('src/main/migrations/0001_initial.py', '4078516141f72292488efd37cd77758e7549c51f3c5b5a977810f795d4b0b0e6'), ('src/main/migrations/0002_alter_profile_role.py', 'b597398d73a33dcdc9e1b4b9470660276ae0921bf55a86edfbd8d94cf2aad13c'), ('src/main/migrations/0003_alter_profile_id.py', 'f3b752419dbb96d97d61d7a648189d6b58f3894e4b20b07339d8726a5be89b13'), ('src/main/migrations/__init__.py', 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'), ('src/main/templates/base.html', '76a1e8ff6bb7713ae7780bbcc6ebd25d8b72f34b6d5933ad18e4cd07b521389b'), ('src/main/templates/edit_profile.html', '03bf4906bffd0d93b68f5b3b6cbf7f80885c6cb6fff3048c1caa9415aee00d27'), ('src/main/templates/feed.html', '1c491577b605da7a7f813d31b98762cf17cb26e43683f0dd42df0d82549c0939'), ('src/main/templates/index.html', 'c4bddde55920bc6e5e4c68b0e88196f5326566cad0cc5721e32e842b5c988aab'), ('src/main/templates/login.html', '79d304b0ab9c2dc4949d381f19ec194fb064daf5b10432687bdc3243c1a5d5c1'), ('src/main/templates/profile.html', '1f173a508f1ce67d736e125b327c20b7e98621532aa033b602fa97768ff89b94'), ('src/main/templates/register.html', '50c89943cf22990d124d864469e36f1ca3ab07558ca81dba08b23b2ee4603a47'), ('src/main/templates/reports.html', 'd3a51381617d30561acf08f295d649c81d724746e73f42b33eb4d47d70f1cae0'), ('src/main/templates/report_detail.html', '00baa6934373ff503a4fe087f4b31e2e0fcbba367207f067c434c54ba94d20c6'), ('src/main/templates/send_menfess.html', 'f0c0f9291773d96e7f749508855fc6d5acf4858048248374f5c88cd681ba3833')]

def test_checksums(app_file_basedir: str) -> bool:
    for file, chksum in FILES:
        fpath = os.path.join(app_file_basedir, file)
        if not os.path.exists(fpath):
            logger.warning(f"[FAIL] File {fpath} not found!")
            return False
        
        with open(fpath, "rb") as f:
            hsh = hashlib.sha256()
            hsh.update(f.read().replace(b'\n',b'').replace(b'\r',b'').replace(b'\t',b'').replace(b' ',b''))
            cur = hsh.hexdigest()
            if cur != chksum:
                logger.warning(f"[FAIL] {fpath} is modified")
                return False
    
    return True

def run_checker(team_id: str, challenge_slug: str, app_file_basedir: str, service_secret: str, current_flag: str) -> Mapping[str, Any]:
    tests = [
        test_checksums,
    ]
    checker_results = all([f(app_file_basedir) for f in tests])
    if not checker_results:
        return {
            "status": "failed",
            "is_code_valid": False,
            "last_checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }

    logger.info("[PASS] all tests passed")
    return {
        "status": "ok",
        "is_code_valid": True,
        "last_checked_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

def main():
    # checker_interval = int(os.getenv("CHECKER_INTERVAL"))
    # checker_secret = os.getenv("CHECKER_SECRET")
    # app_file_basedir = os.getenv("APP_CONTAINER_FILESYSTEM")
    #
    # with open("/configmap/.service_secret") as svc_secret_file:
    #     service_secret = svc_secret_file.read().strip()
    #
    # challenge_slug = os.getenv("REPORT_CHALL_SLUG")
    # team_id = os.getenv("REPORT_TEAM_ID")
    # report_url = os.getenv("REPORT_API_ENDPOINT")
    checker_interval = 20
    checker_secret = "secretbangetbangetbangetlmao"
    app_file_basedir = "/app"
    challenge_slug = os.getenv("CHALLENGE_SLUG", "compfess")
    team_id = os.getenv("TEAM_ID", "20")
    report_url = "https://api.ctf-compfest.com/api/v2/checkeragent/"
    service_secret = os.getenv("SERVICE_SECRET", "yahanehanehlahcompfess")

    while True:
        current_flag = ""
        checker_result = run_checker(
            team_id, challenge_slug, app_file_basedir, service_secret, current_flag)
        try:
            requests.post(
                report_url,
                json={"challenge_slug": challenge_slug,
                      "team_id": team_id, "report": checker_result},
                headers={'X-CHECKER-SECRET': checker_secret},
                timeout=1
            )
        except Exception as e:
            print(e)

        time.sleep(checker_interval)

if __name__ == "__main__":
    main()