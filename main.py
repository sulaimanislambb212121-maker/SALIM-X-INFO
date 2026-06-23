import asyncio
import time
import httpx
import json
import os
import sys
import threading
from collections import defaultdict
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from cachetools import TTLCache
from google.protobuf import json_format
from Crypto.Cipher import AES
import base64
import pickle
from datetime import datetime

# ============= PATH FIX =============
current_dir = os.path.dirname(os.path.abspath(__file__))
proto_dir = os.path.join(current_dir, 'proto')
if proto_dir not in sys.path:
    sys.path.insert(0, proto_dir)

try:
    from proto import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
    print("✅ Proto files imported successfully")
except ImportError:
    try:
        import FreeFire_pb2, main_pb2, AccountPersonalShow_pb2
        print("✅ Proto files imported directly")
    except ImportError as e:
        print(f"❌ Proto import error: {e}")
        sys.exit(1)

# === Settings ===
MAIN_KEY = base64.b64decode('WWcmdGMlREV1aDYlWmNeOA==')
MAIN_IV  = base64.b64decode('Nm95WkRyMjJFM3ljaGpNJQ==')
RELEASEVERSION = "OB53"
USERAGENT = "Dalvik/2.1.0 (Linux; U; Android 13; CPH2095 Build/RKQ1.211119.001)"
REGION_PRIORITY = ["ME", "BD", "IND", "SG", "ID", "TH", "VN", "PK", "BR", "US", "EU"]
SUPPORTED_REGIONS = set(REGION_PRIORITY)
TOKEN_CACHE_FILE = 'token_cache.pkl'
IMAGE_BASE_URL = "https://cdn.jsdelivr.net/gh/ShahGCreator/icon@main/PNG/"

app = Flask(__name__)
CORS(app)
cache = TTLCache(maxsize=100, ttl=300)
token_manager = None

# === Token Manager ===
class TokenManager:
    def __init__(self):
        self.tokens = {}
        self.lock = asyncio.Lock()
        self.load_tokens()

    def load_tokens(self):
        try:
            if os.path.exists(TOKEN_CACHE_FILE):
                with open(TOKEN_CACHE_FILE, 'rb') as f:
                    saved = pickle.load(f)
                    now = time.time()
                    for r, info in saved.items():
                        if info.get('expires_at', 0) > now:
                            self.tokens[r] = info
                            print(f"✅ Loaded cached token: {r}")
        except Exception as e:
            print(f"❌ Load tokens error: {e}")

    def save_tokens(self):
        try:
            with open(TOKEN_CACHE_FILE, 'wb') as f:
                pickle.dump(dict(self.tokens), f)
        except Exception as e:
            print(f"❌ Save tokens error: {e}")

    async def get_token(self, region: str):
        async with self.lock:
            info = self.tokens.get(region)
            if info and info.get('expires_at', 0) > time.time():
                return info
            new_token = await self.generate_token(region)
            if new_token:
                self.tokens[region] = new_token
                self.save_tokens()
                return new_token
            return None

    async def generate_token(self, region: str):
        try:
            account = get_account_credentials(region)
            token_val, open_id = await get_access_token(account)
            if not token_val or not open_id:
                return None
            body = json.dumps({"open_id": open_id, "open_id_type": "4",
                               "login_token": token_val, "orign_platform_type": "4"})
            proto_bytes = await json_to_proto(body, FreeFire_pb2.LoginReq())
            payload = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, proto_bytes)
            url = "https://loginbp.ggblueshark.com/MajorLogin"
            headers = {
                'User-Agent': USERAGENT, 'Connection': "Keep-Alive",
                'Accept-Encoding': "gzip", 'Content-Type': "application/octet-stream",
                'Expect': "100-continue", 'X-Unity-Version': "2018.4.11f1",
                'X-GA': "v1 1", 'ReleaseVersion': RELEASEVERSION
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, data=payload, headers=headers)
                if resp.status_code != 200:
                    print(f"❌ MajorLogin {resp.status_code} for {region}")
                    return None
                login_res = FreeFire_pb2.LoginRes()
                login_res.ParseFromString(resp.content)
                msg = json.loads(json_format.MessageToJson(login_res))
                token_info = {
                    'token': f"Bearer {msg.get('token','0')}",
                    'region': msg.get('lockRegion','0'),
                    'server_url': msg.get('serverUrl','0'),
                    'expires_at': time.time() + 25200
                }
                print(f"✅ Token generated: {region}")
                return token_info
        except Exception as e:
            print(f"❌ generate_token error [{region}]: {e}")
            return None

    async def refresh_all_tokens(self):
        tasks = [self.get_token(r) for r in REGION_PRIORITY]
        await asyncio.gather(*tasks)
        self.save_tokens()

    async def auto_refresh_loop(self):
        while True:
            await asyncio.sleep(6 * 60 * 60)
            print("🔄 Auto-refreshing all tokens...")
            await self.refresh_all_tokens()

