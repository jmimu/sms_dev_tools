#!/usr/bin/python3
# coding: utf-8

from PIL import Image
import glob, os, sys

tileW=8
tileH=8

"""
Find best way to cut a big sprite into 8*8 tiles (remove empty parts)
create metatiles, try to reuse existing tiles
create tiles images

Only for indexed png (color 0=empty)
"""

allTiles=[] #all tiles are unique

def saveAllTiles(name,model):
    #model.palette.save("palette.pal")
    
    tileSetIm = model.resize( (len(allTiles)*tileW,tileH) )
    #tileSetIm.putpalette(model.palette.tobytes())
    x=0
    i=0
    for tile in allTiles:
        tileSetIm.paste(tile.im,(x,0,x+tileW,tileH))
        #print("Put tile %d at %d"%(i,x))
        x+=tileW
        i=i+1
    tileSetIm.save(name,"PNG")
    
    #allTiles[76].im.save("Tile76.png","PNG")

class Tile(object):
    def __init__(self,_im):
        #print("Tile")
        self.im=_im #tileW*tileH image
        self.data=_im.tobytes()

class MetaLine(object):
    def __init__(self,_offsetH):
        #print("MetaLine")
        self.offsetH=_offsetH
        self.tilesIndex=[] #index in allTiles
    def addImage(self,im):
        newTile=Tile(im)
        for (tileId,tile) in enumerate(allTiles):
            if (tile.data==newTile.data):
                self.tilesIndex.append(tileId)
                print("Existing tile: %d"%tileId)
                return
        #new tile
        print("New tile: %d"%len(allTiles))
        allTiles.append(newTile)
        self.tilesIndex.append(len(allTiles)-1)
    def clear(self): #remove last empty tiles
        print("Clear ",len(self.tilesIndex))
        if (len(self.tilesIndex)==0):
            return
        tileId=self.tilesIndex[-1]
        while(allTiles[tileId].im.getextrema()[1]==0):
            self.tilesIndex.pop()
            if (len(self.tilesIndex)==0):
                return
            tileId=self.tilesIndex[-1]
        
        
        
class MetaTile(object):
    def __init__(self):
        #print("MetaTile")
        self.offsetX=0 #sprite origin offset % picture (0,0)
        self.offsetY=0
        self.metaLines=[] #list of metaLines
    def saveMetaTile(self,name):
        nbTiles=0
        imW=0
        for line in self.metaLines:
            nbTiles+=len(line.tilesIndex)
            lineW=line.offsetH+len(line.tilesIndex)*tileW
            if (imW<lineW):
                imW=lineW
        tileSetIm = Image.new("RGBA", (imW,len(self.metaLines)*tileH), 0)
        x=0
        y=(len(self.metaLines)-1)*tileH
        for line in self.metaLines:
            x=line.offsetH
            for tileId in line.tilesIndex:
                tileSetIm.paste(allTiles[tileId].im,(x,y,x+tileW,y+tileH))
                x+=tileW
            y-=tileH
        tileSetIm.save(name,"PNG")
        
    def toASM(self,name):
        str=(name+"_meta_start:\n")
        nbr_lines=0
        for line in self.metaLines:
            if (len(line.tilesIndex)>0):
                nbr_lines+=1
        str+=("  .db %d,%d,%d,\n"%(self.offsetX,self.offsetY,nbr_lines))
        self.metaLines=self.metaLines[::-1]
        for line in self.metaLines:
            if (len(line.tilesIndex)>0):
                str+=("  .db %d,%d,"%(line.offsetH,len(line.tilesIndex)))
                for tileId in line.tilesIndex:
                    str+=("%d,"%tileId)
                str+=("\n")
        str+=(name+"_meta_end:\n\n")
        self.metaLines=self.metaLines[::-1]
        return str


allTiles=[]
allSprites=[]


if __name__ == '__main__':
    if (len(sys.argv) < 2):
        sys.exit('********* Usage: python %s imgPattern*.png' % sys.argv[0])
    
    picList=[]
    
    if (len(sys.argv) == 2):
        pattern= sys.argv[1]
        for imgfile in glob.glob(pattern):
            picList.append(imgfile)
    else:
        picList=sys.argv[1:]
    
    picList=sorted(picList)
    print("All pics: "+' '.join(picList))
    

    text_file = open("Output.inc", "w")
    i=0
    for imgfile in picList:
        i+=1
        file, ext = os.path.splitext(imgfile)
        im = Image.open(imgfile)
        print(imgfile+": "+file+" + "+ext+"  mode: "+im.mode)
        
        #search for first useful tile, starting at the bottom
        searchX=0
        searchY=im.size[1]-tileH
        
        #search startY
        for searchY in range(im.size[1]-1,-1,-1):
            box=[0,searchY,tileW,searchY+1] #xmin, ymin, xmax+1, ymax+1
            subIm=im.crop(box)
            #print(subIm.size)
            #print(subIm.getextrema()) #return (min,max) for each channel
            if (subIm.getextrema()[1]>0):
                #this box has a non-transparent pixel, this is our first line
                break
        if (searchY==-1):
            print("No usable pixel found, finished")
            continue
        if (searchY<tileH-1):
            searchY=tileH-1
        print("First line: ",searchY)
        startY=searchY-tileH+1
        
        #create a new MetaTile
        metaTile=MetaTile()
        
        for y in range(startY,-tileH+1,-tileH):
            #search startX
            for searchX in range(im.size[0]):
                box=[searchX,y,searchX+1,y+tileH] #xmin, ymin, xmax+1, ymax+1
                subIm=im.crop(box)
                #print(subIm.size)
                #print(subIm.getextrema()) #return (min,max) for each channel
                if (subIm.getextrema()[1]>0):
                    #this box has a non-transparent pixel, this is our first col
                    break
            if (searchX==im.size[0]):
                print("No usable pixel found on this line")
                continue
            if (searchX>im.size[0]-tileW):
                searchX=im.size[0]-tileW
            print("  First col: ",searchX)
            startX=searchX
            
            #create a new MetaLine
            metaLine=MetaLine(startX)
            metaTile.metaLines.append(metaLine)
            for x in range(startX,im.size[0],tileW):
                print("Work on tile (%d,%d)"%(x,y))
                box=[x,y,x+tileW,y+tileH] #xmin, ymin, xmax+1, ymax+1
                subIm=im.crop(box)
                #subIm.show()
                metaLine.addImage(subIm)
            if (len(metaTile.metaLines)==0):
                metaTile.metaLines=metaTile.metaLines[:-1]
            metaLine.clear()
            
        metaTile.saveMetaTile("testMetaTIle_%03d.png"%i)
        
        #im.thumbnail(size, Image.ANTIALIAS)
        #im.save(file + ".thumbnail", "JPEG")
        text_file.write(metaTile.toASM(os.path.basename(file)))
    text_file.close()
saveAllTiles("testTileSet.png",Image.open(picList[0]))
