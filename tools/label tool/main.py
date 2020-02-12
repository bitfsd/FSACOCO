#-------------------------------------------------------------------------------
# Name:        Object bounding box label tool
# Purpose:     Label object bboxes for ImageNet Detection data
# Author:      Tairan Chen
# Created:     04/25/2019

#
#-------------------------------------------------------------------------------
from __future__ import division
from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
import ttk
import os
import glob
import random
import math

# colors for the bboxes
COLORS = ['blue', 'yellow', 'red', 'black']
# image sizes for the examples
SIZE = 10, 10
# Micrometers
#focal_length = 4000.0
focal_length = 4215.17
# Micrometers
sensor_width  = 6182.4
sensor_height = 4953.6
# Radians
h_AOV = 1.3158683
v_AOV = 1.1088353
# (cone_width, cone_height) in micrometers
small_cone_width  = 228000.0
small_cone_height = 325000.0
large_cone_width  = 285000.0
large_cone_height = 505000.0

# Distance Flag
SHOW_DISTANCE    = False

# Bounding Box Height Threshold in pixel
HEIGHT_THRESHOLD = 20

def get_color_ix(label):
    '''
    '''
    if label == 'blue-cone':
        return 0
    elif label == 'yellow-cone':
        return 1
    else:
        return 2

