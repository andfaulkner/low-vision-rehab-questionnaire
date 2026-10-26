"""Convert a .docx file to markdown using pandoc (or mammoth as fallback)."""
import argparse
import os
import re
import shutil
import subprocess
import sys

DEFAULT_INPUT = "data/LVR_Q_Study_Outline.docx"


def clean(md):
    md = md.replace("\r\n", "\n").replace("\r", "\n")
    md = re.sub(r"\[([^\]]+)\]\{\.underline\}", r"\1", md)
    md = md.replace("\\'", "'").replace('\\"', '"')
    md = re.sub(r"(?<!\\)\\([>*])", r"\1", md)
    md = "\n".join(line.rstrip() for line in md.split("\n"))
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip("\n") + "\n"


def add_note(md, name):
    lines = md.split("\n")
    note = ["", "_Converted from `%s`._" % name, ""]
    if lines and lines[0].startswith("#"):
        return "\n".join([lines[0]] + note + lines[1:])
    return "\n".join(note + lines)


def convert_pandoc(src):
    result = subprocess.run(
        ["pandoc", src, "-t", "markdown", "--wrap=none", "--markdown-headings=atx"],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def convert_mammoth(src):
    import mammoth
    with open(src, "rb") as f:
        return mammoth.convert_to_markdown(f).value


def main():
    parser = argparse.ArgumentParser(description="Convert a .docx file to markdown.")
    parser.add_argument("input", nargs="?", default=DEFAULT_INPUT,
                        help="input .docx (default: %(default)s)")
    parser.add_argument("output", nargs="?",
                        help="output .md (default: input with .md extension)")
    args = parser.parse_args()

    src = os.path.abspath(args.input)
    if args.output:
        dst = os.path.abspath(args.output)
    else:
        dst = os.path.splitext(src)[0] + ".md"

    if shutil.which("pandoc"):
        md = convert_pandoc(src)
    else:
        try:
            md = convert_mammoth(src)
        except ImportError:
            print("Error: neither pandoc nor mammoth is available.", file=sys.stderr)
            print("Install pandoc (brew install pandoc) or mammoth (pip install mammoth).",
                  file=sys.stderr)
            sys.exit(1)

    md = add_note(clean(md), os.path.basename(src))
    md = clean(md)

    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)

    print("Converted %s → %s" % (args.input, args.output or os.path.relpath(dst)))


if __name__ == "__main__":
    main()
