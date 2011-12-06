# - coding: utf-8 -

# Copyright (C) 2008-2009 Toms Bauģis <toms.baugis at gmail.com>

# This file is part of Project Hamster.

# Project Hamster is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Project Hamster is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Project Hamster.  If not, see <http://www.gnu.org/licenses/>.

import gtk, gobject, pango
import datetime as dt

from ..configuration import runtime
from ..lib import stuff, graphics
from .. import external

class ActivityEntry(gtk.Entry):
    __gsignals__ = {
        'value-entered': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }


    def __init__(self):
        gtk.Entry.__init__(self)
        self.news = False
        self.activities = None
        self.external_activities = [] # suggestions from outer space
        self.categories = None
        self.filter = None
        self.max_results = 10 # limit popup size to 10 results
        self.external = external.ActivitiesSource()

        self.popup = gtk.Window(type = gtk.WINDOW_POPUP)

        box = gtk.ScrolledWindow()
        box.set_shadow_type(gtk.SHADOW_IN)
        box.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

        self.tree = gtk.TreeView()
        self.tree.set_headers_visible(False)
        self.tree.set_hover_selection(True)

        self.time_icon_cell = gtk.CellRendererPixbuf()
        self.time_icon_cell.set_property("icon-name", "appointment-new")

        self.time_icon_column = gtk.TreeViewColumn("", self.time_icon_cell)
        self.tree.append_column(self.time_icon_column)

        self.time_cell = gtk.CellRendererText()
        self.time_cell.set_property("scale", 0.8)

        self.time_column = gtk.TreeViewColumn("Time",
                                              self.time_cell,
                                              text = 3)
        self.tree.append_column(self.time_column)


        self.activity_column = gtk.TreeViewColumn("Activity",
                                                  gtk.CellRendererText(),
                                                  text=1)
        self.activity_column.set_expand(True)
        self.tree.append_column(self.activity_column)

        self.category_cell = gtk.CellRendererText()
        self.category_cell.set_property('alignment', pango.ALIGN_RIGHT)
        self.category_cell.set_property('scale', pango.SCALE_SMALL)
        self.category_cell.set_property('yalign', 0.0)

        self.category_column = gtk.TreeViewColumn("Category",
                                                  self.category_cell,
                                                  text=2)
        self.tree.append_column(self.category_column)



        self.tree.connect("button-press-event", self._on_tree_button_press_event)

        box.add(self.tree)
        self.popup.add(box)

        self.connect("button-press-event", self._on_button_press_event)
        self.connect("key-press-event", self._on_key_press_event)
        self.connect("key-release-event", self._on_key_release_event)
        self.connect("focus-out-event", self._on_focus_out_event)
        self.connect("changed", self._on_text_changed)
        self._parent_click_watcher = None # bit lame but works

        runtime.storage.connect('activities-changed',self.after_activity_update)

        self.show()
        self.populate_suggestions()

    def get_value(self):
        activity_name = self.get_text().decode("utf-8").strip()
        if not activity_name:
            return None, False

        # see if entered text matches something from the outer suggestions
        # only consequence of if it does is that it will not attempt to
        # resurrect the activity if it's deleted (hidden)
        # thus avoiding polluting our local suggestions
        external_names = set()
        for activity in self.external_activities:
            name = activity['name']
            if activity['category']:
                name = "%s@%s" % (name, activity['category'])
            external_names.add(name.lower())

        return activity_name, activity_name in external_names

    def hide_popup(self):
        if self._parent_click_watcher and self.get_toplevel().handler_is_connected(self._parent_click_watcher):
            self.get_toplevel().disconnect(self._parent_click_watcher)
            self._parent_click_watcher = None
        self.popup.hide()

    def show_popup(self):
        result_count = self.tree.get_model().iter_n_children(None)
        if result_count <= 1:
            self.hide_popup()
            return

        if not self._parent_click_watcher:
            self._parent_click_watcher = self.get_toplevel().connect("button-press-event", self._on_focus_out_event)

        fact = stuff.Fact(self.filter)
        time = ''
        if fact.start_time:
            time = fact.start_time.strftime("%H:%M")
            if fact.end_time:
                time += "-%s" % fact.end_time.strftime("%H:%M")

        self.time_icon_column.set_visible(fact.start_time is not None and self.filter.find("@") == -1)
        self.time_column.set_visible(fact.start_time is not None and self.filter.find("@") == -1)


        self.category_column.set_visible(self.filter.find("@") == -1)


        #set proper background color (we can do that only on a realised widget)
        bgcolor = self.get_style().bg[gtk.STATE_NORMAL]
        self.time_icon_cell.set_property("cell-background-gdk", bgcolor)
        self.time_cell.set_property("cell-background-gdk", bgcolor)

        text_color = self.get_style().text[gtk.STATE_NORMAL]
        category_color = graphics.Colors.contrast(text_color,  100)
        self.category_cell.set_property('foreground-gdk', graphics.Colors.gdk(category_color))


        #move popup under the widget
        alloc = self.get_allocation()

        #TODO - this is clearly unreliable as we calculate tree row size based on our gtk entry
        popup_height = (alloc.height-6) * min([result_count, self.max_results])
        self.tree.parent.set_size_request(alloc.width, popup_height)
        self.popup.resize(alloc.width, popup_height)

        x, y = self.get_parent_window().get_origin()
        y = y + alloc.y

        if y + alloc.height + popup_height < self.get_screen().get_height():
            y = y + alloc.height
        else:
            y = y - popup_height

        self.popup.move(x + alloc.x, y)

        self.popup.show_all()

    def complete_inline(self):
        model = self.tree.get_model()
        subject = self.get_text()

        if not subject or model.iter_n_children(None) == 0:
            return

        prefix_length = 0

        labels = [row[0] for row in model]
        shortest = min([len(label) for label in labels])
        first = labels[0] #since we are looking for common prefix, we do not care which label we use for comparisons

        for i in range(len(subject), shortest):
            letter_matching = all([label[i]==first[i] for label in labels])

            if not letter_matching:
                break

            prefix_length +=1

        if prefix_length:
            prefix = first[len(subject):len(subject)+prefix_length]
            self.set_text("%s%s" % (self.filter, prefix))
            self.select_region(len(self.filter), len(self.filter) + prefix_length)

    def refresh_activities(self):
        # scratch category cache so it gets repopulated on demand
        self.categories = None

    def populate_suggestions(self):
        if self.get_selection_bounds():
            cursor = self.get_selection_bounds()[0]
        else:
            cursor = self.get_position()

        if self.activities and self.categories and self.filter == self.get_text().decode('utf8', 'replace')[:cursor]:
            return #same thing, no need to repopulate

        self.filter = self.get_text().decode('utf8', 'replace')[:cursor]
        fact = stuff.Fact(self.filter)

        # do not cache as ordering and available options change over time
        self.activities = runtime.storage.get_activities(fact.activity)
        self.external_activities = self.external.get_activities(fact.activity)
        self.activities.extend(self.external_activities)

        self.categories = self.categories or runtime.storage.get_categories()


        time = ''
        if fact.start_time:
            time = fact.start_time.strftime("%H:%M")
            if fact.end_time:
                time += "-%s" % fact.end_time.strftime("%H:%M")


        store = self.tree.get_model()
        if not store:
            store = gtk.ListStore(str, str, str, str)
            self.tree.set_model(store)
        store.clear()

        if self.filter.find("@") > 0:
            key = self.filter[self.filter.find("@")+1:].decode('utf8', 'replace').lower()
            for category in self.categories:
                if key in category['name'].decode('utf8', 'replace').lower():
                    fillable = (self.filter[:self.filter.find("@") + 1] + category['name'])
                    store.append([fillable, category['name'], fillable, time])
        else:
            key = fact.activity.decode('utf8', 'replace').lower()
            for activity in self.activities:
                fillable = activity['name'].lower()
                if activity['category']:
                    fillable += "@%s" % activity['category']

                if time: #as we also support deltas, for the time we will grab anything up to first space
                    fillable = "%s %s" % (self.filter.split(" ", 1)[0], fillable)

                store.append([fillable, activity['name'].lower(), activity['category'], time])

    def after_activity_update(self, widget):
        self.refresh_activities()

    def _on_focus_out_event(self, widget, event):
        self.hide_popup()

    def _on_text_changed(self, widget):
        self.news = True

    def _on_button_press_event(self, button, event):
        self.populate_suggestions()
        self.show_popup()

    def _on_key_release_event(self, entry, event):
        if (event.keyval in (gtk.keysyms.Return, gtk.keysyms.KP_Enter)):
            if self.popup.get_property("visible"):
                if self.tree.get_cursor()[0]:
                    self.set_text(self.tree.get_model()[self.tree.get_cursor()[0][0]][0])
                self.hide_popup()
                self.set_position(len(self.get_text()))
            else:
                self._on_selected()

        elif (event.keyval == gtk.keysyms.Escape):
            if self.popup.get_property("visible"):
                self.hide_popup()
                return True
            else:
                return False
        elif event.keyval in (gtk.keysyms.Up, gtk.keysyms.Down):
            return False
        else:
            self.populate_suggestions()
            self.show_popup()

            if event.keyval not in (gtk.keysyms.Delete, gtk.keysyms.BackSpace):
                self.complete_inline()




    def _on_key_press_event(self, entry, event):

        if event.keyval in (gtk.keysyms.Up, gtk.keysyms.Down):
            cursor = self.tree.get_cursor()

            if not cursor or not cursor[0]:
                self.tree.set_cursor(0)
                return True

            i = cursor[0][0]

            if event.keyval == gtk.keysyms.Up:
                i-=1
            elif event.keyval == gtk.keysyms.Down:
                i+=1

            # keep it in the sane borders
            i = min(max(i, 0), len(self.tree.get_model()) - 1)

            self.tree.set_cursor(i)
            self.tree.scroll_to_cell(i, use_align = True, row_align = 0.4)
            return True
        else:
            return False

    def _on_tree_button_press_event(self, tree, event):
        model, iter = tree.get_selection().get_selected()
        value = model.get_value(iter, 0)
        self.set_text(value)
        self.hide_popup()
        self.set_position(len(self.get_text()))

    def _on_selected(self):
        if self.news and self.get_text().strip():
            self.set_position(len(self.get_text()))
            self.emit("value-entered")

        self.news = False
