"""
Use this script to download BBC articles (html files) from the Wayback Machine.
The script could fail to download some URLs (Wayback Machine servers temporarily down). Each time you run this script, it stores the missing URLs that should be downloaded in the next turn. [INCORPORATE MISSING URLS]
"""
'''
Libraries
'''
import argparse
import os
import re
import sys
import time
import math
from collections import namedtuple
import hashlib
from itertools import chain
from itertools import repeat
from multiprocessing.pool import Pool
from multiprocessing.pool import ThreadPool
from lxml import html
import requests
import socket
import tqdm 

class ProgressBar(object):
  """Simple progress bar.
  #TODO: Modify using tqdm 
  """

  def __init__(self, total=100, stream=sys.stderr):
    self.total = total
    self.stream = stream
    self.last_len = 0
    self.curr = 0

  def Increment(self):
    self.curr += 1
    self.PrintProgress(self.curr)

    if self.curr == self.total:
      print('')

  def PrintProgress(self, value):
    self.stream.write('\b' * self.last_len)
    pct = 100 * self.curr / float(self.total)
    out = '{:.2f}% [{}/{}]'.format(pct, value, self.total)
    self.last_len = len(out)
    self.stream.write(out)
    self.stream.flush()


def DownloadMapper(zipped_inp):
  """Downloads a URL.
  Args:
    zipped_inp: urls_left_todownload, repeat(downloads_dir), repeat(timestamp_exactness)
  Returns:
    A pair of URL and content.
  """
  # print(set(zipped_inp))
  zipped = list(set(zipped_inp))
  zipped = zipped[0]
  url, downloads_dir, timestamp_exactness = zipped
  # print url
  return url, DownloadUrl(url, downloads_dir, timestamp_exactness)

def DownloadUrl(url, downloads_dir, timestamp_exactness, max_attempts=5, timeout=5): 
  """Downloads a URL.
  Args:
    url: The URL.
    downloads_dir: Download directory 
    timestamp_exactness
    max_attempts: Max attempts for downloading the URL.
    timeout: Connection timeout in seconds for each attempt.
  Returns:
    The HTML content the URL or None if the request failed.
  """

  # Get fileid and htmlid (where html content will be stored)
  fileid = url.replace("http://web.archive.org/web/", "")
  htmlfileid = fileid.replace("http://", "")
  htmlfileid = fileid.replace("/", "-") + ".html"
  # print fileid
  
  # If html content has been saved previously then use that 
  try:
    with open(downloads_dir+"/"+htmlfileid) as f:
      return f.read()
  except Exception as e:
    pass

  # Change download url depending on the timestamp_exactness 
  # Time stamp 14 letters (year month day hour minutes)
  url_data = url.strip().split("/")
  # Update timestamp
  url_data[4] = url_data[4][:timestamp_exactness]
  url = "/".join(url_data)
  
  attempts = 0
  while attempts < max_attempts:
    try:
      print("Requesting html.....")
      req = requests.get(url, allow_redirects=True, timeout=timeout)

      if req.status_code == requests.codes.ok:
        content = req.text.encode(req.encoding)
        with open(downloads_dir+"/"+htmlfileid, 'wb') as f:
          # print("Writing to file....")
          # print(content)
          f.write(content)
        return content
      elif (req.status_code in [301, 302, 404, 503]
            and attempts == max_attempts - 1):
        return None
    # except requests.exceptions.ConnectionError:
    #   pass
    except requests.exceptions.ContentDecodingError:
      return None
    except requests.exceptions.ChunkedEncodingError:
      return None
    # except requests.exceptions.Timeout:
    #   pass
    # except socket.timeout:
    #   pass
    # except requests.exceptions.TooManyRedirects:
    #   pass
    except Exception as e:
      pass 

    # Exponential back-off if attempts exhausted 
    time.sleep(math.pow(2, attempts))
    attempts += 1

  return None


def ReadUrls(filename):
  """
  Helper Function: Reads a list of URLs.
  Args:
    filename: The filename containing the URLs.
  Returns:
    A list of URLs.
  """

  with open(filename) as f:
    return [line.strip('\n') for line in f]


def WriteUrls(filename, urls):
  """
  Helper Function: Writes a list of URLs to given file.
  Args:
    filename: The filename to the file where the URLs should be written.
    urls: The list of URLs to write.
  """

  with open(filename, 'w') as f:
    f.writelines(url + '\n' for url in urls)