# === Helper Functions ===
def pad(text: bytes) -> bytes:
    n = AES.block_size - (len(text) % AES.block_size)
    return text + bytes([n] * n)

def aes_cbc_encrypt(key, iv, plaintext):
    return AES.new(key, AES.MODE_CBC, iv).encrypt(pad(plaintext))

async def json_to_proto(json_data, proto_message):
    json_format.ParseDict(json.loads(json_data), proto_message)
    return proto_message.SerializeToString()

def get_account_credentials(region: str) -> str:
    r = region.upper()
    if r == "ME":
        return "uid=4269012488&password=MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"
    elif r == "BD":
        return "uid=4270778393&password=MG24_GAMER_9NMYG_BY_SPIDEERIO_GAMING_FXK8R"
    elif r == "IND":
        return "uid=4269013803&password=MG24_GAMER_XSBOS_BY_SPIDEERIO_GAMING_TE5NG"
    elif r in {"BR", "US", "SAC"}:
        return "uid=4269012488&password=MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"
    else:
        return "uid=4269012488&password=MG24_GAMER_U27YB_BY_SPIDEERIO_GAMING_0PNCN"

async def get_access_token(account: str):
    url = "https://ffmconnect.live.gop.garenanow.com/oauth/guest/token/grant"
    payload = account + "&response_type=token&client_type=2&client_secret=2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3&client_id=100067"
    headers = {'User-Agent': USERAGENT, 'Content-Type': "application/x-www-form-urlencoded"}
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, data=payload, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("access_token"), data.get("open_id")
                else:
                    print(f"⚠️ Token API attempt {attempt+1}: {resp.status_code}")
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"⚠️ Token API error attempt {attempt+1}: {e}")
            await asyncio.sleep(2)
    return None, None

