MM-label-tool
===============

A simple tool for labeling object bounding boxes in images, implemented with Python Tkinter.
Small adaptations for ease of use and additional functionality on top of original repo: 
https://github.com/puzzledqs/BBox-Label-Tool

Data Organization
-----------------
LabelTool  
|  
|--main.py   *# source code for the tool*  
|  
|--Images/   *# directory containing the images to be labeled*  
|  
|--Labels/   *# directory for the labeling results*  

Environment
----------
- python 2.7
- python PIL (Pillow)

Run
-------
$ conda create -n label-tool python=2.7
$ mkdir Images Labels Images/001 ...
$ cat requirements.txt | xargs -i pip install {}
Move images to be labeled to respective folders
$ python main.py

Usage
-----
0. The current tool requires that **the images to be labeled reside in /Images/001, /Images/002, etc. You will need to modify the code if you want to label images elsewhere**.
1. Input a folder number (e.g, 1, 2, 5...), and click `Load`. The images in the folder, along with a few example results will be loaded.
2. To create a new bounding box, left-click to select the first vertex. Moving the mouse to draw a rectangle, and left-click again to select the second vertex.
  - To switch between the classes, use numbers 1-4. To change the class names or amount of classes, you have to change the code.
  - To cancel the bounding box while drawing, just press `<Esc>` or right-click.
  - To delete a existing bounding box, select it from the listbox, and click `Delete`.
  - To delete all existing bounding boxes in the image, simply click `ClearAll`.
3. After finishing one image, click `Next` to advance. Likewise, click `Prev` to reverse. Or, input an image id and click `Go` to navigate to the speficied image.
  - Be sure to click `Next` after finishing a image, or the result won't be saved. 
 
 Distance Estimation
 -----
 After adjusting the intrinsic parameters in `main.py` for the camera you used to take the pictures you are about to label, the label tool will show you the estimated distance using the width and height of the region of interest. Furthermore, the distance values will also be saved to the labels, making it possible to assess the best case scenario accuracy.

