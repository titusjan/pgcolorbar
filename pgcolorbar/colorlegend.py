""" Color legend.

    Consists of a vertical color bar with a draggable axis that displays the values of the colors.
    Optionally a histogram can be displayed.
"""
from __future__ import print_function, division

import cProfile
import logging
import os
import pstats
import warnings

import numpy as np
import pyqtgraph as pg

from .bindings import QtWidgets, QtCore
from .misc import versionStrToTuple
from pyqtgraph import ImageItem


from .misc import check_is_an_array, check_class

logger = logging.getLogger(__name__)

X_AXIS = pg.ViewBox.XAxis
Y_AXIS = pg.ViewBox.YAxis
BOTH_AXES = pg.ViewBox.XYAxes

COL_PROFILING = False

def assertIsLut(lut):
    """ Checks that lut is Nx3 array of dtype uint8

        If dtype is not an 8 bits integer the resulting image will also not be 8 bits, but e.g.
        32-bits. This not only costs more memory but is also significantly slower.
    """
    check_is_an_array(lut)
    assert lut.ndim == 2, "Expected 2 dimensional LUT. Got {}D".format(lut.ndim)
    assert lut.shape[1] == 3, \
        "Second dimension of LUT should be length 3. Got: {}".format(lut.shape[1])
    assert lut.dtype == np.uint8, \
        "LUT should have dtype np.uint8, got {}".format(lut.dtype)


