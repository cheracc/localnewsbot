#!/usr/bin/env python3
"""
this file was ripped directly from bluesky's official examples. some modifications were made.
Script demonstrating how to create posts using the Bluesky API, covering most of the features and embed options.
To run this Python script, you need the 'requests' and 'bs4' (BeautifulSoup) packages installed.
"""
import html
import re
import logging
import requests
from typing import Dict, List, Any
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from src.config import Config
from src.rsssource import BskyPost

class BskyApiHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def bsky_login_session(self, pds_url: str, handle: str, password: str) -> Dict:
        resp = requests.post(
            pds_url + "/xrpc/com.atproto.server.createSession",
            json={"identifier": handle, "password": password},
        )
        resp.raise_for_status()
        return resp.json()
    
    def parse_hashtags(self, text: str) -> List[Dict]:
        spans = []
        hashtag_regex = rb"[$|\W](#([a-zA-Z0-9_]{1,30}))"
        text_bytes = text.encode("UTF-8")
        for m in re.finditer(hashtag_regex, text_bytes):
            self.logger.debug(f"found hashtag: {m.group(1).decode('UTF-8')} at bytes {m.start(1)} to {m.end(1)}")
            spans.append(
                {
                    "start": m.start(1),
                    "end": m.end(1),
                    "tag": m.group(1).decode("UTF-8"),
                }
            )
        return spans

    def parse_mentions(self, text: str) -> List[Dict]:
        spans = []
        # regex based on: https://atproto.com/specs/handle#handle-identifier-syntax
        mention_regex = rb"[$|\W](@([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)"
        text_bytes = text.encode("UTF-8")
        for m in re.finditer(mention_regex, text_bytes):
            spans.append(
                {
                    "start": m.start(1),
                    "end": m.end(1),
                    "handle": m.group(1)[1:].decode("UTF-8"),
                }
            )
        return spans

    def parse_urls(self, text: str) -> List[Dict]:
        spans = []
        # partial/naive URL regex based on: https://stackoverflow.com/a/3809435
        # tweaked to disallow some training punctuation
        url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
        text_bytes = text.encode("UTF-8")
        for m in re.finditer(url_regex, text_bytes):
            spans.append(
                {
                    "start": m.start(1),
                    "end": m.end(1),
                    "url": m.group(1).decode("UTF-8"),
                }
            )
        return spans

    def parse_facets(self, pds_url: str, text: str) -> List[Dict]:
        """
        parses post text and returns a list of app.bsky.richtext.facet objects for any mentions (@handle.example.com) or URLs (https://example.com)

        indexing must work with UTF-8 encoded bytestring offsets, not regular unicode string offsets, to match Bluesky API expectations
        """
        facets = []
        for m in self.parse_mentions(text):
            resp = requests.get(
                pds_url + "/xrpc/com.atproto.identity.resolveHandle",
                params={"handle": m["handle"]},
            )
            # if handle couldn't be resolved, just skip it! will be text in the post
            if resp.status_code == 400:
                continue
            did = resp.json()["did"]
            facets.append(
                {
                    "index": {
                        "byteStart": m["start"],
                        "byteEnd": m["end"],
                    },
                    "features": [{"$type": "app.bsky.richtext.facet#mention", "did": did}],
                }
            )
        for u in self.parse_urls(text):
            facets.append(
                {
                    "index": {
                        "byteStart": u["start"],
                        "byteEnd": u["end"],
                    },
                    "features": [
                        {
                            "$type": "app.bsky.richtext.facet#link",
                            # NOTE: URI ("I") not URL ("L")
                            "uri": u["url"],
                        }
                    ],
                }
            )

        for h in self.parse_hashtags(text):
            self.logger.debug(f"found hashtag: {h['tag']} at bytes {h['start']} to {h['end']}")
            facets.append(
                {
                    "index": {
                        "byteStart": h["start"],
                        "byteEnd": h["end"],
                    },
                    "features": [
                        {
                            "$type": "app.bsky.richtext.facet#tag",
                            "tag": h["tag"],
                        }
                    ],
                }
            )
        return facets

    def parse_uri(self, uri: str) -> Dict:
        if uri.startswith("at://"):
            repo, collection, rkey = uri.split("/")[2:5]
            return {"repo": repo, "collection": collection, "rkey": rkey}
        elif uri.startswith("https://bsky.app/"):
            repo, collection, rkey = uri.split("/")[4:7]
            if collection == "post":
                collection = "app.bsky.feed.post"
            elif collection == "lists":
                collection = "app.bsky.graph.list"
            elif collection == "feed":
                collection = "app.bsky.feed.generator"
            return {"repo": repo, "collection": collection, "rkey": rkey}
        else:
            raise Exception("unhandled URI format: " + uri)

    def get_reply_refs(self, pds_url: str, parent_uri: str) -> Dict:
        uri_parts = self.parse_uri(parent_uri)
        resp = requests.get(
            pds_url + "/xrpc/com.atproto.repo.getRecord",
            params=uri_parts,
        )
        resp.raise_for_status()
        parent = resp.json()
        root = parent
        parent_reply = parent["value"].get("reply")
        if parent_reply is not None:
            root_uri = parent_reply["root"]["uri"]
            root_repo, root_collection, root_rkey = root_uri.split("/")[2:5]
            resp = requests.get(
                pds_url + "/xrpc/com.atproto.repo.getRecord",
                params={
                    "repo": root_repo,
                    "collection": root_collection,
                    "rkey": root_rkey,
                },
            )
            resp.raise_for_status()
            root = resp.json()

        return {
            "root": {
                "uri": root["uri"],
                "cid": root["cid"],
            },
            "parent": {
                "uri": parent["uri"],
                "cid": parent["cid"],
            },
        }

    def upload_file(self, pds_url, access_token, filename, img_bytes):
        suffix = filename.split(".")[-1].lower()
        mimetype = "application/octet-stream"
        if suffix in ["png"]:
            mimetype = "image/png"
        elif suffix in ["jpeg", "jpg"]:
            mimetype = "image/jpeg"
        elif suffix in ["webp"]:
            mimetype = "image/webp"

        # WARNING: a non-naive implementation would strip EXIF metadata from JPEG files here by default
        resp = requests.post(
            pds_url + "/xrpc/com.atproto.repo.uploadBlob",
            headers={
                "Content-Type": mimetype,
                "Authorization": "Bearer " + access_token,
            },
            data=img_bytes,
        )
        resp.raise_for_status()
        return resp.json()["blob"]

    def upload_images(
        self, pds_url: str, access_token: str, image_paths: List[str], alt_text: str
    ) -> Dict:
        images = []
        for ip in image_paths:
            with open(ip, "rb") as f:
                img_bytes = f.read()
            # this size limit specified in the app.bsky.embed.images lexicon
            if len(img_bytes) > 1000000:
                raise Exception(
                    f"image file size too large. 1000000 bytes maximum, got: {len(img_bytes)}"
                )
            blob = self.upload_file(pds_url, access_token, ip, img_bytes)
            images.append({"alt": alt_text or "", "image": blob})
        return {
            "$type": "app.bsky.embed.images",
            "images": images,
        }

    def fetch_embed_url_card(self, pds_url: str, access_token: str, bsky_post: BskyPost) -> Dict:
        # the required fields for an embed card
        card = {
            "uri": bsky_post.link,
            "title": "",
            "description": "",
        }

        # fetch the HTML
        try:
            resp = requests.get(bsky_post.link)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
        except requests.HTTPError as e:
            self.logger.warning(f"Couldn't fetch embed card for URL {bsky_post.link}, will try to build one but it may be incomplete")
            card["title"] = bsky_post.headline
            card["description"] = bsky_post.description
            img_url = bsky_post.img_url
            if bsky_post.source_name and "ABC27" in bsky_post.tag:
                img_url = "https://bloximages.newyork1.vip.townnews.com/lancasteronline.com/content/tncms/assets/v3/editorial/0/a7/0a74c5f8-fbb4-11e3-aec4-001a4bcf6878/53a99900b2301.image.png"
            if img_url and len(img_url) > 0:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                try:
                    resp = requests.get(str(img_url).split("?")[0], headers=headers)  # strip query params which can cause issues with some CDNs
                    resp.raise_for_status()
                    card["thumb"] = self.upload_file(pds_url, access_token, img_url, resp.content)
                except Exception as e:
                    self.logger.warning(f"Could not fetch image for embed card: {bsky_post.img_url}")
            return {
                "$type": "app.bsky.embed.external",
                "external": card,
            }

        # parse out OpenGraph tags if available
        title_tag = soup.find("meta", property="og:title")
        if title_tag:
            card["title"] = title_tag["content"]

        description_tag = soup.find("meta", property="og:description")
        if description_tag:
            card["description"] = description_tag["content"]

        image_tag = soup.find("meta", property="og:image")
        if image_tag:
            img_url = image_tag["content"]
            if "://" not in img_url:
                img_url = bsky_post.link + img_url
            resp = requests.get(img_url)
            try:
                resp.raise_for_status()
                card["thumb"] = self.upload_file(pds_url, access_token, img_url, resp.content)
            except Exception as e:
                self.logger.warning(f"failed to fetch/upload embed thumbnail: {e}")

        return {
            "$type": "app.bsky.embed.external",
            "external": card,
        }

    def get_embed_ref(self, pds_url: str, ref_uri: str) -> Dict:
        uri_parts = self.parse_uri(ref_uri)
        resp = requests.get(
            pds_url + "/xrpc/com.atproto.repo.getRecord",
            params=uri_parts,
        )
        self.logger.debug(resp.json())
        resp.raise_for_status()
        record = resp.json()

        return {
            "$type": "app.bsky.embed.record",
            "record": {
                "uri": record["uri"],
                "cid": record["cid"],
            },
        }

    def create_post(self, bsky_account, bsky_post: BskyPost):
        args = bsky_post.get_post_args(bsky_account.cfg)
        session = self.bsky_login_session(args["pds_url"], args["handle"], args["password"])

        # trailing "Z" is preferred over "+00:00"
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # these are the required fields which every post must include
        post = {
            "$type": "app.bsky.feed.post",
            "text": args["text"],
            "createdAt": now,
        }

        # parse out mentions and URLs as "facets"
        if len(args["text"]) > 0:
            facets = self.parse_facets(args["pds_url"], post["text"])
            if facets:
                post["facets"] = facets

        # if this is a reply, get references to the parent and root
        
        if args.get("reply_to"):
            post["reply"] = self.get_reply_refs(args["pds_url"], args["reply_to"])

        if args.get("image"):
            post["embed"] = self.upload_images(
                args["pds_url"], session["accessJwt"], args["image"], args["alt_text"]
            )

        elif args.get("embed_ref"):
            post["embed"] = self.get_embed_ref(args["pds_url"], args["embed_ref"])

        elif args.get("embed_url"):
            post["embed"] = self.fetch_embed_url_card(
                args["pds_url"], session["accessJwt"], bsky_post
            )

        resp = requests.post(
            args["pds_url"] + "/xrpc/com.atproto.repo.createRecord",
            headers={"Authorization": "Bearer " + session["accessJwt"]},
            json={
                "repo": session["did"],
                "collection": "app.bsky.feed.post",
                "record": post,
            },
        )

        try:
            resp.raise_for_status()
        except Exception as e:
            self.logger.warning(f"failed to create record: {e}")
            self.logger.debug(f"text length: {len(args['text'])} request body: {post}")
            try:
                self.logger.debug(resp.text)
            except Exception:
                pass

