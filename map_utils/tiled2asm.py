#!/usr/bin/python3
import os
import sys
import xml.etree.ElementTree
import math
import csv
import copy

sys.argv = ('tiled2asm.py', '/home/roa/prog/infos_SMS/asm/badmin/art/floor01.tmx', '0', 'court', '6')

if (len(sys.argv)<5):
  print("Synthax: python3 tiled2asm.py tiles_file.xml first_map_tile_index mapname screens_offset")
  exit()

class Layer(object):
    def __init__(self,xmlelement):
        self.data_bit={}
        self.firstgid=-1
        for (tag,val) in xmlelement.items():
            if (tag=="name"):
                self.name=val
            if (tag=="width"):
                self.width=int(val)
            if (tag=="height"):
                self.height=int(val)
        if (xmlelement.getchildren()[0].items()[0][1]!="csv"):
            print("ERROR!! layer data must be in CSV")
            self.data=0
        else:
            datacsv=xmlelement.getchildren()[0].text[:-1] + ','
            datareader=csv.reader(datacsv.split('\n'), delimiter=',')
            self.data=[]
            for row in datareader:
                self.data.append([int(v) for v in row[:-1]])
            self.data=self.data[1:]
    def make_layer_bit(self,bit,name):
        if (self.firstgid==-1):
            print("Error! Call Layer::get_firstgid before Layer::make_layer_bit!")
            return(1)
        self.data_bit[name]=[]
        bitval=2**bit
        for row in self.data:
            self.data_bit[name].append([int((v&bitval)>0) for v in row])
    def remove_high_bits(self,bit):
        bitval=(2**bit)-1
        for y in range(len(self.data)):
            for x in range(len(self.data[y])):
                self.data[y][x]=(self.data[y][x]&bitval)
    def get_firstgid(self,xmlelement):
        if (self.firstgid>-1):
            print("Error! Can't call Layer::get_firstgid twice!")
            return(1)
        for (tag,val) in xmlelement.items():
            if (tag=="firstgid"):
                self.firstgid=int(val)
        if (self.firstgid==-1):
            print("Error! firstgid not found!")
            return(1)
        for y in range(len(self.data)):
            for x in range(len(self.data[y])):
                if (self.data[y][x]>0):
                    self.data[y][x]-=self.firstgid
    def toStr(self):
        return "%s: %dx%d first:%d"%(self.name,self.width,self.height,self.firstgid)

filename=sys.argv[1]
first_map_tile_index=int(sys.argv[2])
mapname=sys.argv[3]
screens_offset=int(sys.argv[4])
if screens_offset==0 :
    screens_offset = 32
print("first_map_tile_index=",first_map_tile_index)

e = xml.etree.ElementTree.parse(filename).getroot()
#e.items() for attributes of root
#e.getchildren()[3].tag

layer_level=None
layer_foreground=None
layer_collision=None

for xmllayer in e.findall("layer"):
    for (tag,val) in xmllayer.items():
        if (tag=="name"):
            if (val=="level"):
                layer_level=Layer(xmllayer)
            if (val=="collide"):
                layer_collision=Layer(xmllayer)
            if (val=="foreground"):
                layer_foreground=Layer(xmllayer)

#~ print("layer_foreground:")
#~ print(layer_foreground.data)

for xmltileset in e.findall("tileset"):
    for tag in xmltileset.attrib:
        layer_level.firstgid=int(xmltileset.attrib['firstgid'])
        """if (tag=="name"):
            if (val=="collisions"):
                layer_collision.get_firstgid(xmltileset)
            elif (val=="foreground"):
                layer_foreground.get_firstgid(xmltileset)
            else:
                layer_level.get_firstgid(xmltileset)"""

if layer_level==None:
    print('Error: no layer named "level"')
    exit()

#~ print(layer_foreground.data)
#~ print(layer_level.toStr())
#~ print(layer_collision.toStr())
#~ print(layer_foreground.toStr())
layer_level.make_layer_bit(30,"vflip")
layer_level.make_layer_bit(31,"hflip")
layer_level.remove_high_bits(10)

