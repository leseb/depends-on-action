#!/usr/bin/env python3

"""Stage3: inject the local dependencies into the main changeset.
"""

import json
import os
import sys

from golang import process_golang
from javascript import process_javascript
from python import process_python


def extract_repo_name(url):
    "Return the repository name from a git URL in the form github.com/<org>/<repo>."
    if not url:
        return url
    if url.endswith(".git"):
        url = url[:-4]
    return "/".join(url.split("/")[2:5])


def get_remote_url(proj_dir):
    "Return the remote URL of the git repository in proj_dir."
    origin_url = os.popen(f"cd {proj_dir} && git remote get-url origin").read().strip()
    # convert ssh to https
    if origin_url.startswith("git@"):
        origin_url = origin_url.replace(":", "/", 1)
        origin_url = origin_url.replace("git@", "https://")
    return origin_url


def directories(top_dir, main_dir):
    """Return a dict of {repo_name: <dict info>} for all git repositories in top_dir.

    dict info:
    - topdir: the top directory of the repository
    - path: the path to the module in the repository
    - subdir: the subdirectory of the module in the repository (optional)
    """
    ret = {}
    for d in os.listdir(top_dir):
        key_dir = os.path.join(top_dir, d)
        if (
            os.path.isdir(key_dir)
            and key_dir != main_dir
            and os.path.isdir(os.path.join(key_dir, ".git"))
        ):
            info = {"topdir": top_dir, "path": top_dir}
            json_fname = os.path.join(key_dir, "depends-on.json")
            if os.path.exists(json_fname):
                with open(json_fname, "r") as json_stream:
                    data = json.load(json_stream)
                    info.update(data)
                    if "subdir" in data:
                        info["path"] = os.path.join(key_dir, data["subdir"])
            ret[extract_repo_name(get_remote_url(key_dir))] = info
    return ret


def detect_container_mode(main_dir):
    "Return True if main_dir contains a Dockerfile or a Containerfile."
    return os.path.exists(os.path.join(main_dir, "Dockerfile")) or os.path.exists(
        os.path.join(main_dir, "Containerfile")
    )


def main():
    "Main function."
    main_dir = os.getcwd()
    top_dir = os.path.dirname(main_dir)

    dirs = directories(top_dir, main_dir)
    print(
        f"{main_dir=} {top_dir=} {dirs=} called from {__file__}!",
        file=sys.stderr,
    )

    container_mode = detect_container_mode(main_dir)
    print(f"{container_mode=}", file=sys.stderr)
    process_golang(main_dir, dirs, container_mode)
    process_python(main_dir, dirs, container_mode)
    process_javascript(main_dir, dirs, container_mode)


if __name__ == "__main__":
    sys.exit(main())

# stage3.py ends here
