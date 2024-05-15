# Copyright (c) 2024 Joshua Watt
#
# SPDX-License-Identifier: MIT

import argparse
import re
import uuid

from datetime import datetime, timezone
from pathlib import Path

from . import VERSION
from . import spdx3


TOOL_SPDX_ID = "http://spdx.github.com/JPEWdev/spdx3merge/" + VERSION
SPEC_VERSION = "3.0.0"
SPDXID_PREFIX = "https://spdx.dev/"


def add_author(creation_info, objset, name, cls):
    author = cls()
    author._id = (
        SPDXID_PREFIX
        + str(uuid.uuid4())
        + "/Author/"
        + re.sub(r"[^a-zA-Z0-9-]", "_", name)
    )
    author.creationInfo = creation_info
    author.name = name
    creation_info.createdBy.append(author)
    objset.add(author)


def main():
    parser = argparse.ArgumentParser(description="Merge SPDX 3 Documents")
    parser.add_argument("--version", "-V", action="version", version=VERSION)
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        action="append",
        default=[],
        help="Input SPDX 3 Document. The new document root elements will be copied from the first listed document",
    )
    parser.add_argument("--output", "-o", type=Path, help="Output file", required=True)
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Write a pretty output file (e.g. with whitespace and indentation)",
    )
    parser.add_argument(
        "--import",
        metavar=("SPDXID", "URL", "ALGORITHM", "HASH"),
        nargs=4,
        action="append",
        dest="imports",
        default=[],
        help="Import external SPDX ID in another document as an external reference",
    )

    author_group = parser.add_argument_group(
        "Document Author", "Set Document Author (choose at least one)"
    )
    author_group.add_argument(
        "--author-person",
        metavar="NAME",
        action="append",
        default=[],
        help="Create Author with name NAME as a document author",
    )
    author_group.add_argument(
        "--author-org",
        metavar="NAME",
        action="append",
        default=[],
        help="Create Organization with name NAME a document author",
    )
    author_group.add_argument(
        "--author-software-agent",
        metavar="NAME",
        action="append",
        default=[],
        help="Create SoftwareAgent with name NAME a document author",
    )
    author_group.add_argument(
        "--author-spdxid",
        metavar="SPDXID",
        action="append",
        default=[],
        help="Add SPDXID as a document author (may need to add an --import also)",
    )

    args = parser.parse_args()

    if (
        not args.author_person
        and not args.author_org
        and not args.author_software_agent
        and not args.author_spdxid
    ):
        print("ERROR: At least one --author-* argument is required")
        parser.print_help()
        return 1

    out_objset = spdx3.SHACLObjectSet()

    documents = []

    d = spdx3.JSONLDDeserializer()
    for inpath in args.input:
        in_objset = spdx3.SHACLObjectSet()
        with inpath.open("r") as f:
            d.read(f, in_objset)

        for e in in_objset.foreach_type(spdx3.Element):
            if isinstance(e, spdx3.SpdxDocument):
                documents.append(e)
            else:
                out_objset.add(e)

    creation_info = spdx3.CreationInfo()

    doc = spdx3.SpdxDocument()
    doc._id = SPDXID_PREFIX + str(uuid.uuid4()) + "/MergedSpdxDocument"
    doc.creationInfo = creation_info
    if documents:
        doc.rootElement = documents[0].rootElement

    for spdxid, url, alg, hashval in args.imports:
        m = spdx3.ExternalMap(externalSpdxId=spdxid)

        if url:
            m.locationHint = url

        if alg and hashval:
            m.verifiedUsing.append(
                spdx3.Hash(
                    algorithm=spdx3.HashAlgorithm.NAMED_INDIVIDUALS[alg],
                    hashValue=hashval,
                )
            )

        doc.imports.append(m)

    profiles = set()

    # Copy imports
    for d in documents:
        for i in d.imports:
            # If the SPDX ID is resolved but something inside the new document,
            # do not include it
            if i.externalSpdxId in out_objset:
                continue

            # Skip if the external reference is already defined
            if any(m.externalSpdxId == i.externalSpdxId for m in doc.imports):
                continue

            doc.imports.append(i)

        profiles |= set(d.profileConformance)

    doc.profileConformance = sorted(list(profiles))

    out_objset.add(doc)

    this_tool = spdx3.Tool()
    this_tool._id = TOOL_SPDX_ID
    this_tool.creationInfo = creation_info
    this_tool.description = "spdx3merge tool version " + VERSION
    this_tool.name = "spdx3merge"
    out_objset.add(this_tool)

    creation_info.createdUsing = [this_tool]
    creation_info.created = datetime.now(timezone.utc)
    creation_info.specVersion = SPEC_VERSION

    for name in args.author_person:
        add_author(creation_info, out_objset, name, spdx3.Person)

    for name in args.author_org:
        add_author(creation_info, out_objset, name, spdx3.Organization)

    for name in args.author_software_agent:
        add_author(creation_info, out_objset, name, spdx3.SoftwareAgent)

    for spdxid in args.author_spdxid:
        creation_info.createdBy.append(spdxid)

    missing_spdxids = out_objset.link()
    missing_spdxids -= set(m.externalSpdxId for m in doc.imports)
    if missing_spdxids:
        print("WARNING: The following SPDX IDs are unresolved:")
        for i in sorted(list(missing_spdxids)):
            print("  " + i)

    s = spdx3.JSONLDSerializer()
    with args.output.open("wb") as f:
        if args.pretty:
            kwargs = {
                "indent": "  ",
                "separators": (", ", ": "),
            }
        else:
            kwargs = {
                "indent": None,
                "separators": (",", ":"),
            }
        s.write(out_objset, f, **kwargs)

    return 0
