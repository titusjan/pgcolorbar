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

    def __init__(self,
                 imageItem=None,
                 showHistogram=True,
                 subSampleStep='auto',
                 maxTickLength=10):
        """ Constructor.

            :param imageItem pg.ImageItem: PyQtGraph ImageItem to which this legen will be linked
            :param bool showHistogram: if True (the default), a histogram of image values is drawn
            :param subSampleStep:The step size that is used to subsample the array when calculating
                the histogram. Can be a scalar, a tuple with two elements, or 'auto'.
            :param int maxTickLength: Maximum tick length of the color axis. Default = 10
        """
        pg.GraphicsWidget.__init__(self)

        check_class(imageItem, pg.ImageItem, allowNone=True)

        self._histogramIsVisible = showHistogram
        self.histogramWidth = 50
        self._imageItem = None

        # List of mouse buttons that reset the color range when clicked.
        # You can safely modify this list.
        self.resetRangeMouseButtons = [QtCore.Qt.MiddleButton]

        self._subsampleStep = subSampleStep

        # Histogram
        self.histViewBox = pg.ViewBox(enableMenu=False)
        self.histViewBox.disableAutoRange(pg.ViewBox.YAxis)
        self.histViewBox.setMouseEnabled(x=False, y=True)
        self.histViewBox.setFixedWidth(self.histogramWidth)

        self.histPlotDataItem = pg.PlotDataItem()
        self.histPlotDataItem.rotate(90)

        self.histViewBox.addItem(self.histPlotDataItem)
        self.fillHistogram()

        # Color scale
        self.colorScaleViewBox = pg.ViewBox(enableMenu=False, border=None)

        self.colorScaleViewBox.disableAutoRange(pg.ViewBox.XYAxes)
        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)
        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleImageItem = pg.ImageItem() # image data will be set in setLut
        self.colorScaleViewBox.addItem(self.colorScaleImageItem)
        self.colorScaleViewBox.setZValue(10)

        # Overlay viewbox that will have alway have the same geometry as the colorScaleViewBox
        self.overlayViewBox = pg.ViewBox(
            enableMenu=False, border=pg.mkPen(pg.getConfigOption('foreground'), width=1))
        self.overlayViewBox.setZValue(100)

        self.axisItem = pg.AxisItem(
            orientation='right', linkView=self.overlayViewBox,
            showValues=True, maxTickLength=maxTickLength, parent=self)

        self.histViewBox.linkView(pg.ViewBox.YAxis, self.overlayViewBox)

        # Overall layout
        self.mainLayout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(1, 1, 1, 1)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addItem(self.histViewBox, 0, 0)
        self.mainLayout.addItem(self.colorScaleViewBox, 0, 1)
        self.mainLayout.addItem(self.axisItem, 0, 2)
        self.overlayViewBox.setParentItem(self.colorScaleViewBox.parentItem())

        # Connect signals
        self.colorScaleViewBox.geometryChanged.connect(self._updateOverlay)

        # It might also trigger an update when the axis is resized (but can't reproduce it
        # anymore). If needed we could test if the range has changed substantially before updating
        # image levels.
        self.overlayViewBox.sigYRangeChanged.connect(self._updateImageLevels)

        self.showHistogram(showHistogram)
        self.setImageItem(imageItem)


    def _updateOverlay(self):
        """ Makes the overlay the same size as the colorScaleViewBox
        """
        self.overlayViewBox.setGeometry(self.colorScaleViewBox.geometry())


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
            self._imageItem.sigImageChanged.disconnect(self.onImageChanged)

        self._imageItem = imageItem
        self._imageItem.sigImageChanged.connect(self.onImageChanged)

        if self._imageItem.lut is not None:
            self.setLut(self._imageItem.lut) # extents lut if necessary
        self.onImageChanged()


    def onImageChanged(self):
        """ Called when new image data has been set in the linked ImageItem

            Updates the histogram and colorize the image (_updateImageLevels)
        """
        logger.debug("ColorLegendItem._onImageChanged", stack_info=False)
        self._updateHistogram()
        self._updateImageLevels()


    @QtCore.pyqtSlot()
    def _updateImageLevels(self):
        """ Updates the image levels from the color levels of the
        """
        levels = self.getLevels()
        #logger.debug("updateImageToNewLevels: {}".format(levels), stack_info=False)
        if self._imageItem is not None:
            self._imageItem.setLevels(levels)

        self.sigLevelsChanged.emit(levels)


    @property
    def subsampleStep(self):
        """ The step size that is used to subsample the array when calculating the histogram
        """
        return self._subsampleStep


    @subsampleStep.setter
    def subsampleStep(self, value):
        """ The step size that is used to subsample the array when calculating the histogram

            :value: can be a scalar, a tuple with two elements, or 'auto'.
        """
        self._subsampleStep = value


    def _updateHistogram(self):
        """ Updates the histogram with data from the image
        """
        if not self._histogramIsVisible or self._imageItem is None or self._imageItem.image is None:
            self.histPlotDataItem.clear()
            return

        imgArr = self._imageItem.image
        histRange = self._calcHistogramRange(imgArr, step=self.subsampleStep)
        histBins = self._calcHistogramBins(
            histRange, forIntegers=self._imageItemHasIntegerData(self._imageItem))

        histogram = self._imageItem.getHistogram(bins=histBins, range=histRange)

        if histogram[0] is None:
            logger.warning("Histogram empty in imageChanged()") # when does this happen?
            return
        else:
            self.histPlotDataItem.setData(*histogram)


    @classmethod
    def _calcHistogramRange(cls, imgArr, step='auto', targetImageSize=200):
        """ Calculates bins for the histogram.

            We explicitly calculate the range because in PyQtGraph 0.10.0 the histogram range is
            calculated without taking NaNs into account (this was fixed in PyQtGraph issue #699.
            Also it you to derive a subclasses of ColorLegendItem and override this.

            This function was based on PyQtGraph.ImageItem.getHistogram() commit efaf61f

            The *step* argument causes pixels to be skipped when computing the histogram to save
            time. If *step* is 'auto', then a step is chosen such that the analyzed data has
            dimensions roughly *targetImageSize* for each axis.

            * Integer images will have approximately 500 bins,
              with each bin having an integer width.
            * All other types will have 500 bins.

            :returns: (minRange, maxRange) tuple.
        """
        if imgArr is None or imgArr.size == 0:
            return None, None

        if step == 'auto':
            step = (max(1, int(np.ceil(imgArr.shape[0] / targetImageSize))),
                    max(1, int(np.ceil(imgArr.shape[1] / targetImageSize))))

        if np.isscalar(step):
            step = (step, step)

        stepData = imgArr[::step[0], ::step[1]]

        logger.debug("step: {}, stepData.shape: {}".format(step, stepData.shape))

        mn = np.nanmin(stepData)
        mx = np.nanmax(stepData)

        return (mn, mx)


    @classmethod
    def _imageItemHasIntegerData(cls, imageItem):
        """ Returns True if the imageItem contains integer data.

            Allows use to override this.
        """
        check_class(imageItem, ImageItem, allowNone=True)

        if imageItem is None or imageItem.image is None:
            return False
        else:
            return imageItem.image.dtype.kind in "ui"



    @classmethod
    def _calcHistogramBins(cls, histRange, forIntegers=False):
        """ Calculates bins for the histogram give a subSampled image array (stepData)

            This function was based on PyQtGraph.ImageItem.getHistogram() commit efaf61f

            :returns: bins for use in numpy.histogram().
        """
        logger.debug("histRange: {}".format(histRange))
        mn, mx = histRange

        if mn is None or np.isnan(mn) or mx is None or np.isnan(mx):
            # the data are all-nan
            return None, None

        if forIntegers:
            # For integer data, we select the bins carefully to avoid aliasing
            step = np.ceil((mx-mn) / 500.)
            bins = np.arange(mn, mx+1.01*step, step, dtype=np.int)
        else:
            # for float data, let numpy select the bins.
            bins = np.linspace(mn, mx, 500)

        if len(bins) == 0:
            bins = [mn, mx]

        return bins


    def mouseClickEvent(self, mouseClickEvent):
        """ Resets the color range if the middle mouse button is clicked.
        """
        if mouseClickEvent.button() in self.resetRangeMouseButtons:
            mouseClickEvent.accept()
            self.resetColorLevels()


    @QtCore.pyqtSlot()
    def resetColorLevels(self):
        """ Sets the color levels from the min and max of the image
        """
        logger.debug("Reset scale")

        img = self._imageItem.image
        check_is_an_array(img, allow_none=True)

        if img is None:
            levels = (0.0, 1.0)
        else:
            levels = (np.nanmin(img), np.nanmax(img))

        self.setLevels(levels)


    def getLevels(self):
        """ Gets the value range of the legend
        """
        levels = self.axisItem.range # which equals self.histViewBox.state['viewRange'][Y_AXIS]
        assert self.axisItem.range == self.overlayViewBox.state['viewRange'][Y_AXIS], \
            "Sanity check failed {} != {}".format(self.axisItem.range,
                                       self.overlayViewBox.state['viewRange'][Y_AXIS])
        return tuple(levels)


    @QtCore.pyqtSlot(tuple)
    def setLevels(self, levels, padding=0.0):
        """ Sets the value range of the legend.

            :param int padding: percentage that will be added to the color range.
                Use None for PyQtGraph's padding algorithm. Use 0 for no padding.
        """
        #logger.debug("ColorLegendItem.setLevels: {}".format(levels), stack_info=False)
        lvlMin, lvlMax = levels
        # Note: overlayViewBox.setYRange will call _updateImageLevels, which will
        # emit sigLevelsChanged
        self.overlayViewBox.setYRange(lvlMin, lvlMax, padding=padding)


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


    @property
    def histogramIsVisible(self):
        """ Indicates if the histogram is visible
        """
        return self._histogramIsVisible


    @QtCore.pyqtSlot(bool)
    def showHistogram(self, show):
        """ Toggle histogram on or off.
        """
        #logger.debug("showHistogram: {}".format(show))
        self._histogramIsVisible = show
        if show:
            self.histViewBox.setFixedWidth(self.histogramWidth)
            self.histPlotDataItem.show()
            self._updateHistogram()
        else:
            self.histViewBox.setFixedWidth(1) # zero gives error
            self.histPlotDataItem.hide()


    def fillHistogram(self, fill=True, level=0.0, color=(100, 100, 200)):
        """ Fills the histogram
        """
        if fill:
            self.histPlotDataItem.setFillLevel(level)
            self.histPlotDataItem.setFillBrush(color)
        else:
            self.histPlotDataItem.setFillLevel(None)
