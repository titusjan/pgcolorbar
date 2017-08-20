"""

"""

import logging
import sys
import numpy as np
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from pghistlutitem import HistogramLUTItem
from colorlegend import ColorLegendItem

import pyqtgraph as pg

LOG_FMT = '%(asctime)s %(filename)25s:%(lineno)-4d : %(levelname)-7s: pid=%(process)d: %(message)s'

logger = logging.getLogger(__name__)


class MyWindow(QtWidgets.QWidget):

    def __init__(self, img, lut, parent=None):
        super().__init__(parent=parent)

        self.mainLayout = QtWidgets.QVBoxLayout()
        self.setLayout(self.mainLayout)

        self.plotItem = pg.PlotItem()

        viewBox = self.plotItem.getViewBox()
        viewBox.disableAutoRange(pg.ViewBox.XYAxes)

        imageItem = pg.ImageItem()
        self.plotItem.addItem(imageItem)

        nRows, nCols = img.shape
        imageItem.setImage(img)
        imageItem.setLookupTable(lut)

        self.plotItem.setRange(xRange=[0, nCols], yRange=[0, nRows])

        self.colorLegendItem = ColorLegendItem(lut=lut, imageItem=imageItem)
        self.colorLegendItem.setMinimumHeight(60)

        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.graphicsLayoutWidget.addItem(self.colorLegendItem, 0, 0)
        self.graphicsLayoutWidget.addItem(self.plotItem, 0, 1)

        self.mainLayout.addWidget(self.graphicsLayoutWidget)


def main():

    app = QtWidgets.QApplication([])


    ## Create random 3D data set with noisy signals
    #img = pg.gaussianFilter(np.random.normal(size=(300, 200)), (5, 5)) * 20
    #img = np.random.normal(size=(300, 200)) * 100
    img = np.random.uniform(0.0, 1.0, size=(300, 200))

    #cmap = pg.ColorMap([0, 0.25, 0.75, 1], [[0, 0, 0, 255], [255, 0, 0, 255], [255, 255, 0, 255], [255, 255, 255, 255]])
    #lut0 = cmap.getLookupTable()
    lut1 = np.array([(237,248,251), (178,226,226), (102,194,164), (35,139,69)])
    lut2 = np.array([(237,248,251), (204,236,230), (153,216,201), (102,194,164),
                     (65,174,118), (35,139,69), (0,88,36)])



    ## Create window with ImageView widget
    win = MyWindow(img=img, lut=lut1)

    win.resize(800,800)
    win.setWindowTitle('pyqtgraph example: ImageView')
    win.show()


    QtWidgets.QApplication.instance().exec_()


if __name__ == '__main__':
    logging.basicConfig(level='DEBUG', format=LOG_FMT)

    # Interpret image data as row-major instead of col-major
    pg.setConfigOptions(imageAxisOrder='row-major')

    main()