#~ print("layer_level:")
#~ print(layer_level.data)

#~ print("layer_hflip:")
#~ print(layer_level.data_bit["hflip"])

#~ print("layer_vflip:")
#~ print(layer_level.data_bit["vflip"])

#~ print("layer_foreground:")
#~ print(layer_foreground.data)

#~ print("layer_collision:")
#~ print(layer_collision.data)


#make sure there is no hflip and v flip at the same time
flip_ok=True
for y in range(len(layer_level.data_bit["vflip"])):
    for x in range(len(layer_level.data_bit["vflip"][y])):
        if ((layer_level.data_bit["vflip"][y][x]==1)
            and(layer_level.data_bit["hflip"][y][x]==1)):
                print("ERROR! hflip and vflip at the same time on (x,y)=(%d,%d)"%(x,y))
                flip_ok=False
if (not flip_ok):
    exit(1)
else:
    print("Flip check ok.")


#merge layers
""" modified extract from http://www.smspower.org/uploads/Development/msvdp-20021112.txt
 MSB          LSB
 ssspcvhnnnnnnnnn

 s = special, from collision layer
 p = Priority flag. When set, sprites will be displayed underneath the
     background pattern in question.
 c = Palette select.
 v = Vertical flip flag.
 h = Horizontal flip flag.
 n = Pattern index, any one of 512 patterns in VRAM can be selected.
 """
merged_layer=copy.copy(layer_level)
print(len(layer_level.data_bit["vflip"]),len(layer_level.data_bit["vflip"][0]))
for y in range(len(layer_level.data)):
    for x in range(len(layer_level.data[y])):
        merged_layer.data[y][x]= \
            layer_level.data[y][x] - layer_level.firstgid \
            +(layer_level.data_bit["vflip"][y][x])*(2**10) \
            +(layer_level.data_bit["hflip"][y][x])*(2**9) \
            #+(layer_collision.data[y][x])*(2**13) \
            #+(layer_foreground.data[y][x])*(2**12)

#cut it in screens (32 tiles width), with screens_offset
# 1st screen is screens_offset, next are 32
all_screens=[]
nb_screens = 1 + math.ceil((merged_layer.width-screens_offset)/32)
screens_x_start_stop = [ [0,screens_offset-1] ]
x = screens_offset
for i in range(1,nb_screens):
    screens_x_start_stop.append( [x, x+31] )
    x = x + 32
# fix last screen (may not be full)
screens_x_start_stop[-1][-1] = merged_layer.width - 1

for i in range(nb_screens):
    all_screens.append([])
    x_start, x_stop = screens_x_start_stop[i]
    for y in range(merged_layer.height):
        all_screens[i].append(merged_layer.data[y][x_start:x_stop+1])

print("%s_TilemapStart:"%(mapname))
for i,screen in enumerate(all_screens):
    print("%s_scr_%02d_TilemapStart:"%(mapname,i))
    for row in screen:
      str=".dw"
      j=0
      for val in row:
        j+=1
        #str+=' $%04x'%(val-1)
        str+=" %{0:016b}".format(val+first_map_tile_index)
        #if (j==8)or(j==16)or(j==24):
        #  str+="\n.dw"
        #if (j==32):
        #  str+="\n"
        if (j==32):
          str+="\n"
        elif (j%8==0):
          str+="\n.dw"
      print(str)
    print("%s_scr_%02d_TilemapEnd:"%(mapname,i))

print("%s_TilemapEnd:"%(mapname))

#~ print("_TilemapStart:")
#~ for row in merged_layer.data:
  #~ str=".dw"
  #~ j=0
  #~ for val in row:
    #~ j+=1
    #~ #str+=' $%04x'%(val-1)
    #~ str+=" %{0:016b}".format(val)
    #~ #if (j==8)or(j==16)or(j==24):
    #~ #  str+="\n.dw"
    #~ #if (j==32):
    #~ #  str+="\n"
    #~ if (j==merged_layer.width):
      #~ str+="\n"
    #~ elif (j%8==0):
      #~ str+="\n.dw"
  #~ print(str)