def extentLut(lut):
    """ Duplicates the last item of the Lookup Table

        This is necessary because the pyqtgraph.makeARGB function has a wrong default scale. It
        should be equal to the length of the LUT, but it's set to len(lut)-1. We therefore add a
        fake LUT entry. See issue 792 of PyQtGraph.
        It has been fixed in PyQtGraph 1.11.0
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


class NoFiniteDataError(Exception):
    """ Raised when there is no finite data when calculating the histogram
    """
    pass


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
    sigLevelsChanged = QtCore.Signal(tuple)

    def __init__(self,
                 imageItem=None,
                 label=None,
                 showHistogram=True,
                 histFillColor=(100, 100, 200),
                 subsampleStep='auto',
                 histHeightPercentile = 100.0,
                 maxTickLength=10):
        """ Constructor.

            :param imageItem pg.ImageItem: PyQtGraph ImageItem to which this legen will be linked
            :param Optonal[str] label: text to show next to the axis
            :param bool showHistogram: if True (the default), a histogram of image values is drawn.
            :param histFillColor: color to fill the histogram. Default same as in PyQtGraph.
            :param float histHeightPercentile: percentile of data points used for scaling the
                histogram height. Often an image has one color that occurs very often and this
                then will completely dominate the histogram. By discarding this color when scaling
                the histogram the other color occurrences will become visible. E.g. by using
                histHeightPercentile = 99.0, the 1% of the bins with the highest values will be
                discarded. The default is 100.0, so no points are discarded by default.
            :param subsampleStep:The step size that is used to subsample the array when calculating
                the histogram. Can be a scalar, a tuple with two elements, or 'auto'.
            :param int maxTickLength: Maximum tick length of the color axis. Default = 10
        """
        pg.GraphicsWidget.__init__(self)

        check_class(imageItem, pg.ImageItem, allowNone=True)


        if COL_PROFILING:
            # Profiler that measures the drawing of the inspectors.
            self._profFileName = "col_legend.prof"

            logger.warning("Profiling is on for {}. This may cost a bit of CPU time.")
            self._profiler = cProfile.Profile()

        self.histHeightPercentile = histHeightPercentile
        self._histogramIsVisible = showHistogram
        self._histFillColor = histFillColor
        self.histogramWidth = 50
        self._imageItem = None
        self._lutImg = None
        self._overlayVbDragStartRange = None  # Stores positions of the drag lines at drag start

        # List of mouse buttons that reset the color range when clicked.
        # You can safely modify this list.
        self.resetRangeMouseButtons = [QtCore.Qt.MiddleButton]

        self._subsampleStep = subsampleStep

        # Histogram
        self.histViewBox = pg.ViewBox(enableMenu=False)
        self.histViewBox.disableAutoRange(BOTH_AXES)
        self.histViewBox.setMouseEnabled(x=False, y=True)
        self.histViewBox.setFixedWidth(self.histogramWidth)

        self.histPlotDataItem = pg.PlotDataItem()
        self.histPlotDataItem.setRotation(90)

        self.histViewBox.addItem(self.histPlotDataItem)
        self.fillHistogram()

        # Color scale. Viewbox ranges from 0 to number of colors
        borderPenCs = pg.mkPen(color='g', width=0)
        self.colorScaleViewBox = pg.ViewBox(enableMenu=False, border=borderPenCs)

        self.colorScaleViewBox.disableAutoRange(pg.ViewBox.XYAxes)
        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)
        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleImageItem = pg.ImageItem() # image data will be set in setLut
        self.colorScaleViewBox.addItem(self.colorScaleImageItem)

        # Overlay viewbox that will have always have the same geometry as the colorScaleViewBox.
        # The histograms and axis item are linked to this viewbox
        fgColor = pg.getConfigOption('foreground')
        borderPenOl = pg.mkPen(fgColor)
        self.overlayViewBox = pg.ViewBox(enableMenu=False, border=borderPenOl)

        # Axis that shows the ticks and values
        self.axisItem = pg.AxisItem(
            orientation='right', linkView=self.overlayViewBox,
            showValues=True, maxTickLength=maxTickLength, parent=self)
        self.histViewBox.linkView(pg.ViewBox.YAxis, self.overlayViewBox)

        # Infinite lines that allow the user to drag the legend at one end

        self.edgePen = pg.mkPen(color=fgColor, width=3, dash=[1, 8])
        self._orgEdgePen = self.edgePen
        self.hoverPen = pg.mkPen(color=self._histFillColor, width=8, dash=[1, 3])

        lineKwds = dict(movable=True, pen=self.edgePen, hoverPen=self.hoverPen)

        self.lineMin = pg.InfiniteLine(QtCore.QPointF(0, 0.0), angle=0, **lineKwds)
        self.lineMax = pg.InfiniteLine(QtCore.QPointF(0, 1.0), angle=0, **lineKwds)

        self.edgeLinesViewBox = pg.ViewBox(enableMenu=False, border=None)
        self.edgeLinesViewBox.disableAutoRange(pg.ViewBox.XYAxes)
        self.edgeLinesViewBox.setMouseEnabled(x=False, y=False)

        for line in [self.lineMin, self.lineMax]:
            line.setCursor(QtCore.Qt.SplitVCursor)
            self.edgeLinesViewBox.addItem(line)

        # Overall layout
        self.mainLayout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.mainLayout)
        self.mainLayout.setContentsMargins(1, 1, 1, 1)
        self.mainLayout.setSpacing(0)
        self.mainLayout.addItem(self.histViewBox, 0, 0)
        self.mainLayout.addItem(self.colorScaleViewBox, 0, 1)
        self.mainLayout.addItem(self.axisItem, 0, 2)
        self.overlayViewBox.setParentItem(self.colorScaleViewBox.parentItem())
        self.edgeLinesViewBox.setParentItem(self.colorScaleViewBox.parentItem())

        self.edgeLinesViewBox.setZValue(-10)
        self.colorScaleImageItem.setZValue(500)
        self.colorScaleViewBox.setZValue(10)
        self.histViewBox.setZValue(10)
        self.axisItem.setZValue(10)
        self.overlayViewBox.setZValue(20)
        for line in [self.lineMin, self.lineMax]:
            line.setZValue(150)

        # Connect signals
        self.colorScaleViewBox.geometryChanged.connect(self._updateVbGeom)

        # It might also trigger an update when the axis is resized (but can't reproduce it
        # anymore). If needed we could test if the range has changed substantially before updating
        # image levels.
        self.overlayViewBox.sigYRangeChanged.connect(self._updateImageLevels)

        self.setLabel(label)
        self.showHistogram(showHistogram)
        self.setImageItem(imageItem)

        for line in [self.lineMin, self.lineMax]:
            line.sigPositionChanged.connect(self._onEdgeLineChanged)
            line.sigPositionChangeFinished.connect(self._onEdgeDragFinished)

        self._onEdgeDragFinished()  # reset drag


    def finalize(self):
        if COL_PROFILING:
            logger.info("Saving profiling information to {}"
                        .format(os.path.abspath(self._profFileName)))
            profStats = pstats.Stats(self._profiler)
            profStats.dump_stats(self._profFileName)


    def _updateVbGeom(self):
        """ Makes the overlay viewbox the same size as the colorScaleViewBox and makes the
            edge line viewbox the same size as the histogram, color scale, and axis together.
        """
        geomAx = self.axisItem.geometry()
        geomHist = self.histViewBox.geometry()
        geomCs = self.colorScaleViewBox.geometry()
        self.overlayViewBox.setGeometry(geomCs)

        totalWidth = geomHist.width() + geomCs.width() + geomAx.width()
        geomEl = QtCore.QRectF(geomHist.x(), geomCs.y(), totalWidth, geomCs.height())
        self.edgeLinesViewBox.setGeometry(geomEl)


    def setEdgeMargins(self, margin):
        """ Set margin (in pixels) at the both edges of the histogram

            This makes the scale shorter and thus gives the user some more room to drag and extent
            the color scale.
        """
        left, _top, right, _bottom = self.mainLayout.getContentsMargins()
        self.mainLayout.setContentsMargins(left, margin, right, margin)


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

        if self._imageItem:
            self._imageItem.sigImageChanged.connect(self.onImageChanged)

        if self._imageItem and self._imageItem.lut is not None:
            self.setLut(self._imageItem.lut) # extents lut if necessary
        self.onImageChanged()


    def onImageChanged(self):
        """ Called when new image data has been set in the linked ImageItem

            Updates the histogram and colorize the image (_updateImageLevels)
        """
        if self._imageItem.image is None:
            self.colorScaleImageItem.clear()
        else:
            self.colorScaleImageItem.setImage(self._lutImg)

        self._updateHistogram()
        self._updateImageLevels()


    @QtCore.Slot()
    def _updateImageLevels(self):
        """ Updates the image levels from the color levels of the
        """
        if COL_PROFILING:
            self._profiler.enable()
        levels = self.getLevels()
        if self._imageItem is not None:
            self._imageItem.setLevels(levels)

        self.sigLevelsChanged.emit(levels)

        if COL_PROFILING:
            self._profiler.enable()


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
            self.histPlotDataItem.setData([])  # seems necessary to clear data from screen
            self.histPlotDataItem.clear()
            return

        try:
            imgArr = self._imageItem.image
            histRange = self._calcHistogramRange(imgArr, step=self.subsampleStep)

            histBins = self._calcHistogramBins(
                histRange, forIntegers=self._imageItemHasIntegerData(self._imageItem))

            histogram = self._imageItem.getHistogram(bins=histBins, range=histRange)

            assert histogram[0] is not None, "Histogram empty in imageChanged()" # when does this happen again?

        except NoFiniteDataError as ex:
            logger.debug("No finite dataa. Unable to calculate histogram: {}".format(ex))
            self.histPlotDataItem.setData([])  # seems necessary to clear data from screen
            self.histPlotDataItem.clear()
        except Exception as ex:
            logger.warning("Unable to calculate histogram: {}".format(ex)) # unknown reason
            self.histPlotDataItem.setData([])  # seems necessary to clear data from screen
            self.histPlotDataItem.clear()
        else:
            self.histPlotDataItem.setData(*histogram)

            # Discard outliers when setting the histogram height so one dominant color in the
            # image doesn't make the other colors occurrences unreadable.
            histValues = histogram[1]
            histYrange = np.percentile(histValues, (self.histHeightPercentile, ))[0]
            self.histViewBox.setRange(xRange=(-histYrange, 0), padding=None)


    @classmethod
    def _calcHistogramRange(cls, imgArr, step='auto', targetImageSize=200):
        """ Calculates bins for the histogram.

            We explicitly calculate the range because in PyQtGraph 0.10.0 the histogram range is
            calculated without taking NaNs into account (this was fixed in PyQtGraph issue #699.
            Also it allows you to derive a subclasses of ColorLegendItem and override this.

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

        with warnings.catch_warnings():
            # Suppress warnings when stepData consists of only infinite data
            warnings.simplefilter("ignore")
            mn = np.nanmin(stepData)
            mx = np.nanmax(stepData)

        return (mn, mx)


    @classmethod
    def _imageItemHasIntegerData(cls, imageItem):
        """ Returns True if the imageItem contains integer data.

            Allows users to override this.
        """
        check_class(imageItem, ImageItem, allowNone=True)

        if imageItem is None or imageItem.image is None:
            return False
        else:
            return imageItem.image.dtype.kind in "ui"


    @classmethod
    def _calcHistogramBins(cls, histRange, numBins=500, forIntegers=False):
        """ Calculates bins for the histogram give a subsampled image array (stepData)

            This function was based on PyQtGraph.ImageItem.getHistogram() commit efaf61f

            :returns: bins for use in numpy.histogram().
                Returns None if the data are all Nans.
        """
        mn, mx = histRange

        if mn is None or np.isnan(mn) or mx is None or np.isnan(mx):
            raise NoFiniteDataError  # The data are all-nan

        if mn == mx:
            return [mn, mx]

        if forIntegers:
            # For integer data, we select the bins carefully to avoid aliasing
            step = np.ceil((mx-mn) / float(numBins))
            logger.debug("mn {}, mx {}, step {}, mx+1.01*step = {}"
                         .format(mn, mx, step, mx+1.01*step))
            bins = np.arange(mn, mx+1.01*step, step, dtype=np.int)
        else:
            # for float data, let numpy select the bins.
            bins = np.linspace(mn, mx, numBins)

        if len(bins) == 0:
            bins = [mn, mx]

        return bins


    def mouseClickEvent(self, mouseClickEvent):
        """ Resets the color range if the middle mouse button is clicked.
        """
        if mouseClickEvent.button() in self.resetRangeMouseButtons:
            mouseClickEvent.accept()
            self.autoScaleFromImage()


    def getLabel(self):
        """ Returns the axis label. Returns None if no label present.
        """
        return self.axisItem.labelText


    def setLabel(self, text):
        """ Sets the axis label.

            Use None for no label (an empty string will take the screen space).
        """
        self.axisItem.setLabel(text)
        self.axisItem.showLabel(text is not None) # Is not done in axisItem.setLabel when None


    @QtCore.Slot()
    def autoScaleFromImage(self):  # TODO: rename
        """ Sets the color levels from the min and max values of the image
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
        assert np.allclose(self.axisItem.range, self.overlayViewBox.state['viewRange'][Y_AXIS]), \
            "Sanity check failed {} != {}".format(self.axisItem.range,
                                       self.overlayViewBox.state['viewRange'][Y_AXIS])
        return tuple(levels)


    @QtCore.Slot(tuple)
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
        return self._imageItem.lut if self._imageItem else None


    def setLut(self, lut):
        """ Sets the lookup table to the image item.

            :param ndarray Array: an N x 3 array.
        """
        logger.debug("setLut called")
        assertIsLut(lut)

        pgVersionInfo = versionStrToTuple(pg.__version__)
        if pgVersionInfo < (0, 11):
            if not isExtended(lut):
                # The lookup table in the imageItem must be extended. See extentLut doc string
                logger.debug("Side effect: duplicating last item of LUT in image item.")
                extendedLut = extentLut(lut)
            else:
                # The lookup table in the imageItem already is extended. Draw the original
                extendedLut = lut
                lut = np.copy(lut[0:-1, :])

            assert len(lut) == len(extendedLut) - 1, "Sanity check"
        else:
            extendedLut = lut

        if self._imageItem:
            logger.debug("Setting image item to extended lut")
            self._imageItem.setLookupTable(extendedLut)

        # Draw a color scale that shows the LUT.
        barWidth = 1
        imgAxOrder = pg.getConfigOption('imageAxisOrder')
        if imgAxOrder == 'col-major':
            self._lutImg = np.ones(shape=(barWidth, len(lut), 3), dtype=lut.dtype)
            self._lutImg[...] = lut[np.newaxis, :, :]
        elif imgAxOrder == 'row-major':
            self._lutImg = np.ones(shape=(len(lut), barWidth, 3), dtype=lut.dtype)
            self._lutImg[...] = lut[:, np.newaxis, :]
        else:
            raise AssertionError("Unexpected imageAxisOrder config value: {}".format(imgAxOrder))

        self.colorScaleImageItem.setImage(self._lutImg)

        yRange = [0, len(lut)]
        logger.debug("Setting colorScaleViewBox yrange to: {}".format(yRange))

        # Do not set disableAutoRange to True in setRange; it triggers 'one last' auto range.
        # This is why the viewBox' autorange must be False at construction.
        self.colorScaleViewBox.setRange(
            xRange=[0, barWidth], yRange=yRange, padding=0.0,
            update=False, disableAutoRange=False)

        self.edgeLinesViewBox.setRange(
            xRange=[0, barWidth], yRange=yRange, padding=0.0,
            update=False, disableAutoRange=False)

        self._onEdgeDragFinished()


    @property
    def histogramIsVisible(self):
        """ Indicates if the histogram is visible
        """
        return self._histogramIsVisible


    @QtCore.Slot(bool)
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


    @property
    def dragLinesVisible(self):
        """ Indicates if the histogram is visible
        """
        return bool(self.edgePen)


    @QtCore.Slot(bool)
    def showDragLines(self, show):
        """ Shows/hides the dashed lines at the edge of the
        """
        self.edgePen = self._orgEdgePen if show else None
        self._setDragLinesPen(self.edgePen)


    def fillHistogram(self, fill=True, level=0.0, color=None):
        """ Fills the histogram
        """
        if fill:
            self.histPlotDataItem.setFillLevel(level)
            self.histPlotDataItem.setFillBrush(self._histFillColor if color is None else color)
        else:
            self.histPlotDataItem.setFillLevel(None)


    def _setDragLinesPen(self, qPen):
        """ Sets the pen of the dashed lines at the edges which can be dragged to change the range
        """
        self.lineMin.setPen(qPen)
        self.lineMax.setPen(qPen)


    @QtCore.Slot(object)
    def _onEdgeLineChanged(self, lineItem):
        """ Called when the user drags the LUT by one of the edge selectors.

            Will update the LUT range at one edge while keeping the other side fixed.
        """
        if self.getLut() is None:
            logger.debug("Can't extend LUT edges when no LUT is defined.")
            return

        if self._overlayVbDragStartRange is None:   # Executed only at start of drag.
            # Make sure the lines at the end. Otherwise the scaling doesn't work
            self._onEdgeDragFinished()

            self._setDragLinesPen(self.hoverPen) # Use the hover pen during dragging

            self._overlayVbDragStartRange = self.axisItem.range
            logger.debug("Edge range at drag start: {}".format(self._overlayVbDragStartRange))

        orgLenLutViewBox = len(self.getLut())
        curLenLutViewBox = self.lineMax.getYPos() - self.lineMin.getYPos()
        factor = max(0.01, curLenLutViewBox / orgLenLutViewBox) # Prevent negative and zero

        # If the region was extended by a factor X, the overlay/axis should be extended by the
        # same factor as well

        orgMin, orgMax = self._overlayVbDragStartRange
        orgLen = abs(orgMax - orgMin)

        if lineItem == self.lineMin:
            newMin = orgMax - orgLen / factor
            newMax = orgMax
        elif lineItem == self.lineMax:
            newMin = orgMin
            newMax = orgMin + orgLen / factor
        else:
            raise AssertionError("Unexpected lineItem: {}".format(lineItem))

        self.overlayViewBox.setYRange(newMin, newMax, padding=0.0)


    @QtCore.Slot()
    def _onEdgeDragFinished(self):
        """ Called when the user has finished dragging the LUT by one of the edge selectors.

            Will reset the edge range to the edge of the color scale.
        """
        oldBlockStateMin = self.lineMin.blockSignals(True)
        oldBlockStateMax = self.lineMax.blockSignals(True)
        try:
            self._setDragLinesPen(self.edgePen) # revert to default pen
            self.lineMin.setValue(0)
            lutMax = len(self.getLut()) if self.getLut() is not None else 1
            self.lineMax.setValue(lutMax)
        finally:
            self.lineMin.blockSignals(oldBlockStateMin)
            self.lineMax.blockSignals(oldBlockStateMax)

        self._overlayVbDragStartRange = None # reset dragging axis range


