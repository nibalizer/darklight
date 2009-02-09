#!/usr/bin/env python

try:
	import pyinotify

	class DarkEvent(pyinotify.ProcessEvent):
	
		def process_IN_CREATE(self, event):
			path = os.path.join(event.path, event.name)
			twisted.internet.reactor.callFromThread(
				darkcache.DarkCache().folders.append, darkcache.DarkFile(path))
	
		def process_IN_DELETE(self, event):
			pass

	class DarkNotify:
		_state = {"n": None, "wm": pyinotify.WatchManager()}
	
		mask = (pyinotify.EventsCodes.IN_CREATE |
			pyinotify.EventsCodes.IN_DELETE)
	
		def __init__(self):
			self.__dict__ = self._state
	
		def start(self):
			self.n = pyinotify.ThreadedNotifier(self.wm, DarkEvent())
			self.n.setDaemon(True)
			self.n.start()
	
		def add(self, folders):
			print self.wm.add_watch(folders, mask, rec=True,
				auto_add=True)
	
		def stop(self):
			self.n.stop()
except ImportError:
	pass
