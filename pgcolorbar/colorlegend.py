""" Color legend.

    Consists of a vertical color bar with a draggable axis that displays the values of the colors.
    Optionally a histogram may be displayed.
"""
import logging
import numpy as np
import pyqtgraph as pg

from pyqtgraph.Qt import QtWidgets, QtCore
from pyqtgraph import ImageItem


from .misc import check_is_an_array, check_class

logger = logging.getLogger(__name__)

X_AXIS = pg.ViewBox.XAxis
Y_AXIS = pg.ViewBox.YAxis
BOTH_AXES = pg.ViewBox.XYAxes

class ColorLegendItem(pg.GraphicsWidget):
    """ Color legend for an image plot.

        Draws a color legend. It consists of a color bar and axis that show the range of the colors.
        The color legend visualizes a lookup table (LUT) that maps a floating point value to an
        RBG color value. With the lookup table colors can be assigned to an image.

        By default a (rotated) histogram is drawn that shows the distribution of the values of all
        pixels in the array.
    """
    sigLevelsChanged = QtCore.pyqtSignal(tuple) # TODO: use this

    def __init__(self, imageItem=None, lut=None, barWidth=4):
        """ Constructor.

        """
        pg.GraphicsWidget.__init__(self)

        self._barWidth = barWidth
        self._imageItem = None
        self._lut = None

        self.setImageItem(imageItem)
        self.setLut(lut)
        
        # Histogram
        self.histViewBox = pg.ViewBox(enableMenu=False)
        self.histViewBox.setMouseEnabled(x=False, y=True)
        self.histViewBox.setFixedWidth(50)
        self.histPlotDataItem = pg.PlotDataItem()
        self.histPlotDataItem.rotate(90)

        self.histViewBox.addItem(self.histPlotDataItem)
        self.fillHistogram()

        # Axis
        self.layout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        self.axisItem = pg.AxisItem('right', linkView=self.histViewBox,
                                    maxTickLength=-10, parent=self)

        # Image of the color scale.
        imgAxOrder = pg.getConfigOption('imageAxisOrder')
        if imgAxOrder == 'col-major':
            lutImg = np.ones(shape=(self._barWidth, len(lut), 3), dtype=lut.dtype)
            lutImg[...] = lut[np.newaxis, :, :]
        elif imgAxOrder == 'row-major':
            lutImg = np.ones(shape=(len(lut), self._barWidth, 3), dtype=lut.dtype)
            lutImg[...] = lut[:, np.newaxis, :]
        else:
            raise AssertionError("Unexpected imageAxisOrder config value: {}".format(imgAxOrder))

        logger.debug("lutImg.shape: {}".format(lutImg.shape))
        #logger.debug("lutImg: {}".format(lutImg))

        self.colorScaleImageItem = pg.ImageItem()
        self.colorScaleImageItem.setImage(lutImg)
        self.colorScaleViewBox = pg.ViewBox(enableMenu=True,
                                            border=pg.mkPen(pg.getConfigOption('foreground'),
                                                            width=1.5)) 
        self.colorScaleViewBox.addItem(self.colorScaleImageItem)

        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)
        self.colorScaleViewBox.setRange(xRange=[0, self._barWidth],
                                        yRange=[0, len(lut)],
                                        padding=0.0)

        self.layout.addItem(self.histViewBox, 0, 0)
        self.layout.addItem(self.colorScaleViewBox, 0, 1)
        self.layout.addItem(self.axisItem, 0, 2)

        # TODO: this will also trigger an update when the axis is resized. (Or does it?)
        # Perhaps we should test if the range has changed substantially before updating image
        # levels.
        self.histViewBox.sigYRangeChanged.connect(self._updateImageLevels)

        # self.histViewBox.sigYRangeChanged.connect(
        #     lambda _viewBox, range: self._updateImageLevels())

        # # Testing
        # self.histViewBox.sigRangeChangedManually.connect(self._updateImageLevels)

        self.imageChanged(autoLevel=True)

        self._updateImageLevels() # TODO: make setImageItem x


    def getImageItem(self):
        """ Returns the PyQtGraph ImageItem that this legend is linked to.
        """
        return self._imageItem


    def setImageItem(self, imageItem):
        """ Links the legend to an image item.
        """
        check_class(imageItem, ImageItem)
        self._imageItem = imageItem


    def getLut(self):
        """ Returns the Lookup table of the image item.
        """
        return self._lut


    def setLut(self, lut):
        """ Sets the lookup table to the image item.

            :param ndarray Array: an N x 3 array.
        """
        check_is_an_array(lut)
        assert lut.ndim == 2, "Expected 2 dimensional LUT. Got {}D".format(lut.ndim)
        assert lut.shape[1] == 3, \
            "Second dimension of LUT should be length 3. Got: {}".format(lut.shape[1])

        self._lut = lut


    def getLevels(self):
        """ Gets the value range of the legend
        """
        return self.histViewBox.state['viewRange'][Y_AXIS]


    def setLevels(self, levels, padding=0):
        """ Sets the value range of the legend.

            :param int padding: percentage that will be added to the color range.
                Use None for PyQtGraph's padding algorithm. Use 0 for no padding.
        """
        logger.debug("ColorLegendItem.setLevels: {}".format(levels), stack_info=False)
        lvlMin, lvlMax = levels
        self.histViewBox.setYRange(lvlMin, lvlMax, padding=padding)


    @QtCore.pyqtSlot()
    def _updateImageLevels(self):
        """ Updates the image levels from the color levels of the
        """
        levels = self.axisItem.range # == self.histViewBox.state['viewRange'][Y_AXIS]
        logger.debug("updateImageToNewLevels: {}".format(levels))
        if self._imageItem is not None:
            self._imageItem.setLevels(levels)


    def fillHistogram(self, fill=True, level=0.0, color=(100, 100, 200)):
        """ Fills the histogram
        """
        if fill:
            self.histPlotDataItem.setFillLevel(level)
            self.histPlotDataItem.setFillBrush(color)
        else:
            self.histPlotDataItem.setFillLevel(None)


    def imageChanged(self, autoLevel=False):
        """ Called when a new image has been set.

            Updates the histogram
        """
        logger.debug("ColorLegenItem.imageChanged(autoLevel={}) called".format(autoLevel))

        img = self._imageItem.image
        if img is None:
            histRange = None
        else:
            histRange = (np.nanmin(img), np.nanmax(img))

        logger.debug("histRange: {}".format(histRange))

        histogram = self._imageItem.getHistogram(range=histRange)
        if histogram[0] is None:
            logger.warning("Histogram empty in imageChanged()") # when does this happen?
            return
        else:
            self.histPlotDataItem.setData(*histogram)

        # if autoLevel:
        #     mn = h[0][0]
        #     mx = h[0][-1]
        #     self.region.setRegion([mn, mx])