async def GetAccountInformation(uid, region):
    try:
        token_info = await token_manager.get_token(region)
        if not token_info:
            return None
        token = token_info['token']
        server_url = token_info['server_url']
        payload = await json_to_proto(json.dumps({'a': uid, 'b': '7'}), main_pb2.GetPlayerPersonalShow())
        data_enc = aes_cbc_encrypt(MAIN_KEY, MAIN_IV, payload)
        headers = {
            'User-Agent': USERAGENT, 'Connection': "Keep-Alive",
            'Accept-Encoding': "gzip", 'Content-Type': "application/octet-stream",
            'Expect': "100-continue", 'Authorization': token,
            'X-Unity-Version': "2018.4.11f1", 'X-GA': "v1 1",
            'ReleaseVersion': RELEASEVERSION
        }
        print(f"📡 Requesting info for UID {uid} via {region}...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(server_url + '/GetPlayerPersonalShow', data=data_enc, headers=headers)
            if resp.status_code != 200:
                print(f"❌ API {resp.status_code} for {region}")
                return None
            account_info = AccountPersonalShow_pb2.AccountPersonalShowInfo()
            account_info.ParseFromString(resp.content)
            result = json.loads(json_format.MessageToJson(account_info))
            print(f"✅ Info received for UID {uid} from {region}")
            return result
    except Exception as e:
        print(f"❌ GetAccountInformation error: {e}")
        return None

def format_response(data):
    if not data:
        return {"error": "No data"}
    basic  = data.get("basicInfo", {})
    clan   = data.get("clanBasicInfo", {})
    social = data.get("socialInfo", {})
    return {
        "AccountInfo": {
            "AccountAvatarId":   str(basic.get("headPic", "0")),
            "AccountBPBadges":   str(basic.get("badgeCnt", "0")),
            "AccountBPID":       str(basic.get("badgeId", "0")),
            "AccountBannerId":   str(basic.get("bannerId", "0")),
            "AccountCreateTime": str(basic.get("createAt", "0")),
            "AccountEXP":        str(basic.get("exp", "0")),
            "AccountLastLogin":  str(basic.get("lastLoginAt", "0")),
            "AccountLevel":      str(basic.get("level", "0")),
            "AccountLikes":      str(basic.get("liked", "0")),
            "AccountName":       basic.get("nickname", "Unknown"),
            "AccountRegion":     basic.get("region", "Unknown"),
            "AccountSeasonId":   str(basic.get("seasonId", "0")),
            "AccountType":       str(basic.get("accountType", "0")),
            "BrMaxRank":         str(basic.get("maxRank", "0")),
            "BrRankPoint":       str(basic.get("rankingPoints", "0")),
            "CsMaxRank":         str(basic.get("csMaxRank", "0")),
            "CsRankPoint":       str(basic.get("csRankingPoints", "0")),
            "EquippedWeapon":    basic.get("weaponSkinShows", []),
            "ReleaseVersion":    basic.get("releaseVersion", RELEASEVERSION),
            "ShowBrRank":        str(basic.get("showBrRank", "0")),
            "ShowCsRank":        str(basic.get("showCsRank", "0")),
            "Title":             str(basic.get("title", "0"))
        },
        "AccountProfileInfo": {
            "EquippedOutfit": data.get("profileInfo", {}).get("clothes", []),
            "EquippedSkills": data.get("profileInfo", {}).get("equipedSkills", [])
        },
        "GuildInfo": {
            "GuildCapacity": str(clan.get("capacity", "0")),
            "GuildID":       str(clan.get("clanId", "0")),
            "GuildLevel":    str(clan.get("clanLevel", "0")),
            "GuildMember":   str(clan.get("memberNum", "0")),
            "GuildName":     clan.get("clanName", "No Guild"),
            "GuildOwner":    str(clan.get("captainId", "0"))
        },
        "captainBasicInfo": data.get("captainBasicInfo", {}),
        "creditScoreInfo":  data.get("creditScoreInfo", {}),
        "petInfo":          data.get("petInfo", {}),
        "socialinfo": {
            "accountId": str(social.get("accountId", "0")),
            "language":  social.get("language", "en_US")
        }
    }

# === Routes ===
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get')
def get_account_info():
    uid = request.args.get('uid')
    region_param = request.args.get('region', '').upper()
    if not uid:
        return jsonify({"error": "UID required"}), 400

    print(f"\n🔍 Processing info for UID: {uid}")
    print(f"🎯 Region priority: ME -> BD -> IND -> Others")

    regions_to_try = ([region_param] + [r for r in REGION_PRIORITY if r != region_param]
                      if region_param in SUPPORTED_REGIONS else REGION_PRIORITY)

    for region in regions_to_try:
        if region not in token_manager.tokens:
            print(f"⚠️ No token for {region}, skipping...")
            continue
        print(f"🌍 Trying {region}...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            data = loop.run_until_complete(GetAccountInformation(uid, region))
            loop.close()
            if data:
                print(f"✅ Success with {region}")
                return jsonify(format_response(data))
            else:
                print(f"⚠️ No data from {region}")
        except Exception as e:
            print(f"❌ {region} error: {e}")
            continue

    print("\n❌ All regions failed")
    return jsonify({"error": "Player not found"}), 404

@app.route('/status')
def token_status():
    status = {}
    for region, info in token_manager.tokens.items():
        expires_in = info['expires_at'] - time.time()
        status[region] = {
            "has_token": True,
            "expires_in": f"{expires_in/3600:.1f} hours",
            "server_url": info['server_url'][:50] + "..."
        }
    return jsonify({
        "region_priority": REGION_PRIORITY,
        "total_tokens": len(token_manager.tokens),
        "tokens": status
    })

@app.route('/refresh')
def refresh_tokens():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(token_manager.refresh_all_tokens())
    loop.close()
    return jsonify({"status": "refreshed", "count": len(token_manager.tokens)})

@app.route('/test/<region>')
def test_region(region):
    region = region.upper()
    if region not in SUPPORTED_REGIONS:
        return jsonify({"error": f"Region {region} not supported"})
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    token = loop.run_until_complete(token_manager.get_token(region))
    loop.close()
    if token:
        return jsonify({"region": region, "status": "Token ready",
                        "expires_in": f"{(token['expires_at']-time.time())/3600:.1f} hours"})
    return jsonify({"region": region, "status": "Token generation failed"})

# === Startup ===
def start_background_tasks():
    global token_manager
    token_manager = TokenManager()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    print("🎯 Generating priority tokens: ME -> BD -> IND")
    for region in ["ME", "IND", "BD"]:
        try:
            loop.run_until_complete(token_manager.get_token(region))
        except Exception as e:
            print(f"⚠️ {region}: {e}")

    other = [r for r in REGION_PRIORITY if r not in ["ME", "BD", "IND"]]
    for region in other:
        try:
            loop.run_until_complete(token_manager.get_token(region))
        except Exception as e:
            print(f"⚠️ {region}: {e}")

    loop.run_forever()

if __name__ == '__main__':
    print("="*55)
    print("🚀 SALIM X INFO - Free Fire Info Website")
    print("="*55)
    print(f"🎯 Region Priority: {' -> '.join(REGION_PRIORITY[:3])} -> Others")

    bg = threading.Thread(target=start_background_tasks, daemon=True)
    bg.start()

    print("⏳ Initializing tokens (ME, BD, IND)...")
    time.sleep(10)

    if token_manager:
        print(f"✅ Tokens cached: {len(token_manager.tokens)}")
        for region in REGION_PRIORITY:
            mark = "✓" if region in token_manager.tokens else "✗"
            print(f"  {mark} {region}")

    print("="*55)
    print("🚀 API running on port 5000")
    print("📝 Endpoints:")
    print("   /get?uid=UID        - Get player info")
    print("   /get?uid=UID&region=BD - Specific region")
    print("   /status             - Token status")
    print("   /refresh            - Force refresh")
    print("   /test/REGION        - Test region")
    print("="*55)

    app.run(host='0.0.0.0', port=55100, debug=False, threaded=True)