#~ print("_TilemapEnd:")

"""data = json.load(open(filename))



height=data["layers"][0]["height"]
width=data["layers"][0]["width"]


tilesets=data["tilesets"]
back_tileset=None
coll_tileset=None


for tileset in tilesets:
  print("Looking at",tileset["name"],"tileset")
  if tileset["name"]=="bg":
    back_tileset=tileset
  if tileset["name"]=="collisions":
    coll_tileset=tileset

if back_tileset:
  back_tileset_w=int(back_tileset["imagewidth"]/back_tileset["tilewidth"])
  #height is divided by 2 because lower half is first half flipped
  back_tileset_h=int(back_tileset["imageheight"]/back_tileset["tileheight"]/2)
  back_tileset_firstgid=back_tileset["firstgid"]
  back_tileset_nbr_tiles=back_tileset_w*back_tileset_h
  print("back_tileset_w: ",back_tileset_w)
  print("back_tileset_h: ",back_tileset_h)
else:
  print("Error, no tileset \"back\"!")
  exit()

#if in to half return the tile number, else hz flip
#returns number without flip, and a hz flip flag
def numTile2filp_back(num):
  if (num>0):
     num-=back_tileset_firstgid
  if (num<=back_tileset_nbr_tiles):
    return (num,0)
  y=math.floor(num/back_tileset_w)
  x=num-y*back_tileset_w
  return ( (back_tileset_w-x-1)+(y-back_tileset_h)*back_tileset_w, 1)

if coll_tileset:
  coll_tileset_w=int(coll_tileset["imagewidth"]/coll_tileset["tilewidth"])
  #height is divided by 2 because lower half is first half flipped
  coll_tileset_h=int(coll_tileset["imageheight"]/coll_tileset["tileheight"]/2)
  coll_tileset_firstgid=coll_tileset["firstgid"]
  coll_tileset_nbr_tiles=coll_tileset_w*coll_tileset_h
  print("coll_tileset_w: ",coll_tileset_w)
  print("coll_tileset_h: ",coll_tileset_h)
else:
  print("No tileset \"collisions\"!")

#if in to half return the tile number, else remove half
#returns number without flip, and a hz flip flag
def numTile2filp_coll(num):
  if (num>0):
     num-=coll_tileset_firstgid
  if (num<=coll_tileset_nbr_tiles):
    return (num,0)
  return ( num-coll_tileset_nbr_tiles, 1)


layers=data["layers"]
uncompressed_map_bg=None
uncompressed_map_coll=None
for layer in layers:
  print("Looking at",layer["name"],"layer")
  if layer["name"]=="bg":
    uncompressed_map_bg=layer["data"]
  if layer["name"]=="collisions":
    uncompressed_map_coll=layer["data"]





#todo: support >256 rows

k=0
all_values=[]
for i in range(height):
  all_values.append([])
  for j in range(width):
    flip_tile=uncompressed_map_bg[k]
    (non_flip_tile,flip)=numTile2filp_back(flip_tile)
    non_flip_coll=0
    if (coll_tileset):
      flip_coll=uncompressed_map_coll[k]
      (non_flip_coll,flip2)=numTile2filp_coll(flip_coll)
    print("tile",first_map_tile_index+non_flip_tile,"  flip",flip,"  coll",non_flip_coll)

    #final value is composed with the tile number, hz flip bit and collision bits
    final_val=first_map_tile_index+non_flip_tile+flip*512+non_flip_coll*8192
    all_values[-1].append(final_val)
    k+=1


print("_TilemapStart:")
for row in all_values:
  str=".dw"
  j=0
  for val in row:
    j+=1
    #str+=' $%04x'%(val-1)
    str+=" %{0:016b}".format(val)
    #if (j==8)or(j==16)or(j==24):
    #  str+="\n.dw"
    #if (j==32):
    #  str+="\n"
    if (j==width):
      str+="\n"
    elif (j%8==0):
      str+="\n.dw"
  print(str)
print("_TilemapEnd:")

"""


