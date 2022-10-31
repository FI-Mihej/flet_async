__all__ = ['find_template_route', 'SerialAccessViews', 'ViewGenerator', 'RandomAccessViews']


import flet
from flet import AppBar, ElevatedButton, Page, Text, View, colors, TextField, OutlinedButton, TemplateRoute, RouteChangeEvent, ViewPopEvent, Control
from flet_async import async_page_method, app, PageWorker, PageParams, Interface
from flet_node import Node, NC, EntityNode, ENode
from typing import Callable, List, Optional, Dict, Sequence, Set, Union
from cengal.parallel_execution.coroutines.coro_standard_services.sleep import Sleep
from cengal.introspection.inspect import pdi
from flet.control_event import ControlEvent
from cengal.data_manipulation.tree_traversal import KeyMultiValueTreeTraversal, KeyValueTreeTraversal


def find_template_route(route: str, template_routes: Sequence[str]) -> Optional[str]:
    troute: TemplateRoute = TemplateRoute(route)
    for template_route in template_routes:
        if troute.match(template_route):
            return template_route


class SerialAccessViews:
    """New view will be created on `go_to`. View will be destroyed during `view_pop` call. Random access navigation (by browser's `Back` and `Forward` buttuns) is blocked
    """
    def __init__(self, page: Optional[Page] = None):
        self.page: Page = page
        self.routes: Dict[str, Union[Callable, ViewGenerator]] = dict()
        self.template_routes: Dict[str, Union[Callable, ViewGenerator]] = dict()
    
    def get_route_template(self, route: Optional[str]) -> Optional[str]:
        if route is None:
            return None
        
        if route in self.routes:
            return route
        else:
            return find_template_route(route, self.template_routes)
    
    def view_gen_by_route(self, route: Optional[str]) -> Optional[Callable]:
        if route is None:
            return None
        
        if route in self.routes:
            view_generator: View = self.routes[route]
        else:
            view_generator = find_template_route(route, self.template_routes)
        
        return view_generator
    
    def view_gen_by_route_template(self, route_template: Optional[str]) -> Optional[str]:
        if route_template is None:
            return None
        
        if route_template in self.routes:
            return self.routes[route_template]
        else:
            if route_template in self.template_routes:
                return self.template_routes[route_template]
            else:
                return None
    
    def get_page_top_view_route_template(self) -> Optional[str]:
        source_route_template: Optional[str] = None
        page_views = self.page.views
        if page_views is not None:
            if len(page_views) > 1:
                source_route_template = self.page.views[-1].route
        
        return source_route_template
    
    def go_to(self, route: str) -> bool:
        view_generator: Optional[Callable] = self.view_gen_by_route(route)
        if view_generator is None:
            return False
        else:
            self.page.views.append(view_generator())
            self.page.go(route)
            return True

    def route_change(self, e: RouteChangeEvent):
        pdi(e)
        destination_route = e.route
        page = e.page
        page_views = page.views
        if page_views:
            top_view = page_views[-1]
            top_view_route = top_view.route
        else:
            top_view_route = None

        top_view_route = '/' if top_view_route is None else top_view_route
        print("Route-change attempt from:", top_view_route)
        print("Route-change attempt to:", destination_route)
        pdi(destination_route)
        from pprint import pprint
        pprint(page.views)

        if destination_route in self.routes:
            if top_view_route != destination_route:
                print(f'Internal Will go to: {top_view_route}')
                page.go(top_view_route)
        else:
            destination_template_route: Optional[str] = find_template_route(destination_route, self.template_routes.keys())
            if destination_template_route in self.template_routes:
                if find_template_route(top_view_route, self.template_routes.keys()) != destination_template_route:
                    print(f'Internal Will go to: {top_view_route}')
                    page.go(top_view_route)
                else:
                    pass
            else:
                page.go(top_view_route)

    def view_pop(self, e: ViewPopEvent):
        print("View pop:", e.view)
        page = e.page
        v: View = e.view
        print("View pop route:", v.route)
        # find route_template
        route_template: Optional[str] = self.get_page_top_view_route_template()
        # find view gen
        view_generator: Optional[Callable] = self.view_gen_by_route_template(route_template)
        is_view_generator_class: bool = False
        if view_generator is None:
            pass
        else:
            if isinstance(view_generator, ViewGenerator):
                is_view_generator_class = True
            else:
                pass

        # run on_destroy
        if is_view_generator_class:
            view_generator._on_destroy()

        # view destroy
        page.views.pop()
        # run on_destroyed
        if is_view_generator_class:
            view_generator._on_destroyed()

        # self.last_routes.pop()
        top_view = page.views[-1]
        top_view_rote = top_view.route
        print(f'Will go to: {top_view_rote}')
        page.go(top_view_rote)


