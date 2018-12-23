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



def assertIsLut(lut):
    """ Checks that lut is Nx3 array
    """
    check_is_an_array(lut)
    assert lut.ndim == 2, "Expected 2 dimensional LUT. Got {}D".format(lut.ndim)
    assert lut.shape[1] == 3, \
        "Second dimension of LUT should be length 3. Got: {}".format(lut.shape[1])


def extentLut(lut):
    """ Duplicates the last item of the Lookup Table

        This is necessary because the pyqtgraph.makeARGB function has a wrong default scale. It
        should be equal to the length of the LUT, but it's set to len(lut)-1. We therefore add a
        fake LUT entry. See issue 792 of PyQtGraph.
    """
    assertIsLut(lut)
    extendedLut = np.append(lut, [lut[-1, :]], axis=0)
    return extendedLut


def isExtended(lut):
    """ Returns True if the lookup table has been extended with isExtended.
        I.e. returns True if the last and second to last LUT entries are the same
    """
    assertIsLut(lut)
    return np.array_equal(lut[-1, :], lut[-2, :])



class ColorLegendItem(pg.GraphicsWidget):
    """ Color legend for an image plot.

        Draws a color legend. It consists of a color bar and axis that show the range of the colors.
        The color legend visualizes a lookup table (LUT) that maps a floating point value to an
        RBG color value. With the lookup table colors can be assigned to an image.

        By default a (rotated) histogram is drawn that shows the distribution of the values of all
        pixels in the array.

        The histogram is linked to a PyQtGraph ImageItem. An ImageItem has a LUT member.
        Unfortunately there is a bug in PyQtGraph when colorizing an image (issue 792). As a
        work-around we extent this LUT by duplicating the last item. You must therefore set the
        lut with ColorLegendItem.setLut, which adds this duplicate item (if not yet done). This
        class therefore has a side effect.
    """
    sigLevelsChanged = QtCore.pyqtSignal(tuple) # TODO: use this

    def __init__(self, imageItem=None, lut=None):
        """ Constructor.

        """
        pg.GraphicsWidget.__init__(self)

        check_class(imageItem, pg.ImageItem, allowNone=False)  # None has not yet been tested

        self._imageItem = None

        # Histogram
        self.histViewBox = pg.ViewBox(enableMenu=False)
        self.histViewBox.setMouseEnabled(x=False, y=True)
        self.histViewBox.setFixedWidth(50)
        self.histPlotDataItem = pg.PlotDataItem()
        self.histPlotDataItem.rotate(90)

        self.histViewBox.addItem(self.histPlotDataItem)
        self.fillHistogram()

        # Color scale
        self.axisItem = pg.AxisItem(
            'right', linkView=self.histViewBox, maxTickLength=-10, parent=self)

        self.colorScaleViewBox = pg.ViewBox(
            enableMenu=True, border=pg.mkPen(pg.getConfigOption('foreground'), width=1.5))

        self.colorScaleViewBox.disableAutoRange(pg.ViewBox.XYAxes)
        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)
        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleImageItem = pg.ImageItem() # image data will be set in setLut
        self.colorScaleViewBox.addItem(self.colorScaleImageItem)

        # Overall layout
        self.mainLayout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(1, 1, 1, 1)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addItem(self.histViewBox, 0, 0)
        self.mainLayout.addItem(self.colorScaleViewBox, 0, 1)
        self.mainLayout.addItem(self.axisItem, 0, 2)

        # It might also trigger an update when the axis is resized (but can't reproduce it
        # anymore). If needed we could test if the range has changed substantially before updating
        # image levels.
        self.histViewBox.sigYRangeChanged.connect(self._updateImageLevels)


        self.setImageItem(imageItem)
        #self.setLut(lut)
        #self._updateImageLevels() # TODO: make setImageItem x



    def getImageItem(self):
        """ Returns the PyQtGraph ImageItem that this legend is linked to.
        """
        return self._imageItem


    def setImageItem(self, imageItem):
        """ Links the legend to an image item.
        """
        logger.debug("setImageItem")
        check_class(imageItem, ImageItem, allowNone=True)

        # Remove old imageItem
        if self._imageItem:
            self._imageItem.sigImageChanged.disconnect(self._onImageChanged)

        self._imageItem = imageItem
        self._imageItem.sigImageChanged.connect(self._onImageChanged)

        if self._imageItem.lut is not None:
            self.setLut(self._imageItem.lut) # extents lut if necessary
        self._onImageChanged()


    def _onImageChanged(self):
        """ Called when new image data has been set in the linked ImageItem

            Updates the histogram and colorize the image (_updateImageLevels)
        """
        logger.debug("ColorLegendItem._onImageChanged", stack_info=False)

        img = self._imageItem.image
        if img is None:
            histRange = None
            return
        else:
            histRange = (np.nanmin(img), np.nanmax(img))

        #logger.debug("histRange: {}".format(histRange))

        # histogram = self._imageItem.getHistogram(range=histRange)
        # if histogram[0] is None:
        #     logger.warning("Histogram empty in imageChanged()") # when does this happen?
        #     return
        # else:
        #     self.histPlotDataItem.setData(*histogram)

        self._updateImageLevels()


    @QtCore.pyqtSlot()
    def _updateImageLevels(self):
        """ Updates the image levels from the color levels of the
        """
        levels = self.getLevels()
        logger.debug("updateImageToNewLevels: {}".format(levels), stack_info=False)
        if self._imageItem is not None:
            self._imageItem.setLevels(levels)


    def getLevels(self):
        """ Gets the value range of the legend
        """
        levels = self.axisItem.range # which equals self.histViewBox.state['viewRange'][Y_AXIS]
        assert self.axisItem.range == self.histViewBox.state['viewRange'][Y_AXIS], \
            "Mismatch {} != {}".format(self.axisItem.range, self.histViewBox.state['viewRange'][Y_AXIS])
        return levels


    def setLevels(self, levels, padding=0.0):
        """ Sets the value range of the legend.

            :param int padding: percentage that will be added to the color range.
                Use None for PyQtGraph's padding algorithm. Use 0 for no padding.
        """
        logger.debug("ColorLegendItem.setLevels: {}".format(levels), stack_info=False)
        lvlMin, lvlMax = levels
        self.histViewBox.setYRange(lvlMin, lvlMax, padding=padding)




    def getLut(self):
        """ Returns the Lookup table of the image item.
        """
        return self._imageItem.lut


    def setLut(self, lut):
        """ Sets the lookup table to the image item.

            :param ndarray Array: an N x 3 array.
        """
        logger.debug("------ setLut called")
        check_is_an_array(lut)
        assert lut.ndim == 2, "Expected 2 dimensional LUT. Got {}D".format(lut.ndim)
        assert lut.shape[1] == 3, \
            "Second dimension of LUT should be length 3. Got: {}".format(lut.shape[1])

        if not isExtended(lut):
            # The lookup table in the imageItem must be extended. See extentLut doc string
            logger.debug("Side effect: duplicating last item of LUT in image item.")
            extendedLut = extentLut(lut)
        else:
            # The lookup table in the imageItem already is extended. Draw the original
            extendedLut = lut
            lut = np.copy(lut[0:-1, :])

        assert len(lut) == len(extendedLut) - 1, "Sanity check"

        if self._imageItem:
            logger.debug("Setting image item to extended lut")
            self._imageItem.setLookupTable(extendedLut)

        # Draw a color scale that shows the LUT.
        barWidth = 1
        imgAxOrder = pg.getConfigOption('imageAxisOrder')
        if imgAxOrder == 'col-major':
            lutImg = np.ones(shape=(barWidth, len(lut), 3), dtype=lut.dtype)
            lutImg[...] = lut[np.newaxis, :, :]
        elif imgAxOrder == 'row-major':
            lutImg = np.ones(shape=(len(lut), barWidth, 3), dtype=lut.dtype)
            lutImg[...] = lut[:, np.newaxis, :]
        else:
            raise AssertionError("Unexpected imageAxisOrder config value: {}".format(imgAxOrder))

        logger.debug("lutImg.shape: {}".format(lutImg.shape))
        self.colorScaleImageItem.setImage(lutImg)

        yRange = [0, len(lut)]
        logger.debug("Setting colorScaleViewBox yrange to: {}".format(yRange))

        # Do not set disableAutoRange to True in setRange; it triggers 'one last' auto range.
        # This is why the viewBox' autorange must be False at construction.
        self.colorScaleViewBox.setRange(
            xRange=[0, barWidth], yRange=yRange, padding=0.0,
            update=False, disableAutoRange=False)



    def fillHistogram(self, fill=True, level=0.0, color=(100, 100, 200)):
        """ Fills the histogram
        """
        if fill:
            self.histPlotDataItem.setFillLevel(level)
            self.histPlotDataItem.setFillBrush(color)
        else:
            self.histPlotDataItem.setFillLevel(None)
