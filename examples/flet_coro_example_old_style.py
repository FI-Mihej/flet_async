from flet import IconButton, Page, Row, TextField, icons, Control
from cengal.parallel_execution.coroutines.coro_scheduler import Interface
from cengal.parallel_execution.coroutines.coro_standard_services.sleep import Sleep
from flet_async import async_page_method, app, PageWorker, PageParams
from flet_node import Node


class CountingPage(PageWorker):
    def __init__(self) -> None:
        super().__init__()
        self.minuses_allowed: bool = False
        self.pluses_allowed: bool = False
        self.txt_number: Control = None
        self.txt_numbers: Control = None

    @async_page_method
    def minus_click(self, i: Interface, e):
        i(Sleep, 2)
        self.txt_number.value = int(self.txt_number.value) - 1
        # self.page.update()
        self.update()

    @async_page_method
    async def plus_click(self, i: Interface, e):
        await i(Sleep, 1)
        self.txt_number.value = int(self.txt_number.value) + 1
        # self.page.update()
        self.update(self.txt_number)

    def coro_minuses(self, i: Interface):
        while not self.destroyed:
            if self.minuses_allowed:
                self.txt_numbers.value = int(self.txt_numbers.value) - 1
                # self.page.update()
                # self.update()
                self.update(self.txt_numbers)
            
            i(Sleep, 0.02)

    def minuses_click(self, e):
        self.minuses_allowed = True
        self.pluses_allowed = False

    def pluses_click(self, e):
        self.pluses_allowed = True
        self.minuses_allowed = False

    def init(self, root: Node):
        page = root.item
        page.title = "Flet counter example"
        page.vertical_alignment = "center"
        
        self.put_coro(self.coro_minuses)

        def coro_pluses(i: Interface, self: 'CountingPage'):
            while not self.destroyed:
                if self.pluses_allowed:
                    self.txt_numbers.value = int(self.txt_numbers.value) + 1
                    # self.page.update()
                    self.update(self.txt_numbers)
                
                i(Sleep, 0.001)
        
        self.put_coro(coro_pluses, self)

        page.add(
            Row(
                [
                    IconButton(icons.REMOVE, on_click=self.minus_click),
                    self.sa('txt_number', TextField(value="0", text_align="right", width=100)),
                    IconButton(icons.ADD, on_click=self.plus_click),
                ],
                alignment='center'
            ),
            Row(
                [
                    IconButton(icons.REMOVE_CIRCLE, on_click=self.minuses_click),
                    self.sa('txt_numbers', TextField(value="0", text_align="right", width=100)),
                    IconButton(icons.ADD_CIRCLE, on_click=self.pluses_click),
                ],
                alignment="center",
            )
        )


def main():
    app(target=PageParams(CountingPage))


if '__main__' == __name__:
    main()
