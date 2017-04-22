"""

"""
import sys
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui

import pyqtgraph as pg

def main():

    app = QtGui.QApplication([])

    ## Create window with ImageView widget
    win = QtGui.QMainWindow()
    win.resize(800,800)


    imagePlotItem = pg.PlotItem()

    viewBox = imagePlotItem.getViewBox()
    viewBox.disableAutoRange(pg.ViewBox.XYAxes)

    imageItem = pg.ImageItem()
    imagePlotItem.addItem(imageItem)    

    ## Create random 3D data set with noisy signals
    img = pg.gaussianFilter(np.random.normal(size=(300, 200)), (5, 5)) * 20 + 100
    nRows, nCols = img.shape
    imageItem.setImage(img)
    imagePlotItem.setRange(xRange=[0, nCols], yRange=[0, nRows])
    
    
    histLutItem = pg.HistogramLUTItem() # what about GradientLegend?
    histLutItem.setImageItem(imageItem)
    histLutItem.vb.setMenuEnabled(False)
    histLutItem.setHistogramRange(90, 110) # Disables autoscaling

    graphicsLayoutWidget = pg.GraphicsLayoutWidget()

    graphicsLayoutWidget.addItem(imagePlotItem, 0, 0)
    graphicsLayoutWidget.addItem(histLutItem, 0, 1)


    # imv = pg.ImageView()
    win.setCentralWidget(graphicsLayoutWidget)
    win.show()
    win.setWindowTitle('pyqtgraph example: ImageView')


    QtGui.QApplication.instance().exec_()


if __name__ == '__main__':


    # Interpret image data as row-major instead of col-major
    pg.setConfigOptions(imageAxisOrder='row-major')

    main()
