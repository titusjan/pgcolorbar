"""

"""
import sys
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui

from pghistlutitem import HistogramLUTItem
from colorlegend import ColorLegendItem

import pyqtgraph as pg

def main():

    app = QtGui.QApplication([])

    ## Create window with ImageView widget
    win = QtGui.QMainWindow()
    win.resize(800,800)


    plotItem = pg.PlotItem()

    viewBox = plotItem.getViewBox()
    viewBox.disableAutoRange(pg.ViewBox.XYAxes)

    imageItem = pg.ImageItem()
    plotItem.addItem(imageItem)

    ## Create random 3D data set with noisy signals
    img = pg.gaussianFilter(np.random.normal(size=(300, 200)), (5, 5)) * 20 + 100
    nRows, nCols = img.shape
    imageItem.setImage(img)
    plotItem.setRange(xRange=[0, nCols], yRange=[0, nRows])

    cmap = pg.ColorMap([0, 0.25, 0.75, 1], [[0, 0, 0, 255], [255, 0, 0, 255], [255, 255, 0, 255], [255, 255, 255, 255]])
    lut0 = cmap.getLookupTable()
    lut1 = np.array([(237,248,251), (178,226,226), (102,194,164), (35,139,69)])
    lut2 = np.array([(237,248,251), (204,236,230), (153,216,201), (102,194,164), (65,174,118), (35,139,69), (0,88,36)])


    # histLutItem = HistogramLUTItem() # what about GradientLegend?
    # histLutItem.setImageItem(imageItem)
    # histLutItem.vb.setMenuEnabled(False)
    # histLutItem.setHistogramRange(90, 110) # Disables autoscaling
    # #histLutItem.gradient.setLookupTable(lut) # doesn't work

    imageItem.setLookupTable(lut1)

    graphicsLayoutWidget = pg.GraphicsLayoutWidget()

    colorLegendItem = ColorLegendItem()

    graphicsLayoutWidget.addItem(colorLegendItem, 0, 0)
    graphicsLayoutWidget.addItem(plotItem, 0, 1)
    #graphicsLayoutWidget.addItem(histLutItem, 0, 2)

    colorLegendItem.setMinimumHeight(60)

    # imv = pg.ImageView()
    win.setCentralWidget(graphicsLayoutWidget)
    win.show()
    win.setWindowTitle('pyqtgraph example: ImageView')


    QtGui.QApplication.instance().exec_()


if __name__ == '__main__':


    # Interpret image data as row-major instead of col-major
    pg.setConfigOptions(imageAxisOrder='row-major')

    main()
