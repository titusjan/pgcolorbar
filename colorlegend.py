""" Reimplementation of the PyQtGraph HistogramLUTItem.

    Currently only a histogram range in the imageChanged method is added. This prevents errors when
    the image contains NaNs. Later the mouse and scrolling behaviour may be altered.
"""
import logging
import numpy as np
import pyqtgraph as pg

from pyqtgraph.Qt import QtWidgets, QtCore

logger = logging.getLogger(__name__)

X_AXIS = pg.ViewBox.XAxis
Y_AXIS = pg.ViewBox.YAxis
BOTH_AXES = pg.ViewBox.XYAxes

class ColorLegendItem(pg.GraphicsWidget):
    """ Color legend for an image plot.
    """
    def __init__(self, lut, imageItem=None, barWidth=10):
        """ Constructor.
        """
        pg.GraphicsWidget.__init__(self)

        self.lut = lut
        self._imageItem = imageItem
        self.barWidth = barWidth
        self.histogramFilled = True

        # Histogram
        self.histViewBox = pg.ViewBox(enableMenu=False)
        self.histViewBox.setMouseEnabled(x=False, y=True)
        #self.histViewBox.setFixedWidth(300)
        self.histPlotDataItem = pg.PlotDataItem()
        self.histPlotDataItem.rotate(90)

        self.histViewBox.addItem(self.histPlotDataItem)
        self.fillHistogram(self.histogramFilled)


        # Axis
        self.layout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        self.axisItem = pg.AxisItem('right', linkView=self.histViewBox,
                                    maxTickLength=-10, parent=self)

        # Image
        lutImg = np.ones(shape=(len(lut), self.barWidth, 3), dtype=lut.dtype)
        lutImg[...] = lut[:, np.newaxis, :]

        colorScaleImageItem = pg.ImageItem()
        colorScaleImageItem.setImage(lutImg)
        self.colorScaleViewBox = pg.ViewBox(enableMenu=False,
                                            border=pg.getConfigOption('foreground'))
        self.colorScaleViewBox.addItem(colorScaleImageItem)
        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)
        self.colorScaleViewBox.setRange(xRange=[0, self.barWidth],
                                        yRange=[0, len(lut)],
                                        padding=0.0)

        self.layout.addItem(self.histViewBox, 0, 0)
        self.layout.addItem(self.colorScaleViewBox, 0, 1)
        self.layout.addItem(self.axisItem, 0, 2)

        # TODO: this will also trigger an update when the axis is resized.
        # Perhaps we should test if the range has changed substantially before updating image levels.
        self.histViewBox.sigYRangeChanged.connect(
            lambda _viewBox, range: self._updateImageLevels())

        # # Testing
        # self.histViewBox.sigRangeChangedManually.connect(self._updateImageLevels)

        self.imageChanged(autoLevel=True)


    @property
    def imageItem(self):
        """ Returns the ImageItem that this legend is linked to.
        """
        return self._imageItem


    def setLevels(self, levels):
        """ Sets the value range of the legend
        """
        logger.debug("ColorLegendItem.setLevels: {}".format(levels), stack_info=False)
        lvlMin, lvlMax = levels
        self.histViewBox.setYRange(lvlMin, lvlMax, padding=0)


    @QtCore.pyqtSlot()
    def _updateImageLevels(self):
        """ Updates the image levels from the axis item levels
        """
        levels = self.axisItem.range # == self.histViewBox.state['viewRange'][Y_AXIS]
        logger.debug("updateImageToNewLevels: {}".format(levels))
        if self.imageItem is not None:
            self.imageItem.setLevels(levels)



    def fillHistogram(self, fill=True, level=0.0, color=(100, 100, 200)):
        """ Fills the histogram
        """
        if fill:
            self.histPlotDataItem.setFillLevel(level)
            self.histPlotDataItem.setFillBrush(color)
        else:
            self.histPlotDataItem.setFillLevel(None)


    def imageChanged(self, autoLevel=False):
        """" Called when a new image has been set.

            Updates the histogram
        """
        logger.debug("ColorLegenItem.imageChanged(autoLevel={}) called".format(autoLevel))

        img = self.imageItem.image
        if img is None:
            histRange = None
        else:
            histRange = (np.nanmin(img), np.nanmax(img))

        logger.debug("histRange: {}".format(histRange))

        histogram = self.imageItem.getHistogram(range=histRange)
        if histogram[0] is None:
            logger.warning("Hisogram empty in imageChagned()") # when does this happen?
            return
        else:
            self.histPlotDataItem.setData(*histogram)

        # if autoLevel:
        #     mn = h[0][0]
        #     mx = h[0][-1]
        #     self.region.setRegion([mn, mx])
