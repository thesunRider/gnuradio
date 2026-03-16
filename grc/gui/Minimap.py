from gi.repository import Gtk, Gdk
from .canvas import colors


class MiniMap(Gtk.DrawingArea):

    def __init__(self, flow_graph, scrolled_window):
        super().__init__()

        self.flow_graph = flow_graph
        self.scrollbox = scrolled_window
        self.viewport = scrolled_window.get_child()
        self.canvas = self.viewport.get_child()

        self.border_width = 1
        self.padding = 3  # Padding from all sides

        self.dragging = False
        self.window_size = (180, 120)

        self.set_size_request(self.window_size[0], self.window_size[1])
        self.set_hexpand(False)
        self.set_vexpand(False)

        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK
        )

        self.connect("draw", self.draw)
        self.connect("button-press-event", self.on_press)
        self.connect("button-release-event", self.on_release)
        self.connect("motion-notify-event", self.on_motion)
        self.visible = False

    def toggle_visibility(self):
        self.visible = not self.visible

    def compute_scale(self):
        x0, y0, x1, y1 = self.flow_graph.get_extents()
        width = self.get_allocated_width() - 2 * self.padding
        height = self.get_allocated_height() - 2 * self.padding
        graph_w, graph_h = (x1 - x0), (y1 - y0)
        return (width / graph_w, height / graph_h)

    def draw(self, widget, cr):
        if not self.visible:
            return

        width = self.get_allocated_width()
        height = self.get_allocated_height()

        # Panel background
        cr.set_source_rgba(1, 1, 1, 0.5)
        cr.rectangle(0, 0, width, height)
        cr.fill()

        # Panel border
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(self.border_width)
        cr.rectangle(
            self.border_width / 2,
            self.border_width / 2,
            width - self.border_width,
            height - self.border_width
        )
        cr.stroke()

        # Apply padding + scale
        scale = self.compute_scale()
        cr.translate(self.padding, self.padding)
        cr.scale(scale[0], scale[1])

        # Draw blocks
        for block in self.flow_graph.blocks:
            bx, by = block.coordinate
            _, _, bw, bh = block._area
            cr.rectangle(bx, by, bw, bh)
            cr.set_source_rgba(*block._bg_color)
            cr.fill_preserve()
            border_color = colors.HIGHLIGHT_COLOR if block.highlighted else block._border_color
            cr.set_source_rgba(*border_color)
            cr.set_line_width(1 / min(scale))
            cr.stroke()

        # Draw viewport rectangle
        hadj = self.scrollbox.get_hadjustment()
        vadj = self.scrollbox.get_vadjustment()

        vx_ratio = hadj.get_value() / hadj.get_upper()
        vy_ratio = vadj.get_value() / vadj.get_upper()
        vw_ratio = hadj.get_page_size() / hadj.get_upper()
        vh_ratio = vadj.get_page_size() / vadj.get_upper()

        if not (vw_ratio == 1 and vh_ratio == 1):
            x0, y0, x1, y1 = self.flow_graph.get_extents()
            graph_w, graph_h = x1 - x0, y1 - y0

            vx = vx_ratio * graph_w
            vy = vy_ratio * graph_h
            vw = vw_ratio * graph_w
            vh = vh_ratio * graph_h

            cr.set_source_rgba(0, 0, 0, 0.2)
            cr.set_fill_rule(1)  # EVEN_ODD
            cr.rectangle(0, 0, graph_w, graph_h)  # whole minimap inside padding
            cr.rectangle(vx, vy, vw, vh)          # viewport hole
            cr.fill()

            cr.set_source_rgb(1, 0, 0)
            cr.set_line_width(0.5 / min(scale))
            cr.rectangle(vx, vy, vw, vh)
            cr.stroke()

    def on_press(self, widget, event):
        scale = [self.compute_scale()[0] / self.canvas.zoom_factor,
                 self.compute_scale()[1] / self.canvas.zoom_factor]

        target_x = event.x / scale[0]
        target_y = event.y / scale[1]

        hadj = self.scrollbox.get_hadjustment()
        vadj = self.scrollbox.get_vadjustment()

        new_h = max(0, min(target_x - hadj.get_page_size() / 2,
                           hadj.get_upper() - hadj.get_page_size()))
        new_v = max(0, min(target_y - vadj.get_page_size() / 2,
                           vadj.get_upper() - vadj.get_page_size()))

        hadj.set_value(new_h)
        vadj.set_value(new_v)

        # Compute viewport in minimap coordinates
        vx = hadj.get_value() * scale[0]
        vy = vadj.get_value() * scale[1]
        vw = hadj.get_page_size() * scale[0]
        vh = hadj.get_page_size() * scale[1]

        if vx <= event.x <= vx + vw and vy <= event.y <= vy + vh:
            self.dragging = True
            self.drag_offset = (event.x - vx, event.y - vy)
            return True

    def on_release(self, widget, event):
        self.dragging = False

    def on_motion(self, widget, event):
        if not self.dragging:
            return

        scale = [self.compute_scale()[0] / self.canvas.zoom_factor,
                 self.compute_scale()[1] / self.canvas.zoom_factor]

        hadj = self.scrollbox.get_hadjustment()
        vadj = self.scrollbox.get_vadjustment()

        new_vx = (event.x - self.drag_offset[0]) / scale[0]
        new_vy = (event.y - self.drag_offset[1]) / scale[1]

        new_h = max(0, min(new_vx, hadj.get_upper() - hadj.get_page_size()))
        new_v = max(0, min(new_vy, vadj.get_upper() - vadj.get_page_size()))

        hadj.set_value(new_h)
        vadj.set_value(new_v)

        self.queue_draw()