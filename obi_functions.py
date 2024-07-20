import sys
import numpy as np
import time
import os
from block_data import *

def build_layer(ids):
  segments = []
  i = 0
  prev_id = -1
  # for _id in ids: # no compression
      # segments.extend([0, _id])

  while i < len(ids): # compression
    _id = ids[i]
    if prev_id != _id or segments[-2] == 255:
      segments.extend([0, _id])
      prev_id = _id
    else:
      segments[-2] +=1
    i += 1

  _layer = [len(segments)//2]+segments
  return _layer

def build_from_voxels(voxels):
  layers = []
  for i in range(min(voxels.shape[2], 32)):
    layer = build_layer(voxels[:,:,i].ravel())
    layers.extend(layer)
  return np.array(layers, dtype=">u2") # 2 bytes, big endian >

def create_voxels(block_label): # creates array of size 32x32x64 filled with a single block
  return np.ones((32,32,64), dtype=np.int64)*block_label

def to_two_chunks(voxels):
  

  lower = build_from_voxels(voxels[:, :, :32])
  upper = build_from_voxels(voxels[:, :, 32:64])
  return lower, upper

def save_claim(lower, upper, account_id, account_name, chunk_hex):
  with open(f"{chunk_hex}0.chunk", "wb") as binary_file:
    binary_file.write(lower.tobytes())
    binary_file.write(bytes(account_id + account_name))
  with open(f"{chunk_hex}1.chunk", "wb") as binary_file:
    binary_file.write(upper.tobytes())
    binary_file.write(bytes(account_id + account_name))

def print_layer(layer):
  segment_count = layer[0]
  for i in range(segment_count):
    o = (i*2)+1
    print(f"{i:4d}: {layer[o]:3d} {layer[o+1]:x}")

def labels_to_ids(voxels, block_ids):
  fn = np.frompyfunc(lambda v: block_ids[v], 1, 1) 
  return fn(voxels).astype(">u2")

def ids_to_labels(voxels, ids_to_index):
  fn = np.frompyfunc(lambda v: ids_to_index[v], 1, 1) 
  return fn(voxels).astype(">u2")

def to_voxels(layers):
  voxels = []
  i = segments = block_count = 0
  layer = 0
  while layer <= 32:
    if segments <= 0:
      segments = layers[i]
      if segments == 0: voxels.extend([0]*(1024))
      block_count = 0
      i += 1
      layer +=1
    else: 
      block_count += layers[i]+1
      voxels.extend([layers[i+1]]*(layers[i]+1))
      segments -= 1
      if segments == 0: voxels.extend([0]*(1024-block_count))
      i += 2
  voxels = np.array(voxels).reshape((32,32,32))
  voxels = np.swapaxes(voxels, 0, 1)
  voxels = np.swapaxes(voxels, 1, 2)
  return voxels

def from_two_chunks(lower, upper):
  vlower = to_voxels(lower)
  vupper = to_voxels(upper)
  return np.concatenate((vlower, vupper), axis=2)

def read_claim(chunk_hex):
  with open(f"{chunk_hex}0.chunk", "rb") as file:
    file_size = os.path.getsize(file.name)
    lower = np.fromfile(file, dtype=np.dtype('>u2'))
    file.seek(-70, os.SEEK_END)
    last_bytes = np.frombuffer(file.read(70), dtype=np.uint8)
  with open(f"{chunk_hex}1.chunk", "rb") as file:
    file_size = os.path.getsize(file.name)
    upper = np.fromfile(file, dtype=np.dtype('>u2'))
    file.seek(-70, os.SEEK_END)
    last_bytes = np.frombuffer(file.read(70), dtype=np.uint8)
  account_id = last_bytes[:6]
  account_name = f'{"".join([chr(c) for c in last_bytes[6:]])}'
  return lower, upper, account_name, account_id

def read_claim_get_voxels(chunk_hex):
  _lower, _upper, _account_name, _account_id = read_claim(chunk_hex)
  _voxels = from_two_chunks(_lower, _upper)
  return _voxels

def save_claim_from_voxels(voxels, chunk_hex, _account_name="meow"):
  account_name = [0]*64
  account_id = [0, 2, 0, 1, 0, 0]
  account_name[:len(_account_name)] = [ord(char) for char in _account_name]
  lower, upper = to_two_chunks(voxels)
  save_claim(lower, upper, account_id, account_name, chunk_hex)

def read_and_clean_dungeon(path): 
  voxels = read_claim_get_voxels(f"{path}")
  voxels[voxels==0xe00c] = 0xe00d
  voxels[np.isin(voxels, natural_ids[1:])] = natural_ids[0]
  return voxels

def load_unclean(folder_path, load):
  if load == True:
    dungeons, dungeon_voxels = np.load('npsave/unlcean_dungeons.npy'), np.load('npsave/unlcean_dungeon_voxels.npy')
    return dungeons, dungeon_voxels
  dungeons = sorted(list(set([f[:-7] for f in os.listdir(folder_path)])))[:] # 50
  print(f"found {len(dungeons)} dungeons")
  dungeon_voxels = []
  for i,d in enumerate(dungeons): 
    if i % 10 == 0: print(f"{i+1}/{len(dungeons)}", end='\r')
    voxels = read_claim_get_voxels(f"{folder_path}/{d}")
    dungeon_voxels.append(voxels)
  print(f"{i+1}/{len(dungeons)}")
  dungeon_voxels = np.array(dungeon_voxels)
  np.save('npsave/unlcean_dungeons.npy', dungeons)
  np.save('npsave/unlcean_dungeon_voxels.npy', dungeon_voxels)
  return dungeons, dungeon_voxels

def move_claim(from_path, to_path, claimed_by):
  voxels = read_claim_get_voxels(from_path)
  save_claim_from_voxels(voxels, to_path, claimed_by)

def compare_2_claims(from_path1, from_path2, to_path1, to_path2, name1, name2):
  voxels1 = read_claim_get_voxels(from_path1)
  voxels2 = read_claim_get_voxels(from_path2)
  diff = voxels1==voxels2
  voxels2[diff] = 1
  voxels1[diff] = 1
  save_claim_from_voxels(voxels1, to_path1, name1)
  save_claim_from_voxels(voxels2, to_path2, name2)

start_time = time.perf_counter()

# meow

elapsed_time = time.perf_counter()-start_time
print(f"{elapsed_time:.4f} seconds")



