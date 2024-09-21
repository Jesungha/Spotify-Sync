from downloader.dl import Dl
import os
import time

def download_song(track_id, location):
    dl = Dl(
        "./Spotify",
        "./temp",
        "./cookies.txt",
        "./google_aosp_on_ia_emulator_14.0.0_f6d0faa5_4464_l3.wvd",
        "ffmpeg",
        "{album_artist}/{album}",
        "Compilations/{album}",
        "{track:02d} {title}",
        "{disc}-{track:02d} {title}",
        "",
        40,
        False,
        False,
    )
    
    gid = dl.uri_to_gid(track_id)
    metadata = dl.get_metadata(gid)
    file_id = dl.get_file_id(metadata)
    
    pssh = dl.get_pssh(file_id)
    decryption_key = dl.get_decryption_key(pssh)
    stream_url = dl.get_stream_url(file_id)
    
    enc_location = f"{location}/{track_id}_encrypted.m4a"
    dl.download(enc_location, stream_url)
    fixed_location = f"{location}/{track_id}.m4a"
    dl.fixup(decryption_key, enc_location, fixed_location)
    os.remove(enc_location)
    return fixed_location

if __name__ == "__main__":
    start = time.time()
    meta = download_song("1C7KSXR2GVxknex6I4ANco", "./out")
    # print("Downloaded: " + meta["name"]+ " by " + meta["artist"][0]["name"])
    print(f"Time taken: {(time.time() - start) * 1000}ms")