from msilib.schema import Control
import flet
from flet import AppBar, ElevatedButton, Page, Text, View, colors, TextField, OutlinedButton
from flet_async import async_page_method, app, PageWorker, PageParams, Interface
from flet_node import Node, NC, EntityNode, ENode
from typing import List, Optional
from cengal.parallel_execution.coroutines.coro_standard_services.sleep import Sleep
from cengal.introspection.inspect import pdi
from flet.control_event import ControlEvent


class ViewsPage(PageWorker):
    def __init__(self) -> None:
        super().__init__()
        self.main_view_title_text: Text = None
        self.settings_view_title_text: Text = None
        self.settings_view_title_text_index: int = 0
        self.views: List[View] = list()

    def init(self, root: Node):
        page = root.item
        page.title = "Views Example"

        def open_mail_settings(e):
            page.go("/settings/mail")

        def open_settings(e):
            page.go("/settings")

        print("Initial route:", page.route)
        main_view = EntityNode(View, '/')
        with main_view as v:
            with v()(AppBar) as ab:
                self.main_view_title_text = ab(NC('title'))(Text, "Flet app").item
            
            v()(ElevatedButton, "Go to settings", on_click=open_settings)
            v()(TextField, value="0", text_align="right", width=100)
        
        self.views.append(main_view.item)

        with ENode(View, '/settings') as view:
            view()(AppBar, title=self.sa('settings_view_title_text', Text("Settings")), bgcolor=colors.SURFACE_VARIANT)
            view()(Text, "Settings!", style="bodyMedium")
            view()(TextField, value="0", text_align="right", width=100)
            view()(ElevatedButton, "Go to mail settings", on_click=open_mail_settings)
            def title_updater(i: Interface, self: ViewsPage, my_text: str, e: ControlEvent, *, timeout: Optional[float] = None):
                pdi(e)
                print(e.page, e.control, e.target, e.name, e.data)
                page: Page = e.page
                button: OutlinedButton = e.control
                event_name: str = e.name
                event_data: str = e.data
                
                self.settings_view_title_text.value = f'{self.settings_view_title_text.value}_{self.settings_view_title_text_index}'
                if timeout is not None:
                    self.update(self.settings_view_title_text)
                    i(Sleep, timeout)
                
                self.settings_view_title_text.value = f'{self.settings_view_title_text.value}{my_text}'
                self.update(self.settings_view_title_text)
                self.settings_view_title_text_index += 1
            
            view()(OutlinedButton, 'Update title', on_click=self.ah(title_updater, '|=|', timeout=2.0))
            self.views.append(view.item)

        with ENode(View, '/settings/mail') as v:
            v(NC('appbar'))(AppBar, title=Text("Mail Settings"), bgcolor=colors.SURFACE_VARIANT)
            v()(Text, "Mail settings!")
            v()(TextField, value="0", text_align="right", width=100)
            self.views.append(v.item)

        def route_change(e):
            print("Route changed to:", e.route)
            page.views.clear()
            page.views.append(self.views[0])
            if page.route == "/settings" or page.route == "/settings/mail":
                page.views.append(self.views[1])
            if page.route == "/settings/mail":
                page.views.append(self.views[2])
            page.update()

        def view_pop(e):
            print("View pop:", e.view)
            page.views.pop()
            top_view = page.views[-1]
            print(f'Will go to: {top_view.route}')
            page.go(top_view.route)

        page.on_route_change = route_change
        page.on_view_pop = view_pop

        print(f'Page Route: {page.route}')
        page.go(page.route)


def main():
    app(target=PageParams(ViewsPage), view=flet.WEB_BROWSER)


if '__main__' == __name__:
    main()
