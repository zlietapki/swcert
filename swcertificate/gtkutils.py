import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class TreeViewUtils:
    @staticmethod
    def add_column_text(treeview, title=None):
        renderer = Gtk.CellRendererText()
        col = Gtk.TreeViewColumn(title=title, cell_renderer=renderer, text=0)
        treeview.append_column(col)

    @staticmethod
    def set_model(treeview, model=None):
        if not model:
            model = Gtk.ListStore(str)
        treeview.set_model(model)
        return model

    @staticmethod
    def get_records(treeview, column=0):
        model = treeview.get_model()
        iterator = model.get_iter_first()
        records = list()
        while iterator:
            domain = model.get_value(iterator, column)
            records.append(domain)
            iterator = model.iter_next(iterator)
        return records

    @staticmethod
    def get_record(treeview, iterator, column=0):
        model = treeview.get_model()
        record = model.get_value(iterator, column)
        return record

    @staticmethod
    def add_record(treeview, record):
        model = treeview.get_model()
        model.append(record)

    @staticmethod
    def delete_record(treeview, iterator):
        if iterator:
            model = treeview.get_model()
            model.remove(iterator)
