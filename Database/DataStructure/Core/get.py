'''
Author: Austin Shank
Copyright (c) 2025 Austin Shank, All rights reserved.
'''

from pathlib import Path
from itertools import islice

DATA_PATH  = "Database/Data/Core/"

def GET(struct, id, line, idx2d=None, idx3d=None):
    '''
    Core data access function.
    '''
    objectPath = _getObjectPath(struct, id)
    return _getValue(objectPath, line, idx2d, idx3d)

def GETC(struct, id, line, idx2d=None, idx3d=None, cache={}, force=False):
    '''
    Cached variant of GET.
    '''
    cacheKey = _getCacheKey(struct, id, line, idx2d, idx3d)
    if not force and cacheKey in cache:
        return cache[cacheKey]
    objectPath = _getObjectPath(struct, id)
    cache[cacheKey] = _getValue(objectPath, line, idx2d, idx3d)
    return cache[cacheKey]

def _getCacheKey(struct, id, line, idx2d=None, idx3d=None):
    return f"{struct}_{id}_{line}_{idx2d}_{idx3d}"

def _getValue(objectPath, line, idx2d, idx3d):
    value = None
    with open(objectPath, 'r') as object:
        value = _getObjectValue(object, line, idx2d, idx3d)
    return value

def _getObjectValue(object, line, idx2d, idx3d):
    value = next(islice(object, line, line+1), None)
    # TODO - handle idx2d and idx3d if necessary
    return value.strip("\n")

def _getObjectPath(struct, id):
    structPath = Path.home() / "Documents" / "Software" / "DailyTracking" / "Database" / "Data" / struct
    return f"{structPath}/{id}.data"

if __name__ == "__main__":
    print(get("project", "sample", 1))