def DownloadMode(urls_file, missing_urls_file, downloads_dir, request_parallelism, timestamp_exactness):
  """Downloads the URLs for the specified corpus.
  #TODO: Add parallelism 
         Figure out Progress Bar
  Args:
    urls_file: File with urls
    missing_urls_file: File where missing urls are stored 
    downloads_dir: article download directory 
    request_parallelism: The number of concurrent download requests.
    timestamp_exactness: Time stamp exactness (year, month, date, hr, minute and second)
  """
    
  print('Downloading URLs from the {} file:'.format(urls_file))
  urls_full = ReadUrls(urls_file)
  
  urls_valid_todownload = urls_full[:]
  missing_urls_filename = missing_urls_file
  if os.path.exists(missing_urls_filename):
    print('Only downloading missing URLs')
    urls_valid_todownload = list(set(urls_full).intersection(ReadUrls(missing_urls_filename)))

  collected_urls = []
  missing_urls = []
  urls_left_todownload = urls_valid_todownload[:]
  print('urls left to download: ' +  str(len(urls_left_todownload)))
  results = []
  while(len(urls_left_todownload) != 0):

    # p = ThreadPool(request_parallelism)

    # print(urls_left_todownload, type(urls_left_todownload))
    # print(downloads_dir, type(downloads_dir))
    # print(timestamp_exactness, type(timestamp_exactness))
    for urls in urls_left_todownload:
      # print("URL: ", urls)
      ans = DownloadMapper(zip([urls], repeat(downloads_dir), repeat(timestamp_exactness)))
      results.append(ans)
    # results = p.imap_unordered(DownloadMapper, zip(urls_left_todownload, repeat(downloads_dir), repeat(timestamp_exactness)))
      progress_bar = ProgressBar(len(urls_left_todownload))

    try:
      for url, story_html in results:
        if story_html:
          collected_urls.append(url)
        else:
          missing_urls.append(url)

        progress_bar.Increment()
    except KeyboardInterrupt:
      print('Interrupted by user')
      break
    except TypeError:
      print('TypeError (probably a robot.txt case): '+url)
      missing_urls.append(url)
      p.terminate()
    # except IOError:
    #   print 'IOError (probably File name too long): '+url
    #   missing_urls.append(url)
    #  p.terminate()

    # Reset the urls_left_todownload for the rest of not-tried urls
    print('Reset urls_left_todownload - (collected_urls, missing_urls)')
    urls_toignore = collected_urls[:] +  missing_urls[:]
    urls_left_todownload = list(set(urls_left_todownload) - set(urls_toignore))
    print('urls left to download: ' +  str(len(urls_left_todownload)))

  # Write all the final missing urls
  missing_urls = []
  missing_urls.extend(set(urls_valid_todownload) - set(collected_urls))

  WriteUrls(missing_urls_file, missing_urls)

  if missing_urls:
    print('{} URLs couldn\'t be downloaded, see {}.'.format((len(missing_urls), missing_urls_file)))
    print('Try and run the command again to download the missing URLs.')

def main():
  parser = argparse.ArgumentParser(description='Download BBC News Articles')
  parser.add_argument('--urls_file', type=str, default="./Sample.txt")
  parser.add_argument('--missing_urls_file', type=str, default="./Missing.txt")
  parser.add_argument('--downloads_dir', type=str, default="./xsum-raw-downloads")
  parser.add_argument('--request_parallelism', type=int, default=200)
  parser.add_argument('--context_token_limit', type=int, default=2000)
  parser.add_argument('--timestamp_exactness', type=int, default=14)
  args = parser.parse_args()


    
  urls_file_to_download = args.urls_file
  missing_urls_file = args.missing_urls_file
  downloads_dir = args.downloads_dir
  request_parallelism = args.request_parallelism
  context_token_limit = args.context_token_limit
  timestamp_exactness = args.timestamp_exactness

  print('Creating download directory.....')

  if not os.path.exists(downloads_dir):
    os.mkdir(downloads_dir)
  
  
  DownloadMode(urls_file_to_download, missing_urls_file, downloads_dir, request_parallelism, timestamp_exactness)


if __name__ == '__main__':
  main()
