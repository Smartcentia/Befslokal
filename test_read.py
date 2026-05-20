
import os

files = ['/Users/frank/Documents/BEFS_CLEAN/Eiendomfebruar.csv', '/Users/frank/Documents/BEFS_CLEAN/finans.csv']

for f in files:
    try:
        with open(f, 'rb') as fd:
            head = fd.read(1000)
            print(f'File {f} head: {head[:100]}...')
    except Exception as e:
        print(f'Error reading {f}: {e}')
