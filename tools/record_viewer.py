"""Record the MeshCat viewer of a running program as an animated GIF.

The program runs in real time with the viewer (PYRAPID_VIEWER=meshcat) and prints the
address of the viewer; this script opens it in a headless browser that records a video,
and ffmpeg converts the video to the GIF. It needs playwright and ffmpeg, not
dependencies of the project:

    pip install playwright && playwright install chromium
    python tools/record_viewer.py http://127.0.0.1:7000/static/ out.gif --seconds 30
"""

import argparse
import glob
import subprocess
import tempfile
import time

from playwright.sync_api import sync_playwright


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url", help="address of the viewer (MeshCat prints it)")
    parser.add_argument("output", help="the GIF to write")
    parser.add_argument("--seconds", type=float, default=30.0, help="time to record")
    parser.add_argument("--fps", type=float, default=10.0, help="frames of the GIF per second")
    parser.add_argument("--width", type=int, default=560, help="width of the GIF in pixels")
    parser.add_argument("--wait", type=float, default=3.0, help="seconds before the first frame")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as folder, sync_playwright() as p:
        browser = p.chromium.launch(
            args=["--use-gl=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"]
        )
        context = browser.new_context(
            viewport={"width": 960, "height": 600},
            record_video_dir=folder,
            record_video_size={"width": 960, "height": 600},
        )
        page = context.new_page()
        page.goto(args.url)
        time.sleep(args.wait + args.seconds)
        context.close()
        browser.close()
        video = glob.glob(folder + "/*.webm")[0]
        # without the button of the controls of MeshCat (24 pixels), the first seconds cut
        filters = (
            "crop=960:576:0:24,fps=%g,scale=%d:-1:flags=lanczos,split[a][b];"
            "[a]palettegen=max_colors=128[p];[b][p]paletteuse=dither=bayer:bayer_scale=3"
        ) % (args.fps, args.width)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-ss", str(args.wait), "-i", video]
            + ["-t", str(args.seconds), "-vf", filters, "-loop", "0", args.output],
            check=True,
        )
    print("%.1f s of the program, %s" % (args.seconds, args.output))


if __name__ == "__main__":
    main()
