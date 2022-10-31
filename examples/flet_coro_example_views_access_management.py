import flet
from flet import AppBar, ElevatedButton, Page, Text, View, colors, TextField, OutlinedButton, TemplateRoute, RouteChangeEvent, ViewPopEvent, Control
from flet_async import async_page_method, app, PageWorker, PageParams, Interface
from flet_node import Node, NC, EntityNode, ENode
from typing import Callable, List, Optional, Dict, Sequence, Set, Union
from cengal.parallel_execution.coroutines.coro_standard_services.sleep import Sleep
from cengal.introspection.inspect import pdi
from flet.control_event import ControlEvent
from cengal.data_manipulation.tree_traversal import KeyMultiValueTreeTraversal, KeyValueTreeTraversal
from flet_views_access_management import SerialAccessViews, ViewGenerator, RandomAccessViews


class ViewsPage(PageWorker, RandomAccessViews):
    def __init__(self) -> None:
        PageWorker.__init__(self)
        # SerialAccessViews.__init__(self)
        RandomAccessViews.__init__(self)
        self.main_view_title_text: Text = None
        self.settings_view_title_text: Text = None
        self.settings_view_title_text_index: int = 0
        self.views: List[View] = list()

        self.routes: Dict[str, Callable] = {
            '/view': self.page_main,
            '/settings': self.page_settings,
            '/settings/mail': self.page_settings_mail,
        }
        self.template_routes: Dict[str, Callable] = {
            '/books/:id': None,
            '/account/:account_id/orders/:order_id': None
        }
    
    def go_to_with_view(self, route: str, view: View):
        self.page.views.append(view)
        self.page.go(route)
    
    def page_main(self):
        def open_settings(e):
            self.go_to("/settings")

        print("Initial route:", self.page.route)
        main_view = EntityNode(View, '/view')
        with main_view as v:
            with v()(AppBar) as ab:
                self.main_view_title_text = ab(NC('title'))(Text, "Flet app").item
            
            v()(ElevatedButton, "Go to settings", on_click=open_settings)
            v()(TextField, value="0", text_align="right", width=100)
        
        return main_view.item
    
    def page_settings(self):
        def open_mail_settings(e: ControlEvent):
            self.go_to("/settings/mail")

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
            return view.item
    
    def page_settings_mail(self):
        with ENode(View, '/settings/mail') as v:
            v(NC('appbar'))(AppBar, title=Text("Mail Settings"), bgcolor=colors.SURFACE_VARIANT)
            v()(Text, "Mail settings!")
            v()(TextField, value="0", text_align="right", width=100)
            return v.item

    def init(self, root: Node):
        page = root.item
        page.title = "Views Example"
        def open_first_view(e):
            self.go_to("/view")

        with root as r:
            r()(AppBar, title=Text("Main Page"), bgcolor=colors.SURFACE_VARIANT)
            r()(ElevatedButton, "Go to First View", on_click=open_first_view)
            r()(TextField, value="0", text_align="right", width=100)

        page.on_route_change = self.route_change
        page.on_view_pop = self.view_pop


def main():
    app(target=PageParams(ViewsPage), view=flet.WEB_BROWSER)


if '__main__' == __name__:
    main()
