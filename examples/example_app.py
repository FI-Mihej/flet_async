from cengal.parallel_execution.coroutines.coro_scheduler import Interface
from cengal.parallel_execution.coroutines.coro_standard_services.sleep import Sleep
from cengal.parallel_execution.coroutines.coro_standard_services.simple_yield import Yield

from flet import Control, Container, IconButton, Page, Row, Column, TextField, icons, Text, colors, Stack, WEB_BROWSER
from flet.control_event import ControlEvent
import flet.alignment
from flet.theme import Theme

from flet_async import async_page_method, app, PageWorker, PageParams
from flet_node import Node
from flet_views_access_management import SerialAccessViews, ViewGenerator, RandomAccessViews


RUN_AS_DESKTOP_APP: bool = True


class CountingPage(PageWorker, RandomAccessViews):
    def __init__(self) -> None:
        super().__init__()
        RandomAccessViews.__init__(self)
        self.views_access_manager: RandomAccessViews = RandomAccessViews(self.page)
        self.title = 'My App Title'
        self.input: TextField = None
        self.input2: TextField = None
        self.output: Text = None
        self.output_size_label: Text = None
        self.output_size_value: Text = None
    
    def init(self, root: Node):
        page = root.item
        page.on_route_change = self.route_change
        page.on_view_pop = self.view_pop
        page.theme_mode = 'light'
        page.title = self.title
        page.vertical_alignment = "top"
        
        with root:
            with root()(Row, alignment='center') as row:
                with row()(Container, width=400, alignment=flet.alignment.center, padding=35) as cont:
                    self.txt_title = cont()(Text, value=self.title, text_align='center', color='orange', size=60).item
                
                self.container_1 = cont.item
            
            with root()(Row, alignment="center") as r:
                with r()(Column, alignment='center') as c:
                    with c()(Container, width=400, alignment=flet.alignment.center) as con:
                        self.input = con()(TextField, label="Input", hint_text="Please enter text here", on_change=self.input_on_change, multiline=True).item
                        self.input2 = con()(TextField, label="Input 2", hint_text="Please enter text here", on_change=self.ainput_on_change, multiline=True).item
                    
                    with c()(Container, width=400, alignment=flet.alignment.center) as con:
                        self.output = con()(Text, selectable=True, text_align='start', expand=False, no_wrap=False, max_lines=None, overflow='visible').item

                    with c()(Container, width=400, alignment=flet.alignment.center) as con:
                        with con()(Row, alignment='center') as r:
                            self.output_size_label = r()(Text, 'Output string size:', weight='bold').item
                            self.output_size_value = r()(Text, '0').item

    def format(self, original: str, settings = None):
        return original.upper()

    @async_page_method
    def input_on_change(self, i: Interface, e: ControlEvent):
        original: str = self.input.value
        result: str = self.format(original)
        result_len: int = len(result)
        self.output.value = result
        self.output_size_value.value = str(result_len)
        i(Sleep, 0.01)  # async call to service. See 'development' folder of `cengal.parallel_execution.coroutines.coro_tool.run_in_loop` module for an examples
        self.update(self.output, self.output_size_value)

    @async_page_method
    async def ainput_on_change(self, i: Interface, e: ControlEvent):
        original: str = self.input2.value
        result: str = self.format(original)
        result_len: int = len(result)
        self.output.value = result
        self.output_size_value.value = str(result_len)
        await i(Sleep, 0.01)  # async call to service. See 'development' folder of `cengal.parallel_execution.coroutines.coro_tool.run_in_loop` module for an examples
        self.update(self.output, self.output_size_value)


def main_browser():
    app(target=PageParams(CountingPage), view=WEB_BROWSER)


def main_desktop():
    app(target=PageParams(CountingPage))


if '__main__' == __name__:
    if RUN_AS_DESKTOP_APP:
        main_desktop()
    else:
        main_browser()
