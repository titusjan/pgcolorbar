""" Reimplementation of the PyQtGraph HistogramLUTItem.

    Currently only a histogram range in the imageChanged method is added. This prevents errors when
    the image contains NaNs. Later the mouse and scrolling behaviour may be altered.
"""

import pyqtgraph as pg

#from pyqtgraph.Qt import QtWidgets, QtCore
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets

from pyqtgraph.graphicsItems.GraphicsWidget import GraphicsWidget
from pyqtgraph.graphicsItems.ViewBox import *
from pyqtgraph.graphicsItems.GradientEditorItem import *
from pyqtgraph.graphicsItems.LinearRegionItem import *
from pyqtgraph.graphicsItems.PlotDataItem import *
from pyqtgraph.graphicsItems.AxisItem import *
from pyqtgraph.Point import Point
from pyqtgraph import functions as fn
from pyqtgraph import debug as debug

import weakref

__all__ = ['HistogramLUTItem']


class ColorLegendItem(GraphicsWidget):
    """

    """
    def __init__(self, image=None, fillHistogram=True):
        GraphicsWidget.__init__(self)


        self.layout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1, 1, 1, 1)
        self.layout.setSpacing(0)

        #self.viewBox = ViewBox(enableMenu=False, border=pg.getConfigOption('foreground'))
        self.viewBox = ViewBox(enableMenu=False)
        # self.viewBox.setBackgroundColor("666666")
        self.axis = AxisItem('left', linkView=self.viewBox, maxTickLength=-10, parent=self)


        self.rectItem = QtWidgets.QGraphicsRectItem()
        self.rectItem.setBrush(fn.mkBrush("FF0000"))
        self.rectItem.setPen(fn.mkPen(color="FFFF00", width=1, cosmetic=True))
        self.rectItem.setParentItem(self.viewBox.background)
        self.rectItem.setRect(0, 0, 40, 10)
        #self.viewBox.addItem(rectItem)

        lut = np.array([(237,248,251), (178,226,226), (102,194,164), (35,139,69)])
        barWidth = 10
        lutImg = np.ones(shape=(len(lut), barWidth, 3), dtype=lut.dtype)
        lutImg[...] = lut[:, np.newaxis, :]

        colorScaleImageItem = pg.ImageItem()
        colorScaleImageItem.setImage(lutImg)
        #self.colorScaleViewBox = ViewBox(enableMenu=False)
        self.colorScaleViewBox = ViewBox(enableMenu=False, border=pg.getConfigOption('foreground'))
        self.colorScaleViewBox.addItem(colorScaleImageItem)
        self.colorScaleViewBox.setMinimumWidth(10)
        self.colorScaleViewBox.setMaximumWidth(25)

        self.colorScaleViewBox.setMouseEnabled(x=False, y=False)

        self.layout.addItem(self.axis, 0, 0)
        self.layout.addItem(self.colorScaleViewBox, 0, 1)
        self.layout.addItem(self.viewBox, 0, 2)

        self.colorScaleViewBox.setRange(xRange=[0, barWidth], yRange=[0, len(lut)], padding=0.0)
        print("viewRange: {}".format(self.colorScaleViewBox.viewRange()))

        plotDataItem = PlotDataItem()
        plotDataItem.setData([5, 7, 12])
        self.viewBox.addItem(plotDataItem)





