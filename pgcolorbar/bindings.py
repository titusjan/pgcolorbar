""" Harmonize QT bindings
"""

from pyqtgraph.Qt import QT_LIB, PYQT4, PYQT5
from pyqtgraph.Qt import QtWidgets, QtCore

if QT_LIB in [PYQT4, PYQT5]:

    # Add pyqtSlot as Slot for consistency
    if not hasattr(QtCore, 'Slot'):
        QtCore.Slot = QtCore.pyqtSlot



