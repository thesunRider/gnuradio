from gi.repository import Gtk, Gdk

class MiniMap(Gtk.DrawingArea):
    def __init__(self, flow_graph, scrolled_window):
        super().__init__()
        self.flow_graph = flow_graph
        self.scrollbox = scrolled_window
        self.canvas = scrolled_window.get_child()  # Viewport → DrawingArea

        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )

        hadj, vadj = self.scrollbox.get_hadjustment(), self.scrollbox.get_vadjustment()
        self.set_size_request(150, 100)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("draw", self.draw)
        self.connect("button-press-event", self.navigate)
        self.connect("button-press-event", self.on_press)
        self.connect("button-release-event", self.on_release)
        self.connect("motion-notify-event", self.on_motion)
        self.dragging = False
        self.scale_factor = 5
        self.previous_size = (hadj.get_page_size()/self.scale_factor, vadj.get_page_size()/self.scale_factor)


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

        # draw viewport rectangle proportional to the scrollbar/page
        hadj, vadj = self.scrollbox.get_hadjustment(), self.scrollbox.get_vadjustment()
        if not (self.previous_size == (hadj.get_page_size()/self.scale_factor, vadj.get_page_size()/self.scale_factor)):
            self.previous_size = (hadj.get_page_size()/self.scale_factor, vadj.get_page_size()/self.scale_factor)
            #self.set_size_request(hadj.get_page_size()/self.scale_factor, vadj.get_page_size()/self.scale_factor)

        vx_ratio = hadj.get_value() / hadj.get_upper()   # 0..1
        vy_ratio = vadj.get_value() / vadj.get_upper()
        vw_ratio = hadj.get_page_size() / hadj.get_upper()
        vh_ratio = vadj.get_page_size() / vadj.get_upper()

        x0, y0, x1, y1 = self.flow_graph.get_extents()
        graph_w, graph_h = x1 - x0, y1 - y0

        # map ratios to minimap coordinates
        vx = vx_ratio * graph_w
        vy = vy_ratio * graph_h
        vw = vw_ratio * graph_w
        vh = vh_ratio * graph_h


        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(1 / scale)
        cr.rectangle(vx, vy, vw+(100*scale), vh+(100*scale))
        cr.stroke()

    def navigate(self, widget, event):
        scale = self.compute_scale()
        target_x, target_y = event.x / scale, event.y / scale

        hadj, vadj = self.scrollbox.get_hadjustment(), self.scrollbox.get_vadjustment()
        new_h = max(0, target_x - hadj.get_page_size()/2)
        new_v = max(0, target_y - vadj.get_page_size()/2 )

        hadj.set_value(min(new_h, hadj.get_upper() - hadj.get_page_size()))
        vadj.set_value(min(new_v, vadj.get_upper() - vadj.get_page_size()))

    def on_press(self, widget, event):
        scale = self.compute_scale()
        hadj, vadj = self.scrollbox.get_hadjustment(), self.scrollbox.get_vadjustment()
        vx, vy = hadj.get_value() * scale, vadj.get_value() * scale
        vw, vh = hadj.get_page_size() * scale, vadj.get_page_size() * scale

        # Check if click is inside viewport rectangle
        if vx <= event.x <= vx + vw and vy <= event.y <= vy + vh:
            self.dragging = True
            self.drag_offset = (event.x - vx, event.y - vy)
            return True

    def on_release(self, widget, event):
        self.dragging = False

    def on_motion(self, widget, event):
        if self.dragging:
            scale = self.compute_scale()
            hadj, vadj = self.scrollbox.get_hadjustment(), self.scrollbox.get_vadjustment()
            new_vx = (event.x - self.drag_offset[0]) / scale
            new_vy = (event.y - self.drag_offset[1]) / scale

            # Clamp to bounds
            new_h = max(0, min(new_vx, hadj.get_upper() - hadj.get_page_size()))
            new_v = max(0, min(new_vy, vadj.get_upper() - vadj.get_page_size()))

            hadj.set_value(new_h)
            vadj.set_value(new_v)
            self.queue_draw()
            return True