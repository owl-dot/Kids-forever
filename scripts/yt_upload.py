import json, os, sys, requests
req = json.load(open(sys.argv[1]))
name = os.path.splitext(os.path.basename(sys.argv[1]))[0]
res = {"name": name}
def done(extra):
    res.update(extra)
    os.makedirs("inbox-upload", exist_ok=True)
    json.dump(res, open(f"inbox-upload/{name}.json", "w"), indent=1, ensure_ascii=False)
    print(res)
try:
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": os.environ["YT_CLIENT_ID"], "client_secret": os.environ["YT_CLIENT_SECRET"],
        "refresh_token": os.environ["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    r.raise_for_status()
    H = {"Authorization": "Bearer " + r.json()["access_token"]}
    if req.get("check"):
        c = requests.get("https://www.googleapis.com/youtube/v3/channels?part=id,snippet&mine=true", headers=H)
        c.raise_for_status()
        it = c.json().get("items", [])
        done({"ok": True, "channels": [(i["id"], i["snippet"]["title"]) for i in it]})
        sys.exit(0)
    meta = {"snippet": {"title": req["title"], "description": req["description"],
                        "tags": req.get("tags", []), "categoryId": req.get("category", "1"),
                        "defaultLanguage": "tr", "defaultAudioLanguage": "tr"},
            "status": {"privacyStatus": req.get("privacy", "public"),
                       "selfDeclaredMadeForKids": True, "embeddable": True}}
    data = open(req["video"], "rb").read()
    init = requests.post("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        headers={**H, "Content-Type": "application/json", "X-Upload-Content-Type": "video/mp4",
                 "X-Upload-Content-Length": str(len(data))}, json=meta)
    init.raise_for_status()
    up = requests.put(init.headers["Location"], data=data, headers={"Content-Type": "video/mp4"})
    up.raise_for_status()
    vid = up.json()["id"]; res["video_id"] = vid
    if req.get("thumb"):
        t = requests.post(f"https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId={vid}",
            headers={**H, "Content-Type": "image/jpeg"}, data=open(req["thumb"], "rb").read())
        res["thumb"] = t.status_code
    if req.get("playlist_id"):
        p = requests.post("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet",
            headers=H, json={"snippet": {"playlistId": req["playlist_id"],
                             "resourceId": {"kind": "youtube#video", "videoId": vid}}})
        res["playlist"] = p.status_code
    done({"ok": True})
except Exception as e:
    body = getattr(getattr(e, "response", None), "text", "")
    done({"ok": False, "error": str(e), "body": body[:500]})
    sys.exit(1)
