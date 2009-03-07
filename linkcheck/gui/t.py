    def on_treeWidget_customContextMenuRequested (self, point):
        print "XXX", point, self.treeWidget.mapToGlobal(point)
        item = self.treeWidget.itemAt(point)
        if item is not None:
            # show menu
            menu = QtGui.QMenu(self.treeWidget)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(":/icons/online.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
            action = menu.addAction(icon, _("&View Online"))
            self.connect(action, QtCore.SIGNAL("triggered()"), self.item_view_online)
            menu.exec_(self.treeWidget.mapToGlobal(point))

    def item_view_online (self):
        print "XXX view online"

