__all__ = ['async_page_method', 'async_method', 'App', 'PageWorker', 'PageParams', 'app', 'min_sleep', 'Interface', 'CoroID', 'ExplicitWorker', 'Worker']

from functools import partial
import flet
from flet import Page, Event
from cengal.parallel_execution.coroutines.coro_scheduler import CoroScheduler, Interface, CoroID, ExplicitWorker, Worker, CoroWrapperBase, get_interface_for_an_explicit_loop
from cengal.parallel_execution.coroutines.coro_standard_services.put_coro import PutCoro, put_coro_to, put_coro
from cengal.parallel_execution.coroutines.coro_standard_services.sleep import Sleep
from cengal.parallel_execution.coroutines.coro_standard_services.kill_coro import KillCoro
from cengal.parallel_execution.coroutines.coro_standard_services.wait_coro import WaitCoro, WaitCoroRequest, CoroutineNotFoundError, PutSingleCoroParams
from cengal.parallel_execution.coroutines.coro_tools.coro_flow_control import execution_time_limiter, simple_graceful_coro_destroyer
from cengal.code_flow_control.smart_values import ValueExistence
import flet_mock
from threading import Thread
from typing import Callable, Dict, Hashable, Optional, Set, Type, Union
from time import sleep
from cengal.time_management.sleep_tools import try_sleep, get_usable_min_sleep_interval
from uuid import uuid4
from flet_node import Node


def min_sleep():
    try_sleep(get_usable_min_sleep_interval(), sleep)


FLET_THREAD_FINISHED_EVENT_BUS_EVENT_ID: str = str(uuid4())


_coroutines_per_session: Dict[Hashable, Set[CoroID]] = dict()


async def coro_putter(i: Interface, session_id: Hashable, coro_worker: Union[ExplicitWorker, Worker], *args, **kwargs):
    coro_id = await i(PutCoro, coro_worker, *args, **kwargs)
    if session_id not in _coroutines_per_session:
        _coroutines_per_session[session_id] = set()
    
    _coroutines_per_session[session_id].add(coro_id)


def put_session_coro(backup_scheduler: Optional[CoroScheduler], session_id: Hashable, coro_worker: Union[ExplicitWorker, Worker], *args, **kwargs):
    put_coro_to(get_interface_for_an_explicit_loop(backup_scheduler), coro_putter, session_id, coro_worker, *args, **kwargs)


def async_page_method(async_method: Worker):
    def resulting_method(self, *args, **kwargs):
        par_method = partial(async_method, self)
        put_session_coro(self.cs_holder.value, self.page._session_id, par_method, *args, **kwargs)
    
    return resulting_method


def async_method(async_method: Worker):
    def resulting_method(self, *args, **kwargs):
        par_method = partial(async_method, self)
        put_coro_to(get_interface_for_an_explicit_loop(self.cs_holder.value), par_method, *args, **kwargs)
    
    return resulting_method


class PageParams:
    def __init__(self, page_worker_class: Type['PageWorker'], *args, **kwargs) -> None:
        self.page_worker_class: Type['PageWorker'] = page_worker_class
        self.args = args
        self.kwargs = kwargs


class PageDestroyed(Exception):
    pass


class App:
    def __init__(self, page_params: PageParams) -> None:
        self._page_params: PageParams = page_params
        self._sessions: Dict[Hashable, 'PageWorker'] = dict()
        self._original_on_event: Callable = None
        self.cs_holder: ValueExistence = ValueExistence()
        self.window_pid_holder: ValueExistence = ValueExistence()
        self.destroyed: bool = False
        self.ah = self.async_handler

    def async_handler(self, coro_worker: Union[ExplicitWorker, Worker], *args, **kwargs):
        def resulting_func(*secondary_args, **secondary_kwargs):
            resulting_args = (self,) + args + secondary_args
            resulting_kwargs = dict(kwargs)
            resulting_kwargs.update(secondary_kwargs)
            put_coro_to(get_interface_for_an_explicit_loop(self.cs_holder.value), coro_worker, *resulting_args, **resulting_kwargs)
        
        return resulting_func
    
    def put_coro(self, coro_worker: Union[ExplicitWorker, Worker], *args, **kwargs):
        put_coro_to(get_interface_for_an_explicit_loop(self.cs_holder.value), coro_worker, *args, **kwargs)
    
    def destroy(self):
        self.destroyed = True
    
    def __call__(self, page: Page):
        page_worker: PageWorker = self._page_params.page_worker_class(*self._page_params.args, **self._page_params.kwargs)
        page_worker.bind(self)
        self._sessions[page._session_id] = page_worker
        return page_worker(page)
    
    def on_event(self, conn, e):
        result = None
        session_id = e.sessionID
        if session_id in self._sessions:
            need_to_destroy = False
            if e.eventTarget == "page" and (e.eventName in {"close", "disconnect"}):
                print("Async session closed:", session_id)
                need_to_destroy = True
                self._sessions[session_id].destroyed = True
            
            result = self._original_on_event(conn, e)
            if need_to_destroy:
                del self._sessions[session_id]
        
        return result