class ViewGenerator:
    def __init__(self, page_worker: PageWorker, access_view: 'SerialAccessViews', route_template: Optional[str], is_direct_route: bool = True, destroy_on_pop: bool = False) -> None:
        self.page_worker: PageWorker = page_worker
        self.access_view: 'SerialAccessViews' = access_view
        self.route_template: Optional[str] = route_template
        self.is_direct_route: bool = is_direct_route
        self.destroy_on_pop: bool = destroy_on_pop
        if is_direct_route:
            access_view.routes[route_template] = self
        else:
            access_view.template_routes[route_template] = self

    def on_create(self) -> View:
        raise NotImplementedError
    
    def on_destroy(self):
        pass
    
    def on_destroyed(self):
        pass
    
    def __call__(self) -> View:
        return self.on_create()
    
    def _on_destroy(self):
        return self.on_destroy()
    
    def _on_destroyed(self):
        return self.on_destroyed()


class RandomAccessViews(SerialAccessViews):
    """New view will be created on `go_to`. View will be destroyed during `view_pop` call. Random access navigation (by browser's `Back` and `Forward` buttuns) is blocked
    """
    def __init__(self, page: Optional[Page] = None):
        super().__init__(page)
        self.present_route_templates: Dict[str, View] = dict()
        self.destroy_on_pop_set_of_route_templates: Set[str] = set()
        self.route_404: Optional[str] = None
        self.route_template_creation_history: List[str] = list()
        self.route_template_creation_history_index_by_route_template: Dict[str, int] = dict()
        self.destination_route_templates_by_source_route_template: Dict[Optional[str], List[str]] = dict()
        self.source_route_template_by_destination_route_template: Dict[Optional[str], Optional[str]] = dict()
        self.destroyed_route_template_redirection: Dict[Optional[str], Optional[str]] = dict()
    
    def go_to(self, route: Optional[str], create_new_if_not_exists: bool = True) -> bool:
        view_generator: Optional[Callable] = None
        route = '/' if route is None else route
        route_template: Optional[str] = self.get_route_template(route)
        if '/' == route:
            pass
        else:
            view_generator: Optional[Callable] = self.view_gen_by_route_template(route_template)
            if view_generator is None:
                if self.route_404 is None:
                    return False
                else:
                    view_generator = self.view_gen_by_route_template(self.route_404)
                    if view_generator is None:
                        return False
                    else:
                        pass
            else:
                pass
        
        source_route_template: Optional[str] = None
        page_views = self.page.views
        if page_views is not None:
            if len(page_views) > 1:
                source_route_template = self.page.views[-1].route
                first_view = self.page.views[0]
                self.page.views.clear()
                self.page.views.append(first_view)
        
        if source_route_template == self.route_404:
            previous_source_route_template: Optional[str] = self.source_route_template_by_destination_route_template.get(source_route_template, None)
            self.destroy_view_by_route_template(source_route_template)
            source_route_template = previous_source_route_template

        if view_generator is None:
            pass
        else:
            if route_template in self.present_route_templates:
                view: View = self.present_route_templates[route_template]
            else:
                if create_new_if_not_exists:
                    pass
                else:
                    if route_template in self.destroyed_route_template_redirection:
                        return self.go_to(self.destroyed_route_template_redirection[route_template], False)
                    else:
                        pass

                view = view_generator()
                self.present_route_templates[route_template] = view
                self.route_template_creation_history.append(route_template)
                route_template_index: int = len(self.route_template_creation_history) - 1
                self.route_template_creation_history_index_by_route_template[route_template] = route_template_index
                if source_route_template not in self.destination_route_templates_by_source_route_template:
                    self.destination_route_templates_by_source_route_template[source_route_template] = list()
                
                self.destination_route_templates_by_source_route_template[source_route_template].append(route_template)
                self.source_route_template_by_destination_route_template[route_template] = source_route_template
            
            if self.page.views is None:
                self.page.views = list()

            self.page.views.append(view)

        self.page.go(route)
        return True

    def route_change(self, e: RouteChangeEvent):
        current_route_template: Optional[str] = self.get_page_top_view_route_template()
        destination_route = e.route
        result: bool = self.go_to(destination_route, False)
        if result:
            pass
        else:
            self.page.go(current_route_template)

    def pop_and_destroy_top_view(self, destroy: bool = True):
        current_route_template: Optional[str] = self.get_page_top_view_route_template()
        if current_route_template is None:
            if destroy:
                self.destroy_view_by_route_template(current_route_template)
        else:
            previous_route_template: Optional[str] = self.source_route_template_by_destination_route_template.get(current_route_template, None)
            if destroy:
                self.destroy_view_by_route_template(current_route_template)

            self.go_to(previous_route_template, False)

    def view_pop(self, e: ViewPopEvent):
        current_route_template: Optional[str] = self.get_page_top_view_route_template()
        return self.pop_and_destroy_top_view((current_route_template == self.route_404) or ((current_route_template is not None) and (current_route_template in self.destroy_on_pop_set_of_route_templates)))
    
    def travers_through_all_route_templae_children(self, route_template: Optional[str], handler: Callable[[int, Optional[str], Optional[str], int], None], on_switched_to_stack_based_implementation: Optional[Callable]=None):
        t = KeyMultiValueTreeTraversal(self.destination_route_templates_by_source_route_template, None, handler, on_switched_to_stack_based_implementation)
        t(route_template)
    
    def get_set_of_all_route_template_children(self, route_template: Optional[str]):
        set_of_all_route_templae_children = set()
        if route_template is None:
            interested_route_templates = {None, '/'}
        else:
            interested_route_templates = set(route_template)
        
        def handler(deep, parent, child, index):
            set_of_all_route_templae_children.add(child)
        
        for interested_route_template in interested_route_templates:
            self.travers_through_all_route_templae_children(interested_route_template, handler)
        
        return interested_route_templates, set_of_all_route_templae_children
    
    def destroy_view_by_route_template(self, route_template: Optional[str]):
        # find view gen
        view_generator: Optional[Callable] = self.view_gen_by_route_template(route_template)
        is_view_generator_class: bool = False
        if view_generator is None:
            pass
        else:
            if isinstance(view_generator, ViewGenerator):
                is_view_generator_class = True
            else:
                pass

        # run on_destroy
        if is_view_generator_class:
            view_generator._on_destroy()
        
        # find parent
        previous_route_template: Optional[str] = self.source_route_template_by_destination_route_template.get(route_template, None)

        # destroy children
        interested_route_templates, set_of_all_route_templae_children = self.get_set_of_all_route_template_children(route_template)
        for route_templae_child in set_of_all_route_templae_children:
            self.destination_route_templates_by_source_route_template.pop(route_templae_child, None)
            self.source_route_template_by_destination_route_template.pop(route_templae_child, None)
            self.present_route_templates.pop(route_templae_child, None)
            self.destroyed_route_template_redirection[route_templae_child] = previous_route_template
        
        # destroy given route_templlate
        for interested_route_template in interested_route_templates:
            self.destination_route_templates_by_source_route_template.pop(interested_route_template, None)
            self.source_route_template_by_destination_route_template.pop(interested_route_template, None)
            self.present_route_templates.pop(interested_route_template, None)
            self.destroyed_route_template_redirection[interested_route_template] = previous_route_template

        # run on_destroyed
        if is_view_generator_class:
            view_generator._on_destroyed()
    
    def destroy_me(self):
        return self.pop_and_destroy_top_view(True)
