# -*- coding: UTF-8 -*-

import yaml
from io import StringIO
import json
import logging
import hashlib

from http.server import HTTPServer, BaseHTTPRequestHandler
from optparse import OptionParser


from corpwechatbot.chatbot import CorpWechatBot

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[logging.FileHandler('/tmp/wework_bot.log', 'a', 'utf-8'), ])

# bot = CorpWechatBot(key='4780d76e-9219-43f0-a0ba-6d48f5110834')

Bot = {}
Hash = []


class RequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):

        request_headers = self.headers
        length = int(request_headers["Content-Length"])

        data = self.rfile.read(length)
        logging.debug(data)
        hash = hashlib.md5(data).hexdigest()
        print("hash: ", hash)
        self.send_response(200)
        if hash in Hash:
            print("dulp hash: ", hash)
            print("all hash: ", Hash)
            return hash
        Hash.append(hash)
        d = data.decode('utf-8')
        data = json.loads(d)
        print(data)
        # and data["project"]["namespace"] in ["ERMS"]:
        if "object_kind" in data and data["object_kind"] == "merge_request" and data["project"]["id"] in Bot and data["object_attributes"]["state"] in ["merged", "opened"] and Bot and data["object_attributes"]["action"] in ["open", "merge"]:
            content = "# MR: {title}\n# 项目: {project}\n> [{link}]({link}) \n> Maintainer:{mentioned} \n> Developer: <@{developer}> \n> State: {state}".format(
                title=data["object_attributes"]["title"], project=data["project"]["name"], link=data["object_attributes"]["url"], mentioned="".join(
                    map(lambda x: "<@{}>".format(x), Bot[data["project"]["id"]]["maintainer"])),
                developer=data["object_attributes"]["last_commit"]["author"]["email"], state=data["object_attributes"]["state"])
            if data["assignees"]:
                content = "{content}\n> Assignees: {assignees}".format(content=content,
                                                                      assignees="".join(map(lambda x: "<@{}>".format(x["email"]), data["assignees"])))
                
            for bot in Bot[data["project"]["id"]]["robot"]:
                print(content)
                bot.send_markdown(content=content)

    do_PUT = do_POST


def main():
    port = 8980
    print(('Listening on localhost:%s' % port))
    server = HTTPServer(('', port), RequestHandler)
    server.serve_forever()


if __name__ == '__main__':
    with open("config.yml", 'r') as stream:
        dictionary = yaml.safe_load(stream)
        # print(dictionary)
        for key, projects in dictionary["corpwechatbot"].items():
            for project in projects:
                if project in Bot:
                    Bot[project]["robot_key"].append(key)
                    Bot[project]["robot"].append(CorpWechatBot(key=key))
                else:
                    Bot[project] = {}
                    Bot[project]["robot_key"] = []
                    Bot[project]["robot_key"].append(key)
                    Bot[project]["robot"] = []
                    Bot[project]["name"] = projects[project]["name"]
                    Bot[project]["robot"].append(CorpWechatBot(key=key))
                    Bot[project]["maintainer"] = []
                    Bot[project]["maintainer"] = projects[project]["maintainer"]

    print(Bot)
    main()