class PageWorker:
    def __init__(self) -> None:
        self._destroyed: bool = False
        self._destroy_finished: bool = False
        self.app: Optional[App] = None
        self.page: Page = None
        self.ah = self.async_handler
        self._page_update_requests_num: int = 0
        self._controls_should_be_updated: Set = set()
        self.sa = self.set_attr
    
    def set_attr(self, name: str, value):
        setattr(self, name, value)
        return value
    
    def bind(self, app: App):
        self.app = app

    def async_handler(self, coro_worker: Union[ExplicitWorker, Worker], *args, **kwargs):
        def resulting_func(*secondary_args, **secondary_kwargs):
            resulting_args = (self,) + args + secondary_args
            resulting_kwargs = dict(kwargs)
            resulting_kwargs.update(secondary_kwargs)
            put_session_coro(self.cs_holder.value, self.page._session_id, coro_worker, *resulting_args, **resulting_kwargs)
        
        return resulting_func
    
    def put_coro(self, coro_worker: Union[ExplicitWorker, Worker], *args, **kwargs):
        put_session_coro(self.cs_holder.value, self.page._session_id, coro_worker, *args, **kwargs)
    
    @property
    def destroyed(self):
        return self.app.destroyed or self._destroyed
    
    @destroyed.setter
    def destroyed(self, destroyed):
        self._destroyed = destroyed
        if destroyed:
            self._on_destroyed()
    
    @property
    def cs_holder(self):
        return self.app.cs_holder
    
    def _on_destroyed(self):
        def coro_destroyer(i: Interface, self: 'PageWorker'):
            session_id: Hashable = self.page._session_id
            session_coroutines = _coroutines_per_session.get(session_id, set())
            # waiting_time_limit: float = 0.05
            # i(WaitCoro, WaitCoroRequest().put_list([PutSingleCoroParams(execution_time_limiter, session_coro, waiting_time_limit) for session_coro in session_coroutines]))
            waiting_time_limit: float = 0.1
            i(Sleep, waiting_time_limit)
            i(WaitCoro, WaitCoroRequest().put_list([PutSingleCoroParams(simple_graceful_coro_destroyer, waiting_time_limit, session_coro, PageDestroyed) for session_coro in session_coroutines]))
            self._destroy_finished = True
        
        self.app.put_coro(coro_destroyer, self)
        while not self._destroy_finished:
            min_sleep()
        
        self.on_destroyed()
    
    def on_destroyed(self):
        pass
    
    def _page_updater(self, i: Interface):
        while not self.destroyed:
            if self._page_update_requests_num:
                self._page_update_requests_num = 0
                self.page.update()

            i(Sleep, 0.1)
    
    def _controls_updater(self, i: Interface):
        while not self.destroyed:
            if self._controls_should_be_updated:
                items_should_be_updated_bak = self._controls_should_be_updated
                self._controls_should_be_updated = type(self._controls_should_be_updated)()
                self.page.update(*tuple(items_should_be_updated_bak))

            i(Sleep, 1 / 60)
    
    def update(self, *controls):
        if controls:
            self._controls_should_be_updated.update(controls)
        else:
            self._page_update_requests_num += 1
    
    def __call__(self, page: Page):
        self.page = page
        while not self.cs_holder.existence:
            min_sleep()
        
        self.put_coro(self._page_updater)
        self.put_coro(self._controls_updater)
        
        root: Node = Node(page=page)
        result = self.init(root)
        root.construct()
        return result

    def init(self, page: Page):
        raise NotImplementedError


def flet_thread(page_worker: Callable, window_pid_holder: ValueExistence):
    flet_mock.app(target=page_worker, window_pid_holder=window_pid_holder)


def cs_thread_worker(cs_holder: ValueExistence, flet_thread_alive: ValueExistence):
    def coro(i: Interface, flet_thread_alive: ValueExistence):
        while flet_thread_alive.value:
            i(Sleep, 0.1)

    cs = CoroScheduler()
    cs.put_coro(coro, flet_thread_alive)
    cs_holder.value = cs
    cs.loop()


def app(
    name="",
    host=None,
    port=0,
    target=None,
    permissions=None,
    view: flet.AppViewer = flet.FLET_APP,
    assets_dir=None,
    web_renderer="canvaskit",
    route_url_strategy="hash",
    ):
    if isinstance(target, PageParams):
        application: App = App(target)
        flet_thread_alive: ValueExistence = ValueExistence(True, True)
        cs_thread = Thread(target=cs_thread_worker, args=(application.cs_holder, flet_thread_alive, ))
        cs_thread.start()
        flet_mock.app(name, host, port, application, permissions, view, assets_dir, web_renderer, route_url_strategy, application.window_pid_holder)
        application.destroy()
        flet_thread_alive.value = False
        cs_thread.join()
    else:
        flet.app(name, host, port, target, permissions, view, assets_dir, web_renderer, route_url_strategy)
