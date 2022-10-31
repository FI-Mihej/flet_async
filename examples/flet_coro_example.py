from flet import Control, Container, IconButton, Page, Row, Column, TextField, icons, Text, colors, Stack
from flet.control_event import ControlEvent
from cengal.parallel_execution.coroutines.coro_scheduler import Interface
from cengal.parallel_execution.coroutines.coro_standard_services.sleep import Sleep
from cengal.parallel_execution.coroutines.coro_standard_services.simple_yield import Yield
from flet_async import async_page_method, app, PageWorker, PageParams
from flet_node import Node
from flet.theme import Theme


class CountingPage(PageWorker):
    def __init__(self) -> None:
        super().__init__()
        self.title = 'CountingPage'

        self.container_1: Control = None
        self.txt_number: Control = None
        self.txt_numbers: Control = None

        self.numbers: int = 0

        self.minuses_allowed: bool = False
        self.pluses_allowed: bool = False

    @async_page_method
    def minus_click(self, i: Interface, e):
        i(Sleep, 2)
        self.txt_number.value = int(self.txt_number.value) - 1
        self.update()

    @async_page_method
    async def plus_click(self, i: Interface, e):
        await i(Sleep, 1)
        self.txt_number.value = int(self.txt_number.value) + 1
        self.update(self.txt_number)

    def coro_minuses(self, i: Interface):
        while not self.destroyed:
            if self.minuses_allowed:
                self.numbers = self.txt_numbers.value = int(self.txt_numbers.value) - 1
                self.update(self.txt_numbers)
            
            i(Sleep, 0.02)

    def minuses_click(self, e):
        self.minuses_allowed = True
        self.pluses_allowed = False

    def init(self, root: Node):
        page = root.item
        page.theme_mode = 'light'

        page.title = self.title
        page.vertical_alignment = "top"
        
        self.put_coro(self.coro_minuses)

        def coro_pluses_fast(i: Interface, self: 'CountingPage'):
            while not self.destroyed:
                if self.pluses_allowed:
                    self.numbers += 1
                    i(Yield)
                else:
                    i(Sleep, 0.1)

        def coro_pluses(i: Interface, self: 'CountingPage'):
            while not self.destroyed:
                if self.pluses_allowed:
                    self.txt_numbers.value = self.numbers
                    self.update(self.txt_numbers)
                
                i(Sleep, 0.01)
        
        self.put_coro(coro_pluses_fast, self)
        self.put_coro(coro_pluses, self)

        with root:
            with root()(Column, alignment='center') as col:
                with col()(Row, alignment='center') as row:
                    with row()(Container, padding=35) as cont:
                        self.txt_title = cont()(Text, value=self.title, text_align='center', color='orange', size=60).item
                    
                    self.container_1 = cont.item
            
            with root()(Row, alignment="center") as row:
                row()(IconButton, icons.REMOVE, on_click=self.minus_click)
                self.txt_number = row()(TextField, value="0", text_align="right", width=100).item
                row()(IconButton, icons.ADD, on_click=self.plus_click)
            
            with root()(Row, alignment="center") as row:
                row()(IconButton, icons.REMOVE_CIRCLE, on_click=self.minuses_click)
                self.txt_numbers = row()(TextField, value=str(self.numbers), text_align="right", width=100).item
                def pluses_click(i: Interface, self: CountingPage, e: ControlEvent):
                    self.pluses_allowed = True
                    self.minuses_allowed = False
                
                row()(IconButton, icons.ADD_CIRCLE, on_click=self.ah(pluses_click))


def main():
    app(target=PageParams(CountingPage))


if '__main__' == __name__:
    main()
