from gi.repository import Gtk, Gdk

class MiniMap(Gtk.DrawingArea):
    def __init__(self, flow_graph, scrolled_window):
        super().__init__()
        self.flow_graph = flow_graph
        self.scrollbox = scrolled_window
        self.canvas = scrolled_window.get_child()  # Viewport → DrawingArea

        self.set_size_request(200, 150)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("draw", self.draw)
        self.connect("button-press-event", self.navigate)

    def compute_scale(self):
        x0, y0, x1, y1 = self.flow_graph.get_extents()
        graph_w, graph_h = x1 - x0, y1 - y0
        width, height = self.get_allocated_width(), self.get_allocated_height()
        return min(width / graph_w, height / graph_h)

    def draw(self, widget, cr):
        cr.set_source_rgb(0.1, 0.1, 0.1)
        cr.paint()

        scale = self.compute_scale()
        cr.scale(scale, scale)

        # draw blocks
        for block in self.flow_graph.blocks:
            bx, by = block.coordinate
            n,n,bw, bh = block._area
            cr.set_source_rgb(0.7, 0.7, 0.7)
            cr.rectangle(bx, by, bw, bh)
            cr.fill()

        # draw viewport rectangle
        hadj, vadj = self.scrollbox.get_hadjustment(), self.scrollbox.get_vadjustment()
        vx, vy = hadj.get_value(), vadj.get_value()
        vw, vh = hadj.get_page_size(), vadj.get_page_size()

        cr.set_source_rgb(1, 0, 0)
        cr.set_line_width(3/scale)
        cr.rectangle(vx, vy, vw, vh)
        cr.stroke()

    def navigate(self, widget, event):
        scale = self.compute_scale()
        target_x, target_y = event.x / scale, event.y / scale

        hadj, vadj = self.scrollbox.get_hadjustment(), self.scrollbox.get_vadjustment()
        new_h = max(0, target_x - hadj.get_page_size()/2)
        new_v = max(0, target_y - vadj.get_page_size()/2)

        hadj.set_value(min(new_h, hadj.get_upper() - hadj.get_page_size()))
        vadj.set_value(min(new_v, vadj.get_upper() - vadj.get_page_size()))