class HistogramLUTItem(GraphicsWidget):
    """
    This is a graphicsWidget which provides controls for adjusting the display of an image.
    Includes:

    - Image histogram
    - Movable region over histogram to select black/white levels
    - Gradient editor to define color lookup table for single-channel images
    """

    sigLookupTableChanged = QtCore.Signal(object)
    sigLevelsChanged = QtCore.Signal(object)
    sigLevelChangeFinished = QtCore.Signal(object)

    def __init__(self, image=None, fillHistogram=True):
        """
        If *image* (ImageItem) is provided, then the control will be automatically linked to the image and changes to the control will be immediately reflected in the image's appearance.
        By default, the histogram is rendered with a fill. For performance, set *fillHistogram* = False.
        """
        GraphicsWidget.__init__(self)
        self.lut = None
        self.imageItem = lambda: None  # fake a dead weakref

        self.layout = QtWidgets.QGraphicsGridLayout()
        self.setLayout(self.layout)
        self.layout.setContentsMargins(1,1,1,1)
        self.layout.setSpacing(0)
        self.vb = ViewBox(parent=self)
        self.vb.setMaximumWidth(152)
        self.vb.setMinimumWidth(45)
        self.vb.setMouseEnabled(x=False, y=True)
        self.gradient = GradientEditorItem()
        self.gradient.setOrientation('right')
        self.gradient.loadPreset('grey')
        self.region = LinearRegionItem([0, 1], LinearRegionItem.Horizontal)
        self.region.setZValue(1000)
        self.vb.addItem(self.region)
        self.axis = AxisItem('left', linkView=self.vb, maxTickLength=-10, parent=self)
        self.layout.addItem(self.axis, 0, 0)
        self.layout.addItem(self.vb, 0, 1)
        self.layout.addItem(self.gradient, 0, 2)
        self.range = None
        self.gradient.setFlag(self.gradient.ItemStacksBehindParent)
        self.vb.setFlag(self.gradient.ItemStacksBehindParent)

        #self.grid = GridItem()
        #self.vb.addItem(self.grid)

        self.gradient.sigGradientChanged.connect(self.gradientChanged)
        self.region.sigRegionChanged.connect(self.regionChanging)
        self.region.sigRegionChangeFinished.connect(self.regionChanged)
        self.vb.sigRangeChanged.connect(self.viewRangeChanged)
        self.plot = PlotDataItem()
        self.plot.rotate(90)
        self.fillHistogram(fillHistogram)

        self.vb.addItem(self.plot)
        self.autoHistogramRange()

        if image is not None:
            self.setImageItem(image)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Expanding)

    def fillHistogram(self, fill=True, level=0.0, color=(100, 100, 200)):
        if fill:
            self.plot.setFillLevel(level)
            self.plot.setFillBrush(color)
        else:
            self.plot.setFillLevel(None)

    #def sizeHint(self, *args):
        #return QtCore.QSizeF(115, 200)

    def paint(self, p, *args):
        pen = self.region.lines[0].pen
        rgn = self.getLevels()
        p1 = self.vb.mapFromViewToItem(self, Point(self.vb.viewRect().center().x(), rgn[0]))
        p2 = self.vb.mapFromViewToItem(self, Point(self.vb.viewRect().center().x(), rgn[1]))
        gradRect = self.gradient.mapRectToParent(self.gradient.gradRect.rect())
        for pen in [fn.mkPen('k', width=3), pen]:
            p.setPen(pen)
            p.drawLine(p1, gradRect.bottomLeft())
            p.drawLine(p2, gradRect.topLeft())
            p.drawLine(gradRect.topLeft(), gradRect.topRight())
            p.drawLine(gradRect.bottomLeft(), gradRect.bottomRight())
        #p.drawRect(self.boundingRect())


    def setHistogramRange(self, mn, mx, padding=0.1):
        """Set the Y range on the histogram plot. This disables auto-scaling."""
        self.vb.enableAutoRange(self.vb.YAxis, False)
        self.vb.setYRange(mn, mx, padding)

        #d = mx-mn
        #mn -= d*padding
        #mx += d*padding
        #self.range = [mn,mx]
        #self.updateRange()
        #self.vb.setMouseEnabled(False, True)
        #self.region.setBounds([mn,mx])

    def autoHistogramRange(self):
        """Enable auto-scaling on the histogram plot."""
        self.vb.enableAutoRange(self.vb.XYAxes)
        #self.range = None
        #self.updateRange()
        #self.vb.setMouseEnabled(False, False)

    #def updateRange(self):
        #self.vb.autoRange()
        #if self.range is not None:
            #self.vb.setYRange(*self.range)
        #vr = self.vb.viewRect()

        #self.region.setBounds([vr.top(), vr.bottom()])

    def setImageItem(self, img):
        """Set an ImageItem to have its levels and LUT automatically controlled
        by this HistogramLUTItem.
        """
        self.imageItem = weakref.ref(img)
        img.sigImageChanged.connect(self.imageChanged)
        img.setLookupTable(self.getLookupTable)  ## send function pointer, not the result
        #self.gradientChanged()
        self.regionChanged()
        self.imageChanged(autoLevel=True)
        #self.vb.autoRange()

    def viewRangeChanged(self):
        self.update()

    def gradientChanged(self):
        if self.imageItem() is not None:
            if self.gradient.isLookupTrivial():
                self.imageItem().setLookupTable(None) #lambda x: x.astype(np.uint8))
            else:
                self.imageItem().setLookupTable(self.getLookupTable)  ## send function pointer, not the result

        self.lut = None
        #if self.imageItem is not None:
            #self.imageItem.setLookupTable(self.gradient.getLookupTable(512))
        self.sigLookupTableChanged.emit(self)

    def getLookupTable(self, img=None, n=None, alpha=None):
        """Return a lookup table from the color gradient defined by this
        HistogramLUTItem.
        """
        if n is None:
            if img.dtype == np.uint8:
                n = 256
            else:
                n = 512
        if self.lut is None:
            self.lut = self.gradient.getLookupTable(n, alpha=alpha)
        return self.lut

    def regionChanged(self):
        #if self.imageItem is not None:
            #self.imageItem.setLevels(self.region.getRegion())
        self.sigLevelChangeFinished.emit(self)
        #self.update()

    def regionChanging(self):
        if self.imageItem() is not None:
            self.imageItem().setLevels(self.region.getRegion())
        self.sigLevelsChanged.emit(self)
        self.update()

    def imageChanged(self, autoLevel=False, autoRange=False):
        profiler = debug.Profiler()
        img = self.imageItem().image
        if img is None:
            histRange = None
        else:
            histRange = (np.nanmin(img), np.nanmax(img))

        h = self.imageItem().getHistogram(range=histRange)
        profiler('get histogram')
        if h[0] is None:
            return
        self.plot.setData(*h)
        profiler('set plot')
        if autoLevel:
            mn = h[0][0]
            mx = h[0][-1]
            self.region.setRegion([mn, mx])
            profiler('set region')

    def getLevels(self):
        """Return the min and max levels.
        """
        return self.region.getRegion()

    def setLevels(self, mn, mx):
        """Set the min and max levels.
        """
        self.region.setRegion([mn, mx])