class LabelTool():
    def __init__(self, master):
        # set up the main frame
        self.parent = master
        self.parent.title("BITFSD LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width = FALSE, height = FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList= []
        self.egDir = ''
        self.egList = []
        self.outDir = ''
        self.cur = 0
        self.total = 0
        self.category = 0
        self.imagename = ''
        self.labelfilename = ''
        self.tkimg = None
        self.image_width  = 0
        self.image_height = 0
        self.currentLabelclass = ''
        self.cla_can_temp = []
        self.classcandidate_filename = 'class.txt'

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId = None
        self.bboxList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Image Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command = self.loadDir)
        self.ldBtn.grid(row = 0, column = 2,sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross', scrollregion=(0, 0, 1920, 1080))

        hbar = Scrollbar(self.frame, orient=HORIZONTAL)
        hbar.config(command=self.mainPanel.xview)
        hbar.grid(column=0, row=8, columnspan=6, sticky='WE')
        vbar = Scrollbar(self.frame, orient=VERTICAL)
        vbar.config(command=self.mainPanel.yview)
        vbar.grid(column=5, row=0, rowspan= 6,sticky='NS')
        self.mainPanel.config(width=300, height=300)
        self.mainPanel.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Button-3>", self.cancelBBox)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.parent.bind("s", self.cancelBBox)
        self.parent.bind("a", self.prevImage) # press 'a' to go backforward
        self.parent.bind("d", self.nextImage) # press 'd' to go forward
        self.parent.bind("r", self.removeLastBox) 
        self.parent.bind("1", self.setClass1) 
        self.parent.bind("2", self.setClass2) 
        self.parent.bind("3", self.setClass3) 
        self.parent.bind("4", self.setClass4)
        self.mainPanel.grid(row = 1, column = 1, rowspan = 4, sticky = W+N)

        # choose class
        self.classname = StringVar()
        self.classcandidate = ttk.Combobox(self.frame,state='readonly',textvariable=self.classname)
        self.classcandidate.grid(row=1,column=2)
        if os.path.exists(self.classcandidate_filename):
        	with open(self.classcandidate_filename) as cf:
        		for line in cf.readlines():
        			# print line
        			self.cla_can_temp.append(line.strip('\n'))
        #print self.cla_can_temp
        self.classcandidate['values'] = self.cla_can_temp
        self.classcandidate.current(0)
        self.currentLabelclass = self.classcandidate.get() #init
        self.btnclass = Button(self.frame, text = 'ComfirmClass', command = self.setClass)
        self.btnclass.grid(row=2,column=2,sticky = W+E)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 3, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 50, height = 12)
        self.listbox.grid(row = 4, column = 2, sticky = N+S)
        self.btnDel = Button(self.frame, text = 'Delete', command = self.delBBox)
        self.btnDel.grid(row = 5, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command = self.clearBBox)
        self.btnClear.grid(row = 6, column = 2, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 7, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.tmpLabel = Label(self.ctrPanel, text = "Go to Image No.")
        self.tmpLabel.pack(side = LEFT, padx = 5)
        self.idxEntry = Entry(self.ctrPanel, width = 5)
        self.idxEntry.pack(side = LEFT)
        self.goBtn = Button(self.ctrPanel, text = 'Go', command = self.gotoImage)
        self.goBtn.pack(side = LEFT)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        # for debugging
##        self.setImage()
##        self.loadDir()

    def loadDir(self, dbg = False):
        if not dbg:
            s = self.entry.get()
            self.parent.focus()
            self.category = int(s)
        else:
            s = r'D:\workspace\python\labelGUI'
##        if not os.path.isdir(s):
##            tkMessageBox.showerror("Error!", message = "The specified dir doesn't exist!")
##            return
        # get image list
        self.imageDir = os.path.join(r'./Images', '%03d' %(self.category))
        #print self.imageDir 
        #print self.category
        self.imageList = glob.glob(os.path.join(self.imageDir, '*.JPG'))
        #print self.imageList
        if len(self.imageList) == 0:
            print('No .JPG images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

         # set up output dir
        self.outDir = os.path.join(r'./Labels', '%03d' %(self.category))
        if not os.path.exists(self.outDir):
            os.mkdir(self.outDir)

        self.loadImage()
        print('%d images loaded from %s' %(self.total, s))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        self.img = Image.open(imagepath)
        self.tkimg = ImageTk.PhotoImage(self.img)
        self.mainPanel.config(width = max(self.tkimg.width(), 400), height = max(self.tkimg.height(), 400))
        self.image_width  = self.tkimg.width() 
        self.image_height = self.tkimg.height()
        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)
        self.progLabel.config(text = "%04d/%04d" %(self.cur, self.total))

        # load labels
        self.clearBBox()
        self.imagename = os.path.split(imagepath)[-1].split('.')[0]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.outDir, labelname)
        bbox_cnt = 0
        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for (i, line) in enumerate(f):
                    if i == 0:
                        bbox_cnt = int(line.strip())
                        continue
                    # tmp = [int(t.strip()) for t in line.split()]
                    tmp = line.split()
                    #print tmp
                    self.bboxList.append(tuple(tmp))
                    color_ix = get_color_ix(tmp[4])
                    tmpId = self.mainPanel.create_rectangle(int(tmp[0]), int(tmp[1]), \
                                                        int(tmp[2]), int(tmp[3]), \
                                                        width = 2, \
                                                        outline = COLORS[color_ix])
                    # print tmpId
                    self.bboxIdList.append(tmpId)
                    # For backwards compatibility with old label
                    if len(tmp) > 5:
                      self.listbox.insert(END, '%s: d_width %.4fm d_height %.4fm' %(tmp[4], float(tmp[5]), float(tmp[6])))
                    else:
                      self.listbox.insert(END, '%s : (%d, %d) -> (%d, %d)' %(tmp[4],int(tmp[0]), int(tmp[1]), \
                                                                  int(tmp[2]), int(tmp[3])))
                    # self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
                    self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[3])

    def saveImage(self):
        with open(self.labelfilename, 'w') as f:
            f.write('%d\n' %len(self.bboxList))
            for bbox in self.bboxList:
                f.write(' '.join(map(str, bbox)) + '\n')
        print('Image No. %d saved' %(self.cur))


    def mouseClick(self, event):
        abs_x, abs_y = self.mainPanel.canvasx(event.x), self.mainPanel.canvasy(event.y)
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = abs_x, abs_y
        else:
            x1, x2 = min(self.STATE['x'], abs_x), max(self.STATE['x'], abs_x)
            y1, y2 = min(self.STATE['y'], abs_y), max(self.STATE['y'], abs_y)
            # Abort bounding box if object too small
            if abs(y1 - y2) < HEIGHT_THRESHOLD:
                self.cancelBBox(None)
                return
            width_distance  = self.calcWidthDistanceFromBBox(x1, x2, y1, y2, self.currentLabelclass)
            height_distance = self.calcHeightDistanceFromBBox(x1, x2, y1, y2, self.currentLabelclass)
            self.bboxList.append((x1, y1, x2, y2, self.currentLabelclass, width_distance, height_distance))
            self.bboxIdList.append(self.bboxId)
            self.bboxId = None
            color_ix = get_color_ix(self.currentLabelclass)
            self.listbox.insert(END, '%s: d_width %.4fm d_height %.4fm' %(self.currentLabelclass, width_distance, height_distance))
	    #self.listbox.insert(END, 'distance: %d' %(distance))
            self.listbox.itemconfig(len(self.bboxIdList) - 1, fg = COLORS[3])
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        abs_x, abs_y = self.mainPanel.canvasx(event.x), self.mainPanel.canvasy(event.y)
        self.disp.config(text='x: %d, y: %d' % (abs_x, abs_y))

        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, abs_y, self.tkimg.width(), abs_y, width = 1)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(abs_x, 0, abs_x, self.tkimg.height(), width = 1)
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
            color_ix = get_color_ix(self.currentLabelclass)
            self.bboxId = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                            abs_x, abs_y, \
                                                            width = 1, \
                                                            outline = COLORS[color_ix])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId:
                self.mainPanel.delete(self.bboxId)
                self.bboxId = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1 :
            return
        idx = int(sel[0])
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def removeLastBox(self, event=None):
        idx = self.listbox.size() - 1
        if idx < 0:
            return
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.bboxList.pop(idx)
        self.listbox.delete(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
        self.listbox.delete(0, len(self.bboxList))
        self.bboxIdList = []
        self.bboxList = []

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def gotoImage(self):
        idx = int(self.idxEntry.get())
        if 1 <= idx <= self.total:
            self.saveImage()
            self.cur = idx
            self.loadImage()

    def setClass(self):
    	self.currentLabelclass = self.classcandidate.get()
    	print('set label class to :',self.currentLabelclass)

    def setClass1(self, event=None):
        self.classcandidate.current(0)
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to #01:',self.currentLabelclass)

    def setClass2(self, event=None):
        self.classcandidate.current(1)
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to #02:',self.currentLabelclass)

    def setClass3(self, event=None):
        self.classcandidate.current(2)
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to #03:',self.currentLabelclass)
    
    def setClass4(self, event=None):
        self.classcandidate.current(3)
        self.currentLabelclass = self.classcandidate.get()
        print('set label class to #04:',self.currentLabelclass)

    def calcHeightDistanceFromBBox(self, x1, x2, y1, y2, cone_class):

      cone_prefix = cone_class.split('-')[0]

      height_on_sensor = ((float(y2) - float(y1)) / float(self.image_height)) * sensor_height
      angle = ((float(x2) - float(x1)) / float(self.image_width)) * (- h_AOV) + (h_AOV/2.0)
      perpendicular_distance = 0.0

      if( cone_prefix == 'big' ):
          perpendicular_distance = ((large_cone_height * focal_length) / height_on_sensor) / 1000000.0
      else:
          perpendicular_distance = ((small_cone_height * focal_length) / height_on_sensor) / 1000000.0
      straight_distance = perpendicular_distance / math.cos(angle)

      return straight_distance

    def calcWidthDistanceFromBBox(self, x1, x2, y1, y2, cone_class):

      cone_prefix = cone_class.split('-')[0]

      width_on_sensor = ((float(x2) - float(x1)) / float(self.image_width)) * sensor_width
      angle = ((float(x2) - float(x1)) / float(self.image_width)) * (- h_AOV) + (h_AOV/2.0)
      perpendicular_distance = 0.0

      if( cone_prefix == 'big' ):
          perpendicular_distance = ((large_cone_width * focal_length) / width_on_sensor) / 1000000.0
      else:
          perpendicular_distance = ((small_cone_width * focal_length) / width_on_sensor) / 1000000.0
      straight_distance = perpendicular_distance / math.cos(angle)

      return straight_distance



##    def setImage(self, imagepath = r'test2.png'):
##        self.img = Image.open(imagepath)
##        self.tkimg = ImageTk.PhotoImage(self.img)
##        self.mainPanel.config(width = self.tkimg.width())
##        self.mainPanel.config(height = self.tkimg.height())
##        self.mainPanel.create_image(0, 0, image = self.tkimg, anchor=NW)

if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root)
    root.resizable(width =  True, height = True)
    root.mainloop()
