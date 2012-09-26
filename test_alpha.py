#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pygtk
pygtk.require('2.0')
import gtk, sys, cairo
from math import pi

def expose (widget, event):
    cr = widget.window.cairo_create()

    # Sets the operator to clear which deletes everything below where an object is drawn
    cr.set_operator(cairo.OPERATOR_CLEAR)
    # Makes the mask fill the entire window
    cr.rectangle(0.0, 0.0, *widget.get_size())
    # Deletes everything in the window (since the compositing operator is clear and mask fills the entire window
    cr.fill()
    # Set the compositing operator back to the default
    cr.set_operator(cairo.OPERATOR_OVER)

    # Draw a fancy little circle for demonstration purpose
    cr.set_source_rgba(0.5,1.0,0.0,1)
    cr.arc(widget.get_size()[0]/2,widget.get_size()[1]/2,
           widget.get_size()[0]/2,0,pi*2)
    cr.fill()

def main ():

    win = gtk.Window()

    win.set_decorated(False)

    # Makes the window paintable, so we can draw directly on it
    win.set_app_paintable(True)
    win.set_size_request(100, 100)

    # This sets the windows colormap, so it supports transparency.
    # This will only work if the wm support alpha channel
    screen = win.get_screen()
    rgba = screen.get_rgba_colormap()
    win.set_colormap(rgba)

    win.connect('expose-event', expose)

    win.show()
    gtk.main()

if __name__ == "__main__":
    main()

